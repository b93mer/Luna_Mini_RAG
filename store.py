"""JSON chunk store for the Luna retrieval pipeline.

Architecture role: persist section chunks, TF-IDF model, and provenance at
metadata/chunks.json — the only store file provided in this repo.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
STORE_PATH = REPO_ROOT / "metadata" / "chunks.json"


@dataclass
class Chunk:
    """One stored retrieval unit."""

    chunk_id: str
    doc_id: str
    source_path: str
    section_id: str
    heading: str
    kind: str
    text: str
    start_line: int
    end_line: int
    embedding: list[float]
    provenance: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Chunk":
        return cls(
            chunk_id=payload["chunk_id"],
            doc_id=payload["doc_id"],
            source_path=payload["source_path"],
            section_id=payload["section_id"],
            heading=payload["heading"],
            kind=payload.get("kind", "section"),
            text=payload["text"],
            start_line=int(payload["start_line"]),
            end_line=int(payload["end_line"]),
            embedding=list(payload.get("embedding") or []),
            provenance=dict(payload.get("provenance") or {}),
        )


@dataclass
class ChunkStore:
    version: int
    built_at: str
    vocab: dict[str, int]
    idf: list[float]
    chunks: list[Chunk]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "built_at": self.built_at,
            "vocab": self.vocab,
            "idf": self.idf,
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }

    def get_by_section_id(self, section_id: str) -> Chunk | None:
        for chunk in self.chunks:
            if chunk.section_id == section_id:
                return chunk
        return None


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    """NOTE (added helper): write JSON via a temp file so a crash cannot
    leave metadata/chunks.json half-written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def save_store(store: ChunkStore, path: Path = STORE_PATH) -> None:
    atomic_write(path, store.to_dict())


def load_store(path: Path = STORE_PATH) -> ChunkStore | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    payload = json.loads(raw)
    chunks = [Chunk.from_dict(item) for item in payload.get("chunks") or []]
    if not chunks:
        return None
    return ChunkStore(
        version=int(payload.get("version") or 1),
        built_at=str(payload.get("built_at") or ""),
        vocab=dict(payload.get("vocab") or {}),
        idf=list(payload.get("idf") or []),
        chunks=chunks,
    )


def build_store(vocab: dict[str, int], idf: list[float], chunks: list[Chunk]) -> ChunkStore:
    return ChunkStore(
        version=1,
        built_at=datetime.now(timezone.utc).isoformat(),
        vocab=vocab,
        idf=idf,
        chunks=chunks,
    )
