"""Ingest pipeline: data/ markdown → chunk → provenance → embed → store.

Architecture role: the only write path into metadata/chunks.json.
"""

from __future__ import annotations

from pathlib import Path

from embed import fit_transform
from provenance_capture import capture_provenance, rel_source_path, sha256_text
from smart_chunker import chunk_markdown
from store import DATA_DIR, REPO_ROOT, Chunk, build_store, save_store


def iter_source_files(data_dir: Path = DATA_DIR) -> list[Path]:
    """NOTE (added helper): discover ingestible notes under data/."""
    if not data_dir.exists():
        return []
    return sorted(
        path
        for path in data_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    )


def ingest_all(data_dir: Path = DATA_DIR) -> int:
    """Read every note, section-chunk it, embed, and persist.

    Returns the number of stored chunks.
    """
    source_files = iter_source_files(data_dir)
    drafts_by_doc: list[tuple[Path, str, list]] = []
    corpus: list[str] = []

    for source in source_files:
        text = source.read_text(encoding="utf-8")
        drafts = chunk_markdown(text)
        drafts_by_doc.append((source, text, drafts))
        corpus.extend(draft.text for draft in drafts)

    if not corpus:
        save_store(build_store({}, [], []))
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
            )
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}::{draft.section_id}",
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

    save_store(build_store(model.vocab, model.idf, chunks))
    return len(chunks)


def main() -> None:
    count = ingest_all()
    print(f"ingested {count} chunks from {DATA_DIR}")


if __name__ == "__main__":
    main()
