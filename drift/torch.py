from __future__ import annotations

from pathlib import Path
from typing import Any

from .client import DriftClient

try:
    from torch.utils.data import Dataset as TorchDataset
except ImportError:  # pragma: no cover - optional dependency
    class TorchDataset:  # type: ignore[override]
        pass


class DriftDataset(TorchDataset):
    def __init__(
        self,
        dataset_id: str,
        route_id: str | None = None,
        base_url: str | None = None,
        download_dir: str | None = None,
    ) -> None:
        self.dataset_id = dataset_id
        self.route_id = route_id
        self.client = DriftClient(base_url=base_url or "https://drift-api-production-1d47.up.railway.app")
        self.download_dir = Path(download_dir) if download_dir else None

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

    def __len__(self) -> int:
        return len(self._segments)

    def __getitem__(self, index: int) -> dict[str, Any]:
        segment_ref = self._segments[index]
        segment = self.client.get_segment(segment_ref["segment_id"])
        payload: dict[str, Any] = {
            "segment_id": segment.segment_id,
            "route_id": segment.route_id,
            "segment_index": segment.segment_index,
            "files": segment.files,
            "download_url": segment.download_url,
        }
        if self.download_dir is not None:
            file_path = segment.download(destination=str(self.download_dir / segment.segment_id))
            payload["download_path"] = file_path
        return payload
