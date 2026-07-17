from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Route:
    route_id: str
    num_segments: int
    created_at: str | None
    dataset: str
    segments: list[dict[str, Any]]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Route":
        return cls(
            route_id=str(payload["route_id"]),
            num_segments=int(payload.get("num_segments", 0)),
            created_at=payload.get("created_at"),
            dataset=str(payload.get("dataset", "")),
            segments=list(payload.get("segments", [])),
        )
