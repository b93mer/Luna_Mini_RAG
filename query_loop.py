"""Opt-in query-side loop: rewrite → semantic cache → frozen rank_all.

Architecture role: orchestrate H-QRL without changing retrieve scoring.
Enabled by run_query_set.py when LUNA_QUERY_LOOP is set.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from embed import model_from_store
from query_cache import SemanticQueryCache
from query_rewrite import RewriteResult, rewrite_query
from query_tracker import LoopEvent, QueryTracker
from retrieve import RetrievalHit, _ensure_index, rank_all
from store import ChunkStore


@dataclass
class LoopResult:
    ranked: list[RetrievalHit]
    rewrite: RewriteResult
    cache_hit: bool
    nearest_cosine: float | None
    collision: bool
    cache_ns: int
    rank_ns: int


def _now_ns() -> int:
    return time.perf_counter_ns()


def rank_with_loop(
    query: str,
    *,
    cache: SemanticQueryCache,
    tracker: QueryTracker,
    index_sha256: str,
    store: ChunkStore | None = None,
    pass_number: int = 1,
) -> LoopResult:
    """Rewrite, maybe serve a cached ranking, otherwise call frozen rank_all."""
    live_store = store if store is not None else _ensure_index()
    model = model_from_store(live_store.vocab, live_store.idf)
    rewrite = rewrite_query(query, live_store.vocab, live_store.idf)
    vector = model.transform([rewrite.rewritten])[0]

    cache_started = _now_ns()
    lookup = cache.lookup(rewrite.rewritten, vector, index_sha256)
    cache_ns = _now_ns() - cache_started

    rank_ns = 0
    if lookup.hit and lookup.ranking is not None:
        ranked = cache.rehydrate(lookup.ranking, live_store)
        cache_hit = True
    else:
        rank_started = _now_ns()
        ranked = rank_all(rewrite.rewritten)
        rank_ns = _now_ns() - rank_started
        cache.store(rewrite.rewritten, vector, index_sha256, ranked)
        cache_hit = False

    result = LoopResult(
        ranked=ranked,
        rewrite=rewrite,
        cache_hit=cache_hit,
        nearest_cosine=lookup.nearest_cosine,
        collision=lookup.collision,
        cache_ns=cache_ns,
        rank_ns=rank_ns,
    )
    tracker.record(
        LoopEvent(
            pass_number=pass_number,
            original_query=query,
            rewritten_query=rewrite.rewritten,
            stopwords_dropped=list(rewrite.stopwords_dropped),
            expansions=list(rewrite.expansions),
            morphology=list(rewrite.morphology),
            identifier_expansions=list(rewrite.identifier_expansions),
            cache_hit=cache_hit,
            nearest_cosine=lookup.nearest_cosine,
            collision=lookup.collision,
            cache_ns=cache_ns,
            rank_ns=rank_ns,
        )
    )
    return result
