# Preregistration: dense semantic cosine (`H1`)

**Date:** 2026-10-05
**Status:** Preregistered. Hypothesis, dense model, and scoring formula locked before the experiment run.
**Experiment name:** `dense-cosine-h1-v1`
**Branch:** `research/dense-cosine-h1`
**This document is not a result.** It records what will be measured, and why, before `LUNA_DENSE_H1=1` is applied to the sealed set.

H1 is a **representation** intervention. It is not H-QRL. It is not H-MORPH. Query rewriting is off.

Prior experiments:

- Producer-burial forensics (named H1, did not implement it): `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- H-QRL preregistration / findings: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`, `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`
- H-MORPH preregistration / findings: `docs/query_set_expansion/2026-10-05_morphology_only_preregistration.md`, `docs/query_set_expansion/2026-10-05_morphology_only_findings.md`
- System findings: `docs/query_set_expansion/system_findings_hypothesis_testing.md`

H-QRL as a joint claim was weakened. Identifier-segment expansion failed on `qse-docqa-sem-001` and produced `date` alias contamination. H-MORPH isolated closed-vocabulary morphology and repaired `qse-docqa-spec-002`. `qse-docqa-sem-001` and `qse-docqa-lex-001` survived as representation misses.

This experiment tests whether a dense semantic vector can recover producer correspondence that the frozen lexical TF-IDF/Jaccard path cannot connect, without query-specific lexical expansion.

The purpose is **not** to improve global hit rate. The purpose is **not** to beat H-MORPH on morphology-specific `spec-002`.

## What this experiment does not change

- `eval_sets/docqa.yaml` bytes (version `docqa-expanded-v1`)
- query-set sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`
- frozen `rank_all()` / `retrieve()` lexical scoring when `LUNA_DENSE_H1` is unset
- Jaccard implementation (`retrieve.lexical_overlap` over `embed.tokenize`)
- alias implementation and `SECTION_ALIASES`
- alias weights (`+0.5` substring, `+0.35` slug-as-spaces)
- blend weights `0.7` / `0.3`
- chunk boundaries, section IDs, document corpus
- analyzer (`embed.tokenize`), TF-IDF fit stored in `metadata/chunks.json`
- TOP_K=5
- historical JSONL traces, including control `eval_sets/runs/2026-09-29_run-004.jsonl`, H-QRL `eval_sets/runs/2026-10-06_run-002.jsonl`, and H-MORPH `eval_sets/runs/2026-10-06_run-004.jsonl`
- YAML `query` / `expected` / `failure_mode` / locked predictions
- H-QRL `qrl-v1` when `LUNA_QUERY_LOOP=1`
- H-MORPH `morph-v1` when `LUNA_MORPH_LOOP=1`
- evaluation definitions and measurable/unmeasurable classifications

A new dense-index artifact may be written. It is hashed separately. The original frozen lexical index must remain byte-identical.

## Control

Compare against the frozen expanded control, **not** against H-QRL or H-MORPH ranks as if they were the control. Those ranks are prior mechanistic evidence used to form predictions. The three-hypothesis comparison is a later stage and must not begin until H1 findings are frozen.

| Piece | Identity |
| --- | --- |
| Control name | `expanded-control-v1` |
| Control characterization | `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` |
| Control trace | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` |
| Index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| Retriever freeze | `retrieve.py` lexical scoring unchanged since `000e658` |
| `retrieve.py` file sha256 | `91df8254f5888b167ebe15bcd7ef2fc28a4f67ba3fdbd6216043399175a29814` |
| `embed.py` file sha256 | `2567d09b5da424f55f8470363a036926683b3ac6e8d6db8e1b36318bcf66dfcf` |
| `evaluate.py` file sha256 | `97d953d99f0b9136b069a764afa04536555911f9c23f8566a1563933361fc579` |

Primary metric: `rank_gain = control_rank - experiment_rank` on measurable rows, interpreted **only together with** target absolute dense correspondence, total-score movement, and component deltas.

**Score-scale caution.** Control totals are `0.7 * lexical_cosine + 0.3 * jaccard + alias`. H1 totals are `0.7 * dense_cosine + 0.3 * jaccard + alias`. The `0.7` weight is the same number, but `lexical_cosine` and `dense_cosine` are different similarity measures on different vector spaces. Direct comparison of raw totals across control vs H1 is not a like-for-like correspondence metric. Within-H1 comparisons among chunks for the same query are valid. Rank, `dense_cosine` itself, Jaccard, alias, and competitor identity remain comparable.

