from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .dataset import Dataset
from .route import Route
from .segment import Segment


@dataclass
class DriftClient:
    base_url: str = "https://drift-api-production-1d47.up.railway.app"
    timeout: float = 15.0

    def __post_init__(self) -> None:
        self._client = httpx.Client(timeout=self.timeout, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str) -> dict[str, Any]:
        response = self._client.get(f"{self.base_url.rstrip('/')}{path}")
        response.raise_for_status()
        return response.json()

    def load_dataset(self, dataset_id: str) -> Dataset:
        payload = self._get(f"/datasets/{dataset_id}")
        return Dataset.from_payload(payload)

    def list_routes(self, dataset_id: str) -> list[Route]:
        payload = self._get(f"/datasets/{dataset_id}/routes")
        return [Route.from_payload(item) for item in payload]

    def get_route(self, route_id: str) -> Route:
        payload = self._get(f"/routes/{route_id}")
        return Route.from_payload(payload)

    def get_segment(self, segment_id: str) -> Segment:
        payload = self._get(f"/segments/{segment_id}")
        return Segment.from_payload(payload)


def load(dataset_id: str, base_url: str | None = None) -> Dataset:
    client = DriftClient(base_url=base_url or "https://drift-api-production-1d47.up.railway.app")
    try:
        return client.load_dataset(dataset_id)
    finally:
        client.close()


def route(route_id: str, base_url: str | None = None) -> Route:
    client = DriftClient(base_url=base_url or "https://drift-api-production-1d47.up.railway.app")
    try:
        return client.get_route(route_id)
    finally:
        client.close()


def segment(segment_id: str, base_url: str | None = None) -> Segment:
    client = DriftClient(base_url=base_url or "https://drift-api-production-1d47.up.railway.app")
    try:
        return client.get_segment(segment_id)
    finally:
        client.close()
