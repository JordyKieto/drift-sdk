from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass
class Segment:
    segment_id: str
    route_id: str
    segment_index: int
    files: dict[str, str]
    download_url: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Segment":
        return cls(
            segment_id=str(payload["segment_id"]),
            route_id=str(payload.get("route_id", "")),
            segment_index=int(payload.get("segment_index", 0)),
            files=dict(payload.get("files", {})),
            download_url=payload.get("download_url"),
        )

    def download(self, destination: str | None = None, chunk_size: int = 8192) -> str:
        url = self.download_url or self.files.get("fcamera")
        if not url:
            raise ValueError("No download URL available for this segment")

        target = Path(destination) if destination else Path(f"{self.segment_id}.bin")
        target.parent.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            with target.open("wb") as handle:
                for chunk in response.iter_bytes(chunk_size):
                    if chunk:
                        handle.write(chunk)

        return str(target.resolve())