Global hit rate is not an optimization target.

## Hypothesis (`H1`)

A dense semantic representation can recover relevant producer chunks that the frozen lexical TF-IDF/Jaccard representation cannot connect because the query and target express related concepts using different surface vocabulary.

More specifically: because the three producer probes originally shared an absent token-level bridge, replacing the TF-IDF cosine term with dense cosine — while holding Jaccard, aliases, blend weights, TOP_K, chunk boundaries, and the query set fixed — should increase **absolute producer dense correspondence** on the remaining semantic/lexical misses, producing positive rank gain if producer burial is truly a representation problem.

This tests correspondence without query-specific lexical expansion. A rank gain without increased dense target evidence is not sufficient.

H-MORPH later showed that `spec-002` is a morphological miss (`threshold` vs `thresholds`), not the primary dense-semantic failure. That row remains in the diagnostic slice. H1 does **not** need to beat H-MORPH on it.

## Locked scoring formula

Frozen lexical hybrid (unchanged, flag off):

```
score = 0.7 * lexical_cosine + 0.3 * jaccard + alias
```

where `lexical_cosine` is cosine of L2-normalized TF-IDF vectors (`embed.TfidfModel`), `jaccard` is Jaccard of `embed.tokenize` tokens over query vs `heading + text`, and `alias` is `retrieve.alias_boost`.

H1 intervention (flag on):

```
score = 0.7 * dense_cosine + 0.3 * jaccard + alias
```

This is a **replacement of the cosine term**, not an added component and not a weight search.

### Why replacement rather than an extra dense term

The original producer-burial H1 uniquely specified this design:

> introducing a dense semantic representation **for the cosine term**, while holding Jaccard, aliases, blend weights, TOP_K, chunk boundaries, and the query set fixed

It did not propose a third weighted similarity, and it explicitly rejected scoring-weight adjustment. Adding `dense_cosine` beside `lexical_cosine` would invent a new weight. Sweeping weights against sealed rows is forbidden.

Locked constants:

| Symbol | Value | Role under H1 |
| --- | ---: | --- |
| `DENSE_COSINE_WEIGHT` | 0.7 | weight on `dense_cosine` |
| `JACCARD_WEIGHT` | 0.3 | weight on Jaccard; same implementation as control |
| alias | unchanged | `+0.5` / `+0.35`; same table |
| `lexical_cosine` | computed, **not in the blend** | attribution only |

No weight sweep. No hyperparameter search. No post-result adjustment.

Logs and findings must name components as `lexical_cosine`, `dense_cosine`, `jaccard`, and `alias`. Do not call both cosine terms merely “cosine”.

## Locked dense model

Selected **before** any sealed-row ranks are examined. One model. No bake-off.

| Property | Locked value |
| --- | --- |
| Hub id | `sentence-transformers/all-MiniLM-L6-v2` |
| Hugging Face revision | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Local execution | CPU, `device='cpu'` |
| CUDA | unused (`torch.cuda.is_available()` is False on this machine) |
| Python | 3.14.2 |
| `sentence-transformers` | 6.1.0 |
| `torch` | 2.14.1+cpu |
| `transformers` | 5.18.0 |
| `numpy` | 2.3.5 |
| Embedding dimensionality | 384 |
| Max sequence length | 256 tokens (model default; longer inputs truncated) |
| Transformer | MiniLM-L6 |
| Pooling | mean pooling of token embeddings (`pooling_mode='mean'`) |
| Normalization | L2 (`Normalize` module in the SentenceTransformer pipeline; encode with `normalize_embeddings=True`) |
| Similarity | cosine = dot product of L2-normalized 384-d vectors |
| Query encoder | same SentenceTransformer object as chunks |
| Document encoder | same SentenceTransformer object as queries |
| Query text | original YAML `query` string, unmodified |
| Chunk text | stored `chunk.text` (the same string TF-IDF was fitted on; heading already prepended by the chunker) |
| Batch / determinism | `model.eval()` inference on CPU; no dropout; no sampling; encode chunks once into a frozen artifact; encode each query independently through the same encoder |
| External API | none; local Hugging Face cache under the pinned revision |

Why this model, chosen before ranks:

- It is a sentence-similarity encoder, which matches H1’s correspondence claim.
- It is small enough to run locally on CPU.
- Mean pooling + L2 cosine is the model’s standard procedure, not an extra hyperparameter.
- The same encoder for queries and chunks avoids an asymmetric-instruction choice (e.g. E5 prefixes) that would be a second unlocked decision.

