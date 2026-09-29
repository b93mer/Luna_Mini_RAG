# Scoping: the next observability increment for retrieval experiments

**Date:** 2026-09-28
**Status:** Scoping only. Nothing here is implemented by this commit.
**Inputs:** `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
(frozen behavior), `docs/query_set_expansion/2026-09-28_trace_validation.md`
(observation mechanism, validated truthful but bounded).

## Why this document

Trace validation found the JSONL truthful as far as it reaches, with the
reach stopping at three boundaries: everything below rank `k`, everything
inside a score component, and run/config identity outside the record. This
note sizes candidate expansions against those boundaries **before** building
any of them, so the next increment is chosen by diagnostic value rather than
by what happens to be easy to log.

Design principle (binding for every candidate below):

> Instrument information that reduces uncertainty about system behavior or
> allows a hypothesis to be falsified.

A field that is merely available fails this test. A field that is derivable
offline from fields already logged also fails it.

Each candidate answers five questions:

1. What question would this allow us to answer?
2. What failure mode or architectural hypothesis would it help diagnose?
3. Is the information already available at runtime but simply not logged?
4. Would collecting it require changing retrieval behavior?
5. What is the expected diagnostic value relative to implementation
   complexity?

## High-value / low-cost

### A. Expected target's rank and score in the full ranking

1. How far from the top-k was the expected section? Did a later change move
   it, even if it still misses?
2. Every `expected_miss` row — currently semantic gap (sem-001) and lexical
   gap (lex-001). This is the falsifiability gap: validation showed the
   target actually ranked 10/15 and 7/15, but the trace records only
   "absent from top-5." A hypothesis like "multi-vector embeddings close the
   lexical gap" is unfalsifiable from the trace until the target crosses
   rank 5; with this field, movement from 10→6 is already evidence.
3. Yes. `retrieve()` scores all 15 chunks and then truncates to `k`; the
   full ordering exists inside the call and is discarded.
4. No. Same scoring, same sort; the runner reads more of the same ranking
   (e.g. `k` = corpus size) and still records top-5 exactly as today.
5. Highest value of any candidate; low complexity at current corpus size.
   One edit site, shared by `run_query_set.py` and `query_logger.py`.

### B. Run/config/query-set identity block

Four small fields, assessed together because they share one edit and one
purpose — making every trace self-describing across a change:

- `run_uuid` — one id per process, on every row. (1) Which rows belong to
  one execution? (2) Not a failure mode — measurement integrity for
  before/after comparison. (3) Yes, trivially. (4) No. (5) Moderate value
  today (the file name carries run identity, fragilely); near-zero cost.
- `index_sha256` — hash of `chunks.json`. (1) Which index produced this
  trace? (2) The stale-index ops limit named in the failure-mode map; would
  have proved the 2026-09-27 rebuild content-identical without a diff.
  (3) Yes. (4) No. (5) Moderate today (static corpus), high the day the
  corpus changes; trivial cost.
- `query_set_sha256` — hash of `docqa.yaml`. (1) Which exact pre-registered
  rows produced these records? (2) Set-drift confound; backs the change
  discipline (the manifest already anticipates a seal hash). (3) Yes.
  (4) No. (5) High audit value; trivial cost.
- `config` (`top_k`, `weight_cosine`, `weight_lexical`) — (1) Which
  configuration produced this ranking? (2) Config-drift confound; essential
  the moment a hypothesis changes any constant — which is exactly the moment
  the trace must survive. (3) Yes (constants). (4) No. (5) Low value while
  frozen, high at the first unfreeze; trivial cost.

## Useful when a specific hypothesis requires it

### C. Per-query full score distribution (all 15 scores per row)

1. Is the top-k a cliff or a plateau? What does the tail look like?
2. Specificity mismatch (a plateau is an under-specific query); any future
   score-floor design.
3. Yes — the full scan already happens. 4. No.
5. Moderate value; at 15 chunks it is cheap and would subsume candidate A,
   but it triples record size and builds a dump-everything habit that scales
   poorly. Gate on an actual plateau/specificity hypothesis. If enabled,
   enable it **instead of** A, not alongside.

### D. Which alias substring fired

1. Did `disposition` or `hold stands` trigger the boost?
2. Alias-trap out-of-domain rows and alias-collision entity rows — both
   planned in the failure-mode map, neither yet in the set.
3. Yes (the match is computed inside `alias_boost`). 4. No.
5. Zero value today: alias is 0.0 on all 15 baseline hits, and had it fired,
   the substring is derivable by re-matching the logged query against the
   frozen table. Add when alias-trap rows are added, not before.

### E. Zero/unknown query-token record (OOV token list, zero-vector flag)

1. Was a low cosine caused by tokens missing from the fitted vocabulary, or
   by known tokens weakly shared?
2. Lexical gap vs semantic gap attribution — the exact distinction the two
   live failure modes exist to separate. Validation showed lex-001 has 10
   OOV query tokens (sem-001: 4, sem-002: 4); the trace cannot show this.
3. Yes — `tokenize(query)` against `store.vocab`, computed beside retrieval.
   4. No.
5. High value for the branch's central question; low-moderate complexity
   (the logger/runner needs vocabulary access). Second in line after A/B;
   pull forward if lexical-gap rows multiply.

### F. Chunk/document identifiers beyond section_id (`chunk_id`, `doc_id`)

1. Which document did this hit come from?
2. Cross-doc section collision — the regime the 2026-09-22 fail-loud ADR
   documents on a 3-doc corpus.
3. Yes. 4. No.
5. Low now: `source_path` + line span already identify the chunk, and the
   corpus is one document. High the day a second doc lands. The ADR is the
   trigger; the add is one line then.

## Defer until the architecture becomes more complex

### G. Candidate count

Constant 15 today, derivable from index identity. Meaningful only when a
candidate-generation or filtering stage exists (multi-index, routing).
Logging it now records a constant.

### H. Elapsed retrieval time

Performance, not ranking diagnosis. No current hypothesis needs it; timing
on a 15-chunk scan is noise and could invite false comparisons. The Route L
vs Route S cost comparison will legitimately want it — that ADR is the
trigger.

### I. Determinism/reproducibility metadata (Python version, platform, RNG)

The pipeline has no nondeterministic component; three runs produced
identical rankings (validation check 5). The identity block (B) covers the
reproducibility surface that actually varies. Revisit if a stochastic or
version-sensitive component is introduced.

### J. Explicit per-hit rank field

Rank is array position, verified ordered. Adds no information; protects only
against hypothetical consumers that reorder the array. Add when such a
consumer exists.

## Derivable — do not log

- **Score margins** (rank 1 ↔ rank 2, rank 1 ↔ expected): arithmetic on
  logged scores when both parties are in top-k (the sem-002 margin, 0.0134,
  was derived this way). Once A exists, margin-to-cutoff is derivable too.
- **Lexical intersection details** (which tokens overlapped): the query is
  logged and the chunk text is fetchable via logged provenance
  (`source_path` + line span + `content_sha256`). An offline analysis script
  answers this when a hypothesis asks; the trace should not carry it per row.
- **Before/after comparison fields**: not fields. A comparison is a join of
  two traces on `row_id` + query-set hash, with the identity block (B) as
  the change vector. A and B are exactly what make that join meaningful.

## Currently logged: watch list

Nothing logged today is wrong. Two fields deserve a caution, not a change:

- `outcome` is derived (`prediction` + `in_topk`), and `expected_miss` as an
  outcome label can be misread as an observation rather than a confirmed
  prediction. The baseline document states the distinction; keep the field
  for readability, keep the derivation documented.
- `query_uuid` is per-row identity, not run identity; reading it as the
  latter is the confusion `run_uuid` (B) would preclude.
- Naming note only: the `alias` score component is unrelated to the trace
  note's other "alias" (the 2.30 / 5.7 chain named in the failure-mode map).
  No rename; just don't conflate them in future analysis.

## Recommendation: the smallest next increment

**Implement A (expected target's rank, score, and components in the full
ranking), with B (run_uuid, index_sha256, query_set_sha256, config) riding
the same edit.** Both are runner/logger-side; neither touches scoring,
sorting, weights, or the alias table, so the freeze and the baseline remain
valid — the baseline is precisely what A makes measurable against.

Everything else waits for its trigger: C and D for the rows that need them,
E immediately after if lexical-gap rows grow, F for a second document,
G/H/I/J for the architecture that would make them non-constant.

This commit deliberately implements none of it.

## References

- Baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`.
- Trace validation (the boundaries this note sizes against):
  `docs/query_set_expansion/2026-09-28_trace_validation.md`.
- Failure-mode map (change discipline, planned alias-trap/OOD rows, stale
  index as ops limit): `docs/query_set_expansion/2026-09-26_failure_mode_map.md`.
- Growth-route deferral (Route L/S): `docs/design_notes/2026-09-24_taxonomy_schema_design.md`.
- Multi-doc collision regime: `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md`.
