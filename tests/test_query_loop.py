"""Query-side rewrite/cache loop mechanics. Does not score H-QRL success.

Flag-off control ranks stay locked in test_eval_telemetry.py.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from embed import cosine_similarity, model_from_store
from query_cache import SemanticQueryCache
from query_loop import rank_with_loop
from query_rewrite import FUNCTION_WORDS, REWRITE_POLICY_MORPH, rewrite_query
from query_tracker import QueryTracker
from retrieve import rank_all
from run_query_set import load_eval_set, run_rows
from store import load_store


REPO_ROOT = Path(__file__).resolve().parents[1]

CONTROL_RANKS = {
    "qse-docqa-sem-001": ("1_upstream_producer_score_definition", 10, False),
    "qse-docqa-sem-002": ("impact_on_finding_3_5_disposition", 2, True),
    "qse-docqa-lex-001": ("1_upstream_producer_score_definition", 7, False),
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


class TestQueryRewrite(unittest.TestCase):
    def setUp(self):
        store = load_store()
        self.assertIsNotNone(store)
        self.store = store
        self.vocab = store.vocab
        self.idf = store.idf

    def test_rewrite_is_deterministic(self):
        query = "What does the regime-related score represent when it contributes to the conviction assessment?"
        first = rewrite_query(query, self.vocab, self.idf)
        second = rewrite_query(query, self.vocab, self.idf)
        self.assertEqual(first, second)

    def test_function_words_are_dropped(self):
        result = rewrite_query("What is the regime?", self.vocab, self.idf)
        self.assertNotIn("what", result.content_tokens)
        self.assertNotIn("is", result.content_tokens)
        self.assertNotIn("the", result.content_tokens)
        self.assertIn("regime", result.content_tokens)
        for token in result.content_tokens:
            self.assertNotIn(token, FUNCTION_WORDS)

    def test_no_synonym_invention_for_lex_001(self):
        query = (
            "Which upstream market-condition measure supplies the consistency "
            "signal used when assessing trade confidence?"
        )
        result = rewrite_query(query, self.vocab, self.idf)
        self.assertNotIn("stability", result.expansions)
        self.assertNotIn("vwap_dist", result.expansions)
        self.assertNotIn("stability", result.content_tokens)
        self.assertIn("consistency", result.content_tokens)

    def test_morphology_adds_in_vocab_plural(self):
        self.assertIn("thresholds", self.vocab)
        result = rewrite_query("threshold", self.vocab, self.idf)
        self.assertIn("thresholds", result.morphology)
        self.assertIn("thresholds", result.expansions)

    def test_identifier_segment_can_bridge_regime(self):
        self.assertIn("regime_stability", self.vocab)
        result = rewrite_query("regime", self.vocab, self.idf)
        self.assertTrue(result.identifier_expansions)
        for token in result.identifier_expansions:
            self.assertIn("regime", token.replace(".", "_").split("_"))
            self.assertNotEqual(token, "regime")

    def test_rewrite_module_has_no_row_or_gold_branches(self):
        source = (REPO_ROOT / "query_rewrite.py").read_text(encoding="utf-8")
        self.assertNotIn("qse-docqa", source)
        self.assertNotIn("1_upstream_producer_score_definition", source)
        self.assertNotIn("expected_miss", source)


class TestMorphologyOnlyRewrite(unittest.TestCase):
    def setUp(self):
        store = load_store()
        self.assertIsNotNone(store)
        self.store = store
        self.vocab = store.vocab
        self.idf = store.idf

    def test_identifier_expansion_cannot_fire(self):
        self.assertIn("regime_stability", self.vocab)
        self.assertIn("regime_update_interval_seconds", self.vocab)
        result = rewrite_query(
            "regime", self.vocab, self.idf, policy=REWRITE_POLICY_MORPH
        )
        self.assertEqual(result.identifier_expansions, [])
        self.assertNotIn("regime_stability", result.expansions)
        self.assertNotIn("regime_update_interval_seconds", result.rewritten)
        qrl = rewrite_query("regime", self.vocab, self.idf)
        self.assertTrue(qrl.identifier_expansions)

    def test_sealed_queries_never_emit_identifiers(self):
        _, rows = load_eval_set()
        for row in rows:
            result = rewrite_query(
                row["query"], self.vocab, self.idf, policy=REWRITE_POLICY_MORPH
            )
            self.assertEqual(result.identifier_expansions, [])
            self.assertNotIn("regime_update_interval_seconds", result.rewritten)
            self.assertNotIn("regime_update_interval_seconds", result.expansions)

    def test_morphology_only_emits_in_vocab_variants(self):
        vocab = {"cat": 0, "cats": 1}
        result = rewrite_query("cat", vocab, [], policy=REWRITE_POLICY_MORPH)
        self.assertEqual(result.morphology, ["cats"])
        self.assertEqual(result.identifier_expansions, [])
        self.assertEqual(result.rewritten, "cat cats")

    def test_morphology_only_does_not_emit_oov(self):
        vocab = {"cat": 0}
        result = rewrite_query("cat", vocab, [], policy=REWRITE_POLICY_MORPH)
        self.assertEqual(result.morphology, [])
        self.assertEqual(result.rewritten, "cat")

    def test_morphology_does_not_cascade_recursively(self):
        vocab = {"threshold": 0, "thresholds": 1, "thresholdses": 2}
        result = rewrite_query(
            "threshold", vocab, [], policy=REWRITE_POLICY_MORPH
        )
        self.assertEqual(result.morphology, ["thresholds"])
        self.assertNotIn("thresholdses", result.morphology)
        self.assertEqual(result.rewritten, "threshold thresholds")

    def test_function_words_are_kept(self):
        result = rewrite_query(
            "What is the regime?", self.vocab, self.idf, policy=REWRITE_POLICY_MORPH
        )
        self.assertEqual(result.stopwords_dropped, [])
        self.assertEqual(result.original, "What is the regime?")
        self.assertTrue(result.rewritten.startswith("What is the regime?"))
        self.assertIn("what", result.content_tokens)
        self.assertIn("is", result.content_tokens)
        self.assertIn("the", result.content_tokens)
        self.assertIn("the", FUNCTION_WORDS)

    def test_spec_002_emits_thresholds_and_preserves_original(self):
        query = (
            "Which four labels can the percentile-threshold rule assign, "
            "including the in-between and missing-data cases?"
        )
        result = rewrite_query(
            query, self.vocab, self.idf, policy=REWRITE_POLICY_MORPH
        )
        self.assertIn("thresholds", self.vocab)
        self.assertIn("thresholds", result.morphology)
        self.assertTrue(result.rewritten.startswith(query))
        self.assertEqual(result.original, query)
        self.assertEqual(result.identifier_expansions, [])
        self.assertNotIn("stability", result.expansions)

    def test_no_synonym_invention_for_lex_001(self):
        query = (
            "Which upstream market-condition measure supplies the consistency "
            "signal used when assessing trade confidence?"
        )
        result = rewrite_query(
            query, self.vocab, self.idf, policy=REWRITE_POLICY_MORPH
        )
        self.assertNotIn("stability", result.expansions)
        self.assertNotIn("vwap_dist", result.expansions)
        self.assertEqual(result.original, query)

    def test_unknown_policy_raises(self):
        with self.assertRaises(ValueError):
            rewrite_query("regime", self.vocab, self.idf, policy="not-a-policy")


class TestSemanticCache(unittest.TestCase):
    def setUp(self):
        store = load_store()
        self.assertIsNotNone(store)
        self.store = store
        self.model = model_from_store(store.vocab, store.idf)
        self.index_sha256 = "abc123"

    def test_miss_then_hit_on_identical_rewritten_query(self):
        cache = SemanticQueryCache()
        query = "regime score"
        vector = self.model.transform([query])[0]
        ranked = rank_all(query)
        first = cache.lookup(query, vector, self.index_sha256)
        self.assertFalse(first.hit)
        cache.store(query, vector, self.index_sha256, ranked)
        second = cache.lookup(query, vector, self.index_sha256)
        self.assertTrue(second.hit)
        self.assertIsNotNone(second.nearest_cosine)
        self.assertGreaterEqual(second.nearest_cosine, 0.99)
        hydrated = cache.rehydrate(second.ranking, self.store)
        self.assertEqual(
            [hit.chunk.section_id for hit in hydrated],
            [hit.chunk.section_id for hit in ranked],
        )

    def test_invalidates_on_index_hash_change(self):
        cache = SemanticQueryCache()
        query = "regime score"
        vector = self.model.transform([query])[0]
        ranked = rank_all(query)
        cache.store(query, vector, "hash-a", ranked)
        miss = cache.lookup(query, vector, "hash-b")
        self.assertFalse(miss.hit)
        cache.store(query, vector, "hash-b", ranked)
        self.assertEqual(len(cache), 1)
        self.assertEqual(cache._entries[0].index_sha256, "hash-b")

    def test_identical_oov_query_is_a_hit_despite_zero_cosine(self):
        cache = SemanticQueryCache()
        query = "zzzznotinvocab"
        vector = self.model.transform([query])[0]
        self.assertTrue(all(value == 0.0 for value in vector))
        ranked = rank_all(query)
        cache.store(query, vector, self.index_sha256, ranked)
        lookup = cache.lookup(query, vector, self.index_sha256)
        self.assertTrue(lookup.hit)
        self.assertEqual(lookup.nearest_cosine, 0.0)

    def test_collision_with_different_text_is_not_served(self):
        cache = SemanticQueryCache()
        left = "regime score"
        vector = self.model.transform([left])[0]
        ranked = rank_all(left)
        cache.store(left, vector, self.index_sha256, ranked)
        lookup = cache.lookup("other rewritten text", vector, self.index_sha256)
        self.assertFalse(lookup.hit)
        self.assertTrue(lookup.collision)
        self.assertEqual(len(cache.collisions), 1)


class TestQueryLoop(unittest.TestCase):
    def setUp(self):
        store = load_store()
        self.assertIsNotNone(store)
        self.store = store
        self.index_sha256 = "loop-test-hash"

    def test_tracker_does_not_change_rank_all_output(self):
        query = (
            "What does the regime-related score represent when it contributes "
            "to the conviction assessment?"
        )
        rewrite = rewrite_query(query, self.store.vocab, self.store.idf)
        frozen = rank_all(rewrite.rewritten)
        cache = SemanticQueryCache()
        tracker = QueryTracker()
        looped = rank_with_loop(
            query,
            cache=cache,
            tracker=tracker,
            index_sha256=self.index_sha256,
            store=self.store,
        )
        self.assertEqual(
            [hit.chunk.section_id for hit in looped.ranked],
            [hit.chunk.section_id for hit in frozen],
        )
        self.assertEqual(len(tracker.events), 1)
        self.assertFalse(looped.cache_hit)
        second = rank_with_loop(
            query,
            cache=cache,
            tracker=tracker,
            index_sha256=self.index_sha256,
            store=self.store,
        )
        self.assertTrue(second.cache_hit)
        self.assertEqual(
            [hit.chunk.section_id for hit in second.ranked],
            [hit.chunk.section_id for hit in frozen],
        )

    def test_sealed_rewritten_queries_do_not_collide(self):
        _, rows = load_eval_set()
        model = model_from_store(self.store.vocab, self.store.idf)
        rewritten = [
            rewrite_query(row["query"], self.store.vocab, self.store.idf).rewritten
            for row in rows
        ]
        vectors = model.transform(rewritten)
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                cosine = cosine_similarity(vectors[i], vectors[j])
                self.assertLess(
                    cosine,
                    0.99,
                    msg=f"{rows[i]['id']} vs {rows[j]['id']} cosine={cosine}",
                )

    def test_flag_off_run_rows_matches_control_topk(self):
        with patch.dict(
            os.environ, {"LUNA_QUERY_LOOP": "", "LUNA_MORPH_LOOP": ""}, clear=False
        ):
            with patch("run_query_set.log_row"):
                _, rows = load_eval_set()
                by_id = {row["id"]: row for row in rows}
                selected = [by_id[row_id] for row_id in CONTROL_TOP_IDS]
                results = run_rows(selected)
        result_by_id = {result["id"]: result for result in results}
        for row_id, top_ids in CONTROL_TOP_IDS.items():
            self.assertEqual(result_by_id[row_id]["top_ids"], top_ids)
            self.assertFalse(result_by_id[row_id]["loop_enabled"])
        for row_id, (_section, rank, _in_topk) in CONTROL_RANKS.items():
            target = result_by_id[row_id]["expected_targets"][0]
            self.assertEqual(target.rank, rank)

    def test_loop_on_pass2_is_cache_hit_with_identical_ranks(self):
        with patch.dict(
            os.environ, {"LUNA_QUERY_LOOP": "1", "LUNA_MORPH_LOOP": ""}, clear=False
        ):
            with patch("run_query_set.log_row"), patch(
                "query_tracker.QueryTracker.flush"
            ):
                _, rows = load_eval_set()
                results = run_rows(rows)
        self.assertTrue(results[0]["loop_enabled"])
        self.assertEqual(results[0]["query_loop_pass1_hits"], 0)
        self.assertEqual(results[0]["query_loop_pass2_hits"], 12)
        self.assertTrue(results[0]["query_loop_pass2_rank_identical"])
        for result in results:
            frozen = rank_all(result["rewritten_query"])
            self.assertEqual(
                [hit.chunk.section_id for hit in result["ranked"]],
                [hit.chunk.section_id for hit in frozen],
            )

    def test_morph_flag_off_run_rows_matches_control_topk(self):
        _, rows = load_eval_set()
        by_id = {row["id"]: row for row in rows}
        with patch.dict(
            os.environ, {"LUNA_QUERY_LOOP": "", "LUNA_MORPH_LOOP": ""}, clear=False
        ):
            with patch("run_query_set.log_row"):
                selected = [by_id[row_id] for row_id in CONTROL_TOP_IDS]
                results = run_rows(selected)
        result_by_id = {result["id"]: result for result in results}
        for row_id, top_ids in CONTROL_TOP_IDS.items():
            self.assertEqual(result_by_id[row_id]["top_ids"], top_ids)
            self.assertFalse(result_by_id[row_id]["loop_enabled"])
            self.assertEqual(result_by_id[row_id]["rewrite_policy"], "")
            self.assertEqual(result_by_id[row_id]["query"], by_id[row_id]["query"])

    def test_morph_loop_preserves_original_queries_in_records(self):
        logged = []

        def capture(**kwargs):
            logged.append(kwargs)

        _, rows = load_eval_set()
        with patch.dict(
            os.environ, {"LUNA_QUERY_LOOP": "", "LUNA_MORPH_LOOP": "1"}, clear=False
        ):
            with patch("run_query_set.log_row", side_effect=capture), patch(
                "query_tracker.QueryTracker.flush"
            ):
                results = run_rows(rows)
        yaml_by_id = {row["id"]: row["query"] for row in rows}
        self.assertEqual(len(logged), 12)
        for result, entry in zip(results, logged):
            original = yaml_by_id[result["id"]]
            self.assertEqual(result["query"], original)
            self.assertEqual(entry["query"], original)
            self.assertEqual(result["rewrite_policy"], "morph-v1")
            self.assertTrue(result["loop_enabled"])
            if result["rewritten_query"] != original:
                self.assertTrue(result["rewritten_query"].startswith(original))

    def test_morph_loop_on_pass2_is_cache_hit_with_identical_ranks(self):
        with patch.dict(
            os.environ, {"LUNA_QUERY_LOOP": "", "LUNA_MORPH_LOOP": "1"}, clear=False
        ):
            with patch("run_query_set.log_row"), patch(
                "query_tracker.QueryTracker.flush"
            ):
                _, rows = load_eval_set()
                results = run_rows(rows)
        self.assertTrue(results[0]["loop_enabled"])
        self.assertEqual(results[0]["rewrite_policy"], "morph-v1")
        self.assertEqual(results[0]["query_loop_pass1_hits"], 0)
        self.assertEqual(results[0]["query_loop_pass2_hits"], 12)
        self.assertTrue(results[0]["query_loop_pass2_rank_identical"])
        for result in results:
            frozen = rank_all(result["rewritten_query"])
            self.assertEqual(
                [hit.chunk.section_id for hit in result["ranked"]],
                [hit.chunk.section_id for hit in frozen],
            )

    def test_morph_tracker_does_not_change_rank_all_output(self):
        query = (
            "Which four labels can the percentile-threshold rule assign, "
            "including the in-between and missing-data cases?"
        )
        rewrite = rewrite_query(
            query, self.store.vocab, self.store.idf, policy=REWRITE_POLICY_MORPH
        )
        frozen = rank_all(rewrite.rewritten)
        cache = SemanticQueryCache()
        tracker = QueryTracker()
        looped = rank_with_loop(
            query,
            cache=cache,
            tracker=tracker,
            index_sha256=self.index_sha256,
            store=self.store,
            policy=REWRITE_POLICY_MORPH,
        )
        self.assertEqual(
            [hit.chunk.section_id for hit in looped.ranked],
            [hit.chunk.section_id for hit in frozen],
        )
        self.assertEqual(len(tracker.events), 1)
        self.assertEqual(tracker.events[0].rewrite_policy, "morph-v1")
        self.assertEqual(tracker.events[0].identifier_expansions, [])
        self.assertFalse(looped.cache_hit)
        second = rank_with_loop(
            query,
            cache=cache,
            tracker=tracker,
            index_sha256=self.index_sha256,
            store=self.store,
            policy=REWRITE_POLICY_MORPH,
        )
        self.assertTrue(second.cache_hit)
        self.assertEqual(
            [hit.chunk.section_id for hit in second.ranked],
            [hit.chunk.section_id for hit in frozen],
        )

    def test_morph_sealed_rewritten_queries_do_not_collide(self):
        _, rows = load_eval_set()
        model = model_from_store(self.store.vocab, self.store.idf)
        rewritten = [
            rewrite_query(
                row["query"],
                self.store.vocab,
                self.store.idf,
                policy=REWRITE_POLICY_MORPH,
            ).rewritten
            for row in rows
        ]
        vectors = model.transform(rewritten)
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                cosine = cosine_similarity(vectors[i], vectors[j])
                self.assertLess(
                    cosine,
                    0.99,
                    msg=f"{rows[i]['id']} vs {rows[j]['id']} cosine={cosine}",
                )


if __name__ == "__main__":
    unittest.main()
