"""Diagnostic tracker for the query-side loop.

Architecture role: record rewrite/cache events. Does not change ranking.
Does not mutate rewrite rules from observed stats.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class LoopEvent:
    pass_number: int
    original_query: str
    rewritten_query: str
    stopwords_dropped: list[str]
    expansions: list[str]
    morphology: list[str]
    identifier_expansions: list[str]
    rewrite_policy: str
    cache_hit: bool
    nearest_cosine: float | None
    collision: bool
    cache_ns: int
    rank_ns: int


class QueryTracker:
    """Accumulate per-lookup events and flush a sibling JSON aggregate."""

    def __init__(self) -> None:
        self.events: list[LoopEvent] = []

    def record(self, event: LoopEvent) -> None:
        self.events.append(event)

    def _pass_events(self, pass_number: int) -> list[LoopEvent]:
        return [event for event in self.events if event.pass_number == pass_number]

    def _pass_summary(self, pass_number: int) -> dict[str, Any]:
        events = self._pass_events(pass_number)
        hits = sum(1 for event in events if event.cache_hit)
        return {
            "queries": len(events),
            "cache_hits": hits,
            "cache_misses": len(events) - hits,
            "collisions": sum(1 for event in events if event.collision),
            "events": [asdict(event) for event in events],
        }

    def expansion_frequency(self, pass_number: int = 1) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for event in self._pass_events(pass_number):
            counts.update(event.expansions)
        return dict(sorted(counts.items()))

    def morphology_frequency(self, pass_number: int = 1) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for event in self._pass_events(pass_number):
            counts.update(event.morphology)
        return dict(sorted(counts.items()))

    def identifier_frequency(self, pass_number: int = 1) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for event in self._pass_events(pass_number):
            counts.update(event.identifier_expansions)
        return dict(sorted(counts.items()))

    def ranks_identical(self, left: list[list[str]], right: list[list[str]]) -> bool:
        return left == right

    def summary(
        self,
        *,
        index_sha256: str,
        serve_threshold: float,
        pass2_rank_identical: bool | None = None,
        unique_keys: int = 0,
        policy: str = "qrl-v1",
    ) -> dict[str, Any]:
        return {
            "policy": policy,
            "index_sha256": index_sha256,
            "serve_threshold": serve_threshold,
            "unique_keys": unique_keys,
            "pass_1": self._pass_summary(1),
            "pass_2": self._pass_summary(2),
            "pass_2_rank_identical": pass2_rank_identical,
            "expansion_frequency": self.expansion_frequency(1),
            "morphology_frequency": self.morphology_frequency(1),
            "identifier_frequency": self.identifier_frequency(1),
        }

    def flush(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