This is not a comparison among embedding models. If implementation feasibility had forced a different model **before** the measured run, that change would have been documented here first. It did not: `sentence-transformers` and CPU torch installed and loaded this revision successfully. No model will be swapped after seeing evaluation ranks.

## How H1 enters ranking

Opt-in via `LUNA_DENSE_H1` in `run_query_set.py`. Truthy values: `1` / `true` / `yes` / `on`. Default **off**.

When off: frozen `rank_all(original_query)` / `retrieve()`. Dense model is not required. `dense_cosine` is not computed.

When on: `rank_all_h1(original_query)` using the locked formula. Original YAML query text is the only query string. No rewrite, no morphology, no identifier expansion, no function-word stripping, no synonym table, no aliases inserted into queries, no LLM rewriting.

If `LUNA_DENSE_H1` is on **and** `LUNA_QUERY_LOOP` or `LUNA_MORPH_LOOP` is on, the runner must fail loud. Combining H1 with a rewrite policy would be a fourth hypothesis.

`evaluate.py` stays on frozen `retrieve()`. Gold queries are checked through the H1 path separately as a guardrail, not by changing `evaluate.py`.

## Frozen lexical index vs dense artifact

| Artifact | Role |
| --- | --- |
| `metadata/chunks.json` | frozen lexical index; must keep sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| dense index (new) | 384-d L2-normalized vectors keyed by `chunk_id` / `section_id` / `content_sha256` plus model identity; hashed separately |

Do not re-ingest or alter chunk boundaries to compute dense vectors. Read the existing store. If a chunk’s `content_sha256` does not match the dense-index row, fail loud.

## Query rewriting remains off

For the primary H1 experiment:

- original YAML query text
- no function-word stripping
- no morphology
- no identifier expansion
- no synonym expansion
- no query-specific terms
- no aliases inserted into queries
- no LLM rewriting

H-QRL and H-MORPH remain callable when their own flags are set and `LUNA_DENSE_H1` is off.

## Primary predictions (written before ranks)

### Primary target: `qse-docqa-sem-001`

Query: *What does the regime-related score represent when it contributes to the conviction assessment?*
Expected: `1_upstream_producer_score_definition`

| Prior evidence | Value |
| --- | --- |
| Control rank / score | 10 / 0.015352; rank 1 `verdict` 0.316521 |
| Control `lexical_cosine` / Jaccard / alias | 0.017169 / 0.011111 / 0.0 |
| H-QRL | rank 10 → 11; identifier expansion missed `regime_stability`; `date` became rank 1 via alias |
| H-MORPH | rank stayed 10; incidental `does → do`; not a morphological miss |

Diagnosed failure: standalone `regime` is absent from the producer vector; the producer stores `regime_stability` / `RegimeObserver.step`. Identifier dumping is unsafe. Morphology cannot construct identifier superstrings.

**Prediction:** Dense semantic similarity should increase **absolute producer `dense_cosine`** relative to a no-correspondence floor and should produce positive rank gain if burial is a representation problem. A rank gain without increased dense target evidence is not support.

Record for this row: target `dense_cosine`, competitors’ `dense_cosine`, total score, rank, margin to nearest competitors, `lexical_cosine`, Jaccard, alias.

### Primary/secondary target: `qse-docqa-lex-001`

Query: *Which upstream market-condition measure supplies the consistency signal used when assessing trade confidence?*
Expected: `1_upstream_producer_score_definition`

| Prior evidence | Value |
| --- | --- |
| Control rank / score | 7 / 0.037137; rank 1 `upstream_signals_since_verdict_independent` 0.143566 |
| Control `lexical_cosine` / Jaccard / alias | 0.048343 / 0.010989 / 0.0 |
| H-QRL | rank 7 → 3 **for the wrong reason** (competitor collapse after stopword stripping; producer score fell) |
| H-MORPH | rank stayed 7; `signals` strengthened the neighbor |

Diagnosed failure: conceptual mismatch (`consistency` / `confidence` / `market-condition` vs corpus `stability` / `vwap_dist`). Those query strings are not in the chunk.

**Prediction:** If dense representation captures the intended relationship, the producer should gain **absolute dense correspondence**, not merely benefit from weakening competitors. Analyze this row especially carefully because it already demonstrated misleading rank behavior.

