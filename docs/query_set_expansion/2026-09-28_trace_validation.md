# Trace validation: does the JSONL record what the run actually did?

**Date:** 2026-09-28 (validation run executed 2026-09-29T03:06Z; the logger
names run files by UTC date)
**Status:** Validation record. No pipeline or instrumentation change resulted.
**Baseline under observation:** `2026-09-28_retrieval_baseline.md` (freeze
commit `c1756db`).

## Purpose, and what this is not

Two different things are being recorded in this sprint:

- The **baseline measurement** (`2026-09-28_retrieval_baseline.md`) records
  the behavior future systems will be compared against.
- The **JSONL trace** (`query_logger.py` → `eval_sets/runs/*.jsonl`) records
  evidence about how individual retrieval decisions were produced.

This document validates the second. It is not another performance baseline:
the same three rows were rerun unmodified, and the question is whether the
resulting trace is *truthful and sufficient*, not whether the numbers moved.

Central question: **can we reconstruct why the retriever produced each
observed ranking from the trace alone?**

## Method

- Reran `python run_query_set.py` with no changes to retrieval behavior or
  query wording. Output: `eval_sets/runs/2026-09-29_run-002.jsonl`.
- Ran 336 automated checks against that file (throwaway script, not
  committed; the checks are enumerated below so they can be repeated), plus
  manual inspection of all three entries.
- Cross-checked the trace against four independent sources: the frozen
  scoring formula in `retrieve.py`, `metadata/chunks.json` provenance,
  `eval_sets/docqa.yaml` row fields, and the console capture of the same
  process.

## Field checklist

Per row (`QueryLogEntry`) and per hit (`HitTrace`); all verified present with
correct types on all 3 rows / 15 hits.

| Required field | Present | Verified against |
| --- | --- | --- |
| stable row ID (`row_id`) | yes | `id` in `docqa.yaml`, order identical |
| query | yes | `query` in `docqa.yaml`, verbatim |
| expected section(s) | yes | `expected` in `docqa.yaml` |
| failure mode | yes | `failure_mode` in `docqa.yaml` |
| route pressure | yes | `route_pressure` in `docqa.yaml` |
| pre-registered prediction | yes | `current_stack_prediction` (the locked field; the dated `current_stack_after_run` correction does not leak into it) |
| observed outcome | yes | re-derived from `prediction` + `in_topk` |
| `in_topk` | yes | re-derived from hit section IDs vs `expected` |
| query/run identity | partial | `query_uuid` (unique per row) and `ts_utc` present; **no run-level id inside entries** — run identity is the file name only |
| ranked hits | yes | array order is rank order; verified sorted desc by score; no explicit rank field |
| section IDs | yes | unique in store per hit |
| total score | yes | reconstructs from components (below) |
| cosine component | yes | per hit |
| lexical component | yes | per hit |
| alias component | yes | per hit (0.0 on all 15 hits) |
| retrieval method | yes | `hybrid` on all hits (the `section_id` lookup path is not exercised by this runner) |
| source path | yes | matches `chunks.json` |
| line span | yes | `start_line`/`end_line` match `chunks.json` |
| content hash / provenance | yes | `content_sha256` matches `chunks.json` provenance per chunk |

## Truthfulness checks (all pass)

1. **Score reconstruction.** For every hit, `0.7*cosine + 0.3*lexical +
   alias` reproduces the logged `score` within 5e-7 (6dp rounding noise).
   The trace's arithmetic is the frozen formula's arithmetic.
2. **Ordering.** Every row's hit array is strictly descending by score; rank
   is array position.
3. **Provenance.** Every hit's `content_sha256`, line span, and source path
   match the committed `chunks.json` exactly.
4. **Console agreement.** Every console top-k line matches the JSONL at the
   console's 3dp precision, in order, including `in_topk` and `outcome`.
5. **Determinism.** Excluding `ts_utc`/`query_uuid`, run-002 is identical to
   run-001 (same day) and to the 2026-09-27 run — three executions, one
   ranking.
