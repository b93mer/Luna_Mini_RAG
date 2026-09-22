"""Recursive section-aware markdown chunker (v2) — parallel module.

v1 (`smart_chunker.py`) is the frozen baseline tagged v0.1.0-poc-baseline
and is NOT modified. v2 keeps the same public API shape so downstream code
can swap chunkers later:

    chunk_markdown(text, doc_id=None) -> list[SectionDraft]

Differences from v1:
  1. Bold-field lines split in the BODY too, when they form a consecutive
     run of >=2 field lines (solo body fields stay inline).
  2. Oversized sections (> MAX_SECTION_CHARS) are recursively split:
     horizontal rules -> paragraph breaks -> sentence boundaries.
  3. section_ids are corpus-unique when doc_id is passed
     (f"{doc_id}::{slug}"); with doc_id=None, v1 per-call behavior
     (bare slug, _2/_3 suffixes) is kept.

Fenced code blocks are opaque to ALL splitters (same as v1).
"""

from __future__ import annotations

import re
from dataclasses import replace

from smart_chunker import SectionDraft, parse_bold_field, slugify


MAX_SECTION_CHARS = 2000

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
RULE_RE = re.compile(r"^-{3,}\s*$")
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.?!])\s+")


# ---------------------------------------------------------------------------
# Phase 1: structural pass (headings + bold fields)
# ---------------------------------------------------------------------------


def _precompute_line_facts(lines: list[str]) -> dict:
    """Single scan recording fence state, headings, and field lines.

    NOTE (added helper): v2 needs run-detection over field lines, which is
    not a pure left-to-right decision, so fence/heading/field facts are
    computed up front instead of inside the main loop as in v1.
    """
    in_fence = False
    is_fence = [False] * len(lines)
    heading_level: list[int | None] = [None] * len(lines)
    field: list[tuple[str, str] | None] = [None] * len(lines)
    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if line.startswith("```"):
            in_fence = not in_fence
            is_fence[i] = True
            continue
        if in_fence:
            is_fence[i] = True
            continue
        match = HEADING_RE.match(line)
        if match:
            heading_level[i] = len(match.group(1))
            continue
        field[i] = parse_bold_field(line)
    return {
        "is_fence": is_fence,
        "heading_level": heading_level,
        "field": field,
    }


def _field_run_sizes(lines: list[str], facts: dict) -> dict[int, int]:
    """Map field-line index -> size of the consecutive run it belongs to.

    A run is a maximal group of field lines separated only by blank lines.
    Any non-blank, non-field line (including headings and fence lines)
    breaks the run.
    """
    run_size: dict[int, int] = {}
    current: list[int] = []
    last_field_idx: int | None = None

    def close_run() -> None:
        for idx in current:
            run_size[idx] = len(current)

    for i, info in enumerate(facts["field"]):
        if info is None:
            continue
        if last_field_idx is not None:
            gap = lines[last_field_idx + 1 : i]
            if any(part.strip() for part in gap):
                close_run()
                current = []
        current.append(i)
        last_field_idx = i
    close_run()
    return run_size


def _structural_pass(text: str) -> list[SectionDraft]:
    """Heading/field split. Differs from v1 in three ways:

    - body field runs of >=2 split (solo body fields stay inline)
    - horizontal-rule lines are RETAINED in chunk text so the size
      cascade can split on them later (v1 dropped them)
    - blank lines are RETAINED so paragraph splitting is possible
    """
    lines = text.splitlines()
    facts = _precompute_line_facts(lines)
    run_size = _field_run_sizes(lines, facts)

    # Preamble region ends at the first H2+ heading (v1 semantics).
    preamble_end = len(lines)
    for i, level in enumerate(facts["heading_level"]):
        if level is not None and level >= 2:
            preamble_end = i
            break

    drafts: list[SectionDraft] = []
    used_ids: dict[str, int] = {}

    heading: str | None = None
    kind: str | None = None
    body: list[str] = []
    start_line = 0
    end_line = 0
    seen_section_heading = False

    def flush() -> None:
        nonlocal heading, kind, body, start_line, end_line
        if heading is None or kind is None or start_line < 1:
            return
        body_text = "\n".join(body).strip()
        if kind == "field":
            text_out = f"{heading}: {body_text}".strip() if body_text else heading
        elif body_text:
            text_out = f"{heading}\n\n{body_text}"
        else:
            text_out = heading
        if not text_out.strip():
            heading = None
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
                text=text_out,
                start_line=start_line,
                end_line=end_line,
            )
        )
        heading = None

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        i0 = i - 1

        if facts["is_fence"][i0]:
            if heading is None:
                heading, kind, body, start_line = "preamble", "section", [], i
            body.append(line)
            end_line = i
            continue

        level = facts["heading_level"][i0]
        if level is not None:
            flush()
            heading = HEADING_RE.match(line).group(2).strip()
            kind = "title" if level == 1 and not seen_section_heading else "section"
            if level >= 2:
                seen_section_heading = True
            body = []
            start_line = end_line = i
            continue

        field = facts["field"][i0]
        if field is not None:
            in_preamble = i0 < preamble_end
            in_run = run_size.get(i0, 1) >= 2
            # TODO(field-detection): a stricter approach would require an
            # explicit <!-- fields: name1, name2 --> marker at the doc top
            # instead of heuristic run detection. Left for a future pass.
            if in_preamble or in_run:
                flush()
                heading, value = field
                kind = "field"
                body = [value] if value else []
                start_line = end_line = i
                continue
            # Solo body field: falls through and stays inline as body text.

        if heading is None:
            if not line:
                continue
            heading, kind, body, start_line = "preamble", "section", [line], i
            end_line = i
            continue

        body.append(line)
        end_line = i

    flush()
    return drafts


