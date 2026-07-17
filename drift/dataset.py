from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Dataset:
    id: str
    routes_count: int
    segments_count: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Dataset":
        return cls(
            id=str(payload["id"]),
            routes_count=int(payload.get("routes", 0)),
            segments_count=int(payload.get("segments", 0)),
        )
