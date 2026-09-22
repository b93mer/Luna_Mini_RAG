"""Section-aware markdown chunker for the Luna retrieval pipeline.

Architecture role: turn ingested research notes into retrieval units that
preserve heading identity (Question / Verdict / Finding 3.5 disposition)
instead of sliding-window fragments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


FIELD_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
RULE_RE = re.compile(r"^-{3,}\s*$")


@dataclass
class SectionDraft:
    """One retrieval unit before embeddings and provenance are attached."""

    section_id: str
    heading: str
    kind: str  # title | field | section
    text: str
    start_line: int
    end_line: int


def slugify(value: str) -> str:
    """NOTE (added helper): stable section_id from a heading or field name.

    Needed so retrieve.py can look up Question / Verdict / Finding 3.5 by id
    without a separate taxonomy file.
    """
    normalized = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_") or "section"


def parse_bold_field(line: str) -> tuple[str, str] | None:
    """NOTE (added helper): parse `**Question:** ...` preamble fields.

    The Question target is a bold field in the document header, not a `##`
    heading. Without this parser it would be absorbed into the title chunk.
    """
    match = FIELD_RE.match(line)
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip()


def _flush(
    *,
    drafts: list[SectionDraft],
    heading: str | None,
    kind: str | None,
    body_lines: list[str],
    start_line: int,
    end_line: int,
    used_ids: dict[str, int],
) -> None:
    if heading is None or kind is None or start_line < 1:
        return
    body = "\n".join(body_lines).strip()
    if kind == "field":
        text = f"{heading}: {body}".strip() if body else heading
    elif body:
        text = f"{heading}\n\n{body}"
    else:
        text = heading
    if not text.strip():
        return
    section_id = slugify(heading)
    used_ids[section_id] = used_ids.get(section_id, 0) + 1
    if used_ids[section_id] > 1:
        section_id = f"{section_id}_{used_ids[section_id]}"
    drafts.append(
        SectionDraft(
            section_id=section_id,
            heading=heading,
            kind=kind,
            text=text,
            start_line=start_line,
            end_line=end_line,
        )
    )


def chunk_markdown(text: str) -> list[SectionDraft]:
    """Split a research note into heading- and field-aligned chunks.

    Rules:
    - `#` title becomes a title chunk
    - `**Field:**` lines before the first `##` become field chunks (Question)
    - each `##`/`###`/… heading is its own section chunk (Verdict, Impact)
    """
    lines = text.splitlines()
    drafts: list[SectionDraft] = []
    used_ids: dict[str, int] = {}

    heading: str | None = None
    kind: str | None = None
    body: list[str] = []
    start_line = 0
    end_line = 0
    seen_section_heading = False
    in_fence = False

    def flush() -> None:
        _flush(
            drafts=drafts,
            heading=heading,
            kind=kind,
            body_lines=body,
            start_line=start_line,
            end_line=end_line,
            used_ids=used_ids,
        )

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        if line.startswith("```"):
            # NOTE (added helper behavior): ignore headings/fields inside
            # fenced code so comment lines like `# else:` are not chunks.
            in_fence = not in_fence
            if heading is None:
                heading = "preamble"
                kind = "section"
                start_line = idx
            body.append(line)
            end_line = idx
            continue

        if in_fence:
            if heading is None:
                heading = "preamble"
                kind = "section"
                start_line = idx
            body.append(line)
            end_line = idx
            continue

        heading_match = HEADING_RE.match(line)
        field = parse_bold_field(line) if not seen_section_heading else None

        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            flush()
            heading = title
            kind = "title" if level == 1 and not seen_section_heading else "section"
            if level >= 2:
                seen_section_heading = True
            body = []
            start_line = idx
            end_line = idx
            continue

        if field is not None:
            flush()
            heading, value = field
            kind = "field"
            body = [value] if value else []
            start_line = idx
            end_line = idx
            continue

        if RULE_RE.match(line):
            if heading is not None:
                end_line = idx
            continue

        if heading is None:
            if not line:
                continue
            heading = "preamble"
            kind = "section"
            body = [line]
            start_line = idx
            end_line = idx
            continue

        body.append(line)
        end_line = idx

    flush()
    return drafts
