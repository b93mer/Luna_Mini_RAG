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

    @classmethod
    def from_hit(cls, hit: RetrievalHit) -> "HitTrace":
        """NOTE (added helper): capture provenance, not just the ranking."""
        prov = hit.chunk.provenance or {}
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
            )
        return cls(
            section_id=section_id,
            rank=rank,
            score=round(hit.score, 6),
            cosine=round(hit.cosine, 6),
            lexical=round(hit.lexical, 6),
            alias=round(hit.alias, 6),
            in_topk=rank <= top_k,
        )


@dataclass
class RunConfigTrace:
    """Runtime cutoff and blend weights the runner observed, not copies defined here.

    top_k belongs to run_query_set.TOP_K.
    weight_cosine / weight_lexical belong to retrieve.scoring_config().
    """

    top_k: int
    weight_cosine: float
    weight_lexical: float


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
        ),
        hits=[HitTrace.from_hit(h) for h in hits],
        expected_targets=list(expected_targets),
    )
    _append(entry)
