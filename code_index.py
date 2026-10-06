"""Frozen code-vector artifact for H-CODE, separate from chunks.json.

Architecture role: store 768-d Jina code vectors keyed by chunk identity.
Does not change lexical TF-IDF embeddings, MiniLM H1 vectors, or chunk
boundaries.

The lexical index remains metadata/chunks.json. The MiniLM index remains
metadata/dense_h1_index.json. This file is hashed separately so H-CODE
cannot silently rebuild those frozen artifacts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from code_embed import (
    EMBEDDING_DIM,
    MODEL_ID,
    MODEL_REVISION,
    encode_texts,
    model_identity,
)
from store import STORE_PATH, Chunk, ChunkStore, load_store


REPO_ROOT = Path(__file__).resolve().parent
CODE_INDEX_PATH = REPO_ROOT / "metadata" / "code_hcode_index.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class CodeVectorRow:
    chunk_id: str
    section_id: str
    content_sha256: str
    vector: list[float]


@dataclass
class CodeIndex:
    identity: dict[str, object]
    lexical_index_sha256: str
    rows: list[CodeVectorRow]

    def by_chunk_id(self) -> dict[str, CodeVectorRow]:
        return {row.chunk_id: row for row in self.rows}

    def by_section_id(self) -> dict[str, CodeVectorRow]:
        return {row.section_id: row for row in self.rows}


def _content_sha256(chunk: Chunk) -> str:
    return str((chunk.provenance or {}).get("content_sha256", ""))


def _payload_from_index(index: CodeIndex) -> dict[str, object]:
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


def index_from_payload(payload: dict[str, object]) -> CodeIndex:
    rows = [
        CodeVectorRow(
            chunk_id=str(item["chunk_id"]),
            section_id=str(item["section_id"]),
            content_sha256=str(item["content_sha256"]),
            vector=[float(value) for value in item["vector"]],
        )
        for item in payload["rows"]
    ]
    return CodeIndex(
        identity=dict(payload["identity"]),
        lexical_index_sha256=str(payload["lexical_index_sha256"]),
        rows=rows,
    )


def build_code_index(
    store: ChunkStore,
    *,
    lexical_index_sha256: str,
) -> CodeIndex:
    """Encode stored chunk.text. Does not re-chunk, rewrite, or split ids."""
    texts = [chunk.text for chunk in store.chunks]
    vectors = encode_texts(texts)
    rows = [
        CodeVectorRow(
            chunk_id=chunk.chunk_id,
            section_id=chunk.section_id,
            content_sha256=_content_sha256(chunk),
            vector=vector,
        )
        for chunk, vector in zip(store.chunks, vectors)
    ]
    return CodeIndex(
        identity=model_identity(),
        lexical_index_sha256=lexical_index_sha256,
        rows=rows,
    )


def save_code_index(index: CodeIndex, path: Path = CODE_INDEX_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _payload_from_index(index)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return sha256_file(path)


def load_code_index(path: Path = CODE_INDEX_PATH) -> CodeIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return index_from_payload(payload)


def validate_code_index(
    index: CodeIndex,
    store: ChunkStore,
    *,
    lexical_index_sha256: str,
) -> None:
    """Fail loud if vectors drifted from the frozen lexical chunks."""
    identity = index.identity
    if identity.get("model_id") != MODEL_ID:
        raise ValueError(f"code index model_id {identity.get('model_id')!r} != {MODEL_ID!r}")
    if identity.get("revision") != MODEL_REVISION:
        raise ValueError(
            f"code index revision {identity.get('revision')!r} != {MODEL_REVISION!r}"
        )
    if int(identity.get("embedding_dim") or 0) != EMBEDDING_DIM:
        raise ValueError("code index embedding_dim mismatch")
    if identity.get("external_identifier_segmentation") is not False:
        raise ValueError("code index must record external_identifier_segmentation=false")
    if index.lexical_index_sha256 != lexical_index_sha256:
        raise ValueError(
            "code index lexical_index_sha256 does not match live chunks.json"
        )
    by_id = index.by_chunk_id()
    if len(by_id) != len(store.chunks) or len(index.rows) != len(store.chunks):
        raise ValueError("code index row count does not match lexical store")
    for chunk in store.chunks:
        row = by_id.get(chunk.chunk_id)
        if row is None:
            raise ValueError(f"code index missing chunk_id {chunk.chunk_id!r}")
        if row.section_id != chunk.section_id:
            raise ValueError(
                f"code index section_id mismatch for {chunk.chunk_id}: "
                f"{row.section_id!r} != {chunk.section_id!r}"
            )
        expected_sha = _content_sha256(chunk)
        if row.content_sha256 != expected_sha:
            raise ValueError(
                f"code index content_sha256 mismatch for {chunk.section_id}"
            )
        if len(row.vector) != EMBEDDING_DIM:
            raise ValueError(
                f"code vector for {chunk.section_id} has dim {len(row.vector)}"
            )


def ensure_code_index(
    store: ChunkStore | None = None,
    *,
    path: Path = CODE_INDEX_PATH,
    lexical_index_path: Path = STORE_PATH,
) -> tuple[CodeIndex, str]:
    """Load a valid code index, or build one if the artifact is absent."""
    live = store if store is not None else load_store()
    if live is None:
        raise RuntimeError("lexical store is empty; cannot build code index")
    lexical_sha = sha256_file(lexical_index_path)
    if path.exists():
        index = load_code_index(path)
        validate_code_index(index, live, lexical_index_sha256=lexical_sha)
        return index, sha256_file(path)
    index = build_code_index(live, lexical_index_sha256=lexical_sha)
    code_sha = save_code_index(index, path)
    validate_code_index(index, live, lexical_index_sha256=lexical_sha)
    return index, code_sha


def main() -> None:
    index, code_sha = ensure_code_index()
    print(f"rows: {len(index.rows)}")
    print(f"model_id: {index.identity['model_id']}")
    print(f"revision: {index.identity['revision']}")
    print(f"lexical_index_sha256: {index.lexical_index_sha256}")
    print(f"code_index_sha256: {code_sha}")
    print(f"path: {CODE_INDEX_PATH}")


if __name__ == "__main__":
    main()
