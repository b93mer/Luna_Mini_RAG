"""Run eval_sets/docqa.yaml through retrieve() and print per-row outcomes.

Architecture role: read-only query-set loop over the hybrid retriever.
Owns TOP_K (the eval cutoff). Does not define scoring weights.
Does not change retrieve ranking, evaluate.py, or the eval-set file.
"""

from __future__ import annotations

import hashlib
import sys
import uuid
from collections import Counter
from pathlib import Path

import yaml

from query_logger import ExpectedTargetTrace, log_row
from retrieve import RetrievalHit, rank_all, scoring_config
from store import STORE_PATH


REPO_ROOT = Path(__file__).resolve().parent
EVAL_SET_PATH = REPO_ROOT / "eval_sets" / "docqa.yaml"
# Eval cutoff. Owned here, not by retrieve.py (whose default k=5 is a
# separate API default for evaluate.py / CLI callers). The trace records
# this runtime value.
TOP_K = 5


def sha256_file(path: Path) -> str:
    """Hash of the artifact bytes this process actually reads."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def expected_target_traces(
    expected: list[str],
    ranked: list[RetrievalHit],
    top_k: int,
) -> list[ExpectedTargetTrace]:
    """Locate each expected section in the already-scored full ranking."""
    position: dict[str, tuple[int, RetrievalHit]] = {}
    for rank, hit in enumerate(ranked, start=1):
        section_id = hit.chunk.section_id
        if section_id not in position:
            position[section_id] = (rank, hit)
    traces: list[ExpectedTargetTrace] = []
    for section_id in expected:
        found = position.get(section_id)
        if found is None:
            traces.append(
                ExpectedTargetTrace.from_ranked_hit(section_id, None, None, top_k)
            )
        else:
            rank, hit = found
            traces.append(
                ExpectedTargetTrace.from_ranked_hit(section_id, rank, hit, top_k)
            )
    return traces


def run_rows(
    rows: list[dict],
    *,
    query_set_path: Path = EVAL_SET_PATH,
    index_path: Path = STORE_PATH,
) -> list[dict]:
    run_uuid = str(uuid.uuid4())
    query_set_sha256 = sha256_file(query_set_path)
    weights = scoring_config()
    index_sha256 = ""
    results: list[dict] = []
    for row in rows:
        query = row["query"]
        expected = list(row.get("expected") or [])
        prediction = row.get("current_stack_prediction", "")
        ranked = rank_all(query)
        if not index_sha256:
            index_sha256 = sha256_file(index_path)
        hits = ranked[:TOP_K]
        top_ids = [hit.chunk.section_id for hit in hits]
        in_topk = expected_in_topk(expected, top_ids)
        outcome = outcome_for(prediction, in_topk)
        targets = expected_target_traces(expected, ranked, TOP_K)
        log_row(
            row_id=row["id"],
            query=query,
            expected=expected,
            failure_mode=row.get("failure_mode", ""),
            route_pressure=row.get("route_pressure", ""),
            prediction=prediction,
            outcome=outcome,
            in_topk=in_topk,
            hits=hits,
            run_uuid=run_uuid,
            query_set_sha256=query_set_sha256,
            index_sha256=index_sha256,
            top_k=TOP_K,
            weight_cosine=weights["weight_cosine"],
            weight_lexical=weights["weight_lexical"],
            expected_targets=targets,
        )
        results.append(
            {
                "id": row["id"],
                "failure_mode": row.get("failure_mode", ""),
                "prediction": prediction,
                "outcome": outcome,
                "query": query,
                "expected": expected,
                "top_ids": top_ids,
                "hits": hits,
                "in_topk": in_topk,
                "run_uuid": run_uuid,
                "query_set_sha256": query_set_sha256,
                "index_sha256": index_sha256,
                "expected_targets": targets,
                "ranked": ranked,
            }
        )
    return results


def print_results(manifest: dict, results: list[dict]) -> None:
    print(f"query_set: {manifest.get('query_set', '?')}")
    print(f"rows: {len(results)}")
    print(f"governs: {manifest.get('governs', '')}")
    print(f"not_list: {manifest.get('not_list', '')}")
    if results:
        print(f"run_uuid: {results[0]['run_uuid']}")
        print(f"query_set_sha256: {results[0]['query_set_sha256']}")
        print(f"index_sha256: {results[0]['index_sha256']}")
        print(f"top_k: {TOP_K}")
        weights = scoring_config()
        print(
            f"scoring: weight_cosine={weights['weight_cosine']} "
            f"weight_lexical={weights['weight_lexical']}"
        )
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
        print("expected targets:")
        for target in result["expected_targets"]:
            rank_s = "?" if target.rank is None else str(target.rank)
            n = len(result["ranked"])
            print(
                f"  {target.section_id}"
                f"  rank={rank_s}/{n}"
                f"  score={target.score}"
                f"  cos={target.cosine}"
                f"  lex={target.lexical}"
                f"  alias={target.alias}"
                f"  in_topk={target.in_topk}"
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


if __name__ == "__main__":
    main()
