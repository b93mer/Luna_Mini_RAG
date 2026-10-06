# Comparative findings: control, H-QRL, H-MORPH, and H1

**Date:** 2026-10-05
**Status:** Comparative audit of frozen traces. No retrieval behavior was changed for this document.
**Analysis plan:** `docs/query_set_expansion/2026-10-05_three_hypothesis_comparison_plan.md`
**This document is observation.** It does not select a production retriever and does not implement a composite system.

Classifications use the locked vocabulary: HOLDS, BREAKS, REVERSES, MECHANISM-SPECIFIC, ARTIFACT, STABLE GUARDRAIL, UNRESOLVED.

## Experimental lineage

Control → H-QRL → H-MORPH → H1 → H-CODE

| Stage | Mechanism | Frozen trace |
| --- | --- | --- |
| Control | `0.7 * lexical_cosine + 0.3 * jaccard + alias` | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| H-QRL | function-word strip + morphology + identifier-segment expansion | `eval_sets/runs/2026-10-06_run-002.jsonl` |
| H-MORPH | closed-vocabulary morphology only | `eval_sets/runs/2026-10-06_run-004.jsonl` |
| H1 | replace cosine term with MiniLM `dense_cosine` | `eval_sets/runs/2026-10-06_run-006.jsonl` |
| H-CODE | replace cosine term with Jina `code_cosine` | `eval_sets/runs/2026-10-06_run-008.jsonl` |

Query-set sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` and lexical index sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` match across all four.

## Why these experiments are comparable

They share the sealed YAML, gold labels, chunk boundaries, TOP_K=5, Jaccard implementation, alias table, and measurable/unmeasurable definitions.

They are **not** directly comparable on raw total score once H1 replaces `lexical_cosine` with `dense_cosine` or H-CODE replaces it with `code_cosine`. Control vs H-QRL vs H-MORPH totals remain comparable because those three still use the frozen lexical hybrid. Ranks, hit/miss, component identity, rewrite expansions, and qualitative mechanism remain comparable for all five.

This is not a bake-off. Sample size is 12 rows, 7 measurable.

## Cross-experiment matrix

`hit` / `miss` here means unique-target membership in top-5. Unmeasurable rows stay unmeasurable. H1 scores are on the dense blend and are not like-for-like with the other totals.

| row | C rank | QRL | MORPH | H1 | C | QRL | MORPH | H1 | C top-1 | QRL top-1 | MORPH top-1 | H1 top-1 | class |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sem-001 | 10 | 11 | 10 | 9 | miss | miss | miss | miss | verdict | **date** alias 0.35 | verdict | verdict | UNRESOLVED repair; ARTIFACT under QRL |
| sem-002 | 2 | 4 | 1 | 1 | hit | hit | hit | hit | verdict | **date** alias 0.35 | gold | gold | STABLE GUARDRAIL; QRL rank-1 ARTIFACT |
| sem-003 | 2 | 2 | 1 | 3 | hit | hit | hit | hit | verdict | **date** alias 0.35 | gold | verdict | STABLE GUARDRAIL; MORPH rank-1 is B |
| lex-001 | 7 | 3 | 7 | 3 | miss | hit | miss | hit | signals | signals | signals | signals | REVERSES (QRL artifact vs H1 A); MECHANISM-SPECIFIC dense synonymy |
| lex-002 | 4 | 3 | 4 | 4 | hit | hit | hit | hit | input_fields | consumer | input_fields | impact | STABLE GUARDRAIL |
| spec-001 | — | — | — | — | unm. | unm. | unm. | unm. | verdict | **date** | verdict | verdict | STABLE diagnostic; QRL ARTIFACT |
| spec-002 | 9 | 1 | 3 | 10 | miss | hit | hit | miss | verdict | **producer** | verdict | signals | MECHANISM-SPECIFIC morphology |
| mch-001 stamp | 5 | 2 | 5 | 5 | miss* | hit* | miss* | hit* | verdict | consumer | verdict | consumer | UNRESOLVED conjunction; incidental hits |
| mch-001 consumer | 6 | 1 | 6 | 1 | miss* | hit* | miss* | hit* | verdict | consumer | verdict | consumer | UNRESOLVED conjunction |
| ood-001 | — | — | — | — | unm. | unm. | unm. | unm. | question 0.153 | title **0.0** | question 0.134 | stamp 0.110 | no reject HOLDS; QRL zero-vector ARTIFACT |
| ood-002 | — | — | — | — | unm. | unm. | unm. | unm. | impact 0.164 | verdict 0.115 | impact 0.172 | verdict 0.271 | UNRESOLVED reject; H1 more confident |
| ood-003 | — | — | — | — | unm. | unm. | unm. | unm. | verdict alias 0.5 | verdict alias 0.5 | verdict alias 0.5 | verdict alias 0.5 | HOLDS alias pathology |
| gold question | top-3 | top-3 | top-3 | top-3 | — | date rank 2 | held | held | — | ARTIFACT overlay | STABLE | STABLE | STABLE GUARDRAIL membership |

\*mch-001 hit requires **both** targets in top-k.

Signals = `upstream_signals_since_verdict_independent`. date = section `date` with slug-as-spaces alias.

On every H1 in-scope producer row, Jaccard, alias, and `lexical_cosine` matched control. H1 movement is the cosine-term replacement. H-QRL/H-MORPH movement is query-string change into the same lexical scorer.

## Row-level questions

### sem-001

A. Identifier-register miss: query `regime` vs producer `regime_stability` / `RegimeObserver.step`.
B. H-QRL identifier expansion theoretically; H1 dense theoretically; H-MORPH should not.
C. QRL selected the wrong `regime_*` family and injected `date`. MORPH rank 10. H1 rank 9, producer `dense_cosine` 0.263 vs verdict 0.600.
D. H1 has some dense correspondence; not enough. QRL producer score fell. MORPH unchanged.
E. QRL rank-1 is alias. H1 rank-1 is prosaic dense attraction, not alias.
F. Specialized: neither generic identifier dumping nor MiniLM prose embeddings recover this chunk. UNRESOLVED as a repair.

### lex-001

A. Closed-vocab synonymy (`consistency`/`confidence`/`market-condition` vs `stability`/`vwap_dist`).
B. H1 theoretically; H-QRL should not invent those names; H-MORPH must not.
C. QRL rank 7→3 while producer score 0.037→0.031. MORPH rank 7, neighbor strengthened by `signals`. H1 rank 7→3, producer `dense_cosine` 0.284, Jaccard frozen.
D. Only H1 improved target correspondence. QRL improved rank only.
E. QRL: stopword stripping (B). H1: dense cosine (A). Neighbor remains rank 1 in all four traces.
F. MECHANISM-SPECIFIC dense synonymy. Same rank delta under QRL and H1 is not the same mechanism. REVERSES the interpretation of “lex-001 improved.”

### spec-002

A. Morphology (`threshold` vs stored `thresholds`) plus label-set paraphrase.
B. H-QRL/H-MORPH morphology; H1 not required to win.
C. QRL rank 9→1 cosine 0.052→0.183. MORPH rank 9→3 cosine 0.052→0.145, alias 0. H1 rank 9→10, `dense_cosine` 0.108.
D. Morphology raised absolute producer cosine/Jaccard. Dense did not.
E. QRL rank 1 mixed morphology with stripping. MORPH kept `the`, so verdict stayed rank 1. Cleaner A.
F. MECHANISM-SPECIFIC morphology. H1 non-win does not weaken morphology.

### mch-001

A. Conjunction: stamp write + consumer read.
B. None of the three interventions was a hop/conjunction controller.
C. QRL both entered top-k (consumer rank 1). MORPH still 5 and 6. H1 consumer rank 1, stamp rank 5, conjunction hits.
D/E. QRL used identifier expansion plus stripping. H1 used dense attraction to the consumer paragraph. Neither was a designed multi-chunk planner.
F. UNRESOLVED architecture. Incidental hits are not a conjunction solution.

