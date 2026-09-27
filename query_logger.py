"""Append-only JSONL trace of eval rows run through retrieve().

Architecture role: one JSON line per query-set row, with full per-hit
provenance (source_path, line span, content_sha256) next to the score
components, so later reclassifications can cite the exact chunk at each
rank. One log file per Python process run.

Primary API:
    log_row(...)  — one JSON line per eval row + top-k hits

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
    hits: list[HitTrace] = field(default_factory=list)


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
) -> None:
    """Record one eval row: query + expected + outcome + full hit traces."""
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
        hits=[HitTrace.from_hit(h) for h in hits],
    )
    _append(entry)
