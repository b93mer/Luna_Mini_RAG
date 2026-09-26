"""Hybrid RetrievalHit components reconstruct the blended score.

Uses the live store the same way evaluate.py does. Does not change
retrieve_by_section_id; that path keeps the 0.0 component defaults.
"""

import unittest

from retrieve import retrieve


class TestRetrieveScoreComponents(unittest.TestCase):
    def test_weighted_components_sum_to_score(self):
        hits = retrieve(
            "What is the question about conviction_detail.factors regime?",
            k=3,
        )
        self.assertTrue(hits)
        hit = hits[0]
        reconstructed = 0.7 * hit.cosine + 0.3 * hit.lexical + hit.alias
        self.assertAlmostEqual(hit.score, reconstructed)


if __name__ == "__main__":
    unittest.main()
