# Drift

Drift is a small Python SDK for the Drift dataset API. It gives you a simple way to discover datasets, inspect routes and segments, and download segment files from the backing object store.

The SDK is intentionally thin: it talks to the HTTP API for metadata and returns Python objects you can use in your own training or evaluation pipelines.

## Installation

```bash
pip install drift
```

## Prerequisites

This SDK talks to the hosted API at:

```text
https://drift-api-production-1d47.up.railway.app
```

You do not need to run the backend locally to try the examples below.

## Quick start

```python
import drift

# Load dataset metadata
Dataset = drift.load("jordy-v0")
print(Dataset.id)
print(Dataset.routes_count)
print(Dataset.segments_count)
```

## Explore routes and segments

```python
import drift

# Load the dataset
Dataset = drift.load("jordy-v0")
print(f"Dataset: {Dataset.id}")

# List routes for the dataset
routes = drift.client.DriftClient(base_url="https://drift-api-production-1d47.up.railway.app").list_routes("jordy-v0")
print("First route:", routes[0].route_id)

# Inspect a single route
route = drift.route(routes[0].route_id, base_url="https://drift-api-production-1d47.up.railway.app")
print(route.num_segments)
print(route.segments[:3])
```

## What files are available per segment?

Each segment response includes a `files` dictionary. The current API returns presigned URLs for the files that are present for that segment. The available names are the aliases that the service exposes, for example:

- `qcamera`
- `qlog`
- `rlog`
- `ecamera`
- `fcamera`
- `navigation`

Example:

```python
import drift

segment = drift.segment("<segment-id>", base_url="https://drift-api-production-1d47.up.railway.app")
print(segment.segment_id)
print(segment.files)
print(segment.download_url)
```

## Download a segment file

```python
import drift

segment = drift.segment("<segment-id>", base_url="https://drift-api-production-1d47.up.railway.app")
segment.download("downloads/segment.bin")
print("Downloaded to downloads/segment.bin")
```

## End-to-end workflow example

This is the simplest end-to-end pattern for a metadata-driven pipeline:

```python
import os
import drift

BASE_URL = "https://drift-api-production-1d47.up.railway.app"
DATASET_ID = "jordy-v0"
OUTPUT_DIR = "downloads"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1) Load dataset metadata
Dataset = drift.load(DATASET_ID, base_url=BASE_URL)
print(f"Loaded {Dataset.id} with {Dataset.routes_count} routes and {Dataset.segments_count} segments")

# 2) List routes
client = drift.client.DriftClient(base_url=BASE_URL)
routes = client.list_routes(DATASET_ID)

# 3) Inspect the first route and fetch one segment
first_route = routes[0]
print(f"Route {first_route.route_id} has {first_route.num_segments} segments")

first_segment_ref = first_route.segments[0]
segment = client.get_segment(first_segment_ref["segment_id"])
print("Segment files:", segment.files)

# 4) Download the primary file if available
if segment.download_url:
    target = os.path.join(OUTPUT_DIR, f"{segment.segment_id}.bin")
    segment.download(target)
    print(f"Downloaded {target}")
```

## A simple training loop pattern

The SDK does not provide a full training abstraction. Instead, it gives you metadata and download links so you can build your own loop. A minimal example looks like this:

```python
import os
import drift

BASE_URL = "https://drift-api-production-1d47.up.railway.app"
DATASET_ID = "jordy-v0"
OUTPUT_DIR = "training-cache"

os.makedirs(OUTPUT_DIR, exist_ok=True)
client = drift.client.DriftClient(base_url=BASE_URL)
routes = client.list_routes(DATASET_ID)

for route in routes[:3]:
    for segment_ref in route.segments[:2]:
        segment = client.get_segment(segment_ref["segment_id"])
        if segment.download_url:
            target = os.path.join(OUTPUT_DIR, f"{segment.segment_id}.bin")
            segment.download(target)
            print(f"Prepared {target}")
```

This pattern is intentionally simple: fetch metadata, decide which segments to use, download the files you need, and then feed them into your preferred training stack.

## PyTorch

```python
from drift.torch import DriftDataset

loader = DriftDataset("jordy-v0", base_url="https://drift-api-production-1d47.up.railway.app")
sample = loader[0]
print(sample)
```

## TensorFlow / Keras

```python
from drift.tensorflow import DriftDataset

dataset = DriftDataset("jordy-v0", base_url="https://drift-api-production-1d47.up.railway.app")
for item in dataset:
    print(item)
```

## Release notes

### 0.1.1
- polished package metadata and documentation
- added release workflow and repository scaffolding
- improved SDK examples for downloads and framework integrations