No synonym may be inserted. If rank moves while producer `dense_cosine` does not exceed competitors’ dense evidence in a way that explains the movement, classify it as competitor collapse or artifact, not as H1 support.

### Mechanism-specific diagnostic: `qse-docqa-spec-002`

Query: *Which four labels can the percentile-threshold rule assign, including the in-between and missing-data cases?*
Expected: `1_upstream_producer_score_definition`

H-MORPH repaired this row through `threshold → thresholds`. That is a surface morphology failure, not the primary dense-semantic failure.

H1 does **not** need to beat H-MORPH on this row to succeed.

**Diagnostic question:** Does dense representation preserve reasonable retrieval for this concept, improve it, or degrade a case that morphology solves more cleanly?

This row is required later in the three-hypothesis comparison. It is not a hidden success condition for H1.

## Guardrails

Do not declare H1 successful from producer ranks alone.

| Guardrail | Control observation to preserve |
| --- | --- |
| `qse-docqa-sem-002` | rank 2 hit, margin −0.013370 vs `verdict` |
| `qse-docqa-sem-003` | rank 2 hit, margin −0.011192 vs `verdict` |
| `qse-docqa-lex-002` | rank 4 hit (`2_state_stamp_before_conviction`) |
| `qse-docqa-mch-001` stamp | rank 5 (in top-k); consumer rank 6 remains a conjunction observation |
| `qse-docqa-mch-001` consumer | rank 6; conjunction still fails under control |
| `qse-docqa-spec-001` | unmeasurable underspecific; diagnostic rank-1 identity |
| frozen `evaluate.py` gold queries | question / verdict / Finding 3.5 still in top-3 on the **frozen** path |
| H1 gold queries | same three gold queries through `rank_all_h1` still place each target in top-3 |

Also keep diagnostic observation (not scored reject metrics) of:

- near-OOD `qse-docqa-ood-002` (impact currently rank 1 at 0.164)
- far-OOD `qse-docqa-ood-001`
- alias-trap `qse-docqa-ood-003` (`verdict` rank 1 at 0.700 with `alias=0.5`; `scope` rank 2 with `alias=0.35`)

H1 must not win producer rows by stuffing aliases into in-scope queries. Alias should remain 0.0 on the in-scope producer-target rows.

### Dense-specific blast radius

Dense similarity may create a different blast radius from lexical rewriting. Inspect whether it causes unrelated semantically broad chunks to become attractive.

Look for:

- semantic overgeneralization
- generic sections becoming universal neighbors
- collapse of score margins
- OOD queries receiving unjustifiably high similarity
- alias interactions
- producer improvement accompanied by guardrail degradation

## OOD caution

Dense models may assign nontrivial similarity even when a query should have weak corpus correspondence.

Do **not** treat high `dense_cosine` as automatically meaningful.

For near-OOD, far-OOD, and alias-trap diagnostics, record:

- top `dense_cosine`
- score distribution
- top-k identities
- margin
- whether similarity becomes more confident than the lexical baseline

H1 is a retrieval hypothesis, not an OOD/reject solution. Do not invent a reject threshold during this experiment. If dense retrieval exposes an OOD calibration problem, document it as a later hypothesis.

## Success (locked before execution)

H1 is **supported** if the predicted semantic-miss rows show evidence resembling:

1. meaningful positive target `dense_cosine` correspondence;
2. meaningful improvement in total target score and/or rank, interpreted with the score-scale caution above;
3. improvements attributable to `dense_cosine` rather than alias or competitor collapse;
4. better behavior on at least the key semantic producer-burial row (`sem-001`);
5. guardrail rows remain reasonably stable;
6. no severe new pathology on OOD/alias diagnostics.

Do **not** require H1 to solve morphology-specific `spec-002`.
Do **not** define success as global hit rate.
Do **not** define success as `dense_cosine` being numerically high in isolation.
Entry into TOP_K=5 is supporting detail, not the definition of success.

Use language: supported / partially supported / weakened / rejected / inconclusive.

## Falsification (locked before execution)

H1 is weakened or rejected if:

- `sem-001` remains buried with little meaningful dense target correspondence;
- `lex-001` moves only because competitors change rather than target correspondence;
- dense similarity promotes broad but incorrect conceptual neighbors;
- guardrails regress substantially (sem-002/003 or lex-002 leave top-k; frozen `evaluate.py` FAILs; H1 gold queries fail);
- near/far-OOD queries become pathologically confident;
- aliases or unrelated scorer components explain apparent wins;
- gains require changing weights after seeing results;
- gains depend on changing chunks/golds/TOP_K/query text;
- only aggregate hit rate improves while the predicted mechanism fails;
- query rewriting, morphology, or identifier expansion is silently applied;
- a different embedding model is selected after seeing sealed ranks.

