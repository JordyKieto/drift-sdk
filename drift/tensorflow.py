from __future__ import annotations

from typing import Any

from .client import DriftClient


class DriftDataset:
    def __init__(self, dataset_id: str, route_id: str | None = None, base_url: str | None = None) -> None:
        self.dataset_id = dataset_id
        self.route_id = route_id
        self.client = DriftClient(base_url=base_url or "https://drift-api-production-1d47.up.railway.app")

        if route_id:
            route = self.client.get_route(route_id)
            self._segments = route.segments
        else:
            routes = self.client.list_routes(dataset_id)
            self._segments = [
                segment
                for route in routes
                for segment in route.segments
            ]

    def __iter__(self):
        for segment_ref in self._segments:
            segment = self.client.get_segment(segment_ref["segment_id"])
            yield {
                "segment_id": segment.segment_id,
                "route_id": segment.route_id,
                "segment_index": segment.segment_index,
                "files": segment.files,
                "download_url": segment.download_url,
            }

    def to_keras_dataset(self):
        try:
            import tensorflow as tf
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("tensorflow is required for to_keras_dataset") from exc

        def generator():
            for item in self:
                yield item

        return tf.data.Dataset.from_generator(
            generator,
            output_types={
                "segment_id": tf.string,
                "route_id": tf.string,
                "segment_index": tf.int32,
                "files": tf.string,
                "download_url": tf.string,
            },
        )
