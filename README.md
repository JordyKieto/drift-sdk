# Drift

Drift is an open-source Python SDK for working with real-world driving data and
training end-to-end driving models.

The goal is to make embodied driving research easier to start. Instead of
spending days wiring up dataset parsers, route metadata, and segment downloads,
you can install one package, load a dataset, and begin building a training
pipeline from real driving data.

Today, Drift includes a complete real-world driving dataset with:

- 15.08 hours of human driving
- 933 synchronized driving segments
- 68 routes
- 74.9 GiB of synchronized camera, vehicle telemetry, and navigation data

Drift exposes datasets, routes, and segments as simple Python objects while
hiding the storage details underneath. It is best understood as a clean access
layer over driving data and artifacts, rather than a fully prepared ML dataset.

## Quickstart

For a one-click start, open the example notebook in Google Colab:

- [drift_train_driving.ipynb](https://github.com/JordyKieto/drift-sdk/blob/main/examples/drift_train_driving.ipynb)

It is a simple end-to-end quickstart for loading the dataset, downloading
segments, training a driving policy, and exporting a model. The notebook is set
up to work well on an NVIDIA A100.

Drift aims to do for end-to-end driving data what Hugging Face Datasets did for
NLP datasets: provide a simple, reproducible interface that makes
experimentation more accessible.

The intended SDK flow is:

1. Load dataset metadata.
2. List routes.
3. Inspect route segment references.
4. Resolve each segment.
5. Download the specific files your pipeline needs.

## Installation

```bash
pip install drift-sdk

import drift
```

## API endpoint

The hosted API used by the examples below is:

```text
https://drift-api-production-1d47.up.railway.app
```

You do not need to run the backend locally to try the examples.

## Core objects

The SDK exposes three data objects plus one client:

- `drift.client.DriftClient`
- `drift.dataset.Dataset`
- `drift.route.Route`
- `drift.segment.Segment`

The top-level convenience helpers are:

- `drift.load(dataset_id, base_url=None) -> Dataset`
- `drift.route(route_id, base_url=None) -> Route`
- `drift.segment(segment_id, base_url=None) -> Segment`

## Client methods

`DriftClient` is the full method-level API:

```python
from drift.client import DriftClient

client = DriftClient(base_url="https://drift-api-production-1d47.up.railway.app")

dataset = client.load_dataset("jordy-v0")
routes = client.list_routes("jordy-v0")
route = client.get_route(routes[0].route_id)
segment = client.get_segment(route.segments[0]["segment_id"])

client.close()
```

Available methods:

- `load_dataset(dataset_id)` returns a `Dataset`
- `list_routes(dataset_id)` returns `list[Route]`
- `get_route(route_id)` returns a `Route`
- `get_segment(segment_id)` returns a `Segment`
- `close()` closes the underlying HTTP client

## Dataset methods

Use `drift.load(...)` or `DriftClient.load_dataset(...)` when you need dataset
summary metadata.

```python
import drift

dataset = drift.load("jordy-v0")
print(dataset.id)
print(dataset.routes_count)
print(dataset.segments_count)
```

`Dataset` fields:

- `id`
- `routes_count`
- `segments_count`

## Route methods

Use `drift.route(...)` or `DriftClient.get_route(...)` when you need the segment
references for a route.

```python
import drift

client = drift.client.DriftClient()
routes = client.list_routes("jordy-v0")

route = client.get_route(routes[0].route_id)
print(route.route_id)
print(route.num_segments)
print(route.dataset)
print(route.segments[:3])

client.close()
```

`Route` fields:

- `route_id`
- `num_segments`
- `created_at`
- `dataset`
- `segments`

Each `route.segments` item is currently a small reference dictionary such as:

```python
{"segment_id": "...", "segment_index": 0}
```

## Segment methods

Use `drift.segment(...)` or `DriftClient.get_segment(...)` when you need the
downloadable files for one segment.

```python
import drift

segment = drift.segment("<segment-id>")
print(segment.segment_id)
print(segment.route_id)
print(segment.segment_index)
print(segment.files)
print(segment.download_url)
```

`Segment` fields:

- `segment_id`
- `route_id`
- `segment_index`
- `files`
- `download_url`

`segment.files` is a dictionary of alias to presigned URL. Current aliases may
include:

- `qcamera`
- `qlog`
- `rlog`
- `ecamera`
- `fcamera`
- `navigation`

## Downloading files

`Segment.download(destination=None, chunk_size=8192)` downloads the segment's
primary file. Today that is `download_url` if present, otherwise `files["fcamera"]`.

```python
import os
import drift

os.makedirs("downloads", exist_ok=True)

segment = drift.segment("<segment-id>")
path = segment.download("downloads/segment.bin")
print(path)
```

Important limitation:

- `Segment.download(...)` downloads one file per call.
- It does not download every file listed in `segment.files`.
- If your pipeline needs `navigation`, `qlog`, or another alias specifically,
  fetch the URL from `segment.files` and download it yourself.

## End-to-end metadata workflow

This is the real SDK usage pattern that a training pipeline should start from.

```python
from pathlib import Path
import drift

BASE_URL = "https://drift-api-production-1d47.up.railway.app"
DATASET_ID = "jordy-v0"
CACHE_DIR = Path("training-cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

client = drift.client.DriftClient(base_url=BASE_URL)

dataset = client.load_dataset(DATASET_ID)
print(f"dataset={dataset.id} routes={dataset.routes_count} segments={dataset.segments_count}")

routes = client.list_routes(DATASET_ID)
segment_ids = [
    segment_ref["segment_id"]
    for route in routes
    for segment_ref in route.segments
]

print(f"resolved {len(segment_ids)} segment references")

for segment_id in segment_ids[:8]:
    segment = client.get_segment(segment_id)
    target = CACHE_DIR / f"{segment.segment_id}.bin"
    segment.download(str(target))
    print(f"downloaded {target}")

client.close()
```

## Training-pipeline pattern

The SDK does not expose `download_dataset(...)`, and it does not materialize a
ready-made parquet or CSV training table. A trainer should explicitly:

1. Query dataset and route metadata.
2. Expand route segment references into segment IDs.
3. Download the needed segment files.
4. Parse those raw artifacts into model-ready tensors or tables.

This is a simplified version of the same control flow used by `train_driving.py`:

```python
from pathlib import Path
import drift

BASE_URL = "https://drift-api-production-1d47.up.railway.app"
DATASET_ID = "jordy-v0"
CACHE_DIR = Path(".cache/drift-data")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

client = drift.client.DriftClient(base_url=BASE_URL)
routes = client.list_routes(DATASET_ID)

segment_ids = []
for route in routes:
    for segment_ref in route.segments:
        segment_ids.append(segment_ref["segment_id"])

for segment_id in segment_ids[:32]:
    segment = client.get_segment(segment_id)

    if "navigation" in segment.files:
        print("navigation url:", segment.files["navigation"])

    target = CACHE_DIR / f"{segment.segment_id}.bin"
    segment.download(str(target))

client.close()
```

If your trainer expects `.parquet`, `.csv`, `.jsonl`, or image tensors, you
still need a conversion step after download.

## PyTorch example

`drift.torch.DriftDataset` is a metadata dataset. It does not decode frames or
controls for you. It resolves segment metadata lazily and can optionally
download one primary file per sample.

```python
from torch.utils.data import DataLoader
from drift.torch import DriftDataset

dataset = DriftDataset(
    dataset_id="jordy-v0",
    base_url="https://drift-api-production-1d47.up.railway.app",
    download_dir=".cache/drift-torch",
)

print("segments:", len(dataset))

sample = dataset[0]
print(sample["segment_id"])
print(sample["files"])
print(sample.get("download_path"))

loader = DataLoader(dataset, batch_size=4, shuffle=False)
batch = next(iter(loader))
print(batch["segment_id"])
```

The payload returned by each item is shaped for a downstream parser:

- `segment_id`
- `route_id`
- `segment_index`
- `files`
- `download_url`
- `download_path` when `download_dir` is set

## TensorFlow / Keras example

`drift.tensorflow.DriftDataset` is also metadata-first. Iterate over it directly
or convert it into a `tf.data.Dataset` if you want a Keras-compatible input
stream.

```python
import tensorflow as tf
from drift.tensorflow import DriftDataset

segments = DriftDataset(
    dataset_id="jordy-v0",
    base_url="https://drift-api-production-1d47.up.railway.app",
)

for item in segments:
    print(item["segment_id"], item["files"])
    break

keras_dataset = segments.to_keras_dataset()
keras_dataset = keras_dataset.take(4)

for item in keras_dataset:
    tf.print(item["segment_id"], item["download_url"])
```

This is useful when your actual model input pipeline lives in a later mapping
stage that downloads or decodes the referenced artifacts.

## Common mistake

This is wrong:

```python
client.load_dataset("jordy-v0")
```

That only returns summary metadata. It does not download data.

This is the correct conceptual flow:

```python
dataset = client.load_dataset("jordy-v0")
routes = client.list_routes(dataset.id)
route = client.get_route(routes[0].route_id)
segment = client.get_segment(route.segments[0]["segment_id"])
segment.download("downloads/example.bin")
```

## Release notes

### 0.1.1
- polished package metadata and documentation
- added release workflow and repository scaffolding
- improved SDK examples for downloads and framework integrations
