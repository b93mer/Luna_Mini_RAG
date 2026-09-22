"""Parallel ingest for chunker v2: data/ markdown → metadata/chunks_v2.json.

Mirrors ingest.py exactly, except:
  - chunks come from smart_chunker_v2.chunk_markdown (recursive splitter)
  - doc_id is ALWAYS passed (corpus-unique section_ids per chunker v2)
  - output goes to metadata/chunks_v2.json via store_v2

ingest.py and metadata/chunks.json are frozen v1 artifacts and are not
touched here.
"""

from __future__ import annotations

from pathlib import Path

from embed import fit_transform
from ingest import iter_source_files  # read-only reuse of v1 discovery
from provenance_capture import capture_provenance, rel_source_path, sha256_text
from smart_chunker_v2 import chunk_markdown
from store import DATA_DIR, REPO_ROOT, Chunk, build_store
from store_v2 import save_store_v2


def ingest_all_v2(data_dir: Path = DATA_DIR) -> int:
    """Read every note, v2-chunk it, embed, and persist to chunks_v2.json.

    Returns the number of stored chunks.
    """
    source_files = iter_source_files(data_dir)
    drafts_by_doc: list[tuple[Path, str, list]] = []
    corpus: list[str] = []

    for source in source_files:
        text = source.read_text(encoding="utf-8")
        drafts = chunk_markdown(text, doc_id=source.stem)
        drafts_by_doc.append((source, text, drafts))
        corpus.extend(draft.text for draft in drafts)

    if not corpus:
        save_store_v2(build_store({}, [], []))
        return 0

    model, vectors = fit_transform(corpus)
    chunks: list[Chunk] = []
    cursor = 0

    for source, text, drafts in drafts_by_doc:
        relative = rel_source_path(source, REPO_ROOT)
        doc_id = source.stem
        doc_sha = sha256_text(text)
        for draft in drafts:
            embedding = vectors[cursor]
            cursor += 1
            provenance = capture_provenance(
                source_path=relative,
                doc_sha256=doc_sha,
                section_text=draft.text,
                start_line=draft.start_line,
                end_line=draft.end_line,
                parser="smart_chunker_v2.chunk_markdown",
            )
            chunks.append(
                Chunk(
                    # NOTE: section_id already carries the doc_id:: prefix
                    # (chunker v2 was called with doc_id), so it doubles as
                    # the corpus-unique chunk_id.
                    chunk_id=draft.section_id,
                    doc_id=doc_id,
                    source_path=relative,
                    section_id=draft.section_id,
                    heading=draft.heading,
                    kind=draft.kind,
                    text=draft.text,
                    start_line=draft.start_line,
                    end_line=draft.end_line,
                    embedding=embedding,
                    provenance=provenance,
                )
            )

    save_store_v2(build_store(model.vocab, model.idf, chunks))
    return len(chunks)


def main() -> None:
    count = ingest_all_v2()
    print(f"ingested {count} chunks from {DATA_DIR} -> metadata/chunks_v2.json")


if __name__ == "__main__":
    main()
