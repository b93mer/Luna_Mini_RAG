"""Retrieve Question, Verdict, and Finding 3.5 disposition sections.

Architecture role: read-only query layer over metadata/chunks.json.

Evaluation status: FROZEN as the measurement baseline for the query-set
expansion evaluation sequence. Do not change weights, ranking, or the
alias table until a pre-registered hypothesis is measured against
docs/query_set_expansion/2026-09-28_retrieval_baseline.md.

Primary API:
    retrieve_target_sections()  — exact section_id lookup for the three
                                  requested regions
    rank_all(query)             — full hybrid ranking over the store
    retrieve(query, k=5)        — rank_all truncated to k
    scoring_config()            — weights rank_all/retrieve actually apply
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from embed import cosine_similarity, model_from_store, tokenize
from store import Chunk, ChunkStore, load_store


TARGET_SECTION_IDS = (
    "question",
    "verdict",
    "impact_on_finding_3_5_disposition",
)

# NOTE (added helper data): aliases so natural-language queries still boost
# the three target sections. Not a separate config file because the user
# asked to keep extra tools inside the provided retrieval files.
SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "question": ("question", "question section"),
    "verdict": ("verdict", "verdict section"),
    "impact_on_finding_3_5_disposition": (
        "finding 3.5",
        "finding 3_5",
        "disposition",
        "impact on finding",
        "hold stands",
    ),
}


# Single source of truth for the hybrid blend. retrieve() applies these;
# the eval trace records the same values. Do not change until a
# pre-registered hypothesis is measured against the frozen baseline.
COSINE_WEIGHT = 0.7
LEXICAL_WEIGHT = 0.3


@dataclass
class RetrievalHit:
    chunk: Chunk
    score: float
    method: str
    cosine: float = 0.0
    lexical: float = 0.0
    alias: float = 0.0


def scoring_config() -> dict[str, float]:
    """Weights the live hybrid formula uses. For logging, not a second config."""
    return {
        "weight_cosine": COSINE_WEIGHT,
        "weight_lexical": LEXICAL_WEIGHT,
    }


def _ensure_index() -> ChunkStore:
    """NOTE (added helper): build the store on first retrieve if empty."""
    store = load_store()
    if store is not None:
        return store
    from ingest import ingest_all

    ingest_all()
    store = load_store()
    if store is None:
        raise RuntimeError("ingest produced no chunks; check data/")
    return store


def lexical_overlap(query: str, chunk: Chunk) -> float:
    """NOTE (added helper): Jaccard overlap of query tokens vs heading+text.

    Complements TF-IDF when the query is basically a section name
    ('verdict section') rather than body content.
    """
    query_tokens = set(tokenize(query))
    doc_tokens = set(tokenize(f"{chunk.heading} {chunk.text}"))
    if not query_tokens or not doc_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens | doc_tokens)


def alias_boost(query: str, chunk: Chunk) -> float:
    """NOTE (added helper): extra score when the query names a target section."""
    lowered = query.lower()
    aliases = SECTION_ALIASES.get(chunk.section_id, ())
    if any(alias in lowered for alias in aliases):
        return 0.5
    if chunk.section_id.replace("_", " ") in lowered:
        return 0.35
    return 0.0


def rank_all(query: str) -> list[RetrievalHit]:
    """Score every chunk and sort. retrieve() is this list truncated to k.

    Same loop, weights, sort, and tie-breaking as the previous retrieve()
    body. Exposed so the eval runner can observe expected-target rank
    without a second scoring pass.
    """
    store = _ensure_index()
    model = model_from_store(store.vocab, store.idf)
    query_vec = model.transform([query])[0]
    hits: list[RetrievalHit] = []
    for chunk in store.chunks:
        cosine = cosine_similarity(query_vec, chunk.embedding)
        lexical = lexical_overlap(query, chunk)
        alias = alias_boost(query, chunk)
        score = COSINE_WEIGHT * cosine + LEXICAL_WEIGHT * lexical + alias
        hits.append(
            RetrievalHit(
                chunk=chunk,
                score=score,
                method="hybrid",
                cosine=cosine,
                lexical=lexical,
                alias=alias,
            )
        )
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits


def retrieve(query: str, k: int = 5) -> list[RetrievalHit]:
    """Hybrid search: cosine(TF-IDF) + lexical overlap + section alias boost."""
    return rank_all(query)[:k]


def retrieve_by_section_id(section_id: str) -> RetrievalHit | None:
    """Direct lookup used for the known Question / Verdict / 3.5 ids."""
    store = _ensure_index()
    chunk = store.get_by_section_id(section_id)
    if chunk is None:
        return None
    return RetrievalHit(chunk=chunk, score=1.0, method="section_id")


def retrieve_target_sections() -> dict[str, RetrievalHit | None]:
    """NOTE (added helper): pull the three requested sections in one call.

    This is the system the architecture is aimed at: Question, Verdict, and
    Impact on Finding 3.5 disposition, keyed by smart_chunker section ids.
    Falls back to hybrid search if an id is missing after a re-chunk.
    """
    bundle: dict[str, RetrievalHit | None] = {}
    for section_id in TARGET_SECTION_IDS:
        hit = retrieve_by_section_id(section_id)
        if hit is None:
            query = SECTION_ALIASES.get(section_id, (section_id,))[0]
            hits = retrieve(query, k=1)
            hit = hits[0] if hits else None
        bundle[section_id] = hit
    return bundle


def format_hit(hit: RetrievalHit | None, label: str) -> str:
    """NOTE (added helper): printable provenance + body for CLI output."""
    if hit is None:
        return f"=== {label} ===\n(missing)\n"
    chunk = hit.chunk
    loc = f"{chunk.source_path}:{chunk.start_line}-{chunk.end_line}"
    return (
        f"=== {label} ===\n"
        f"section_id: {chunk.section_id}\n"
        f"method: {hit.method}  score: {hit.score:.3f}\n"
        f"source: {loc}\n"
        f"content_sha256: {chunk.provenance.get('content_sha256', '')}\n"
        f"\n{chunk.text}\n"
    )


def _configure_stdout() -> None:
    """NOTE (added helper): Windows consoles default to cp1252.

    The source notes use Unicode arrows (→) that otherwise crash print.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    _configure_stdout()
    bundle = retrieve_target_sections()
    labels = {
        "question": "Question",
        "verdict": "Verdict",
        "impact_on_finding_3_5_disposition": "Impact on Finding 3.5 disposition",
    }
    parts = [
        format_hit(bundle[section_id], labels[section_id])
        for section_id in TARGET_SECTION_IDS
    ]
    print("\n".join(parts))


if __name__ == "__main__":
    main()
