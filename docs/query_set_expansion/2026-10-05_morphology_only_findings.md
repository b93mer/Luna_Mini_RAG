# Findings: closed-vocabulary morphology ablation (`H-MORPH`)

**Date:** 2026-10-05 (runs executed 2026-10-06T02:51Z UTC; the logger names run files by UTC date)
**Status:** Experiment result. Query-set bytes unchanged. Frozen hybrid scoring unchanged. Historical control traces unchanged. H-QRL traces unchanged.
**Preregistration:** `docs/query_set_expansion/2026-10-05_morphology_only_preregistration.md`
**Control:** `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` / `eval_sets/runs/2026-09-29_run-004.jsonl`
**This document is observation.** Predictions stay in the preregistration. YAML queries, golds, and locked `current_stack_prediction` values were not rewritten.

H-MORPH is a query-side ablation of H-QRL. It is not H1. It is not a retry of identifier-segment expansion.

## Experimental state

| Piece | Identity |
| --- | --- |
| Branch | `research/morphology-only-ablation` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` (seal matched) |
| Index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` (matched the frozen control) |
| Scoring | Unchanged: `0.7 * cosine(TF-IDF) + 0.3 * Jaccard + alias_boost` |
| TOP_K | 5 |
| Rewrite policy | `morph-v1` via `LUNA_MORPH_LOOP=1` (function words retained; identifier expansion disabled) |
| `embed.py` sha256 | `2567d09b5da424f55f8470363a036926683b3ac6e8d6db8e1b36318bcf66dfcf` (matched preregistration) |
| `evaluate.py` sha256 | `97d953d99f0b9136b069a764afa04536555911f9c23f8566a1563933361fc579` (matched preregistration) |
| `retrieve.py` sha256 | `91df8254f5888b167ebe15bcd7ef2fc28a4f67ba3fdbd6216043399175a29814` (docstring-only mention of `LUNA_MORPH_LOOP`; scoring/weights/aliases unchanged since `000e658`) |
| Flag-off sanity | `eval_sets/runs/2026-10-06_run-003.jsonl` (run UUID `a84506af-cf2b-4e71-9553-0dd63d625101`); expected-target ranks and six-decimal scores matched frozen control exactly |
| Experiment pass 1 | `eval_sets/runs/2026-10-06_run-004.jsonl` (run UUID `a3cbb75a-adac-4982-8970-54623cd66ae0`) |
| Tracker | `eval_sets/runs/2026-10-06_run-004_query_loop.json` |
| Frozen `evaluate.py` | PASS (section lookup + hybrid gold queries, no re-ingest in this measurement) |
| Loop gold queries | question / verdict / Finding 3.5 each remain in top-3 under morph-v1 |
| Unit tests | 46/46 pass |

`rank_gain = control_rank - experiment_rank`. Positive is movement toward rank 1.

Comparison is to `expanded-control-v1`, not to H-QRL ranks.

## Verdict on H-MORPH

**Supported**, with a small evaluation surface. Do not treat the 3/7 → 4/7 measurable hit count as the result.

The locked morphology family reproduced the spec-002 mechanism without identifier expansion:

1. **Primary morphological miss replicated.** `threshold → thresholds` (plus `labels → label`) moved the producer from rank 9 to rank 3. Producer cosine 0.051815 → 0.145072. Jaccard 0.021739 → 0.043478. Alias stayed 0.0. Absolute correspondence rose; this is mechanism **A**.
2. **Rank 1 was not reproduced.** Verdict remained rank 1 at 0.152476. That is the function-word decision working as designed: H-QRL’s rank-1 win mixed morphology with stopword stripping. H-MORPH kept `the`, so verdict’s leftover-function-word advantage survived. The preregistration said rank 1 was the strongest supporting pattern if it occurred, not a requirement.
3. **Identifier contamination disappeared.** Every identifier-expansion list was empty. `regime_update_interval_seconds` never appeared. The `date` section scored 0.0 with alias 0.0 on the previously contaminated in-scope rows.
4. **sem-001 did not get a false morphological cure.** Rank stayed 10. The only fire was `does → do`. Lack of movement is not H-MORPH failure.
5. **lex-001 rank-only H-QRL artifact did not recur.** Rank stayed 7. Producer score fell. The lexical neighbor strengthened on `signals`. Rank gain without target correspondence is not counted as support.

The cache claim is **supported**. The tracker claim (observe only) is **supported**.

## Measurable rank table

| row | control rank | experiment rank | rank_gain | control outcome | experiment outcome | target alias | experiment rank-1 |
| --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| sem-001 | 10 | 10 | 0 | expected_miss | expected_miss | 0.0 | `verdict` |
| sem-002 | 2 | 1 | +1 | hit | hit | 0.0 | gold (`impact_on_finding_3_5_disposition`) |
| sem-003 | 2 | 1 | +1 | hit | hit | 0.0 | gold (consumer) |
| lex-001 | 7 | 7 | 0 | expected_miss | expected_miss | 0.0 | `upstream_signals_since_verdict_independent` |
| lex-002 | 4 | 4 | 0 | hit | hit | 0.0 | `input_fields_consumed` |
| spec-002 | 9 | 3 | +6 | expected_miss | hit | 0.0 | `verdict` |
| mch-001 stamp | 5 | 5 | 0 | expected_miss (conjunction) | expected_miss (conjunction) | 0.0 | `verdict` |
| mch-001 consumer | 6 | 6 | 0 | expected_miss (conjunction) | expected_miss (conjunction) | 0.0 | `verdict` |