# ---------------------------------------------------------------------------
# Phase 2: size cascade (rules -> paragraphs -> sentences)
# ---------------------------------------------------------------------------


def _split_on_lines(
    text: str, start_line: int, is_boundary
) -> list[tuple[str, int, int]]:
    """Split text at boundary lines (outside fences); boundary lines drop.

    NOTE (added helper): shared machinery for the rule and paragraph
    cascade levels — both are 'split at this kind of line' operations.
    Returns (text, start_line, end_line) triples, line numbers computed
    from the parent's start_line.
    """
    lines = text.split("\n")
    parts: list[tuple[str, int, int]] = []
    current: list[str] = []
    current_start = start_line
    in_fence = False
    for offset, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            current.append(line)
            continue
        if not in_fence and is_boundary(line):
            piece = "\n".join(current).strip()
            if piece:
                parts.append((piece, current_start, start_line + offset - 1))
            current = []
            current_start = start_line + offset + 1
            continue
        current.append(line)
    piece = "\n".join(current).strip()
    if piece:
        parts.append((piece, current_start, start_line + len(lines) - 1))
    return parts


def _split_sentences(
    text: str, start_line: int, end_line: int
) -> list[tuple[str, int, int]]:
    """Last-resort split on sentence boundaries outside code fences.

    NOTE (added helper): sentence units are re-joined with newlines, so
    intra-line spacing is normalized — acceptable for a research chunker.
    Line spans on emitted parts are the PARENT paragraph's span (sentence
    splitting can cut mid-line, so precise spans are not recoverable
    without a column tracker — TODO if provenance precision matters).
    """
    units: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_fence = not in_fence
            units.append(line)
            continue
        if in_fence:
            units.append(line)  # fence lines stay whole
            continue
        units.extend(part for part in SENTENCE_BOUNDARY_RE.split(line) if part)

    parts: list[tuple[str, int, int]] = []
    current: list[str] = []
    current_len = 0
    for unit in units:
        if current and current_len + len(unit) + 1 > MAX_SECTION_CHARS:
            parts.append(("\n".join(current), start_line, end_line))
            current = []
            current_len = 0
        current.append(unit)
        current_len += len(unit) + 1
    if current:
        parts.append(("\n".join(current), start_line, end_line))
    return parts


def _size_cascade(drafts: list[SectionDraft]) -> list[SectionDraft]:
    """Recursively shrink sections over MAX_SECTION_CHARS.

    Priority: horizontal rules -> paragraph breaks -> sentence boundaries.
    A level only fires when the previous level's output is still too long.
    """
    out: list[SectionDraft] = []
    for draft in drafts:
        if len(draft.text) <= MAX_SECTION_CHARS:
            out.append(draft)
            continue

        # Keep the heading line attached to the first part: paragraph
        # splitting would otherwise detach it into its own tiny chunk.
        heading_line, sep, body = draft.text.partition("\n")
        if not sep:
            out.append(draft)  # single-line oversize draft: nothing to split
            continue
        body_start = draft.start_line + 1  # approximate; blank line follows

        parts = _split_on_lines(
            body, body_start, lambda line: bool(RULE_RE.match(line))
        )
        refined: list[tuple[str, int, int]] = []
        for part_text, part_start, part_end in parts:
            if len(part_text) <= MAX_SECTION_CHARS:
                refined.append((part_text, part_start, part_end))
            else:
                refined.extend(
                    _split_on_lines(part_text, part_start, lambda line: not line.strip())
                )
        final: list[tuple[str, int, int]] = []
        for part_text, part_start, part_end in refined:
            if len(part_text) <= MAX_SECTION_CHARS:
                final.append((part_text, part_start, part_end))
            else:
                final.extend(_split_sentences(part_text, part_start, part_end))

        for index, (part_text, part_start, part_end) in enumerate(final):
            section_id = (
                draft.section_id
                if index == 0
                else f"{draft.section_id}__part{index + 1}"
            )
            if index == 0:
                # NOTE: re-attaching the heading can push part 1 a few
                # chars over MAX_SECTION_CHARS; accepted (heading is tiny).
                part_text = f"{heading_line}\n\n{part_text}"
                part_start = draft.start_line
            out.append(
                SectionDraft(
                    section_id=section_id,
                    heading=draft.heading,
                    kind=draft.kind,
                    text=part_text,
                    start_line=part_start,
                    end_line=part_end,
                )
            )
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chunk_markdown(text: str, doc_id: str | None = None) -> list[SectionDraft]:
    """Chunk a markdown doc. Same return shape as v1.

    doc_id given  -> section_ids prefixed f"{doc_id}::{slug}" (corpus-unique)
    doc_id=None   -> v1 behavior (bare slug, _2/_3 on per-call collision)
    """
    drafts = _size_cascade(_structural_pass(text))
    if doc_id is None:
        return drafts
    return [
        replace(draft, section_id=f"{doc_id}::{draft.section_id}")
        for draft in drafts
    ]
