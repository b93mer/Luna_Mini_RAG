"""H1 dense-cosine path. Does not score H1 success on sealed ranks.

Flag-off control ranks stay locked in test_eval_telemetry.py.
H-QRL / H-MORPH remain covered by test_query_loop.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from query_logger import HitTrace
from retrieve import rank_all, retrieve
from run_query_set import load_eval_set, run_rows
from store import STORE_PATH, load_store


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

SEM_001_QUERY = (
    "What does the regime-related score represent when it contributes "
    "to the conviction assessment?"
)
LEX_001_QUERY = (
    "Which upstream market-condition measure supplies the consistency "
    "signal used when assessing trade confidence?"
)


class TestFlagOffFrozenBehavior(unittest.TestCase):
    def test_flag_off_run_rows_matches_control_topk(self):
        _, rows = load_eval_set()
        by_id = {row["id"]: row for row in rows}
        with patch.dict(
            os.environ,
            {
                "LUNA_DENSE_H1": "",
                "LUNA_QUERY_LOOP": "",
                "LUNA_MORPH_LOOP": "",
            },
            clear=False,
        ):
            with patch("run_query_set.log_row"):
                selected = [by_id[row_id] for row_id in CONTROL_TOP_IDS]
                results = run_rows(selected)
        result_by_id = {result["id"]: result for result in results}
        for row_id, top_ids in CONTROL_TOP_IDS.items():
            self.assertEqual(result_by_id[row_id]["top_ids"], top_ids)
            self.assertFalse(result_by_id[row_id]["dense_h1_enabled"])
            self.assertEqual(result_by_id[row_id]["query"], by_id[row_id]["query"])
            self.assertEqual(result_by_id[row_id]["rewritten_query"], "")
            self.assertEqual(result_by_id[row_id]["expansions"], [])
        for row_id, (_section, rank, _in_topk) in CONTROL_RANKS.items():
            target = result_by_id[row_id]["expected_targets"][0]
            self.assertEqual(target.rank, rank)

    def test_frozen_rank_all_does_not_compute_dense(self):
        ranked = rank_all(SEM_001_QUERY)
        self.assertEqual(len(ranked), 15)
        for hit in ranked:
            self.assertEqual(hit.dense_cosine, 0.0)
            self.assertEqual(hit.lexical_cosine, hit.cosine)
            reconstructed = 0.7 * hit.cosine + 0.3 * hit.lexical + hit.alias
            self.assertAlmostEqual(hit.score, reconstructed)
            self.assertEqual(hit.method, "hybrid")

    def test_frozen_retrieve_still_matches_rank_all(self):
        ranked = rank_all(SEM_001_QUERY)
        sliced = retrieve(SEM_001_QUERY, k=5)
        self.assertEqual(
            [hit.chunk.section_id for hit in sliced],
            [hit.chunk.section_id for hit in ranked[:5]],
        )


class TestDenseEncoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dense_embed import encode_query, encode_texts, get_encoder

        cls.encode_query = staticmethod(encode_query)
        cls.encode_texts = staticmethod(encode_texts)
        cls.encoder = get_encoder()

    def test_dimensionality_is_384(self):
        from dense_embed import EMBEDDING_DIM

        vector = self.encode_query("regime stability")
        self.assertEqual(len(vector), EMBEDDING_DIM)
        self.assertEqual(EMBEDDING_DIM, 384)

    def test_vectors_are_l2_normalized(self):
        from dense_embed import l2_norm

        vector = self.encode_query("regime stability")
        self.assertAlmostEqual(l2_norm(vector), 1.0, places=5)

    def test_embeddings_are_deterministic_within_tolerance(self):
        first = self.encode_query(SEM_001_QUERY)
        second = self.encode_query(SEM_001_QUERY)
        self.assertEqual(len(first), len(second))
        for left, right in zip(first, second):
            self.assertAlmostEqual(left, right, places=6)

    def test_same_encoder_for_query_and_chunk_strings(self):
        from dense_embed import MODEL_ID, MODEL_REVISION, model_identity

        identity = model_identity()
        self.assertEqual(identity["model_id"], MODEL_ID)
        self.assertEqual(identity["revision"], MODEL_REVISION)
        self.assertTrue(identity["same_encoder_for_query_and_chunks"])
        query_vec = self.encode_query("stability")
        chunk_vec = self.encode_texts(["stability"])[0]
        for left, right in zip(query_vec, chunk_vec):
            self.assertAlmostEqual(left, right, places=6)


class TestDenseIndexIdentity(unittest.TestCase):
    def test_section_vector_association_and_hash_validation(self):
        from dense_embed import EMBEDDING_DIM, l2_norm
        from dense_index import (
            build_dense_index,
            index_from_payload,
            save_dense_index,
            sha256_file,
            validate_dense_index,
        )

        store = load_store()
        self.assertIsNotNone(store)
        lexical_sha = hashlib.sha256(STORE_PATH.read_bytes()).hexdigest()
        index = build_dense_index(store, lexical_index_sha256=lexical_sha)
        self.assertEqual(len(index.rows), len(store.chunks))
        by_section = index.by_section_id()
        for chunk in store.chunks:
            row = by_section[chunk.section_id]
            self.assertEqual(row.chunk_id, chunk.chunk_id)
            self.assertEqual(
                row.content_sha256, chunk.provenance.get("content_sha256", "")
            )
            self.assertEqual(len(row.vector), EMBEDDING_DIM)
            self.assertAlmostEqual(l2_norm(row.vector), 1.0, places=5)
        validate_dense_index(index, store, lexical_index_sha256=lexical_sha)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dense_h1_index.json"
            dense_sha = save_dense_index(index, path)
            self.assertEqual(dense_sha, sha256_file(path))
            loaded = index_from_payload(json.loads(path.read_text(encoding="utf-8")))
            validate_dense_index(loaded, store, lexical_index_sha256=lexical_sha)
            loaded.rows[0].content_sha256 = "deadbeef"
            with self.assertRaises(ValueError):
                validate_dense_index(
                    loaded, store, lexical_index_sha256=lexical_sha
                )


class TestH1ScorerAndQueryPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dense_h1 import rank_all_h1
        from dense_index import build_dense_index
        from store import load_store

        store = load_store()
        lexical_sha = hashlib.sha256(STORE_PATH.read_bytes()).hexdigest()
        cls.store = store
        cls.dense_index = build_dense_index(store, lexical_index_sha256=lexical_sha)
        cls.rank_all_h1 = staticmethod(rank_all_h1)

    def test_formula_matches_preregistration(self):
        from dense_h1 import DENSE_COSINE_WEIGHT, JACCARD_WEIGHT, scoring_config_h1

        cfg = scoring_config_h1()
        self.assertEqual(DENSE_COSINE_WEIGHT, 0.7)
        self.assertEqual(JACCARD_WEIGHT, 0.3)
        self.assertEqual(cfg["cosine_term"], "dense_cosine")
        hits = self.rank_all_h1(
            SEM_001_QUERY, store=self.store, dense_index=self.dense_index
        )
        self.assertTrue(hits)
        for hit in hits:
            reconstructed = (
                0.7 * hit.dense_cosine + 0.3 * hit.lexical + hit.alias
            )
            self.assertAlmostEqual(hit.score, reconstructed, places=6)
            self.assertEqual(hit.method, "hybrid-h1")
            self.assertEqual(hit.lexical_cosine, hit.cosine)

    def test_h1_does_not_rewrite_or_expand_queries(self):
        from dense_h1 import rank_all_h1

        source = (REPO_ROOT / "dense_h1.py").read_text(encoding="utf-8")
        embed_src = (REPO_ROOT / "dense_embed.py").read_text(encoding="utf-8")
        for text in (source, embed_src):
            self.assertNotIn("rewrite_query", text)
            self.assertNotIn("query_rewrite", text)
            self.assertNotIn("FUNCTION_WORDS", text)
            self.assertNotIn("identifier_expansions", text)
            self.assertNotIn("regime_stability", text)
        hits = rank_all_h1(
            LEX_001_QUERY, store=self.store, dense_index=self.dense_index
        )
        self.assertTrue(hits)
        self.assertNotIn("stability", LEX_001_QUERY)
        self.assertNotIn("vwap_dist", LEX_001_QUERY)

    def test_original_query_preserved_in_h1_run_rows(self):
        logged = []

        def capture(**kwargs):
            logged.append(kwargs)

        _, rows = load_eval_set()
        by_id = {row["id"]: row for row in rows}
        selected = [by_id["qse-docqa-sem-001"], by_id["qse-docqa-lex-001"]]
        with patch.dict(
            os.environ,
            {
                "LUNA_DENSE_H1": "1",
                "LUNA_QUERY_LOOP": "",
                "LUNA_MORPH_LOOP": "",
            },
            clear=False,
        ):
            with patch("run_query_set.log_row", side_effect=capture):
                with patch(
                    "dense_index.ensure_dense_index",
                    return_value=(self.dense_index, "dense-sha-test"),
                ), patch(
                    "dense_h1.ensure_dense_index",
                    return_value=(self.dense_index, "dense-sha-test"),
                ):
                    results = run_rows(selected)
        self.assertEqual(len(results), 2)
        for result, entry in zip(results, logged):
            original = by_id[result["id"]]["query"]
            self.assertEqual(result["query"], original)
            self.assertEqual(entry["query"], original)
            self.assertEqual(result["rewritten_query"], "")
            self.assertEqual(result["expansions"], [])
            self.assertTrue(result["dense_h1_enabled"])
            self.assertFalse(result["loop_enabled"])
            self.assertEqual(result["cosine_term"], "dense_cosine")
            self.assertEqual(entry["cosine_term"], "dense_cosine")
            self.assertEqual(entry["rewritten_query"], "")
            self.assertEqual(entry["expansions"], [])
            gold = result["expected_targets"][0]
            self.assertIsNotNone(gold.dense_cosine)
            self.assertIsNotNone(gold.lexical_cosine)
            top = HitTrace.from_hit(result["hits"][0])
            self.assertIn("lexical_cosine", top.__dict__)
            self.assertIn("dense_cosine", top.__dict__)

    def test_logging_exposes_named_score_components(self):
        hits = self.rank_all_h1(
            SEM_001_QUERY, store=self.store, dense_index=self.dense_index
        )
        trace = HitTrace.from_hit(hits[0])
        self.assertNotEqual(trace.dense_cosine, 0.0)
        self.assertEqual(trace.lexical, round(hits[0].lexical, 6))
        self.assertEqual(trace.alias, round(hits[0].alias, 6))
        self.assertEqual(trace.lexical_cosine, round(hits[0].lexical_cosine, 6))
        self.assertEqual(trace.dense_cosine, round(hits[0].dense_cosine, 6))
        self.assertEqual(trace.cosine, round(hits[0].cosine, 6))

    def test_h1_cannot_combine_with_rewrite_flags(self):
        _, rows = load_eval_set()
        with patch.dict(
            os.environ,
            {"LUNA_DENSE_H1": "1", "LUNA_QUERY_LOOP": "1", "LUNA_MORPH_LOOP": ""},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                run_rows(rows[:1])
        with patch.dict(
            os.environ,
            {"LUNA_DENSE_H1": "1", "LUNA_QUERY_LOOP": "", "LUNA_MORPH_LOOP": "1"},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                run_rows(rows[:1])


class TestHistoricalModesRemainCallable(unittest.TestCase):
    def test_qrl_and_morph_rewrite_still_callable(self):
        from query_rewrite import REWRITE_POLICY_MORPH, rewrite_query

        store = load_store()
        self.assertIsNotNone(store)
        qrl = rewrite_query(SEM_001_QUERY, store.vocab, store.idf)
        morph = rewrite_query(
            SEM_001_QUERY, store.vocab, store.idf, policy=REWRITE_POLICY_MORPH
        )
        self.assertTrue(qrl.identifier_expansions)
        self.assertEqual(morph.identifier_expansions, [])
        self.assertTrue(morph.rewritten.startswith(SEM_001_QUERY))

    def test_frozen_rank_all_still_callable_under_h1_modules(self):
        ranked = rank_all(SEM_001_QUERY)
        rank = next(
            i
            for i, hit in enumerate(ranked, start=1)
            if hit.chunk.section_id == "1_upstream_producer_score_definition"
        )
        self.assertEqual(rank, 10)


if __name__ == "__main__":
    unittest.main()
