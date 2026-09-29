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
    expected_in_topk,
    expected_target_traces,
    load_eval_set,
    outcome_for,
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

CALIBRATION_QUERIES = {
    "qse-docqa-sem-001": (
        "What does the regime-related score represent when it contributes "
        "to the conviction assessment?"
    ),
    "qse-docqa-sem-002": (
        "What does the regime control determine about the status of the "
        "existing finding?"
    ),
    "qse-docqa-lex-001": (
        "Which upstream market-condition measure supplies the consistency "
        "signal used when assessing trade confidence?"
    ),
}

EXPANDED_ROW_IDS = [
    "qse-docqa-sem-001",
    "qse-docqa-sem-002",
    "qse-docqa-sem-003",
    "qse-docqa-lex-001",
    "qse-docqa-lex-002",
    "qse-docqa-spec-001",
    "qse-docqa-spec-002",
    "qse-docqa-mch-001",
    "qse-docqa-ood-001",
    "qse-docqa-ood-002",
    "qse-docqa-ood-003",
    "qse-docqa-hop-001",
]

UNMEASURABLE_IDS = {
    "qse-docqa-spec-001",
    "qse-docqa-ood-001",
    "qse-docqa-ood-002",
    "qse-docqa-ood-003",
    "qse-docqa-hop-001",
}


def _calibration_rows(rows: list[dict]) -> list[dict]:
    """Retrieve only the frozen three-row anchors during unit tests."""
    return [row for row in rows if row["id"] in CONTROL_RANKS]


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
            results = run_rows(_calibration_rows(rows))
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
            results = run_rows(_calibration_rows(rows))
        run_ids = {result["run_uuid"] for result in results}
        self.assertEqual(len(run_ids), 1)
        self.assertEqual(len(results), 3)

    def test_hashes_match_files_on_disk(self):
        with patch("run_query_set.log_row"):
            _, rows = load_eval_set()
            results = run_rows(_calibration_rows(rows))
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

    def test_expanded_manifest_and_row_ids_are_sealed(self):
        manifest, rows = load_eval_set()
        self.assertEqual(manifest.get("version"), "docqa-expanded-v1")
        self.assertEqual([row["id"] for row in rows], EXPANDED_ROW_IDS)
        self.assertEqual(len(rows), 12)

    def test_calibration_rows_not_rewritten(self):
        _, rows = load_eval_set()
        by_id = {row["id"]: row for row in rows}
        for row_id, query in CALIBRATION_QUERIES.items():
            self.assertEqual(by_id[row_id]["query"], query)
            self.assertEqual(by_id[row_id]["expected"], [CONTROL_RANKS[row_id][0]])
            self.assertEqual(
                by_id[row_id]["current_stack_prediction"], "expected_miss"
            )

    def test_unmeasurable_rows_have_no_expected_section(self):
        _, rows = load_eval_set()
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(set(UNMEASURABLE_IDS), {
            row["id"]
            for row in rows
            if row.get("current_stack_prediction") == "unmeasurable"
        })
        for row_id in UNMEASURABLE_IDS:
            self.assertEqual(list(by_id[row_id].get("expected") or []), [])

    def test_unmeasurable_prediction_is_not_scored_as_miss(self):
        self.assertEqual(outcome_for("unmeasurable", False), "unmeasurable")
        self.assertEqual(outcome_for("unmeasurable", True), "unmeasurable")
        self.assertEqual(outcome_for("expected_miss", False), "expected_miss")
        self.assertEqual(outcome_for("supported", True), "hit")
        self.assertEqual(outcome_for("supported", False), "miss")

    def test_expected_in_topk_requires_all_targets(self):
        self.assertTrue(expected_in_topk(["a", "b"], ["a", "b", "c"]))
        self.assertFalse(expected_in_topk(["a", "b"], ["a", "c"]))
        self.assertFalse(expected_in_topk([], ["a"]))


if __name__ == "__main__":
    unittest.main()
