"""Opt-in H1 ranker: replace lexical cosine with dense cosine.

Architecture role: compute
    score = 0.7 * dense_cosine + 0.3 * jaccard + alias
over original YAML query text. Jaccard and alias stay the frozen
implementations. Query rewriting is not applied.

Enabled by run_query_set.py when LUNA_DENSE_H1 is set. Frozen
retrieve.rank_all() remains the default path.
"""

from __future__ import annotations

from embed import cosine_similarity, model_from_store
from dense_index import DenseIndex, ensure_dense_index
from retrieve import RetrievalHit, _ensure_index, alias_boost, lexical_overlap
from store import ChunkStore


DENSE_COSINE_WEIGHT = 0.7
JACCARD_WEIGHT = 0.3
COSINE_TERM = "dense_cosine"


def scoring_config_h1() -> dict[str, object]:
    """H1 blend. Weights match the frozen 0.7/0.3 split; cosine term is dense."""
    return {
        "weight_cosine": DENSE_COSINE_WEIGHT,
        "weight_lexical": JACCARD_WEIGHT,
        "weight_dense_cosine": DENSE_COSINE_WEIGHT,
        "weight_jaccard": JACCARD_WEIGHT,
        "cosine_term": COSINE_TERM,
    }


def rank_all_h1(
    query: str,
    *,
    store: ChunkStore | None = None,
    dense_index: DenseIndex | None = None,
) -> list[RetrievalHit]:
    """Score every chunk with the preregistered H1 formula.

    The query string is used as-is. lexical_cosine is computed for
    attribution and is not part of the blend.
    """
    live = store if store is not None else _ensure_index()
    if dense_index is None:
        dense_index, _sha = ensure_dense_index(live)
    from dense_embed import encode_query

    query_dense = encode_query(query)
    lexical_model = model_from_store(live.vocab, live.idf)
    query_lex = lexical_model.transform([query])[0]
    by_chunk = dense_index.by_chunk_id()
    hits: list[RetrievalHit] = []
    for chunk in live.chunks:
        row = by_chunk[chunk.chunk_id]
        dense_cosine = cosine_similarity(query_dense, row.vector)
        lexical_cosine = cosine_similarity(query_lex, chunk.embedding)
        jaccard = lexical_overlap(query, chunk)
        alias = alias_boost(query, chunk)
        score = DENSE_COSINE_WEIGHT * dense_cosine + JACCARD_WEIGHT * jaccard + alias
        hits.append(
            RetrievalHit(
                chunk=chunk,
                score=score,
                method="hybrid-h1",
                cosine=lexical_cosine,
                lexical=jaccard,
                alias=alias,
                lexical_cosine=lexical_cosine,
                dense_cosine=dense_cosine,
            )
        )
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits
