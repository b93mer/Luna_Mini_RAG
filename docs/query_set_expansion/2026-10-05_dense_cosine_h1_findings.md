# Findings: dense semantic cosine (`H1`)

**Date:** 2026-10-05 (runs executed 2026-10-06T03:23Z–03:25Z UTC; the logger names run files by UTC date)
**Status:** Experiment result. Query-set bytes unchanged. Frozen lexical hybrid scoring unchanged when the flag is off. Historical control, H-QRL, and H-MORPH traces unchanged.
**Preregistration:** `docs/query_set_expansion/2026-10-05_dense_cosine_h1_preregistration.md`
**Control:** `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` / `eval_sets/runs/2026-09-29_run-004.jsonl`
**This document is observation.** Predictions stay in the preregistration. YAML queries, golds, and locked `current_stack_prediction` values were not rewritten.

H1 is a representation intervention: replace the TF-IDF cosine term with MiniLM dense cosine. It is not H-QRL. It is not H-MORPH. Query rewriting was off.

## Experimental state

| Piece | Identity |
| --- | --- |
| Branch | `research/dense-cosine-h1` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` (seal matched) |
| Lexical index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` (matched the frozen control) |
| Dense index | `metadata/dense_h1_index.json`, 15 rows |
| Dense index sha256 | `bc1cb4f3a354cf14250bcf7a41ac6edfb16e1e6f98f4d38819542129b11db3c6` |
| Frozen lexical scoring | Unchanged: `0.7 * lexical_cosine + 0.3 * jaccard + alias` |
| H1 scoring | `0.7 * dense_cosine + 0.3 * jaccard + alias` |
| TOP_K | 5 |
| Dense model | `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Encoder runtime | CPU; `sentence-transformers` 6.1.0; `torch` 2.14.1+cpu; 384-d; mean pooling; L2-normalized |
| `embed.py` sha256 | `2567d09b5da424f55f8470363a036926683b3ac6e8d6db8e1b36318bcf66dfcf` (matched preregistration) |
| `evaluate.py` sha256 | `97d953d99f0b9136b069a764afa04536555911f9c23f8566a1563933361fc579` (matched preregistration) |
| `retrieve.py` sha256 | `cb73333592d634b24ca0bb3157a9ce625a75a067c0546b2bba2e600b970946a0` (explicit `lexical_cosine`/`dense_cosine` fields; frozen lexical formula/weights/aliases unchanged since `000e658`) |
| Flag-off sanity | `eval_sets/runs/2026-10-06_run-005.jsonl` (run UUID `5796798e-2cb2-4124-8b7d-88617081c5f7`); expected-target ranks and six-decimal lexical scores matched frozen control exactly; `dense_cosine` 0.0 |
| Experiment pass | `eval_sets/runs/2026-10-06_run-006.jsonl` (run UUID `67368f9e-2323-409d-9b71-4180d7086392`) |
| Frozen `evaluate.py` functions | PASS (section lookup + hybrid gold queries, no re-ingest in this measurement) |
| H1 gold queries | question / verdict / Finding 3.5 each remain in top-3 under `rank_all_h1` |
| Unit tests | 61/61 pass |

`rank_gain = control_rank - experiment_rank`. Positive is movement toward rank 1.

Comparison is to `expanded-control-v1`, not to H-QRL or H-MORPH ranks.

**Score-scale caution.** Control totals and H1 totals are not like-for-like correspondence metrics. Jaccard and alias used identical implementations and, on every sealed row, matched control to six decimals. Rank, `dense_cosine` among chunks of the same query, and within-H1 margins are the valid comparisons.

## Verdict on H1

**Partially supported.** Do not treat the 3/7 → 5/7 measurable hit count as the result.

Dense cosine recovered **closed-vocab synonymy** on `qse-docqa-lex-001` and did **not** recover the **identifier-bound producer** on `qse-docqa-sem-001`. Morphology-specific `spec-002` stayed a miss and moved slightly backward, which is a diagnostic, not a requirement.

1. **Primary semantic producer-burial was not recovered.** `sem-001` moved rank 10 → 9 and stayed a miss. Producer `dense_cosine` is 0.263470 against `verdict` 0.600096, `question` 0.551463, and the consumer 0.552181. MiniLM prefers prosaic conviction/regime neighbors over the identifier-heavy score-definition chunk. Rank +1 is not meaningful recovery.
2. **Lexical synonymy was recovered as mechanism A.** `lex-001` moved rank 7 → 3 and entered top-k. Producer `dense_cosine` 0.284254 exceeds former TF-IDF leftovers (`verdict` dense 0.260085) while Jaccard, `lexical_cosine`, and alias are identical to control. Rank 1 remains the diagnosed lexical neighbor (`upstream_signals_since_verdict_independent`, dense 0.379759). This is target correspondence, not H-QRL-style competitor collapse after stopword stripping.
3. **Morphology is not interchangeable with dense cosine.** `spec-002` rank 9 → 10. Producer `dense_cosine` 0.107786 is weak. H-MORPH’s `threshold → thresholds` remains the matching mechanism for that row.
4. **Guardrails stayed hits.** `sem-002` became rank 1. `sem-003` slipped 2 → 3 but stayed in top-k. `lex-002` held rank 4. Frozen and H1 gold queries still place each target in top-3.
5. **Unexpected conjunction hit is not H1 success.** `mch-001` became a hit because the consumer jumped rank 6 → 1 (`dense_cosine` 0.515935) while the stamp stayed rank 5. That was not a producer-burial prediction.
6. **Dense overgeneralization is real.** The document-title chunk entered top-k on `lex-001` and `sem-002` with Jaccard 0. Near-OOD top `dense_cosine` rose to ~0.37. Far-OOD stayed weakly similar (~0.15). Alias-trap still fires from the original `verdict` substring.

## Measurable rank table

| row | control rank | experiment rank | rank_gain | control outcome | experiment outcome | target alias | experiment rank-1 |
| --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| sem-001 | 10 | 9 | +1 | expected_miss | expected_miss | 0.0 | `verdict` |
| sem-002 | 2 | 1 | +1 | hit | hit | 0.0 | gold (`impact_on_finding_3_5_disposition`) |
| sem-003 | 2 | 3 | −1 | hit | hit | 0.0 | `verdict` |
| lex-001 | 7 | 3 | +4 | expected_miss | hit | 0.0 | `upstream_signals_since_verdict_independent` |
| lex-002 | 4 | 4 | 0 | hit | hit | 0.0 | `impact_on_finding_3_5_disposition` |
| spec-002 | 9 | 10 | −1 | expected_miss | expected_miss | 0.0 | `upstream_signals_since_verdict_independent` |
| mch-001 stamp | 5 | 5 | 0 | expected_miss (conjunction) | hit (conjunction) | 0.0 | consumer |
| mch-001 consumer | 6 | 1 | +5 | expected_miss (conjunction) | hit (conjunction) | 0.0 | consumer (gold) |

Measurable outcomes: control `hit=3, expected_miss=4`; experiment `hit=5, expected_miss=2`. Global hit rate is still not an optimization target.

## Score-component table

Raw control score and H1 score are **not** directly comparable. Jaccard and alias matched control on every row below.

| row | control rank | H1 rank | rank gain | control score | H1 score | lexical_cosine | dense_cosine | jaccard | alias | mechanism interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sem-001 | 10 | 9 | +1 | 0.015352 | 0.187763 | 0.017169 | 0.263470 | 0.011111 | 0.0 | weak A; producer still buried by prosaic neighbors |
| sem-002 | 2 | 1 | +1 | 0.250598 | 0.348368 | 0.337091 | 0.476763 | 0.048780 | 0.0 | A on an already-good guardrail |
| sem-003 | 2 | 3 | −1 | 0.312499 | 0.322686 | 0.396006 | 0.410560 | 0.117647 | 0.0 | still a hit; verdict dense 0.541 outranks gold 0.411 |
| lex-001 | 7 | 3 | +4 | 0.037137 | 0.202274 | 0.048343 | 0.284254 | 0.010989 | 0.0 | A; synonymy, not stripping; neighbor remains rank 1 |
| lex-002 | 4 | 4 | 0 | 0.074985 | 0.189501 | 0.093297 | 0.256891 | 0.032258 | 0.0 | stable guardrail; rank-1 identity changed to impact |
| spec-002 | 9 | 10 | −1 | 0.042792 | 0.081972 | 0.051815 | 0.107786 | 0.021739 | 0.0 | diagnostic: dense does not replace morphology |
| mch-001 stamp | 5 | 5 | 0 | 0.149995 | 0.268618 | 0.187905 | 0.357366 | 0.061538 | 0.0 | stamp stable; conjunction hit via consumer |
| mch-001 consumer | 6 | 1 | +5 | 0.137716 | 0.383980 | 0.164129 | 0.515935 | 0.076087 | 0.0 | unexpected A on consumer, not the producer-burial claim |

## Primary slice

### qse-docqa-sem-001 — predicted strongest test, not recovered

Original YAML query. Rewritten query empty. Expansions empty. Alias 0.0 on the producer.

| Quantity | Control | Experiment |
| --- | ---: | ---: |
| producer rank | 10 | 9 |
| producer Jaccard / alias / lexical_cosine | 0.011111 / 0.0 / 0.017169 | identical |
| producer `dense_cosine` | (not computed) | 0.263470 |
| rank-1 identity | `verdict` 0.316521 | `verdict` 0.457567 (`dense_cosine` 0.600096) |

Producer `dense_cosine` is not a near-zero floor. It is also not competitive. Margin to rank 1 on dense cosine is −0.336626. The same prosaic chunks that won under TF-IDF (`verdict`, `question`, consumer) remain the dense neighbors because the query is natural-language “regime-related score / conviction assessment” and those chunks are short prose, while the gold is identifier-heavy (`regime_stability`, `RegimeObserver.step`, `vwap_dist`).

Classification: weak **A** (nonzero dense target evidence) that fails to unbury the producer. Rank +1 is not support for the primary claim. This is the falsification fragment “sem-001 remains buried.”

### qse-docqa-lex-001 — predicted secondary test, mechanism A

No `stability`. No `vwap_dist`. Query text identical to YAML. Jaccard and `lexical_cosine` identical to control.

| Quantity | Control | Experiment |
| --- | ---: | ---: |
| producer rank | 7 | 3 |
| producer Jaccard / alias / lexical_cosine | 0.010989 / 0.0 / 0.048343 | identical |
| producer `dense_cosine` | (not computed) | 0.284254 |
| rank-1 identity | signals neighbor 0.143566 | same neighbor 0.276545 (`dense_cosine` 0.379759) |

Within H1, producer dense 0.284254 exceeds `verdict` 0.260085 and is below the neighbor 0.379759 and impact 0.331066. Rank movement is the cosine-term replacement, not stopword stripping (function words were never removed) and not alias.

Overlay: the title chunk `regime_factor_composition_trace` is rank 4 with Jaccard 0.0, `lexical_cosine` 0.0, `dense_cosine` 0.270298. That is semantic overgeneralization, not producer correspondence.

Classification: **A**. Count as support for dense synonymy. Do not treat H-QRL’s earlier rank-7→3 as the same mechanism; that one lowered producer score. This one raises producer dense correspondence and leaves the neighbor first.

### qse-docqa-spec-002 — mechanism-specific diagnostic, dense did not help

H-MORPH repaired this row with `threshold → thresholds`. H1 used the original query.

Producer rank 9 → 10. Producer `dense_cosine` 0.107786, among the weakest content chunks. Rank 1 is the signals neighbor (`dense_cosine` 0.291467), not the four-way label set.

Dense paraphrase did not map “percentile-threshold / in-between / missing-data” onto `thresholds` / `TRANSITION` / `UNKNOWN` strongly enough to compete. This is the predicted diagnostic: morphology solves this failure class more cleanly. Not H1 falsification.

## Guardrails

| Guardrail | Result |
| --- | --- |
| sem-002 stays a hit | Held and became rank 1. Gold `dense_cosine` 0.476763 beats verdict 0.350917. Mechanism **A** on an already-good row. Title chunk entered top-k (Jaccard 0.071). |
| sem-003 stays ≤ rank 2 or in top-k | Held in top-k at rank 3. Gold dense 0.410560; verdict 0.540934. Not a miss. |
| lex-002 in top-k | Held at rank 4. Rank 1 changed from `input_fields_consumed` to impact (`dense_cosine` 0.361507). |
| mch-001 stamp in top-k | Held at rank 5. Consumer rank 6 → 1, so the conjunction flipped to hit. Not counted as producer-burial support. |
| frozen `evaluate.py` PASS | Held (no re-ingest) |
| H1 gold queries in top-3 | Held: question rank 1 (alias 0.5 + dense 0.712067); verdict rank 1 (alias 0.5 + dense 0.566486); Finding 3.5 rank 1 (alias 0.5 + dense 0.515125) |

Producer-target alias remained 0.0 on in-scope golds. No rewrite tokens existed to fire slug-as-spaces `date`.

## Unmeasurable / diagnostic

Not scored as hit/miss.

| row | control rank-1 | experiment rank-1 | note |
| --- | --- | --- | --- |
| spec-001 | verdict 0.284 | verdict 0.287 dense 0.379 | still underspecific; title chunk rank 2 |
| ood-001 | question 0.153 | stamp 0.110 dense 0.150 | far-OOD top dense ~0.15, well below in-scope 0.4–0.6; residual ranking, no reject path |
| ood-002 | impact 0.164 | verdict 0.271 dense 0.370 | near-OOD more confident than the lexical baseline; producer also 0.348 because it contains COMPRESS; still no reject path |
| ood-003 | verdict 0.701 alias 0.5 | verdict 0.677 alias 0.5 | trap still fires; dense actually prefers `scope` (0.274) over `verdict` (0.235), but alias restores verdict |
| hop-001 | verdict 0.260 | question 0.495 dense 0.635 | not hop success; dense strongly attracts the short `question` field |

Far-OOD is not pathologically confident relative to in-scope dense scores. Near-OOD calibration is a later hypothesis, not a reject threshold invented here.

## Dense blast radius

Observed, not patched:

- Generic/title chunks become neighbors when Jaccard is 0 (`lex-001` rank 4, `sem-002` rank 4).
- Short prosaic fields (`verdict`, `question`) remain strong dense attractors for regime/conviction wording.
- Near-OOD `dense_cosine` (~0.37) sits closer to in-scope scores than far-OOD (~0.15).
- Score margins among top dense neighbors are smaller than TF-IDF’s producer-vs-verdict gap on `sem-001` in the sense that many chunks now have `dense_cosine` 0.2–0.6, but in-scope vs far-OOD still separates.

No alias contamination from generated identifiers, because no identifiers were generated.

## Falsification checklist (from the preregistration)

- `sem-001` remains buried with little meaningful dense target correspondence → **partially triggered** (buried, yes; correspondence is 0.263 vs neighbor 0.60, not a floor of ~0)
- `lex-001` moves only because competitors change rather than target correspondence → **not triggered** (Jaccard/`lexical_cosine` frozen; producer dense 0.284 is the moving term)
- dense similarity promotes broad but incorrect conceptual neighbors → **triggered as overlay** (title chunk; prosaic verdict/question on sem-001)
- guardrails regress substantially → **not triggered**
- near/far-OOD become pathologically confident → **far-OOD no; near-OOD more confident, documented, no reject invented**
- aliases explain apparent wins → **not triggered**
- gains require changing weights after seeing results → **not triggered**
- gains depend on changing chunks/golds/TOP_K/query text → **not triggered**
- only aggregate hit rate improves while the predicted mechanism fails → **hit rate rose, but lex-001 is a real A; sem-001 mechanism failed; do not accept 5/7**
- query rewriting / morphology / identifier expansion silently applied → **not triggered**
- a different embedding model selected after seeing ranks → **not triggered**

`spec-002` non-improvement relative to H-MORPH is **not** falsification.

H1 as the claim “dense cosine recovers producer burial that lexical TF-IDF cannot connect” is **partially supported**: it recovers the synonymy miss and does not recover the identifier-register miss.

## Deliberate non-actions after seeing results

This sprint did not:

- swap MiniLM for another embedding model
- retune 0.7 / 0.3 or add lexical cosine back into the blend
- add `regime_stability` or other semantic bridges
- blacklist `date` or retune aliases
- rewrite YAML queries or golds
- change TOP_K or chunk boundaries
- turn morphology or identifier expansion on
- invent an OOD reject threshold
- implement a hybrid morphology + dense retriever

## What a next experiment could ask (not implemented)

- Whether a code-aware or identifier-aware encoder recovers `sem-001` without promoting title/verdict neighbors (new representation hypothesis).
- Whether combining frozen morphology with dense cosine is useful (a fourth, separately preregistered hypothesis). Do not build that composite on this branch.
- Near-OOD calibration / reject, now that dense scores on `ood-002` are closer to in-scope values.
- Constrained identifier expansion (H-ID) remains a different mechanism; H1 did not make it unnecessary for `sem-001`.

Do not start those experiments on this branch as part of this measurement.

## References

- Preregistration: `docs/query_set_expansion/2026-10-05_dense_cosine_h1_preregistration.md`
- Producer-burial forensics: `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- H-QRL findings: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`
- H-MORPH findings: `docs/query_set_expansion/2026-10-05_morphology_only_findings.md`
- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
- Flag-off sanity: `eval_sets/runs/2026-10-06_run-005.jsonl`
- Experiment trace: `eval_sets/runs/2026-10-06_run-006.jsonl`
- Dense index: `metadata/dense_h1_index.json`
