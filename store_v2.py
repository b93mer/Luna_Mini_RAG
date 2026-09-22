"""Parallel store path for the chunker-v2 index (metadata/chunks_v2.json).

Why a separate module instead of extending store.py: store.py is part of
the frozen v1 pipeline (tag v0.1.0-poc-baseline) and must remain
byte-identical so the earlier alias-boost ablation stays reproducible.
Adding STORE_PATH_V2 to store.py would edit a frozen file, so the v2 path
and its load/save helpers live here, reusing store.py's Chunk /
ChunkStore / atomic_write unchanged.

Reason for the parallel path overall: v1 baseline must remain
byte-identical for reproducibility of the earlier ablation.
"""

from __future__ import annotations

import json
from pathlib import Path

from store import REPO_ROOT, Chunk, ChunkStore, atomic_write


STORE_PATH_V2 = REPO_ROOT / "metadata" / "chunks_v2.json"


def save_store_v2(store: ChunkStore, path: Path = STORE_PATH_V2) -> None:
    atomic_write(path, store.to_dict())


def load_store_v2(path: Path = STORE_PATH_V2) -> ChunkStore | None:
    """Mirror of store.load_store against the v2 path."""
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
