"""Provenance capture for retrieved research sections.

Architecture role: stamp each chunk with source path, line span, and hashes
so a later reader can verify that Question / Verdict / Finding 3.5 text
came from a specific file region.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_text(text: str) -> str:
    """NOTE (added helper): content hash for lineage checks.

    No checksum utility existed in the pipeline stubs; this lets evaluate.py
    and retrieve.py prove a hit still matches the ingested bytes.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel_source_path(source_path: str | Path, repo_root: Path) -> str:
    """NOTE (added helper): store portable, repo-relative paths."""
    path = Path(source_path)
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def capture_provenance(
    *,
    source_path: str,
    doc_sha256: str,
    section_text: str,
    start_line: int,
    end_line: int,
    parser: str = "smart_chunker.chunk_markdown",
) -> dict[str, Any]:
    """Build the provenance record attached to a stored chunk."""
    return {
        "source_path": source_path,
        "doc_sha256": doc_sha256,
        "content_sha256": sha256_text(section_text),
        "start_line": start_line,
        "end_line": end_line,
        "parser": parser,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
