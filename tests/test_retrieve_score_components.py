"""Hybrid RetrievalHit components reconstruct the blended score.

Uses the live store the same way evaluate.py does. Does not change
retrieve_by_section_id; that path keeps the 0.0 component defaults.
"""

import unittest

from retrieve import (
    COSINE_WEIGHT,
    LEXICAL_WEIGHT,
    rank_all,
    retrieve,
    scoring_config,
)


QUERY = "What is the question about conviction_detail.factors regime?"


class TestRetrieveScoreComponents(unittest.TestCase):
    def test_weighted_components_sum_to_score(self):
        hits = retrieve(QUERY, k=3)
        self.assertTrue(hits)
        hit = hits[0]
        reconstructed = 0.7 * hit.cosine + 0.3 * hit.lexical + hit.alias
        self.assertAlmostEqual(hit.score, reconstructed)

    def test_scoring_config_is_the_live_blend(self):
        cfg = scoring_config()
        self.assertEqual(cfg["weight_cosine"], COSINE_WEIGHT)
        self.assertEqual(cfg["weight_lexical"], LEXICAL_WEIGHT)
        self.assertEqual(COSINE_WEIGHT, 0.7)
        self.assertEqual(LEXICAL_WEIGHT, 0.3)
        hit = retrieve(QUERY, k=1)[0]
        reconstructed = (
            cfg["weight_cosine"] * hit.cosine
            + cfg["weight_lexical"] * hit.lexical
            + hit.alias
        )
        self.assertAlmostEqual(hit.score, reconstructed)

    def test_retrieve_is_rank_all_truncated(self):
        ranked = rank_all(QUERY)
        for k in (1, 3, 5, len(ranked)):
            sliced = retrieve(QUERY, k=k)
            self.assertEqual(len(sliced), k)
            for left, right in zip(sliced, ranked[:k]):
                self.assertEqual(left.chunk.section_id, right.chunk.section_id)
                self.assertEqual(left.score, right.score)
                self.assertEqual(left.cosine, right.cosine)
                self.assertEqual(left.lexical, right.lexical)
                self.assertEqual(left.alias, right.alias)


if __name__ == "__main__":
    unittest.main()

