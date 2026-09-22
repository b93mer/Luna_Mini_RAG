"""Retrieval ablation: does the hybrid formula in retrieve.retrieve() matter?

Hypothesis under test:
  H0: TF-IDF cosine alone is sufficient to retrieve the three target
      sections in top-3 for their gold queries.
  H1: Cosine alone fails on at least one gold query and either lexical
      overlap or alias boost is decisive.

Configurations (per gold query from evaluate.QUERIES):
  A. baseline            — retrieve() as written
  B. no alias boost      — retrieve.alias_boost monkeypatched to return 0.0
  C. no lexical overlap  — local wrapper, lexical weight set to 0
  D. pure cosine         — monkeypatched alias_boost=0 AND wrapper with
                           lexical weight 0 (score = 0.7 * cosine only)
  E. no section_id path  — retrieve_by_section_id monkeypatched to None so
                           retrieve_target_sections() must use its
                           retrieve() fallback

No pipeline files are modified; all variation is runtime monkeypatching or
local wrappers in this file. chunks.json is read, never written.
"""

from __future__ import annotations

import sys
from pathlib import Path

# NOTE (added helper): research scripts live two levels below repo root;
# put the root on sys.path so the frozen pipeline modules import unchanged.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import retrieve  # noqa: E402
from embed import cosine_similarity, model_from_store  # noqa: E402
from evaluate import QUERIES  # noqa: E402  (read-only import of gold queries)
from store import load_store  # noqa: E402

W_COSINE = 0.7  # must match retrieve.retrieve()
W_LEXICAL = 0.3