### ood-003

A. Alias trap: `verdict` substring.
B. None is an alias-contract experiment (H-ALIAS is future).
C. All four keep verdict rank 1 with alias 0.5.
F. HOLDS as an architecture invariant. Representation changes do not remove the trap.

## Findings that HOLD

1. **Rank is not correspondence.** The same lex-001 rank 7→3 is B under H-QRL and A under H1. sem-003 can become rank 1 under H-MORPH while gold score falls. HOLDS across all three tests.
2. **Global hit rate is not an optimization target.** 3/7 → 6/7 (QRL, joint claim weakened) → 4/7 (MORPH, predicted morphology hit) → 5/7 (H1, mixed A plus incidental mch-001). HOLDS.
3. **Generic identifier-segment expansion is not a semantic bridge.** sem-001 never received `regime_stability`. HOLDS; H1 did not revive that mechanism.
4. **Closed-vocabulary morphology repairs the morphological miss.** spec-002 is A under QRL and MORPH. HOLDS as a specialized claim.
5. **Machine-generated identifier tokens can fire alias matching.** The `date` artifact is present only when `regime_update_interval_seconds` is emitted. HOLDS; causal isolation by H-MORPH and H1 (no such token) strengthens it.
6. **Alias-trap ood-003 is representation-invariant.** Verdict +0.5 in all four. HOLDS.
7. **There is still no reject path.** Far and near OOD always return a top-k. HOLDS.
8. **The lex-001 signals neighbor is an invariant competitor.** Rank 1 in control, QRL, MORPH, and H1. HOLDS.

## Findings that BREAK

1. **“Query rewriting improves lexical-gap retrieval” as a general claim.** BREAKS: H-QRL’s lex-001 hit does not survive H-MORPH, and its producer score had fallen.
2. **H-QRL as a joint producer-burial repair.** BREAKS: identifier half failed; morphology half is a different failure class; dense is a third class.
3. **H-QRL far-OOD residual ranking.** BREAKS into a zero-vector after stripping, unlike control/MORPH/H1 residual scores.
4. **Generality of MiniLM as the producer-burial representation.** BREAKS the original H1 hope that one dense cosine term would move all three producer probes. spec-002 and sem-001 did not follow lex-001.

## Findings that REVERSE

1. **lex-001 rank gain.** Positive under H-QRL (artifact B) and H1 (correspondence A); zero under H-MORPH. Direction of “did the producer improve?” reverses with the mechanism.
2. **spec-002.** Strongly positive under morphology; slightly negative under H1 (rank 9→10).
3. **sem-001 rank.** Slightly worse under H-QRL (−1), unchanged under MORPH, slightly better under H1 (+1) without recovery. Direction changes; none is a solution.
4. **sem-003 rank-1 identity.** Control/QRL/H1 keep or restore `verdict` as rank 1 (QRL with `date` overlay). H-MORPH puts gold first by competitor weakening. Rank-1 “win” reverses without correspondence gain.
5. **mch-001 conjunction.** Miss under control and MORPH; hit under QRL and H1 for different non-conjunction reasons.

## Mechanism-specific successes

| Failure class | Matching intervention | Evidence |
| --- | --- | --- |
| Simple morphology | H-MORPH (and H-QRL morphology fragment) | spec-002 producer cosine/Jaccard rise, alias 0 |
| Closed-vocab synonymy | H1 dense cosine | lex-001 producer `dense_cosine` 0.284, Jaccard frozen, neighbor still rank 1 |
| Identifier-register producer burial | none of the three | sem-001 remains ranks 11/10/9 |
| Alias contract for generated tokens | not tested as a fix; H-MORPH/H1 only remove the offending tokens | date artifact gone when identifiers are not emitted |
| Conjunction / multi-hop | none designed | incidental hits only |

