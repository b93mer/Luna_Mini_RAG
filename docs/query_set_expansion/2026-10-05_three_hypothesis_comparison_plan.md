# Analysis plan: three-hypothesis comparative audit

**Date:** 2026-10-05
**Status:** Preregistered audit method. Not a retrieval hypothesis. Classifications are not computed in this document.
**Branch:** `research/dense-cosine-h1`
**This document is not a result.** It locks how frozen traces will be compared after H1 findings exist.

H1 findings are already frozen:

- Preregistration: `docs/query_set_expansion/2026-10-05_dense_cosine_h1_preregistration.md`
- Findings: `docs/query_set_expansion/2026-10-05_dense_cosine_h1_findings.md`
- Trace: `eval_sets/runs/2026-10-06_run-006.jsonl`

This audit must not retune H1, swap the MiniLM encoder, change weights, or implement a composite retriever.

## Purpose

Determine what remains stable or breaks when the same sealed queries are exposed to three different mechanisms, relative to frozen control.

The purpose is **not** to select the best system from this tiny sealed set.
The purpose is **not** to maximize hit rate.
The purpose is a failure-mode map: which conclusions survive intervention changes, which apparent improvements are artifacts, and which repairs are mechanism-specific.

## Lineage under comparison

| Stage | Name | Frozen artifact |
| --- | --- | --- |
| Control | lexical TF-IDF/Jaccard hybrid | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| H-QRL | query rewrite/cache loop (`qrl-v1`) | `eval_sets/runs/2026-10-06_run-002.jsonl` |
| H-MORPH | morphology-only ablation (`morph-v1`) | `eval_sets/runs/2026-10-06_run-004.jsonl` |
| H1 | dense cosine replacement | `eval_sets/runs/2026-10-06_run-006.jsonl` |

Use historical traces exactly as produced. Do not rerun or mutate older experiments unless required solely to verify trace integrity (hashes / readable JSONL). Do not rewrite those JSONL files.

## What is comparable, and what is not

Comparable across all four:

- original YAML query identity
- expected section ids
- ranks
- hit/miss/unmeasurable labels under the same TOP_K=5 rule
- Jaccard (same implementation; H-QRL/H-MORPH may change the string Jaccard sees)
- alias
- rank-1 section identity
- qualitative mechanism (A/B/C/D as previously defined)

Not directly comparable:

- H1 total score vs control/H-QRL/H-MORPH total score, because H1 replaces `lexical_cosine` with `dense_cosine` on a different vector space
- H-QRL/H-MORPH `cosine` vs H1 `dense_cosine`
- aggregate hit rate as an optimization metric

Within-experiment deltas remain valid. Ranks remain valid. Component names must stay explicit: `lexical_cosine`, `dense_cosine`, `jaccard`, `alias`.

## Locked classification categories

Every important row or finding is assigned **one primary** category. Overlays may be named. Definitions are locked before the combined matrix is filled.

### HOLDS

The same underlying retrieval conclusion or mechanism remains supported across the relevant interventions.

Example shape: rank vs correspondence must be decomposed, and all three tests still require that decomposition.

### BREAKS

A previously supported behavior fails under another intervention in a way that matters to its claimed generality.

Example shape: a claim that a rewrite “improves lexical-gap retrieval” does not survive once stripping is removed.

### REVERSES

The direction of the effect changes materially.

Example: target improves under one mechanism but degrades under another.

### MECHANISM-SPECIFIC

A result holds only when the intervention matches the diagnosed failure class. This is not necessarily a failure.

Example: `spec-002` improving under morphology but not under dense retrieval.

### ARTIFACT

An apparent improvement is explained by alias, competitor collapse, rewrite contamination, or another unintended mechanism.

### STABLE GUARDRAIL

The row remains functionally stable across interventions (still a hit at comparable rank, or still the same unmeasurable diagnostic behavior, without a new pathology).

### UNRESOLVED

Evidence remains insufficient or contradictory.

Do not force a row into HOLDS because hit rate rose. Do not treat MECHANISM-SPECIFIC as automatic failure.

## Rows in the matrix

At minimum:

- sem-001
- sem-002
- sem-003
- lex-001
- lex-002
- spec-001
- spec-002
- mch-001 stamp
- mch-001 consumer
- near-OOD (`ood-002`)
- far-OOD (`ood-001`)
- alias-trap (`ood-003`)
- frozen gold-query guardrails (question / verdict / Finding 3.5)

