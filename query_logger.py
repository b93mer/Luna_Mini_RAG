"""Append-only JSONL trace of eval rows run through retrieve().

Architecture role: one JSON line per query-set row, with full per-hit
provenance (source_path, line span, content_sha256) next to the score
components, so later reclassifications can cite the exact chunk at each
rank. One log file per Python process run.

This module observes. It does not define retrieval weights, TOP_K, or
artifact hashes; the runner passes the values the process actually used.

Primary API:
    log_row(...)  — one JSON line per eval row + top-k hits + expected-target
                    full-ranking telemetry + run/config identity

Optional loop fields (rewritten_query, cache_hit, expansions,
config.loop_enabled, config.rewrite_policy) are written when the runner
enables a query loop. Optional H1 fields (lexical_cosine, dense_cosine,
config.dense_h1_enabled, config.cosine_term, config.dense_index_sha256)
are written so dense vs lexical cosine remain distinguishable. Historical
JSONL files were not rewritten.

No external deps: json + uuid + time only.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from retrieve import RetrievalHit


REPO_ROOT = Path(__file__).resolve().parent
_RUNS_DIR = REPO_ROOT / "eval_sets" / "runs"


def _next_run_log_path() -> Path:
    """Pick YYYY-MM-DD_run-NNN.jsonl for today's UTC date, next free NNN."""
    date = time.strftime("%Y-%m-%d", time.gmtime())
    nnn = 1
    if _RUNS_DIR.exists():
        existing: list[int] = []
        for path in _RUNS_DIR.glob(f"{date}_run-*.jsonl"):
            suffix = path.stem.rsplit("run-", 1)[-1]
            if suffix.isdigit():
                existing.append(int(suffix))
        if existing:
            nnn = max(existing) + 1
    return _RUNS_DIR / f"{date}_run-{nnn:03d}.jsonl"


LOG_PATH = _next_run_log_path()


@dataclass
class HitTrace:
    """One retrieved chunk, with the score components that produced it."""

    section_id: str
    score: float
    cosine: float
    lexical: float
    alias: float
    method: str
    source_path: str
    start_line: int
    end_line: int
    content_sha256: str
    lexical_cosine: float = 0.0
    dense_cosine: float = 0.0

    @classmethod
    def from_hit(cls, hit: RetrievalHit) -> "HitTrace":
        """NOTE (added helper): capture provenance, not just the ranking."""
        prov = hit.chunk.provenance or {}
        lexical_cosine = getattr(hit, "lexical_cosine", hit.cosine)
        dense_cosine = getattr(hit, "dense_cosine", 0.0)
        return cls(
            section_id=hit.chunk.section_id,
            score=round(hit.score, 6),
            cosine=round(hit.cosine, 6),
            lexical=round(hit.lexical, 6),
            alias=round(hit.alias, 6),
            method=hit.method,
            source_path=hit.chunk.source_path,
            start_line=hit.chunk.start_line,
            end_line=hit.chunk.end_line,
            content_sha256=prov.get("content_sha256", ""),
            lexical_cosine=round(lexical_cosine, 6),
            dense_cosine=round(dense_cosine, 6),
        )


@dataclass
class ExpectedTargetTrace:
    """Expected section as observed in the full ranking, not only top-k."""

    section_id: str
    rank: int | None
    score: float | None
    cosine: float | None
    lexical: float | None
    alias: float | None
    in_topk: bool
    lexical_cosine: float | None = None
    dense_cosine: float | None = None

    @classmethod
    def from_ranked_hit(
        cls,
        section_id: str,
        rank: int | None,
        hit: RetrievalHit | None,
        top_k: int,
    ) -> "ExpectedTargetTrace":
        """Copy components from a ranked hit. Does not rescore."""
        if hit is None or rank is None:
            return cls(
                section_id=section_id,
                rank=None,
                score=None,
                cosine=None,
                lexical=None,
                alias=None,
                in_topk=False,
                lexical_cosine=None,
                dense_cosine=None,
            )
        lexical_cosine = getattr(hit, "lexical_cosine", hit.cosine)
        dense_cosine = getattr(hit, "dense_cosine", 0.0)
        return cls(
            section_id=section_id,
            rank=rank,
            score=round(hit.score, 6),
            cosine=round(hit.cosine, 6),
            lexical=round(hit.lexical, 6),
            alias=round(hit.alias, 6),
            in_topk=rank <= top_k,
            lexical_cosine=round(lexical_cosine, 6),
            dense_cosine=round(dense_cosine, 6),
        )


