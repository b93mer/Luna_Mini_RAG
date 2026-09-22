"""Evaluate retrieval of Question, Verdict, and Finding 3.5 disposition.

Architecture role: confirm the ingest → store → retrieve path actually
returns the three target sections with the expected gold phrases.
"""

from __future__ import annotations

from ingest import ingest_all
from retrieve import retrieve, retrieve_target_sections


# NOTE (added helper data): gold phrases taken from the ingested trace note.
# Kept here rather than a new fixtures file so evaluation stays in the
# provided pipeline module.
GOLD = {
    "question": {
        "heading": "Question",
        "must_contain": [
            "conviction_detail.factors",
            "regime_boss_block_type",
        ],
    },
    "verdict": {
        "heading": "Verdict",
        "must_contain": [
            "independent-of-block_type",
            "VolatilityRegimeClassifier",
        ],
    },
    "impact_on_finding_3_5_disposition": {
        "heading": "Impact on Finding 3.5 disposition",
        "must_contain": [
            "HOLD stands",
            "Finding 3.5",
        ],
    },
}

QUERIES = (
    (
        "What is the question about conviction_detail.factors regime?",
        "question",
    ),
    (
        "What is the verdict on whether the regime factor is independent of block_type?",
        "verdict",
    ),
    (
        "Does this change Finding 3.5 disposition?",
        "impact_on_finding_3_5_disposition",
    ),
)


def _contains_all(text: str, needles: list[str]) -> bool:
    """NOTE (added helper): gold-phrase check used by both eval modes."""
    return all(needle in text for needle in needles)


def evaluate_section_lookup() -> list[str]:
    failures: list[str] = []
    bundle = retrieve_target_sections()
    for section_id, spec in GOLD.items():
        hit = bundle.get(section_id)
        if hit is None:
            failures.append(f"lookup miss: {section_id}")
            continue
        if spec["heading"].lower() not in hit.chunk.heading.lower():
            failures.append(
                f"heading mismatch for {section_id}: {hit.chunk.heading!r}"
            )
        if not _contains_all(hit.chunk.text, spec["must_contain"]):
            failures.append(f"gold phrases missing in {section_id}")
    return failures


def evaluate_query_retrieval() -> list[str]:
    failures: list[str] = []
    for query, expected_id in QUERIES:
        hits = retrieve(query, k=3)
        if not hits:
            failures.append(f"no hits for query → {expected_id}")
            continue
        top_ids = [hit.chunk.section_id for hit in hits]
        if expected_id not in top_ids:
            failures.append(
                f"query did not retrieve {expected_id} in top 3: {top_ids!r}"
            )
    return failures


def main() -> None:
    ingest_all()
    failures = evaluate_section_lookup() + evaluate_query_retrieval()
    if failures:
        print("FAIL")
        for item in failures:
            print(f"  - {item}")
        raise SystemExit(1)
    print("PASS")
    print("  section_id lookup: question, verdict, impact_on_finding_3_5_disposition")
    print("  hybrid queries: top-3 contains each gold section")


if __name__ == "__main__":
    main()
