"""Expected-target telemetry observes rank_all without changing outcomes.

Patches log_row so tests do not write eval_sets/runs/*.jsonl.
"""

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from query_logger import ExpectedTargetTrace, HitTrace
from retrieve import rank_all, retrieve, scoring_config
from run_query_set import (
    EVAL_SET_PATH,
    TOP_K,
    expected_target_traces,
    load_eval_set,
    run_rows,
    sha256_file,
)
from store import STORE_PATH


CONTROL_RANKS = {
    "qse-docqa-sem-001": ("1_upstream_producer_score_definition", 10, False),
    "qse-docqa-sem-002": ("impact_on_finding_3_5_disposition", 2, True),
    "qse-docqa-lex-001": ("1_upstream_producer_score_definition", 7, False),
}

CONTROL_OUTCOMES = {
    "qse-docqa-sem-001": "expected_miss",
    "qse-docqa-sem-002": "hit",
    "qse-docqa-lex-001": "expected_miss",
}

CONTROL_TOP_IDS = {
    "qse-docqa-sem-001": [
        "verdict",
        "question",
        "impact_on_finding_3_5_disposition",
        "2_state_stamp_before_conviction",
        "3_conviction_factor_entry_the_field_under_audit",
    ],
    "qse-docqa-sem-002": [
        "verdict",
        "impact_on_finding_3_5_disposition",
        "question",
        "input_fields_consumed",
        "3_conviction_factor_entry_the_field_under_audit",
    ],
    "qse-docqa-lex-001": [
        "upstream_signals_since_verdict_independent",
        "verdict",
        "impact_on_finding_3_5_disposition",
        "3_conviction_factor_entry_the_field_under_audit",
        "2_state_stamp_before_conviction",
    ],
}


class TestEvalTelemetry(unittest.TestCase):
    def test_control_expected_target_ranks(self):
        _, rows = load_eval_set()
        by_id = {row["id"]: row for row in rows}
        for row_id, (section_id, rank, in_topk) in CONTROL_RANKS.items():
            row = by_id[row_id]
            ranked = rank_all(row["query"])
            self.assertEqual(len(ranked), 15)
            traces = expected_target_traces(row["expected"], ranked, TOP_K)
            self.assertEqual(len(traces), 1)
            target = traces[0]
            self.assertEqual(target.section_id, section_id)
            self.assertEqual(target.rank, rank)
            self.assertEqual(target.in_topk, in_topk)
            self.assertEqual(target.in_topk, rank <= TOP_K)
            live = ranked[rank - 1]
            self.assertEqual(live.chunk.section_id, section_id)
            self.assertEqual(target.score, round(live.score, 6))
            self.assertEqual(target.cosine, round(live.cosine, 6))
            self.assertEqual(target.lexical, round(live.lexical, 6))
            self.assertEqual(target.alias, round(live.alias, 6))

    def test_control_topk_and_outcomes_unchanged(self):
        with patch("run_query_set.log_row"):
            _, rows = load_eval_set()
            results = run_rows(rows)
        by_id = {result["id"]: result for result in results}
        for row_id, top_ids in CONTROL_TOP_IDS.items():
            result = by_id[row_id]
            self.assertEqual(result["top_ids"], top_ids)
            self.assertEqual(result["outcome"], CONTROL_OUTCOMES[row_id])
            sliced = retrieve(result["query"], k=TOP_K)
            self.assertEqual(
                [hit.chunk.section_id for hit in sliced],
                result["top_ids"],
            )

    def test_one_run_uuid_distinct_query_rows(self):
        with patch("run_query_set.log_row"):
            _, rows = load_eval_set()
            results = run_rows(rows)
        run_ids = {result["run_uuid"] for result in results}
        self.assertEqual(len(run_ids), 1)
        self.assertEqual(len(results), 3)

    def test_hashes_match_files_on_disk(self):
        with patch("run_query_set.log_row"):
            _, rows = load_eval_set()
            results = run_rows(rows)
        self.assertTrue(results)
        self.assertEqual(
            results[0]["query_set_sha256"],
            hashlib.sha256(EVAL_SET_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            results[0]["index_sha256"],
            hashlib.sha256(STORE_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            results[0]["query_set_sha256"],
            sha256_file(EVAL_SET_PATH),
        )

    def test_missing_expected_section_is_not_in_topk(self):
        ranked = rank_all(
            "What is the question about conviction_detail.factors regime?"
        )
        traces = expected_target_traces(["does_not_exist"], ranked, TOP_K)
        self.assertEqual(len(traces), 1)
        self.assertIsNone(traces[0].rank)
        self.assertFalse(traces[0].in_topk)

    def test_in_topk_target_matches_hit_trace_components(self):
        _, rows = load_eval_set()
        row = next(r for r in rows if r["id"] == "qse-docqa-sem-002")
        ranked = rank_all(row["query"])
        hits = ranked[:TOP_K]
        target = expected_target_traces(row["expected"], ranked, TOP_K)[0]
        hit_trace = HitTrace.from_hit(hits[target.rank - 1])
        self.assertEqual(target.section_id, hit_trace.section_id)
        self.assertEqual(target.score, hit_trace.score)
        self.assertEqual(target.cosine, hit_trace.cosine)
        self.assertEqual(target.lexical, hit_trace.lexical)
        self.assertEqual(target.alias, hit_trace.alias)
        self.assertIsInstance(target, ExpectedTargetTrace)

    def test_runner_config_matches_retrieve_and_topk(self):
        self.assertEqual(TOP_K, 5)
        cfg = scoring_config()
        self.assertEqual(cfg["weight_cosine"], 0.7)
        self.assertEqual(cfg["weight_lexical"], 0.3)


if __name__ == "__main__":
    unittest.main()