For each row record, where available from frozen traces:

- control / H-QRL / H-MORPH / H1 rank
- hit/miss per experiment (unmeasurable stays unmeasurable)
- target score movement only where the scoring formula is the same (control vs H-QRL vs H-MORPH)
- `lexical_cosine`, `dense_cosine` (H1), Jaccard, alias
- rewrite expansions where applicable
- top-ranked section
- mechanism classification using the categories above

## Row-level questions (asked of every important row)

A. What was the original diagnosed failure mode?
B. Which intervention should theoretically address that failure?
C. What actually happened under each intervention?
D. Did target correspondence improve, or only rank?
E. Did another component create the movement?
F. Does the evidence support a specialized mechanism or a general one?

These questions exist to prevent a winner-takes-all reading.

## System-findings claims to audit

Every substantive claim in `docs/query_set_expansion/system_findings_hypothesis_testing.md` as of the H-MORPH update will be audited against all three experiments.

Locked claim list:

1. Closed-vocabulary morphology can repair lexical representation misses.
2. Generic identifier-segment expansion is not a reliable semantic bridge.
3. High IDF is not a sufficient relevance criterion for query expansion.
4. Machine-generated rewrite tokens can violate alias-layer assumptions.
5. Rank gain is not equivalent to improved semantic correspondence.
6. Global hit rate is not a valid optimization target for this evaluation stage.
7. Cache behavior is ranking-transparent under the tested conditions.
8. Tracker instrumentation is useful when it remains observational.

Final statuses after three tests, locked as a vocabulary:

- strengthened
- unchanged
- narrowed
- weakened
- contradicted
- still untested

H1 not outperforming morphology on `spec-002` must not automatically weaken claim 1.
If H1 repairs `sem-001` where identifier expansion failed, that would strengthen the interpretation that semantic correspondence—not identifier dumping—was the missing mechanism. If H1 does not repair `sem-001`, that claim about identifier expansion can still stand on H-QRL/H-MORPH evidence; H1 would then show that MiniLM cosine is also not a sufficient bridge for that row.

## Failure-mode × intervention map

Fill only from actual evidence. Cells may be `N/A`, `diagnostic`, or `unresolved` when the mechanism was not designed for that class.

Planned rows:

- simple morphology
- semantic producer burial (identifier-register)
- lexical synonym mismatch
- conjunction / multi-chunk
- alias trap
- far OOD
- near OOD

Do not force every cell into success/failure.

## Invariants and brittle findings

An **invariant** is behavior that persists despite changing the retrieval intervention.

A **brittle finding** looked true after one experiment and did not survive comparison.

Contradictions will be recorded, not patched.

## Specialization vs robustness

Do not assume a mechanism is better because it performs well on more rows.

A desirable outcome of this audit may be specialization:

- morphology solves morphological misses
- dense similarity solves some semantic/synonym misses
- neither solves conjunction as a designed mechanism
- aliases remain a separate architecture concern

If the evidence supports that decomposition, state it. The goal is a failure-mode map, not a leaderboard.

## Explicit non-actions during this audit

- Do not implement morphology + dense + lexical + identifier expansion as a composite retriever
- Do not change query text, golds, aliases, TOP_K, chunk boundaries, or H1 weights
- Do not blacklist `date`
- Do not add `regime_stability`
- Do not select a new embedding model
- Do not promote a mechanism because global hit rate rose
- Do not rewrite H-QRL or H-MORPH documents as if H1 had been known beforehand

If a hybrid looks useful, write it as a future preregistered hypothesis only.

## Deliverables after this plan is committed

1. `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md`
2. Update `docs/query_set_expansion/system_findings_hypothesis_testing.md` with a Cross-Experiment Findings section, preserving historical progression

## References

- Control: `eval_sets/runs/2026-09-29_run-004.jsonl`
- H-QRL: `eval_sets/runs/2026-10-06_run-002.jsonl` plus findings
- H-MORPH: `eval_sets/runs/2026-10-06_run-004.jsonl` plus findings
- H1: `eval_sets/runs/2026-10-06_run-006.jsonl` plus findings
- System findings (pre-audit): `docs/query_set_expansion/system_findings_hypothesis_testing.md`
