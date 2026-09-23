"""Tests for ChunkStore.get_by_section_id ambiguity handling.

Built entirely in-memory; does not touch metadata/chunks.json or data/.
"""

import unittest

from store import AmbiguousSectionIdError, Chunk, ChunkStore


def make_chunk(chunk_id: str, doc_id: str, section_id: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        source_path=f"data/{doc_id}.md",
        section_id=section_id,
        heading=section_id,
        kind="section",
        text=f"text of {chunk_id}",
        start_line=1,
        end_line=5,
        embedding=[],
    )


def make_store(chunks: list[Chunk]) -> ChunkStore:
    return ChunkStore(version=1, built_at="", vocab={}, idf=[], chunks=chunks)


class TestGetBySectionId(unittest.TestCase):
    def test_unique_section_id_returns_chunk(self):
        chunk = make_chunk("c1", "doc_a", "1_session_summary")
        store = make_store([chunk, make_chunk("c2", "doc_b", "3_fire")])
        self.assertIs(store.get_by_section_id("1_session_summary"), chunk)

    def test_missing_section_id_returns_none(self):
        store = make_store([make_chunk("c1", "doc_a", "1_session_summary")])
        self.assertIsNone(store.get_by_section_id("nonexistent_section"))

    def test_colliding_section_id_raises_with_both_doc_ids(self):
        store = make_store(
            [
                make_chunk("c1", "doc_a", "3_fire"),
                make_chunk("c2", "doc_b", "3_fire"),
            ]
        )
        with self.assertRaises(AmbiguousSectionIdError) as ctx:
            store.get_by_section_id("3_fire")
        message = str(ctx.exception)
        self.assertIn("doc_a", message)
        self.assertIn("doc_b", message)


if __name__ == "__main__":
    unittest.main()
