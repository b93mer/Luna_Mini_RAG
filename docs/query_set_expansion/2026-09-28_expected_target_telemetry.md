# Expected-target rank and run identity telemetry

**Date:** 2026-09-28 (control rerun executed 2026-09-29T03:34:24Z; the logger
names run files by UTC date)
**Status:** Instrumentation increment. Retrieval behavior unchanged.
**Baseline under observation:** `2026-09-28_retrieval_baseline.md`
**Scoping:** implements candidates A and B from
`docs/design_notes/2026-09-28_observability_scoping.md`. Does not implement
the rest.

New fields begin with this run (`eval_sets/runs/2026-09-29_run-003.jsonl`).
Historical JSONL files were not rewritten.

## Problem

Top-k membership censored expected-target movement outside the cutoff.
`retrieve()` already scored and sorted every chunk, then discarded the tail.
Ranks 6–15 were observationally the same state: absent from top-k. A later
change that moved a target from rank 10 to rank 6 would still log
`expected_miss` at `TOP_K=5`.

## Change

The trace now captures expected-target full-ranking telemetry and minimal
run/config identity.

The eval runner calls `rank_all(query)` once, slices that list to `TOP_K`
for existing hit/miss semantics, and records each expected section's
position in the same ranking. Scoring weights are named in `retrieve.py`
(`COSINE_WEIGHT`, `LEXICAL_WEIGHT`) and applied there; the logger records
`scoring_config()` rather than defining a second copy. `TOP_K` remains
owned by `run_query_set.py` and is logged as the runtime cutoff.

Per row, the new fields are:

- `run_uuid` — one id for the whole query-set execution
- `query_set_sha256` — sha256 of the YAML file actually read
- `index_sha256` — sha256 of `metadata/chunks.json` after the index load
- `config.top_k` / `config.weight_cosine` / `config.weight_lexical`
- `expected_targets[]` — `section_id`, `rank`, `score`, `cosine`,
  `lexical`, `alias`, `in_topk` (a list, so later multi-target rows fit)

Existing `hits`, `outcome`, and `in_topk` are unchanged in meaning.

## What this enables

Future experiments can measure:

- absolute target rank
- change in target rank
- movement toward/away from TOP_K
- target score/component changes
- whether a hypothesis improved ranking without yet producing a hit

## What did not change

Retrieval behavior, queries, expected targets, scoring, aliases, corpus,
and evaluation outcome semantics were unchanged. No embeddings, BM25,
reranking, query expansion, or query-set expansion.

## Validation

`pytest tests` 13/13; `python evaluate.py` PASS (ingest touched only
`built_at` / `captured_at`; the frozen index was restored before the
control rerun so `index_sha256` is the committed artifact). Control rerun:
`eval_sets/runs/2026-09-29_run-003.jsonl`.

Observed control ranks (and original top-k outcomes):

- `qse-docqa-sem-001` = **10/15**, still `expected_miss` (not in top-k)
- `qse-docqa-sem-002` = **2/15**, still `hit`
- `qse-docqa-lex-001` = **7/15**, still `expected_miss` (not in top-k)

Target scores match the 2026-09-28 trace-validation offline computation
(sem-001 0.015352, lex-001 0.037137). Logged `hits` arrays match
`2026-09-29_run-002.jsonl`. Query-set and index hashes match the frozen
baseline artifacts (lowercase `hashlib` vs the baseline document's
uppercase PowerShell hashes). 192 mechanical checks on run-003 passed.
Historical traces were not modified.

## Remaining deliberate gaps

Not implemented here, still waiting on their triggers:

- OOV-token telemetry
- full score distributions
- alias-trigger substring telemetry
- latency
- doc/chunk identity expansion
- reranker diagnostics
- second-document support
- OOD-specific telemetry
- query-set expansion

Runtime hashing is provenance for this run. It does not seal the query-set
manifest.

## References

- Frozen behavior: `2026-09-28_retrieval_baseline.md`
- Observation bounds this increment closes (A, B):
  `2026-09-28_trace_validation.md`,
  `docs/design_notes/2026-09-28_observability_scoping.md`
- Raw trace: `eval_sets/runs/2026-09-29_run-003.jsonl`
