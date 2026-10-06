"""Opt-in H-CODE ranker: replace lexical cosine with code cosine.

Architecture role: compute
    score = 0.7 * code_cosine + 0.3 * jaccard + alias
over original YAML query text. Jaccard and alias stay the frozen
implementations. Query rewriting and identifier expansion are not
applied. MiniLM dense_cosine is diagnostic only.

Enabled by run_query_set.py when LUNA_HCODE is set. Frozen
retrieve.rank_all() remains the default path.
"""

from __future__ import annotations

from pathlib import Path

from code_index import CodeIndex, ensure_code_index
from embed import cosine_similarity, model_from_store
from retrieve import RetrievalHit, _ensure_index, alias_boost, lexical_overlap
from store import ChunkStore


CODE_COSINE_WEIGHT = 0.7
JACCARD_WEIGHT = 0.3
COSINE_TERM = "code_cosine"


def scoring_config_hcode() -> dict[str, object]:
    """H-CODE blend. Weights match the frozen 0.7/0.3 split; cosine term is code."""
    return {
        "weight_cosine": CODE_COSINE_WEIGHT,
        "weight_lexical": JACCARD_WEIGHT,
        "weight_code_cosine": CODE_COSINE_WEIGHT,
        "weight_jaccard": JACCARD_WEIGHT,
        "cosine_term": COSINE_TERM,
    }


def _minilm_diagnostic(
    query: str,
    store: ChunkStore,
) -> dict[str, float]:
    """MiniLM cosine against the frozen H1 index. Not part of the blend."""
    from dense_index import DENSE_INDEX_PATH, load_dense_index

    path = Path(DENSE_INDEX_PATH)
    if not path.exists():
        return {}
    from dense_embed import encode_query

    query_dense = encode_query(query)
    index = load_dense_index(path)
    by_chunk = index.by_chunk_id()
    values: dict[str, float] = {}
    for chunk in store.chunks:
        row = by_chunk.get(chunk.chunk_id)
        if row is None:
            continue
        values[chunk.chunk_id] = cosine_similarity(query_dense, row.vector)
    return values


def rank_all_hcode(
    query: str,
    *,
    store: ChunkStore | None = None,
    code_index: CodeIndex | None = None,
) -> list[RetrievalHit]:
    """Score every chunk with the preregistered H-CODE formula.

    The query string is used as-is. lexical_cosine and MiniLM
    dense_cosine are computed for attribution and are not part of
    the blend.
    """
    live = store if store is not None else _ensure_index()
    if code_index is None:
        code_index, _sha = ensure_code_index(live)
    from code_embed import encode_query

    query_code = encode_query(query)
    lexical_model = model_from_store(live.vocab, live.idf)
    query_lex = lexical_model.transform([query])[0]
    minilm = _minilm_diagnostic(query, live)
    by_chunk = code_index.by_chunk_id()
    hits: list[RetrievalHit] = []
    for chunk in live.chunks:
        row = by_chunk[chunk.chunk_id]
        code_cosine = cosine_similarity(query_code, row.vector)
        lexical_cosine = cosine_similarity(query_lex, chunk.embedding)
        jaccard = lexical_overlap(query, chunk)
        alias = alias_boost(query, chunk)
        score = CODE_COSINE_WEIGHT * code_cosine + JACCARD_WEIGHT * jaccard + alias
        hits.append(
            RetrievalHit(
                chunk=chunk,
                score=score,
                method="hybrid-hcode",
                cosine=lexical_cosine,
                lexical=jaccard,
                alias=alias,
                lexical_cosine=lexical_cosine,
                dense_cosine=minilm.get(chunk.chunk_id, 0.0),
                code_cosine=code_cosine,
            )
        )
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits
