"""Tests for smart_chunker_v2 (parallel chunker; v1 untouched).

Run: python tests/test_smart_chunker_v2.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# NOTE (added helper): tests live one level below repo root; put the root
# on sys.path so the pipeline modules import unchanged.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from smart_chunker_v2 import MAX_SECTION_CHARS, chunk_markdown  # noqa: E402


def by_id(drafts):
    return {draft.section_id: draft for draft in drafts}


class TestPreambleFields(unittest.TestCase):
    def test_single_preamble_field_splits(self):
        text = (
            "# Title\n"
            "\n"
            "**Question:** What is x?\n"
            "\n"
            "## Body\n"
            "\n"
            "Some text.\n"
        )
        drafts = by_id(chunk_markdown(text))
        self.assertIn("question", drafts)
        self.assertEqual(drafts["question"].kind, "field")
        self.assertIn("What is x?", drafts["question"].text)

    def test_preamble_run_of_three_splits_each(self):
        text = (
            "# Title\n"
            "\n"
            "**Date:** 2026-01-01\n"
            "**Scope:** analysis only\n"
            "**Question:** What is x?\n"
            "\n"
            "## Body\n"
            "\n"
            "Some text.\n"
        )
        drafts = by_id(chunk_markdown(text))
        for field_id in ("date", "scope", "question"):
            self.assertIn(field_id, drafts)
            self.assertEqual(drafts[field_id].kind, "field")


class TestBodyFields(unittest.TestCase):
    def test_solo_body_field_stays_inline(self):
        text = (
            "## Section\n"
            "\n"
            "Intro paragraph.\n"
            "\n"
            "**Note:** this should stay inline.\n"
            "\n"
            "Outro paragraph.\n"
        )
        drafts = chunk_markdown(text)
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].section_id, "section")
        self.assertIn("**Note:** this should stay inline.", drafts[0].text)

    def test_body_run_of_two_splits(self):
        text = (
            "## Section\n"
            "\n"
            "Intro paragraph.\n"
            "\n"
            "**Alpha:** first\n"
            "**Beta:** second\n"
            "\n"
            "Outro paragraph.\n"
        )
        drafts = by_id(chunk_markdown(text))
        self.assertIn("alpha", drafts)
        self.assertIn("beta", drafts)
        self.assertEqual(drafts["alpha"].kind, "field")
        self.assertEqual(drafts["beta"].kind, "field")
        # The parent section must not absorb the field lines.
        self.assertNotIn("**Alpha:**", drafts["section"].text)


class TestSizeCascade(unittest.TestCase):
    def test_rule_split(self):
        part_a = "a" * 1500
        part_b = "b" * 1500
        text = f"## Big\n\n{part_a}\n\n---\n\n{part_b}\n"
        drafts = chunk_markdown(text)
        self.assertEqual(len(drafts), 2)
        self.assertEqual(drafts[0].section_id, "big")
        self.assertEqual(drafts[1].section_id, "big__part2")
        for draft in drafts:
            self.assertLessEqual(len(draft.text), MAX_SECTION_CHARS)
        self.assertIn(part_a, drafts[0].text)
        self.assertIn(part_b, drafts[1].text)

    def test_paragraph_split_when_no_rules(self):
        paragraphs = ["x" * 900, "y" * 900, "z" * 900]
        text = "## Big\n\n" + "\n\n".join(paragraphs) + "\n"
        drafts = chunk_markdown(text)
        self.assertEqual(len(drafts), 3)
        self.assertEqual(
            [d.section_id for d in drafts], ["big", "big__part2", "big__part3"]
        )
        for draft in drafts:
            self.assertLessEqual(len(draft.text), MAX_SECTION_CHARS)

    def test_sentence_split_as_last_resort(self):
        sentence = "This is a filler sentence for the cascade test fixture. "
        paragraph = sentence * 45  # ~2700 chars, one paragraph, no rules
        text = f"## Big\n\n{paragraph}\n"
        drafts = chunk_markdown(text)
        self.assertGreaterEqual(len(drafts), 2)
        self.assertEqual(drafts[0].section_id, "big")
        self.assertEqual(drafts[1].section_id, "big__part2")
        for draft in drafts:
            self.assertLessEqual(len(draft.text), MAX_SECTION_CHARS)
        # No content lost: every sentence survives somewhere.
        rejoined = "\n".join(d.text for d in drafts)
        self.assertEqual(rejoined.count("filler sentence"), 45)


class TestFenceOpacity(unittest.TestCase):
    def test_fenced_code_does_not_split(self):
        text = (
            "## Code Section\n"
            "\n"
            "Some text.\n"
            "\n"
            "```text\n"
            "# not a heading\n"
            "**Field:** value\n"
            "---\n"
            "```\n"
            "\n"
            "Trailing text.\n"
        )
        drafts = chunk_markdown(text)
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].section_id, "code_section")
        self.assertIn("# not a heading", drafts[0].text)
        self.assertIn("**Field:** value", drafts[0].text)
        self.assertIn("Trailing text.", drafts[0].text)


class TestDocIdPrefixing(unittest.TestCase):
    def test_shared_heading_gets_distinct_ids(self):
        text = "## Verdict\n\nSame heading, different doc.\n"
        ids_a = {d.section_id for d in chunk_markdown(text, doc_id="doc_a")}
        ids_b = {d.section_id for d in chunk_markdown(text, doc_id="doc_b")}
        self.assertEqual(ids_a, {"doc_a::verdict"})
        self.assertEqual(ids_b, {"doc_b::verdict"})
        self.assertEqual(len(ids_a & ids_b), 0)

    def test_no_doc_id_keeps_v1_behavior(self):
        text = "## Verdict\n\nFirst.\n\n## Verdict\n\nSecond.\n"
        ids = [d.section_id for d in chunk_markdown(text)]
        self.assertEqual(ids, ["verdict", "verdict_2"])

    def test_doc_id_prefixes_collision_suffixes(self):
        text = "## Verdict\n\nFirst.\n\n## Verdict\n\nSecond.\n"
        ids = [d.section_id for d in chunk_markdown(text, doc_id="doc_a")]
        self.assertEqual(ids, ["doc_a::verdict", "doc_a::verdict_2"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