Specialization is the supported decomposition. More rows “won” is not more mechanism.

## Persistent failures / invariants

Behavior that persists despite changing the intervention:

- `1_upstream_producer_score_definition` stays outside a decisive recovery on sem-001 (ranks 10, 11, 10, 9).
- `upstream_signals_since_verdict_independent` remains lex-001 rank 1 under every scorer.
- `verdict` remains a default prosaic attractor for regime/conviction wording (control, much of H1, leftover-`the` under MORPH).
- Alias-trap `ood-003` keeps verdict rank 1 with +0.5.
- No OOD reject exists.
- Conjunction is not a first-class retrieval object.
- Cache/tracker were ranking-transparent when used (QRL, MORPH); H1 did not use them.
- Exact-term gold queries still retrieve question / verdict / Finding 3.5 in top-3 on each path that was checked.

These point at architecture (alias substring matching, single-chunk ranking, analyzer that keeps identifiers whole, MiniLM’s prose bias) rather than a local weight.

## Artifact-driven results

| Apparent result | Actual mechanism | Status after comparison |
| --- | --- | --- |
| H-QRL lex-001 rank 7→3 hit | competitor collapse after stripping; producer score down | ARTIFACT; disappears under H-MORPH |
| H-QRL rank-1 `date` on many rows | `regime_update_interval_seconds` ⊃ `date` alias +0.35 | ARTIFACT; gone under MORPH and H1 |
| H-QRL spec-002 rank 1 | morphology plus stripping of `the` | morphology HOLDS; rank 1 is bundled |
| H-QRL far-OOD score 0 | all remaining tokens OOV | ARTIFACT of stripping |
| H-MORPH sem-003 rank 1 | gold score fell; verdict fell more (B) | not semantic improvement |
| H1 title-chunk neighbors | MiniLM similarity with Jaccard 0 | overlay, not producer correspondence |
| H1 mch-001 hit | consumer dense 0.516, stamp still rank 5 | incidental, not a conjunction design |

## Guardrails across all interventions

| Guardrail | Control | QRL | MORPH | H1 |
| --- | --- | --- | --- | --- |
| sem-002 hit | yes r2 | yes r4, wrong winner `date` | yes r1 | yes r1 |
| sem-003 in top-k | yes r2 | yes r2, wrong winner `date` | yes r1 (B) | yes r3 |
| lex-002 in top-k | yes r4 | yes r3 | yes r4 | yes r4 |
| gold queries top-3 | yes | yes, with `date` rank 2 on some | yes | yes |
| producer-row alias 0 | yes | yes on gold; other chunks aliased | yes | yes |

H-QRL is the only intervention that contaminates guardrail **winners** with `date`. Membership in top-k is otherwise STABLE.

## OOD behavior

| Row | Control | QRL | MORPH | H1 |
| --- | --- | --- | --- | --- |
| far ood-001 | residual question 0.153 | rewritten zero-vector / title 0.0 | residual question 0.134 | residual stamp dense 0.150 |
| near ood-002 | impact 0.164 | verdict 0.115 | impact 0.172 | verdict dense 0.370 |
| alias-trap ood-003 | verdict 0.701 alias 0.5 | verdict 0.570 alias 0.5 | verdict 0.680 alias 0.5 | verdict 0.677 alias 0.5 |

Far-OOD is never a confident in-domain hit except the QRL zero-vector collapse, which is not a reject. Near-OOD becomes most confident under H1. Do not invent a threshold here. That is a later hypothesis.

## Failure-mode × intervention map

