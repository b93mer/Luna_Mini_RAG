"""Frozen dense-vector artifact for H1, separate from metadata/chunks.json.

Architecture role: store 384-d MiniLM vectors keyed by chunk identity.
Does not change lexical TF-IDF embeddings or chunk boundaries.

The lexical index remains metadata/chunks.json. This file is hashed
separately so H1 cannot silently rebuild the frozen control store.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from dense_embed import (
    EMBEDDING_DIM,
    MODEL_ID,
    MODEL_REVISION,
    encode_texts,
    model_identity,
)
from store import STORE_PATH, Chunk, ChunkStore, load_store


REPO_ROOT = Path(__file__).resolve().parent
DENSE_INDEX_PATH = REPO_ROOT / "metadata" / "dense_h1_index.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class DenseVectorRow:
    chunk_id: str
    section_id: str
    content_sha256: str
    vector: list[float]


@dataclass
class DenseIndex:
    identity: dict[str, object]
    lexical_index_sha256: str
    rows: list[DenseVectorRow]

    def by_chunk_id(self) -> dict[str, DenseVectorRow]:
        return {row.chunk_id: row for row in self.rows}

    def by_section_id(self) -> dict[str, DenseVectorRow]:
        return {row.section_id: row for row in self.rows}


def _content_sha256(chunk: Chunk) -> str:
    return str((chunk.provenance or {}).get("content_sha256", ""))


def _payload_from_index(index: DenseIndex) -> dict[str, object]:
    return {
        "identity": index.identity,
        "lexical_index_sha256": index.lexical_index_sha256,
        "rows": [
            {
                "chunk_id": row.chunk_id,
                "section_id": row.section_id,
                "content_sha256": row.content_sha256,
                "vector": row.vector,
            }
            for row in index.rows
        ],
    }


def index_from_payload(payload: dict[str, object]) -> DenseIndex:
    rows = [
        DenseVectorRow(
            chunk_id=str(item["chunk_id"]),
            section_id=str(item["section_id"]),
            content_sha256=str(item["content_sha256"]),
            vector=[float(value) for value in item["vector"]],
        )
        for item in payload["rows"]
    ]
    return DenseIndex(
        identity=dict(payload["identity"]),
        lexical_index_sha256=str(payload["lexical_index_sha256"]),
        rows=rows,
    )


def build_dense_index(
    store: ChunkStore,
    *,
    lexical_index_sha256: str,
) -> DenseIndex:
    """Encode stored chunk.text. Does not re-chunk or re-ingest."""
    texts = [chunk.text for chunk in store.chunks]
    vectors = encode_texts(texts)
    rows = [
        DenseVectorRow(
            chunk_id=chunk.chunk_id,
            section_id=chunk.section_id,
            content_sha256=_content_sha256(chunk),
            vector=vector,
        )
        for chunk, vector in zip(store.chunks, vectors)
    ]
    return DenseIndex(
        identity=model_identity(),
        lexical_index_sha256=lexical_index_sha256,
        rows=rows,
    )


def save_dense_index(index: DenseIndex, path: Path = DENSE_INDEX_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _payload_from_index(index)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return sha256_file(path)


def load_dense_index(path: Path = DENSE_INDEX_PATH) -> DenseIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return index_from_payload(payload)


def validate_dense_index(
    index: DenseIndex,
    store: ChunkStore,
    *,
    lexical_index_sha256: str,
) -> None:
    """Fail loud if vectors drifted from the frozen lexical chunks."""
    identity = index.identity
    if identity.get("model_id") != MODEL_ID:
        raise ValueError(f"dense index model_id {identity.get('model_id')!r} != {MODEL_ID!r}")
    if identity.get("revision") != MODEL_REVISION:
        raise ValueError(
            f"dense index revision {identity.get('revision')!r} != {MODEL_REVISION!r}"
        )
    if int(identity.get("embedding_dim") or 0) != EMBEDDING_DIM:
        raise ValueError("dense index embedding_dim mismatch")
    if index.lexical_index_sha256 != lexical_index_sha256:
        raise ValueError(
            "dense index lexical_index_sha256 does not match live chunks.json"
        )
    by_id = index.by_chunk_id()
    if len(by_id) != len(store.chunks) or len(index.rows) != len(store.chunks):
        raise ValueError("dense index row count does not match lexical store")
    for chunk in store.chunks:
        row = by_id.get(chunk.chunk_id)
        if row is None:
            raise ValueError(f"dense index missing chunk_id {chunk.chunk_id!r}")
        if row.section_id != chunk.section_id:
            raise ValueError(
                f"dense index section_id mismatch for {chunk.chunk_id}: "
                f"{row.section_id!r} != {chunk.section_id!r}"
            )
        expected_sha = _content_sha256(chunk)
        if row.content_sha256 != expected_sha:
            raise ValueError(
                f"dense index content_sha256 mismatch for {chunk.section_id}"
            )
        if len(row.vector) != EMBEDDING_DIM:
            raise ValueError(
                f"dense vector for {chunk.section_id} has dim {len(row.vector)}"
            )


def ensure_dense_index(
    store: ChunkStore | None = None,
    *,
    path: Path = DENSE_INDEX_PATH,
    lexical_index_path: Path = STORE_PATH,
) -> tuple[DenseIndex, str]:
    """Load a valid dense index, or build one if the artifact is absent."""
    live = store if store is not None else load_store()
    if live is None:
        raise RuntimeError("lexical store is empty; cannot build dense index")
    lexical_sha = sha256_file(lexical_index_path)
    if path.exists():
        index = load_dense_index(path)
        validate_dense_index(index, live, lexical_index_sha256=lexical_sha)
        return index, sha256_file(path)
    index = build_dense_index(live, lexical_index_sha256=lexical_sha)
    dense_sha = save_dense_index(index, path)
    validate_dense_index(index, live, lexical_index_sha256=lexical_sha)
    return index, dense_sha


def main() -> None:
    index, dense_sha = ensure_dense_index()
    print(f"rows: {len(index.rows)}")
    print(f"model_id: {index.identity['model_id']}")
    print(f"revision: {index.identity['revision']}")
    print(f"lexical_index_sha256: {index.lexical_index_sha256}")
    print(f"dense_index_sha256: {dense_sha}")
    print(f"path: {DENSE_INDEX_PATH}")


if __name__ == "__main__":
    main()