@dataclass
class RunConfigTrace:
    """Runtime cutoff and blend weights the runner observed, not copies defined here.

    top_k belongs to run_query_set.TOP_K.
    weight_cosine / weight_lexical belong to retrieve.scoring_config().
    loop_enabled belongs to run_query_set.loop_enabled(); default off.
    rewrite_policy is empty when the loop is off.
    dense_h1_enabled belongs to run_query_set.dense_h1_enabled(); default off.
    cosine_term is lexical_cosine on the frozen path and dense_cosine under H1.
    dense_index_sha256 is empty when H1 is off.
    """

    top_k: int
    weight_cosine: float
    weight_lexical: float
    loop_enabled: bool = False
    rewrite_policy: str = ""
    dense_h1_enabled: bool = False
    cosine_term: str = "lexical_cosine"
    dense_index_sha256: str = ""


@dataclass
class QueryLogEntry:
    row_id: str
    query: str
    expected: list[str]
    failure_mode: str
    route_pressure: str
    prediction: str
    outcome: str
    in_topk: bool
    ts_utc: str
    query_uuid: str
    run_uuid: str
    query_set_sha256: str
    index_sha256: str
    config: RunConfigTrace
    hits: list[HitTrace] = field(default_factory=list)
    expected_targets: list[ExpectedTargetTrace] = field(default_factory=list)
    rewritten_query: str = ""
    cache_hit: bool = False
    expansions: list[str] = field(default_factory=list)


def _append(entry: QueryLogEntry) -> None:
    """Append one entry as a JSON line. No lock: single-run, single-writer."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry), sort_keys=False) + "\n")


def log_row(
    *,
    row_id: str,
    query: str,
    expected: list[str],
    failure_mode: str,
    route_pressure: str,
    prediction: str,
    outcome: str,
    in_topk: bool,
    hits: list,
    run_uuid: str,
    query_set_sha256: str,
    index_sha256: str,
    top_k: int,
    weight_cosine: float,
    weight_lexical: float,
    expected_targets: list[ExpectedTargetTrace],
    rewritten_query: str = "",
    cache_hit: bool = False,
    expansions: list[str] | None = None,
    loop_enabled: bool = False,
    rewrite_policy: str = "",
    dense_h1_enabled: bool = False,
    cosine_term: str = "lexical_cosine",
    dense_index_sha256: str = "",
) -> None:
    """Record one eval row: query + expected + outcome + hits + identity."""
    entry = QueryLogEntry(
        row_id=row_id,
        query=query,
        expected=expected,
        failure_mode=failure_mode,
        route_pressure=route_pressure,
        prediction=prediction,
        outcome=outcome,
        in_topk=in_topk,
        ts_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        query_uuid=str(uuid.uuid4()),
        run_uuid=run_uuid,
        query_set_sha256=query_set_sha256,
        index_sha256=index_sha256,
        config=RunConfigTrace(
            top_k=top_k,
            weight_cosine=weight_cosine,
            weight_lexical=weight_lexical,
            loop_enabled=loop_enabled,
            rewrite_policy=rewrite_policy,
            dense_h1_enabled=dense_h1_enabled,
            cosine_term=cosine_term,
            dense_index_sha256=dense_index_sha256,
        ),
        hits=[HitTrace.from_hit(h) for h in hits],
        expected_targets=list(expected_targets),
        rewritten_query=rewritten_query,
        cache_hit=cache_hit,
        expansions=list(expansions or []),
    )
    _append(entry)