Measurable outcomes: control `hit=3, expected_miss=4`; experiment `hit=4, expected_miss=3`. Global hit rate is still not an optimization target.

## Primary slice

### qse-docqa-spec-002 — predicted mover, confirmed as mechanism A

Morphology: `label`, `thresholds`. Identifier expansions: none. Alias 0.0 on every scored chunk of this row.

| Quantity | Control | Experiment | Delta |
| --- | ---: | ---: | ---: |
| producer rank | 9 | 3 | +6 |
| producer score | 0.042792 | 0.114594 | +0.071802 |
| producer cosine | 0.051815 | 0.145072 | +0.093257 |
| producer Jaccard | 0.021739 | 0.043478 | +0.021739 |
| producer alias | 0.0 | 0.0 | 0.0 |
| rank-1 identity | `verdict` 0.140694 | `verdict` 0.152476 | +0.011782 |

The producer entered TOP_K. Cosine carried most of the gain; Jaccard also rose. Competitors did **not** collapse: verdict and `input_fields_consumed` scores increased slightly, but the producer increased more (+0.072 vs +0.012 and +0.023). Rank movement is therefore **A** (target correspondence), not **B**.

This is weaker than H-QRL’s cosine 0.183 / rank 1 because function words were retained on purpose. It is a cleaner attribution: the `thresholds` token is in the producer chunk, was missing from the raw query, and is now in the rewritten query.

### qse-docqa-sem-001 — predicted non-target, matched

Morphology: `do` (`does` ends in `es`, stem `do` is in-vocab). Identifier expansions: none. `regime_update_interval_seconds` absent.

Producer rank 10 → 10. Score 0.015352 → 0.014319. Cosine 0.017169 → 0.015746. Rank 1 remains `verdict` (0.316521 → 0.292624), not `date`. The `date` section is rank 11 at score 0.0, cosine 0, Jaccard 0, alias 0.0.

The incidental `do` token slightly dilutes TF. That is not a morphological repair of `regime` vs `regime_stability`. Non-movement is consistent with the diagnosis that this miss is identifier/semantic correspondence.

## Negative control

### qse-docqa-lex-001 — rank-only support withheld

No `stability`. No `vwap_dist`. Morphology: `measures`, `signals`. Rank stayed 7. Producer score 0.037137 → 0.027761, cosine 0.048343 → 0.035051.

Rank 1 remains the lexical neighbor `upstream_signals_since_verdict_independent`, and that neighbor **strengthened** (0.143566 → 0.188172) because `signals` is its distinctive token.

This is the opposite of H-QRL’s rank 7 → 3. H-QRL’s rank gain was competitor collapse after function-word stripping. With function words kept, that artifact disappeared. Morphology of `signal → signals` helped the wrong chunk.

Classification: not A, not a hit, not support. Overlay: morphology can amplify a lexical neighbor when the generated form already lives in the competitor.

## Guardrails

| Guardrail | Result |
| --- | --- |
| sem-002 stays a hit | Held and became rank 1. Gold score +0.004596; cosine slightly down (−0.000403); Jaccard up (`finding → findings`). Verdict fell 0.263968 → 0.237475. Mixed **A** (Jaccard from `findings`) and **B** (verdict dilution). Not counted as primary H-MORPH support. |
| sem-003 stays ≤ rank 2 or in top-k | Held and became rank 1. Gold **score fell** (0.312499 → 0.302373; cosine −0.018861). Rank gain is **B**: verdict fell more (0.323691 → 0.296124). Jaccard rose slightly (`produce`). Do not label this semantic improvement. |
| lex-002 in top-k | Held at rank 4. Score 0.074985 → 0.069618. Morphology: `field`. |
| mch-001 stamp in top-k | Held at rank 5; consumer remained rank 6; conjunction still misses. Morphology: `do`, `factor`, `objects`. |
| frozen `evaluate.py` PASS | Held |
| loop gold queries in top-3 | Held: question (no morphology); verdict (`factors`); Finding 3.5 (`changes`, `do`, `findings`). Finding 3.5 remains rank 1. Identifier lists empty. |

Producer-target alias remained 0.0 on in-scope golds. No slug-as-spaces `date` fire on in-scope rows.

### `date` alias contamination — gone with identifier expansion

Direct checks demanded by the preregistration:

1. `regime_update_interval_seconds` is absent from every rewritten query and every expansion list.
2. Identifier-frequency in the tracker is `{}`.
3. On H-QRL’s previously contaminated rows (sem-001/002/003, spec-001, hop-001), `date` scores 0.0 with alias 0.0.
4. Experiment top-k alias fires are only the pre-existing alias-trap row ood-003 (`verdict` +0.5, `scope` +0.35 from `scopes` / generated `scope`).