`spec-002` non-improvement relative to H-MORPH is **not** falsification.

## Mechanism labels for every important row

For every measurable/important row, report control rank, H1 rank, rank_gain, control total score, H1 total score (with scale caution), `lexical_cosine`, `dense_cosine`, Jaccard, alias, top competitor changes, and hit/miss.

Classify any rank improvement as exactly one primary mechanism, with overlays named if needed:

- **A.** target correspondence increasing (`dense_cosine` on the gold, and/or Jaccard if it actually moved)
- **B.** competitors weakening
- **C.** alias behavior
- **D.** some other mechanism

Do not label B as semantic improvement. Do not count B as support for H1.

## Implementation requirements (after this document exists)

Keep the dense path isolated and auditable. Prefer separate modules:

- dense encoder (`dense_embed.py`)
- dense index (`dense_index.py`)
- H1 ranker (`dense_h1.py`)
- experiment orchestration in `run_query_set.py` behind `LUNA_DENSE_H1`

Do not contaminate frozen `retrieve()` / `rank_all()` scoring when H1 is disabled.

`RetrievalHit` may gain explicit `lexical_cosine` and `dense_cosine` fields with defaults so logs can name both. Frozen `rank_all()` must still compute `score = 0.7 * lexical_cosine + 0.3 * jaccard + alias` and must not load the dense model.

Logs must expose at least: query, target section, `dense_cosine`, `lexical_cosine`, Jaccard, alias, total score, rank, top-k sections, component-level scores. Never collapse component scores into only one opaque final number.

## Tests before measured run

Add tests for:

- flag-off frozen behavior (control calibration ranks unchanged)
- deterministic/reproducible embeddings within reasonable numeric tolerance
- dense vector dimensionality 384
- vector L2 normalization
- stable section/vector association (`section_id` + `content_sha256`)
- original query preservation
- no morphology / query rewriting in H1 mode
- no identifier expansion
- scorer formula exactly matches this preregistration
- historical H-QRL / H-MORPH behavior remains callable
- dense-index identity/hash validation
- logging exposes score components

Run full tests before sealed execution. Record test counts.

## Measurement protocol (after this document exists)

1. Preregistration committed (this file).
2. Implementation and tests committed.
3. Flag-off: `pytest tests` and `python run_query_set.py` still reproduce control calibration ranks.
4. Verify query-set and lexical-index hashes.
5. Build/freeze the dense representation artifact; record its hash.
6. Execute sealed H1 pass: `LUNA_DENSE_H1=1 python run_query_set.py` (new JSONL).
7. Preserve the trace. Do not edit YAML predictions.
8. Analyze results. Write H1 findings.
9. Commit findings.
10. Only then begin the three-experiment comparison.

Do not modify the dense model, pooling, weights, or formula after seeing results.

## Out of scope

- Query rewriting, morphology, identifier expansion
- Combining morphology + dense + lexical into a composite retriever
- Constrained identifier expansion (H-ID)
- Alias-contract changes (H-ALIAS)
- Embedding-model bake-off
- Weight search
- BM25, reranking, reject/OOD scoring, hop control, GraphRAG
- Changing TOP_K, golds, aliases, chunk boundaries, or query text
- Expanding the query set after inspecting results and folding new cases into this experiment

## Deliberate non-actions during and after the measured test

This sprint will not:

- change query text or gold labels
- manually insert semantic bridges or synonyms
- add `regime_stability` to queries
- blacklist `date`
- tune dense weights from sealed ranks
- test many embedding models and pick the best
- change TOP_K or chunk boundaries
- change aliases
- create query-specific boosts
- define success after seeing results
- promote a mechanism because global hit rate rose
- implement a hybrid morphology+dense retriever on this branch as part of the measured experiment

If the experiment exposes another failure, document it as a new hypothesis.

## References

- Producer-burial forensics (original H1): `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- H-QRL preregistration / findings
- H-MORPH preregistration / findings
- System findings: `docs/query_set_expansion/system_findings_hypothesis_testing.md`
- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Frozen three-row baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Failure-mode map: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Sealed set: `eval_sets/docqa.yaml`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