| failure class | control | H-QRL | H-MORPH | H1 | H-CODE | current best explanation |
| --- | --- | --- | --- | --- | --- | --- |
| simple morphology | fails (spec-002 r9) | repaired but bundled (r1) | repaired cleanly (r3, A) | fails (r10) | unexpected hit (r3) via code/label correspondence, not `threshold→thresholds` | morphology remains the matching surface-form repair; H-CODE overlay is not a substitute |
| semantic producer burial (identifier-register) | fails (sem-001 r10) | identifier expansion fails (r11) + date artifact | unchanged (r10) | still buried (r9), dense 0.263 vs 0.60 | correspondence A (r6, code 0.520 vs MiniLM 0.263); still miss; consumer 0.665 | code-register representation repairs correspondence, not full retrieval; MiniLM prose cosine insufficient |
| lexical synonym mismatch | fails (lex-001 r7) | misleading rank gain (artifact B) | unchanged (r7); `signals` helps neighbor | repaired as A (r3); neighbor still r1 | repaired as A (r1); neighbor falls to r7 | MiniLM and code cosine both recover synonymy; H-CODE stronger here |
| conjunction / multi-chunk | fails (stamp r5, consumer r6) | incidental hit | fails | incidental hit | incidental hit (consumer r1, stamp r2) | unresolved architecture |
| alias trap | pathological | remains | remains | remains | remains | alias architecture |
| far OOD | no reject, residual scores | rewritten zero-vector | residual scores | residual dense ~0.15 | residual code ~0.36 | reject mechanism absent |
| near OOD | mention attraction | less impact, still no reject | similar to control | more confident (~0.37) | producer rank 1 (code 0.527) via identifier attraction | reject mechanism absent; code-register false neighbor |

N/A is not used: every cell has an observation, even when the intervention was not designed for that class.

## System claims audit

| system finding | H-QRL evidence | H-MORPH evidence | H1 evidence | status after 3 tests | reason |
| --- | --- | --- | --- | --- | --- |
| Closed-vocabulary morphology repairs simple surface-form misses | spec-002 A | spec-002 A isolated | spec-002 not repaired | **strengthened** as specialized, not general | H1 non-win is predicted, not a morphology failure |
| Generic identifier-segment expansion is not a reliable semantic bridge | sem-001 missed `regime_stability`; wrong family | identifiers disabled; still miss | no identifier dumping; still miss | **strengthened** | H1 shows a different bridge also fails this row; dumping remains unsupported |
| High IDF is not a sufficient relevance criterion for expansion | IDF cap picked rare wrong identifiers | N/A (no IDF ranking) | N/A | **unchanged** | still H-QRL-only test |
| Machine-generated rewrite tokens can violate alias assumptions | date +0.35 from `...update...date...` | offending token absent; date alias 0 | no generated tokens; date not rank 1 | **strengthened** | causal isolation across two later tests |
| Rank gain is not equivalent to improved correspondence | lex-001 score down, rank up | sem-003 rank up, score down | lex-001 rank up with dense A; QRL same delta was B | **strengthened** | identical rank deltas can be A or B |
| Global hit rate is not a valid optimization target | 3/7→6/7, joint claim weakened | 3/7→4/7 from predicted spec-002 | 3/7→5/7 mixed | **strengthened** | three different hit counts, none is the verdict |
| Cache is ranking-transparent | 0/12 then 12/12 | replicated under morph-v1 | not used | **unchanged** (loop); **still untested** on H1 | H1 had no rewrite cache |
| Tracker is useful when observational | observe-only | observe-only | no rewrite tracker | **unchanged** (loop); **still untested** on H1 | operational, not quality |

## What the three tests collectively establish

1. Failure classes in this corpus do not share one repair.
2. Morphology, identifier expansion, and dense cosine are different mechanisms with different blast radii.
3. Apparent rank wins must be decomposed into A/B/C/D every time, including when two experiments show the same rank delta.
4. Alias matching is an independent architecture surface. It created the `date` artifact and still owns ood-003 after representation changes.
5. Producer burial is at least two remaining problems: identifier-register (sem-001, unsolved) and morphology (spec-002, solved when isolated). Synonymy (lex-001) is a third class and is the one MiniLM actually moved.
6. A composite retriever is a **new** hypothesis, not a conclusion licensed by this audit.

## What they do NOT establish

