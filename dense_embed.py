"""Locked MiniLM encoder for the H1 dense-cosine experiment.

Architecture role: turn query/chunk strings into 384-d L2-normalized
vectors using one pinned sentence-transformers model. Does not rank.
Does not rewrite queries. Does not touch the frozen TF-IDF analyzer.

Identity is locked in
docs/query_set_expansion/2026-10-05_dense_cosine_h1_preregistration.md.
Do not swap models after seeing sealed ranks.
"""

from __future__ import annotations

import math
from typing import Sequence

from sentence_transformers import SentenceTransformer


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
EMBEDDING_DIM = 384
MAX_SEQ_LENGTH = 256
POOLING = "mean"
DEVICE = "cpu"
LIBRARY = "sentence-transformers"
LIBRARY_VERSION = "6.1.0"
TORCH_VERSION = "2.14.1+cpu"
TRANSFORMERS_VERSION = "5.18.0"
NUMPY_VERSION = "2.3.5"
PYTHON_VERSION = "3.14.2"

_ENCODER: SentenceTransformer | None = None


def model_identity() -> dict[str, object]:
    """Exact encoder identity recorded beside dense vectors."""
    return {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "embedding_dim": EMBEDDING_DIM,
        "max_seq_length": MAX_SEQ_LENGTH,
        "pooling": POOLING,
        "normalized": True,
        "device": DEVICE,
        "library": LIBRARY,
        "library_version": LIBRARY_VERSION,
        "torch_version": TORCH_VERSION,
        "transformers_version": TRANSFORMERS_VERSION,
        "numpy_version": NUMPY_VERSION,
        "python_version": PYTHON_VERSION,
        "same_encoder_for_query_and_chunks": True,
    }


def get_encoder() -> SentenceTransformer:
    """Load the pinned MiniLM once. CPU inference only."""
    global _ENCODER
    if _ENCODER is None:
        encoder = SentenceTransformer(
            MODEL_ID,
            revision=MODEL_REVISION,
            device=DEVICE,
        )
        encoder.eval()
        encoder.max_seq_length = MAX_SEQ_LENGTH
        _ENCODER = encoder
    return _ENCODER


def l2_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in vector))


def encode_texts(texts: list[str]) -> list[list[float]]:
    """Encode strings with mean pooling and L2 normalization.

    The same encoder is used for queries and chunks. Inputs longer than
    MAX_SEQ_LENGTH tokens are truncated by the model.
    """
    if not texts:
        return []
    encoder = get_encoder()
    matrix = encoder.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        device=DEVICE,
    )
    vectors: list[list[float]] = []
    for row in matrix:
        vector = [float(value) for value in row.tolist()]
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(
                f"expected {EMBEDDING_DIM}-d dense vector, got {len(vector)}"
            )
        vectors.append(vector)
    return vectors


def encode_query(query: str) -> list[float]:
    """Encode one original query string. No rewriting."""
    return encode_texts([query])[0]