6. **Corroboration.** The trace reproduces the sem-002 `after_run_note`
   numbers independently (rank 2 at cosine 0.337 / Jaccard 0.049, 0.013370
   behind rank 1 at 0.341 / 0.083), so the dated reclassification in
   `docqa.yaml` is backed by the recorded evidence.

## Instrumentation defects

**None found.** No instrumentation fix was required, and none was made. The
trace accurately records existing runtime behavior for this three-row set.

## Can the ranking be reconstructed from the trace alone?

- **What the ranking is: yes.** Components, weights-implied total, order,
  and provenance are all in the record; checks 1–4 show the record equals
  what the code produced.
- **Why a component has its value: no.** The trace logs component totals,
  not term-level contributions. See below.
- **Where the expected target ranked when outside top-k: no.** The trace
  contains top-5 only.

## Observable / diagnosable / ambiguous

**Currently observable (directly in the record):** full top-k membership and
order; all three score components per hit; per-hit provenance sufficient to
re-fetch the exact chunk text; prediction vs observation per row; per-row
timing and uuid; the fact that the alias boost never fired in this set.

**Currently diagnosable (derivable from the trace alone):** which component
drove a ranking (e.g. sem-001: `verdict` won on cosine, 0.399, against a
lexical component only half that of `question`'s; sem-002 was decided by
cosine, not alias); score margins inside the top-k (sem-002's 0.0134);
whether a hit is heading-anchored vs body-anchored (line span vs the note's
structure); cross-run determinism; that lex-001's top hit is a lexical
near-miss (`upstream_signals_since_verdict_independent`, lexical 0.036).

**Remains ambiguous even with the trace** (each item below was computed from
code + corpus during validation precisely to demonstrate the boundary —
none of it is in the record):

- **Expected target's rank outside top-k.** `1_upstream_producer_score_definition`
  actually ranked **10/15** (score 0.015352) on sem-001 and **7/15** (score
  0.037137) on lex-001. The trace says only "absent from top-5." A future
  change that moved the target from 10th to 6th would be invisible in the
  trace despite being real progress toward the row's hypothesis.
- **Why cosine was low.** lex-001 has **10 of its query tokens outside the
  fitted vocabulary** (`which, market, condition, measure, supplies,
  consistency, signal, assessing, trade, confidence`); sem-001 has 4 OOV
  tokens; sem-002 has 4. The trace shows the resulting low cosines but
  cannot distinguish "token unknown to the vocabulary" from "token known
  but low-IDF / weakly shared" — the difference between the lexical-gap and
  semantic-gap explanations the rows exist to separate.
- **Run and config identity inside the record.** Run identity is the file
  name; TOP_K and the 0.7/0.3 weights are implicit in the frozen code. If
  run files are renamed, concatenated, or compared across a config change,
  the record cannot say which configuration produced it.
- **Which alias substring fired, when alias > 0.** Derivable only by
  re-matching the query against the `SECTION_ALIASES` table in code. Moot in
  this set (alias is 0.0 everywhere) but live for the alias-trap rows the
  failure-mode map plans.

## Consequences

The trace is trustworthy as far as it reaches, and its reach stops exactly
at: (a) everything below rank `k`, and (b) everything inside a component.
Those two boundaries — not any defect — are what a future instrumentation
increment should be sized against. The scoping of that increment is a
separate document: `docs/design_notes/2026-09-28_observability_scoping.md`.
Per the freeze, nothing discovered here changed the retriever.

## References

- Baseline this run re-observed: `2026-09-28_retrieval_baseline.md`.
- Trace under test: `eval_sets/runs/2026-09-29_run-002.jsonl`; deterministic
  twins `2026-09-29_run-001.jsonl`, `2026-09-27_run-001.jsonl`.
- Instrumentation: `query_logger.py`; runner: `run_query_set.py`; frozen
  scoring: `retrieve.py` (`0.7*cosine + 0.3*Jaccard + alias`, TOP_K 5).
- Change discipline: `2026-09-26_failure_mode_map.md`.