- Which encoder would recover sem-001.
- Whether morphology + dense + lexical evidence should be combined, or at what weights.
- A production ranking policy.
- An OOD reject threshold.
- Generality beyond this 15-chunk note and 12-row set.
- That H1 “won” because it has more hits than H-MORPH.

## Next hypotheses (not implemented)

- **H-HYBRID:** preregister a combination such as morph-v1 query text + dense cosine, or `0.7 * dense + 0.3 * jaccard + alias` with morphology, without identifier expansion. Do not tune on these sealed rows.
- **H-CODE:** a code/identifier-aware representation for producer-register misses that MiniLM treated as weak neighbors.
- **H-ID:** constrained identifier expansion that forbids filename tokens and short section-id substring traps.
- **H-ALIAS:** different alias semantics for natural-language tokens vs generated tokens; do not blacklist `date` from this set.
- **H-OOD:** reject/calibration now that near-OOD dense scores approach in-scope values.
- **H-MORPH-N:** more morphological coverage / minimum token length.

Do not implement these on this branch as part of this audit.

---

# H-CODE addendum (fifth experiment)

H-CODE was executed after this four-way audit froze. Details: `docs/query_set_expansion/2026-10-05_hcode_findings.md`. This addendum does not rewrite the four-way row narratives above. It records what the fifth representation changed.

Query-set and lexical-index hashes still match. MiniLM index `bc1cb4f3a354cf14250bcf7a41ac6edfb16e1e6f98f4d38819542129b11db3c6` was used only as diagnostic `dense_cosine`.

## What HOLDS after H-CODE

- Rank is not correspondence. spec-002 rank 9→3 under H-CODE is A on code/label cosine, not H-MORPH’s `threshold→thresholds`.
- Global hit rate is not an optimization target. H-CODE measurable hits are 6/7. The verdict is partial support on sem-001 correspondence, not 6/7.
- Generic identifier-segment expansion is still unsupported. H-CODE never emitted `regime_stability` into the query.
- Closed-vocabulary morphology remains the matching spec-002 mechanism. H-CODE’s spec-002 hit is a different overlay.
- Machine-generated identifier tokens can fire alias matching. H-CODE generated none; `date` was not rank 1.
- Alias-trap ood-003 is representation-invariant. Verdict +0.5 in all five traces.
- There is still no reject path.

## What BREAKS or narrows after H-CODE

- **“MiniLM prose cosine is the last word on sem-001.”** BREAKS as a terminal diagnosis. Code cosine 0.520 vs MiniLM 0.263; rank 10/11/10/9 → 6. Still a miss.
- **“The signals neighbor is rank 1 on lex-001 under every intervention.”** BREAKS. H-CODE puts the producer at rank 1 and the neighbor at rank 7.
- **“Identifier-register burial survives all representation interventions.”** NARROWS. It survives MiniLM. It does not survive code cosine as a correspondence failure. It survives as a top-k miss against the consumer.

## Mechanism-specific successes after five tests

| Failure class | Matching intervention | Evidence |
| --- | --- | --- |
| Simple morphology | H-MORPH | spec-002 producer cosine/Jaccard rise from `thresholds` |
| Closed-vocab synonymy | H1 MiniLM (also H-CODE, stronger rank) | lex-001 A; H-CODE rank 1 is additional A, not a MiniLM retraction |
| Identifier-register producer burial | H-CODE **partial** | sem-001 code 0.520, rank 6, consumer still 0.665; MiniLM and identifier dumping failed |
| Alias contract for generated tokens | not tested as a fix | date artifact gone when identifiers are not emitted |
| Conjunction / multi-hop | none designed | incidental hits only |

## Next hypotheses (not implemented)

Unchanged in kind: H-HYBRID/H-ROUTE, H-OOD, H-ID, H-ALIAS, H-MORPH-N. H-CODE is no longer an open representation question on this sealed set. Do not implement hybrids on the H-CODE branch as part of this measurement.
