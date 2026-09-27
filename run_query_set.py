"""Run eval_sets/docqa.yaml through retrieve() and print per-row outcomes.

Architecture role: read-only query-set loop over the hybrid retriever.
Does not change retrieve.py, evaluate.py, or the eval-set file.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

from retrieve import retrieve


REPO_ROOT = Path(__file__).resolve().parent
EVAL_SET_PATH = REPO_ROOT / "eval_sets" / "docqa.yaml"
RUN_OUTPUT_PATH = (
    REPO_ROOT / "eval_sets" / "runs" / "2026-09-26_first_end_to_end.yaml"
)
TOP_K = 5


def _configure_stdout() -> None:
    """Windows consoles default to cp1252; the YAML uses an em dash."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_eval_set(path: Path = EVAL_SET_PATH) -> tuple[dict, list[dict]]:
    """Split the two-document YAML into manifest + rows."""
    documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    if len(documents) < 2:
        raise ValueError(f"{path} must have a manifest document then a row list")
    manifest = documents[0] or {}
    rows = documents[1] or []
    if not isinstance(manifest, dict):
        raise ValueError("first YAML document must be a mapping (manifest)")
    if not isinstance(rows, list):
        raise ValueError("second YAML document must be a list of rows")
    return manifest, rows


def expected_in_topk(expected: list[str], top_ids: list[str]) -> bool:
    """Hit when every expected section_id appears in the retrieved top-k."""
    if not expected:
        return False
    return all(section_id in top_ids for section_id in expected)


def outcome_for(prediction: str, in_topk: bool) -> str:
    """Map retrieve result + current_stack_prediction to hit / miss / expected_miss."""
    if in_topk:
        return "hit"
    if prediction == "expected_miss":
        return "expected_miss"
    return "miss"


def run_rows(rows: list[dict]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        query = row["query"]
        expected = list(row.get("expected") or [])
        prediction = row.get("current_stack_prediction", "")
        hits = retrieve(query, k=TOP_K)
        top_ids = [hit.chunk.section_id for hit in hits]
        in_topk = expected_in_topk(expected, top_ids)
        results.append(
            {
                "id": row["id"],
                "failure_mode": row.get("failure_mode", ""),
                "prediction": prediction,
                "outcome": outcome_for(prediction, in_topk),
                "query": query,
                "expected": expected,
                "top_ids": top_ids,
                "hits": hits,
                "in_topk": in_topk,
            }
        )
    return results


def results_for_dump(results: list[dict]) -> list[dict]:
    """Minimal per-row record: id, prediction, outcome, scored top-k."""
    payload: list[dict] = []
    for result in results:
        payload.append(
            {
                "id": result["id"],
                "prediction": result["prediction"],
                "outcome": result["outcome"],
                "top_k": [
                    {
                        "section_id": hit.chunk.section_id,
                        "score": hit.score,
                        "cosine": hit.cosine,
                        "lexical": hit.lexical,
                        "alias": hit.alias,
                    }
                    for hit in result["hits"]
                ],
            }
        )
    return payload


def write_results(results: list[dict], path: Path = RUN_OUTPUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            results_for_dump(results),
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def print_results(manifest: dict, results: list[dict]) -> None:
    print(f"query_set: {manifest.get('query_set', '?')}")
    print(f"rows: {len(results)}")
    print(f"governs: {manifest.get('governs', '')}")
    print(f"not_list: {manifest.get('not_list', '')}")
    print()

    counts: Counter[str] = Counter()
    for result in results:
        counts[result["outcome"]] += 1
        print(f"=== {result['id']} ===")
        print(f"failure_mode: {result['failure_mode']}")
        print(f"prediction:   {result['prediction']}")
        print(f"outcome:      {result['outcome']}")
        print(f"query:        {result['query']}")
        print(f"expected:     {result['expected']}")
        print(f"in_topk:      {result['in_topk']}")
        print("top-k:")
        for rank, hit in enumerate(result["hits"], start=1):
            print(
                f"  {rank}. {hit.chunk.section_id}"
                f"  score={hit.score:.3f}"
                f"  cos={hit.cosine:.3f}"
                f"  lex={hit.lexical:.3f}"
                f"  alias={hit.alias:.3f}"
            )
        print()

    print("--- summary ---")
    print(
        f"{'id':<24} {'prediction':<16} {'outcome':<16} {'expected in top-k'}"
    )
    for result in results:
        print(
            f"{result['id']:<24} {result['prediction']:<16} "
            f"{result['outcome']:<16} {'yes' if result['in_topk'] else 'no'}"
        )
    print()
    print(
        f"hit={counts['hit']}  miss={counts['miss']}  "
        f"expected_miss={counts['expected_miss']}"
    )


def main() -> None:
    _configure_stdout()
    manifest, rows = load_eval_set()
    results = run_rows(rows)
    print_results(manifest, results)
    write_results(results)
    print(f"wrote: {RUN_OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