def _configure_stdout() -> None:
    """NOTE (added helper): match retrieve.py's Windows encoding guard."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _load_frozen_store():
    """Read chunks.json only. Never ingests — the index is frozen for this
    ablation, and rebuilding it is out of scope (and disallowed)."""
    store = load_store()
    if store is None:
        raise RuntimeError(
            "metadata/chunks.json missing or empty; run ingest on main first"
        )
    return store


def _full_ranking(query: str, w_cosine: float, w_lexical: float):
    """NOTE (added helper): local scoring wrapper around retrieve() parts.

    Replicates retrieve.retrieve()'s formula with adjustable weights so
    configs C and D can zero the lexical term without editing retrieve.py.
    Returns the FULL ranking (not top-k) so margins are computable even
    when the expected chunk falls outside the displayed window.
    """
    store = _load_frozen_store()
    model = model_from_store(store.vocab, store.idf)
    query_vec = model.transform([query])[0]
    hits = []
    for chunk in store.chunks:
        cosine = cosine_similarity(query_vec, chunk.embedding)
        lexical = retrieve.lexical_overlap(query, chunk)
        alias = retrieve.alias_boost(query, chunk)  # monkeypatch-visible
        score = w_cosine * cosine + w_lexical * lexical + alias
        hits.append(retrieve.RetrievalHit(chunk=chunk, score=score, method="wrapper"))
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits


def _baseline_full_ranking(query: str):
    """retrieve() as written, but with k large enough to return every chunk
    so runner-up margins are measurable."""
    store = _load_frozen_store()
    return retrieve.retrieve(query, k=len(store.chunks))


def measure(hits, expected_id: str) -> dict:
    """Rank, top-1/top-3 membership, and margin over runner-up."""
    rank = None
    expected_score = None
    runner_up_score = None
    for index, hit in enumerate(hits, start=1):
        if hit.chunk.section_id == expected_id and rank is None:
            rank = index
            expected_score = hit.score
        elif runner_up_score is None:
            runner_up_score = hit.score
        if rank is not None and runner_up_score is not None:
            break
    margin = None
    if expected_score is not None and runner_up_score is not None:
        margin = expected_score - runner_up_score
    return {
        "rank": rank,
        "top1": rank == 1,
        "top3": rank is not None and rank <= 3,
        "margin": margin,
    }


def _with_alias_disabled(fn):
    """NOTE (added helper): context-style monkeypatch of alias_boost."""
    original = retrieve.alias_boost
    retrieve.alias_boost = lambda query, chunk: 0.0
    try:
        return fn()
    finally:
        retrieve.alias_boost = original


def run_config_a(query: str, expected_id: str) -> dict:
    return measure(_baseline_full_ranking(query), expected_id)


def run_config_b(query: str, expected_id: str) -> dict:
    return _with_alias_disabled(
        lambda: measure(_baseline_full_ranking(query), expected_id)
    )


def run_config_c(query: str, expected_id: str) -> dict:
    return measure(_full_ranking(query, W_COSINE, 0.0), expected_id)


def run_config_d(query: str, expected_id: str) -> dict:
    # TODO(review): D keeps the 0.7 cosine weight so margins stay on the
    # same scale as A-C. Ranking is identical to raw cosine; only the
    # absolute margin values are 0.7x. Simpler than special-casing w=1.0.
    return _with_alias_disabled(
        lambda: measure(_full_ranking(query, W_COSINE, 0.0), expected_id)
    )


def run_config_e() -> dict[str, dict]:
    """Force retrieve_target_sections() down its retrieve() fallback path.

    NOTE (design choice): E does not use the gold queries — the fallback
    issues SECTION_ALIASES' first alias as the query with k=1. Margins are
    therefore measured by re-running retrieve() on that alias query and
    scoring the expected section against the runner-up.
    """
    original = retrieve.retrieve_by_section_id
    retrieve.retrieve_by_section_id = lambda section_id: None
    try:
        bundle = retrieve.retrieve_target_sections()
    finally:
        retrieve.retrieve_by_section_id = original

    results: dict[str, dict] = {}
    for expected_id, hit in bundle.items():
        correct = hit is not None and hit.chunk.section_id == expected_id
        alias_query = retrieve.SECTION_ALIASES.get(expected_id, (expected_id,))[0]
        ranking = _baseline_full_ranking(alias_query)
        m = measure(ranking, expected_id)
        results[expected_id] = {
            "rank": 1 if correct else None,
            "top1": correct,
            "top3": correct,  # fallback returns k=1, so top-1 == top-3
            "margin": m["margin"],
        }
    return results


CONFIGS = (
    ("A", "baseline (hybrid as written)", run_config_a),
    ("B", "no alias boost", run_config_b),
    ("C", "no lexical overlap (0.7*cos + alias)", run_config_c),
    ("D", "pure cosine only", run_config_d),
)


def sanity_check_wrapper_matches_baseline() -> list[str]:
    """NOTE (added helper): the wrapper with baseline weights must reproduce
    retrieve()'s top-3 ordering, or configs C/D are measuring a different
    retriever than the one under test."""
    failures = []
    for query, _ in QUERIES:
        baseline_ids = [h.chunk.section_id for h in _baseline_full_ranking(query)[:3]]
        wrapper_ids = [
            h.chunk.section_id
            for h in _full_ranking(query, W_COSINE, W_LEXICAL)[:3]
        ]
        if baseline_ids != wrapper_ids:
            failures.append(
                f"wrapper mismatch for {query!r}: {baseline_ids} vs {wrapper_ids}"
            )
    return failures


def _fmt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:+.4f}"
    return str(value)


def print_markdown_table(all_results: dict) -> None:
    """Markdown results table (also pasted into findings.md)."""
    print("\n| Config | Query (gold) | Expected section | Rank | Top-1? | Top-3? | Margin over runner-up |")
    print("|---|---|---|---|---|---|---|")
    for letter, description, _ in CONFIGS:
        for (query, expected_id), result in all_results[letter].items():
            print(
                f"| {letter} {description} | {query} | {expected_id} "
                f"| {_fmt(result['rank'])} | {_fmt(result['top1'])} "
                f"| {_fmt(result['top3'])} | {_fmt(result['margin'])} |"
            )
    for expected_id, result in all_results["E"].items():
        print(
            f"| E no section_id lookup | (fallback alias query) | {expected_id} "
            f"| {_fmt(result['rank'])} | {_fmt(result['top1'])} "
            f"| {_fmt(result['top3'])} | {_fmt(result['margin'])} |"
        )


def main() -> None:
    _configure_stdout()
    sanity_failures = sanity_check_wrapper_matches_baseline()
    if sanity_failures:
        print("FAIL")
        for item in sanity_failures:
            print(f"  - {item}")
        raise SystemExit(1)

    all_results: dict[str, dict] = {}
    config_pass: dict[str, bool] = {}
    for letter, _, runner in CONFIGS:
        per_query = {}
        for query, expected_id in QUERIES:
            per_query[(query, expected_id)] = runner(query, expected_id)
        all_results[letter] = per_query
        config_pass[letter] = all(r["top3"] for r in per_query.values())

    all_results["E"] = run_config_e()
    config_pass["E"] = all(r["top3"] for r in all_results["E"].values())

    print_markdown_table(all_results)

    print()
    overall_fail = False
    for letter, description, _ in CONFIGS:
        verdict = "PASS" if config_pass[letter] else "FAIL"
        if not config_pass[letter]:
            overall_fail = True
        print(f"{verdict}  config {letter}: {description} (top-3 on all 3 gold queries)")
    verdict = "PASS" if config_pass["E"] else "FAIL"
    if not config_pass["E"]:
        overall_fail = True
    print(f"{verdict}  config E: no section_id lookup (fallback retrieves all 3 targets)")

    print()
    if config_pass["D"]:
        print("H0 NOT REJECTED: pure TF-IDF cosine retrieved all three target "
              "sections in top-3 for their gold queries.")
    else:
        failed = [
            expected_id
            for (query, expected_id), r in all_results["D"].items()
            if not r["top3"]
        ]
        print(f"H0 REJECTED: pure cosine failed top-3 on: {', '.join(failed)}")

    if overall_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
