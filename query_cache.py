"""Near-duplicate query ranking cache for the H-QRL experiment.

Architecture role: skip a second frozen rank_all() when the rewritten
query string is already cached for this index. Does not change scoring.

Serve policy is locked in
docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md:
identical rewritten text + matching index hash is a hit; cosine >= 0.99
with a different string is a logged collision and is not served.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from embed import cosine_similarity
from retrieve import RetrievalHit
from store import ChunkStore


SERVE_THRESHOLD = 0.99


@dataclass
class CachedHit:
    section_id: str
    score: float
    cosine: float
    lexical: float
    alias: float
    method: str


@dataclass
class CachedRanking:
    rewritten_query: str
    vector: list[float]
    index_sha256: str
    hits: list[CachedHit]


@dataclass
class CacheLookup:
    hit: bool
    ranking: CachedRanking | None
    nearest_cosine: float | None
    collision: bool = False


class SemanticQueryCache:
    """In-memory rewritten-query cache keyed by TF-IDF vector + index hash."""

    def __init__(self, serve_threshold: float = SERVE_THRESHOLD) -> None:
        self.serve_threshold = serve_threshold
        self._entries: list[CachedRanking] = []
        self.collisions: list[dict[str, object]] = []

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self.collisions.clear()

    def lookup(
        self,
        rewritten_query: str,
        vector: list[float],
        index_sha256: str,
    ) -> CacheLookup:
        nearest_cosine: float | None = None
        nearest: CachedRanking | None = None
        exact: CachedRanking | None = None
        exact_cosine: float | None = None
        for entry in self._entries:
            if entry.index_sha256 != index_sha256:
                continue
            cosine = cosine_similarity(vector, entry.vector)
            if nearest_cosine is None or cosine > nearest_cosine:
                nearest_cosine = cosine
                nearest = entry
            if entry.rewritten_query == rewritten_query:
                exact = entry
                exact_cosine = cosine
        if exact is not None:
            # Identical rewritten text is a hit even when both vectors are
            # all-zero (OOV-only queries): cosine_similarity of zeros is 0.0.
            return CacheLookup(
                hit=True, ranking=exact, nearest_cosine=exact_cosine
            )
        if nearest is None or nearest_cosine is None:
            return CacheLookup(hit=False, ranking=None, nearest_cosine=None)
        if nearest_cosine < self.serve_threshold:
            return CacheLookup(
                hit=False, ranking=None, nearest_cosine=nearest_cosine
            )
        collision = {
            "cached_query": nearest.rewritten_query,
            "incoming_query": rewritten_query,
            "cosine": nearest_cosine,
        }
        self.collisions.append(collision)
        return CacheLookup(
            hit=False,
            ranking=None,
            nearest_cosine=nearest_cosine,
            collision=True,
        )

    def store(
        self,
        rewritten_query: str,
        vector: list[float],
        index_sha256: str,
        hits: list[RetrievalHit],
    ) -> CachedRanking:
        live = [entry for entry in self._entries if entry.index_sha256 == index_sha256]
        stale = len(live) != len(self._entries)
        if stale:
            self._entries = live
        ranking = CachedRanking(
            rewritten_query=rewritten_query,
            vector=list(vector),
            index_sha256=index_sha256,
            hits=[
                CachedHit(
                    section_id=hit.chunk.section_id,
                    score=hit.score,
                    cosine=hit.cosine,
                    lexical=hit.lexical,
                    alias=hit.alias,
                    method=hit.method,
                )
                for hit in hits
            ],
        )
        self._entries.append(ranking)
        return ranking

    def rehydrate(
        self, ranking: CachedRanking, store: ChunkStore
    ) -> list[RetrievalHit]:
        """Rebuild RetrievalHit objects from stored section_ids + scores."""
        by_id = {chunk.section_id: chunk for chunk in store.chunks}
        hits: list[RetrievalHit] = []
        for cached in ranking.hits:
            chunk = by_id.get(cached.section_id)
            if chunk is None:
                raise KeyError(
                    f"cached section_id {cached.section_id!r} missing from store"
                )
            hits.append(
                RetrievalHit(
                    chunk=chunk,
                    score=cached.score,
                    cosine=cached.cosine,
                    lexical=cached.lexical,
                    alias=cached.alias,
                    method=cached.method,
                )
            )
        return hits

    def snapshot(self) -> dict[str, object]:
        return {
            "serve_threshold": self.serve_threshold,
            "size": len(self._entries),
            "collisions": list(self.collisions),
            "entries": [asdict(entry) for entry in self._entries],
        }
