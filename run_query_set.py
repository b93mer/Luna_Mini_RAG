"""Run eval_sets/docqa.yaml through retrieve() and print per-row outcomes.

Architecture role: read-only query-set loop over the hybrid retriever.
Owns TOP_K (the eval cutoff). Does not define scoring weights.
Does not change retrieve ranking, evaluate.py, or the eval-set file.

Query-side rewrite/cache loop is opt-in via LUNA_QUERY_LOOP (H-QRL
qrl-v1) or LUNA_MORPH_LOOP (H-MORPH morph-v1) and does not run unless
that env var is a truthy value (1/true/yes/on). Default off.

Dense cosine H1 is opt-in via LUNA_DENSE_H1 (dense-cosine-h1-v1) and
does not run unless that env var is truthy. Default off. Combining H1
with a rewrite loop is a fourth hypothesis and is rejected at runtime.
"""

from __future__ import annotations

import hashlib
import os
import sys
import uuid
from collections import Counter
from pathlib import Path

import yaml

from query_logger import ExpectedTargetTrace, LOG_PATH, log_row
from retrieve import RetrievalHit, _ensure_index, rank_all, scoring_config
from store import STORE_PATH


REPO_ROOT = Path(__file__).resolve().parent
EVAL_SET_PATH = REPO_ROOT / "eval_sets" / "docqa.yaml"
# Eval cutoff. Owned here, not by retrieve.py (whose default k=5 is a
# separate API default for evaluate.py / CLI callers). The trace records
# this runtime value.
TOP_K = 5

LOOP_ENV_TRUE = {"1", "true", "yes", "on"}


def env_flag_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in LOOP_ENV_TRUE


def qrl_loop_enabled() -> bool:
    """Opt-in H-QRL qrl-v1 loop."""
    return env_flag_on("LUNA_QUERY_LOOP")


def morph_loop_enabled() -> bool:
    """Opt-in H-MORPH morph-v1 loop. Isolates morphology; no identifiers."""
    return env_flag_on("LUNA_MORPH_LOOP")


def dense_h1_enabled() -> bool:
    """Opt-in H1 dense cosine. Original query text; no rewriting."""
    return env_flag_on("LUNA_DENSE_H1")


def loop_enabled() -> bool:
    """Any query-side loop. Default off so control tests keep using rank_all."""
    return qrl_loop_enabled() or morph_loop_enabled()


def rewrite_policy() -> str:
    """Active rewrite policy. morph-v1 wins if both flags are set."""
    if morph_loop_enabled():
        return "morph-v1"
    if qrl_loop_enabled():
        return "qrl-v1"
    return ""


def reject_combined_h1_and_rewrite() -> None:
    """H1 plus rewrite would be a fourth hypothesis. Fail loud."""
    if dense_h1_enabled() and loop_enabled():
        raise RuntimeError(
            "LUNA_DENSE_H1 cannot be combined with LUNA_QUERY_LOOP or "
            "LUNA_MORPH_LOOP; that would be a separate hypothesis"
        )


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
    """Hit when every expected section_id appears in the retrieved top-k.

    An empty expected list is not a reject: there is no unique-target
    membership to score, so this returns False. Callers must not treat
    that False as a miss when prediction is unmeasurable.
    """
    if not expected:
        return False
    return all(section_id in top_ids for section_id in expected)