This is consistent with the H-QRL causal claim that identifier expansion produced the `date` artifact. It does not by itself prove a general alias-contract law.

## Unmeasurable / diagnostic

Not scored as hit/miss.

| row | control rank-1 | experiment rank-1 | note |
| --- | --- | --- | --- |
| spec-001 | verdict 0.284 | verdict 0.284 | no morphology; rewritten equals original; ranking identical |
| ood-001 | question 0.153 | question 0.134 | `a → as`; residual far-OOD ranking, no reject path |
| ood-002 | impact 0.164 | impact 0.172 | `does → do`; still no reject path; not materially more pathological |
| ood-003 | verdict 0.701 alias 0.5 | verdict 0.680 alias 0.5 | trap still fires; `scopes → scope` raised `scope` cosine 0.070 → 0.215 while alias 0.35 remains |
| hop-001 | verdict 0.260 | verdict 0.240 | not hop success; rank 1 is not `date` |

Near-OOD did not become a confident in-domain hit. Alias-trap still fires from the original `verdict` substring. Far-OOD did not collapse to a zero vector, unlike H-QRL stopword stripping of that row.

## Cache and tracker

| Claim | Observation |
| --- | --- |
| Pass 1 cache hits | 0/12 |
| Pass 2 cache hits | 12/12 |
| Pass 2 ranks identical to pass 1 | true |
| Collisions (cosine ≥ 0.99, different text) | none |
| Unique keys | 12 |
| Ranking transparency | pass-1 `rank_all(rewritten)` matches cached pass-2 section_id order |
| Tracker policy | `morph-v1` |
| Identifier frequency | empty |
| Morphology frequency | `do` 5, `as` 2, then one each of `factor`, `factors`, `field`, `findings`, `label`, `measures`, `objects`, `produce`, `scope`, `signals`, `thresholds` |

The tracker flushed morphology without mutating rewrite rules. `thresholds` fired once (spec-002). `regime_stability` never fired. No identifier expansions fired.

## Mechanism labels

| row | Rank change source |
| --- | --- |
| spec-002 | **A.** producer cosine/Jaccard rose because `thresholds` (and `label`) entered the query |
| sem-001 | no rank change; incidental `do` dilution only |
| lex-001 | no rank change; `signals` helped the competitor (**not A**) |
| sem-002 | mixed A (Jaccard from `findings`) and B (verdict dilution); already a hit |
| sem-003 | **B.** gold score down; rank up because verdict fell more |
| lex-002 / mch-001 | stable ranks; small score dilution from extra tokens |
| ood-003 | **C.** pre-existing alias trap, plus morphology boosting `scope` cosine |

Do not label B as semantic improvement.

## Falsification checklist (from the preregistration)

- spec-002 fails to reproduce the morphology effect → **not triggered** (`thresholds` fired; cosine/score rose; rank +6)
- spec-002 gain is competitor collapse rather than target-score improvement → **not triggered** (producer +0.072; verdict +0.012)
- morphology introduces significant unrelated ranking damage → **not triggered** (guardrail hits remained hits; gold queries still top-3)
- alias artifacts remain from generated identifiers → **not triggered** (`date` alias 0.0; offending identifier absent)
- unrelated rows “solved” without a named mechanism → **not triggered** (sem-001 and lex-001 remain misses; sem-002/003 were already hits)
- cache changes first-pass ranks → **not triggered**
- TOP_K / golds / weights / chunks changed → **not triggered**

H-MORPH as the isolated morphology claim is **supported**. Coverage is still one sealed morphological miss plus incidental fires. That is enough to retain morphology as a candidate mechanism and too little to promote it to default production policy.

## Deliberate non-actions after seeing results

This sprint did not:

- add a minimum token length to stop `a → as` or `does → do`
- re-introduce function-word stripping to chase H-QRL’s spec-002 rank 1
- manually inject `thresholds`
- add `regime_stability`
- blacklist `date`
- retune aliases, TOP_K, or 0.7/0.3
- rewrite YAML queries or golds
- implement dense embeddings (H1) or constrained identifier expansion (H-ID)
- mutate rewrite rules from tracker stats

## What a next experiment could ask (not implemented)

- Larger sealed morphology coverage, or a minimum-length constraint on `+s`/`+es` so function-word stems do not emit `do`/`as`.
- Constrained identifier expansion that forbids filename tokens and tokens whose substrings match short `section_id` slugs (H-ID).
- Alias matching with different semantics for natural-language tokens vs generated tokens (H-ALIAS).
- Existing H1: dense cosine with Jaccard/aliases/weights held fixed, for producer-burial cases morphology cannot reach.

Do not start those experiments on this branch as part of this measurement.

## References

- Preregistration: `docs/query_set_expansion/2026-10-05_morphology_only_preregistration.md`
- H-QRL preregistration: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`
- H-QRL findings: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`
- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Producer-burial forensics: `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
- Flag-off sanity: `eval_sets/runs/2026-10-06_run-003.jsonl`
- Experiment trace: `eval_sets/runs/2026-10-06_run-004.jsonl`
- Tracker: `eval_sets/runs/2026-10-06_run-004_query_loop.json`