def outcome_for(prediction: str, in_topk: bool) -> str:
    """Map retrieve result + current_stack_prediction to an outcome label.

    unmeasurable is not hit/miss/reject: retrieval still runs, but the
    current evaluation architecture cannot validly score the row (no
    reject path, no hop controller, or no unique expected section).
    """
    if prediction == "unmeasurable":
        return "unmeasurable"
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
    reject_combined_h1_and_rewrite()
    use_h1 = dense_h1_enabled()
    use_loop = loop_enabled()
    policy = rewrite_policy()
    cosine_term = "lexical_cosine"
    dense_index_sha256 = ""
    if use_h1:
        from dense_h1 import scoring_config_h1
        from dense_index import ensure_dense_index

        weights = scoring_config_h1()
        cosine_term = str(weights["cosine_term"])
    else:
        weights = scoring_config()
    _ensure_index()
    index_sha256 = sha256_file(index_path)
    if use_h1:
        _index, dense_index_sha256 = ensure_dense_index()
    cache = None
    tracker = None
    if use_loop:
        from query_cache import SemanticQueryCache
        from query_loop import rank_with_loop
        from query_tracker import QueryTracker

        cache = SemanticQueryCache()
        tracker = QueryTracker()
    results: list[dict] = []
    pass1_ids: list[list[str]] = []
    for row in rows:
        query = row["query"]
        expected = list(row.get("expected") or [])
        prediction = row.get("current_stack_prediction", "")
        rewritten_query = ""
        cache_hit = False
        expansions: list[str] = []
        if use_h1:
            from dense_h1 import rank_all_h1

            ranked = rank_all_h1(query)
        elif use_loop:
            looped = rank_with_loop(
                query,
                cache=cache,
                tracker=tracker,
                index_sha256=index_sha256,
                pass_number=1,
                policy=policy,
            )
            ranked = looped.ranked
            rewritten_query = looped.rewrite.rewritten
            cache_hit = looped.cache_hit
            expansions = list(looped.rewrite.expansions)
        else:
            ranked = rank_all(query)
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
            weight_cosine=float(weights["weight_cosine"]),
            weight_lexical=float(weights["weight_lexical"]),
            expected_targets=targets,
            rewritten_query=rewritten_query,
            cache_hit=cache_hit,
            expansions=expansions,
            loop_enabled=use_loop,
            rewrite_policy=policy,
            dense_h1_enabled=use_h1,
            cosine_term=cosine_term,
            dense_index_sha256=dense_index_sha256,
        )
        pass1_ids.append([hit.chunk.section_id for hit in ranked])
        results.append(
            {
                "id": row["id"],
                "failure_mode": row.get("failure_mode", ""),
                "prediction": prediction,
                "outcome": outcome,
                "query": query,
                "rewritten_query": rewritten_query,
                "cache_hit": cache_hit,
                "expansions": expansions,
                "expected": expected,
                "top_ids": top_ids,
                "hits": hits,
                "in_topk": in_topk,
                "run_uuid": run_uuid,
                "query_set_sha256": query_set_sha256,
                "index_sha256": index_sha256,
                "expected_targets": targets,
                "ranked": ranked,
                "loop_enabled": use_loop,
                "rewrite_policy": policy,
                "dense_h1_enabled": use_h1,
                "cosine_term": cosine_term,
                "dense_index_sha256": dense_index_sha256,
            }
        )

    if use_loop and cache is not None and tracker is not None:
        from query_loop import rank_with_loop

        pass2_ids: list[list[str]] = []
        for row in rows:
            looped = rank_with_loop(
                row["query"],
                cache=cache,
                tracker=tracker,
                index_sha256=index_sha256,
                pass_number=2,
                policy=policy,
            )
            pass2_ids.append([hit.chunk.section_id for hit in looped.ranked])
        payload = tracker.summary(
            index_sha256=index_sha256,
            serve_threshold=cache.serve_threshold,
            pass2_rank_identical=pass1_ids == pass2_ids,
            unique_keys=len(cache),
            policy=policy,
        )
        payload["collisions"] = list(cache.collisions)
        tracker.flush(
            LOG_PATH.with_name(f"{LOG_PATH.stem}_query_loop.json"), payload
        )
        if results:
            results[0]["query_loop_pass2_rank_identical"] = pass1_ids == pass2_ids
            results[0]["query_loop_pass2_hits"] = sum(
                1 for event in tracker.events if event.pass_number == 2 and event.cache_hit
            )
            results[0]["query_loop_pass1_hits"] = sum(
                1 for event in tracker.events if event.pass_number == 1 and event.cache_hit
            )

    return results


def print_results(manifest: dict, results: list[dict]) -> None:
    print(f"query_set: {manifest.get('query_set', '?')}")
    print(f"version: {manifest.get('version', '')}")
    print(f"rows: {len(results)}")
    print(f"governs: {manifest.get('governs', '')}")
    print(f"not_list: {manifest.get('not_list', '')}")
    if results:
        print(f"run_uuid: {results[0]['run_uuid']}")
        print(f"query_set_sha256: {results[0]['query_set_sha256']}")
        print(f"index_sha256: {results[0]['index_sha256']}")
        print(f"top_k: {TOP_K}")
        print(f"loop_enabled: {results[0].get('loop_enabled', False)}")
        print(f"rewrite_policy: {results[0].get('rewrite_policy', '')}")
        print(f"dense_h1_enabled: {results[0].get('dense_h1_enabled', False)}")
        print(f"cosine_term: {results[0].get('cosine_term', 'lexical_cosine')}")
        if results[0].get("dense_h1_enabled"):
            from dense_h1 import scoring_config_h1

            weights = scoring_config_h1()
            print(
                "scoring: 0.7 * dense_cosine + 0.3 * jaccard + alias "
                f"(weight_dense_cosine={weights['weight_dense_cosine']} "
                f"weight_jaccard={weights['weight_jaccard']})"
            )
            print(f"dense_index_sha256: {results[0].get('dense_index_sha256', '')}")
        else:
            weights = scoring_config()
            print(
                f"scoring: weight_cosine={weights['weight_cosine']} "
                f"weight_lexical={weights['weight_lexical']}"
            )
        if results[0].get("loop_enabled"):
            print(
                f"query_loop_pass1_hits: {results[0].get('query_loop_pass1_hits')}"
            )
            print(
                f"query_loop_pass2_hits: {results[0].get('query_loop_pass2_hits')}"
            )
            print(
                "query_loop_pass2_rank_identical: "
                f"{results[0].get('query_loop_pass2_rank_identical')}"
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
        if result.get("loop_enabled"):
            print(f"rewritten:    {result.get('rewritten_query', '')}")
            print(f"cache_hit:    {result.get('cache_hit', False)}")
            print(f"expansions:   {result.get('expansions', [])}")
        print(f"expected:     {result['expected']}")
        print(f"in_topk:      {result['in_topk']}")
        print("top-k:")
        for rank, hit in enumerate(result["hits"], start=1):
            print(
                f"  {rank}. {hit.chunk.section_id}"
                f"  score={hit.score:.3f}"
                f"  lexical_cosine={hit.lexical_cosine:.3f}"
                f"  dense_cosine={hit.dense_cosine:.3f}"
                f"  jaccard={hit.lexical:.3f}"
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
                f"  lexical_cosine={target.lexical_cosine}"
                f"  dense_cosine={target.dense_cosine}"
                f"  jaccard={target.lexical}"
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
        f"expected_miss={counts['expected_miss']}  "
        f"unmeasurable={counts['unmeasurable']}"
    )


def main() -> None:
    _configure_stdout()
    manifest, rows = load_eval_set()
    results = run_rows(rows)
    print_results(manifest, results)


if __name__ == "__main__":
    main()
