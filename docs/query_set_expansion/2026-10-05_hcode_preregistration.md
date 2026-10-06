# Preregistration: identifier/code-register representation (`H-CODE`)

**Date:** 2026-10-05
**Status:** Preregistered. Hypothesis, code-aware model, and scoring formula locked before the experiment run.
**Experiment name:** `code-register-hcode-v1`
**Branch:** `research/code-register-hcode`
**This document is not a result.** It records what will be measured, and why, before `LUNA_HCODE=1` is applied to the sealed set.

H-CODE is a **representation** intervention. It is not H-QRL. It is not H-MORPH. It is not H1 MiniLM. It is not H-HYBRID. Query rewriting is off. Identifier expansion is off.

Prior experiments:

- Frozen expanded-control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Producer-burial forensics: `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- H-QRL preregistration / findings: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`, `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`
- H-MORPH preregistration / findings: `docs/query_set_expansion/2026-10-05_morphology_only_preregistration.md`, `docs/query_set_expansion/2026-10-05_morphology_only_findings.md`
- H1 preregistration / findings: `docs/query_set_expansion/2026-10-05_dense_cosine_h1_preregistration.md`, `docs/query_set_expansion/2026-10-05_dense_cosine_h1_findings.md`
- Three-hypothesis comparison plan / findings: `docs/query_set_expansion/2026-10-05_three_hypothesis_comparison_plan.md`, `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md`
- System findings: `docs/query_set_expansion/system_findings_hypothesis_testing.md`

The purpose is **not** to improve global hit rate. The purpose is **not** to beat MiniLM on synonymy or morphology on `spec-002`. The purpose is **not** to combine representations.

## Verified diagnosis of `sem-001` (from repository artifacts, not restated from memory)

This section is the locked reading of the research chain. It was written before any H-CODE ranks.

### What the frozen control actually computed

`eval_sets/runs/2026-09-29_run-004.jsonl`, query-set sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`, lexical index sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c`.

Row `qse-docqa-sem-001`, original YAML query:

> What does the regime-related score represent when it contributes to the conviction assessment?

Expected: `1_upstream_producer_score_definition`. Control rank **10 / 15**, score **0.015352**, alias **0.0**. Rank 1 is `verdict` at 0.316521.

`docs/query_set_expansion/2026-09-29_producer_burial_forensics.md` reconstructed the frozen TF-IDF path:

- Analyzer `embed.tokenize` (`[a-z0-9]+(?:[._][a-z0-9]+)*`) does **not** split snake_case, dotted names, or camelCase.
- The producer stores `regime_stability`, `regimeobserver.step`, `regime_observer.yaml`, `regimeboss` as **whole tokens**. Standalone `regime` is absent from the producer vector.
- Standalone `regime` **does** occur in eight other chunks, including `verdict` (2) and the consumer (6). It is one of the two lowest-IDF terms (df=8), tied with `the`.
- Producer cosine 0.017169 is 100% from heading token `score`. Jaccard 0.011111 is `{score}` over 90 unique tokens. Four conceptually central query terms (`assessment`, `contributes`, `related`, `represent`) are OOV.

This is identifier-register burial, not a near-miss on the same vocabulary item.

### What later interventions did on this same row

| Intervention | Trace | Producer rank | What happened |
| --- | --- | ---: | --- |
| Control | `eval_sets/runs/2026-09-29_run-004.jsonl` | 10 | buried; `verdict` rank 1 |
| H-QRL | `eval_sets/runs/2026-10-06_run-002.jsonl` | 11 | identifier-segment expansion selected the wrong `regime_*` family (`RegimeBoss`, `regime_state`, filenames) and **did not emit `regime_stability`**; `date` became rank 1 via alias +0.35 on `regime_update_interval_seconds` |
| H-MORPH | `eval_sets/runs/2026-10-06_run-004.jsonl` | 10 | identifiers off; incidental `does → do`; morphology cannot construct identifier superstrings |
| H1 MiniLM | `eval_sets/runs/2026-10-06_run-006.jsonl` | 9 | original query unchanged; Jaccard / alias / `lexical_cosine` identical to control; producer `dense_cosine` **0.263470** vs `verdict` **0.600096**, consumer **0.552181**, `question` **0.551463** |

`docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md` classifies this cell as **UNRESOLVED repair**. MiniLM recognized general regime/conviction prose but did not recover the identifier-heavy score definition. Rank +1 is not recovery.

### What this is not

The comparative audit already assigned other failure classes to other mechanisms:

- `spec-002`: morphology (`threshold` vs stored `thresholds`). Control miss, H-QRL repaired but bundled, H-MORPH repaired cleanly (rank 9→3, cosine 0.052→0.145, alias 0), H1 did not repair (rank 9→10, `dense_cosine` 0.108).
- `lex-001`: closed-vocab synonymy (`consistency` / `market-condition` vs `stability` / `vwap_dist`). Control miss, H-QRL rank 7→3 by competitor collapse, H-MORPH unchanged rank 7, H1 genuine correspondence (rank 7→3, `dense_cosine` 0.284, Jaccard frozen).

H-CODE is not a second attempt at those classes.

### Why identifier expansion is the wrong next test

H-QRL already tested query-side identifier dumping. Segment overlap produced heterogeneous identifiers and alias contamination. H-CODE must not append `regime_stability`, `regime_state`, `RegimeObserver`, filenames, aliases, or synonyms to the query.

The remaining question is whether the **representation itself** can preserve identifier/code structure well enough to increase absolute producer correspondence from the original YAML text.

## What this experiment does not change

- `eval_sets/docqa.yaml` bytes (version `docqa-expanded-v1`)
- query-set sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`
- frozen `rank_all()` / `retrieve()` lexical scoring when `LUNA_HCODE` is unset
- Jaccard implementation (`retrieve.lexical_overlap` over `embed.tokenize`)
- alias implementation and `SECTION_ALIASES`
- alias weights (`+0.5` substring, `+0.35` slug-as-spaces)
- blend weights `0.7` / `0.3`
- chunk boundaries, section IDs, document corpus
- analyzer (`embed.tokenize`), TF-IDF fit stored in `metadata/chunks.json`
- TOP_K=5
- historical JSONL traces, including control `eval_sets/runs/2026-09-29_run-004.jsonl`, H-QRL `eval_sets/runs/2026-10-06_run-002.jsonl`, H-MORPH `eval_sets/runs/2026-10-06_run-004.jsonl`, and H1 `eval_sets/runs/2026-10-06_run-006.jsonl`
- YAML `query` / `expected` / `failure_mode` / locked predictions
- H-QRL `qrl-v1` when `LUNA_QUERY_LOOP=1`
- H-MORPH `morph-v1` when `LUNA_MORPH_LOOP=1`
- H1 `dense-cosine-h1-v1` when `LUNA_DENSE_H1=1`
- evaluation definitions and measurable/unmeasurable classifications
- frozen MiniLM artifact `metadata/dense_h1_index.json`

A new code-index artifact may be written. It is hashed separately. The original frozen lexical index and the frozen H1 MiniLM index must remain byte-identical.

## Control

Compare against the frozen expanded control, **not** against H-QRL, H-MORPH, or H1 ranks as if they were the control. Those ranks are prior mechanistic evidence used to form predictions. H1 MiniLM cosine is a **reference correspondence**, not the H-CODE control total.

| Piece | Identity |
| --- | --- |
| Control name | `expanded-control-v1` |
| Control characterization | `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` |
| Control trace | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| H1 reference trace | `eval_sets/runs/2026-10-06_run-006.jsonl` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` |
| Index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| Retriever freeze | `retrieve.py` lexical scoring unchanged since `000e658` |
| `retrieve.py` file sha256 | `cb73333592d634b24ca0bb3157a9ce625a75a067c0546b2bba2e600b970946a0` |
| `embed.py` file sha256 | `2567d09b5da424f55f8470363a036926683b3ac6e8d6db8e1b36318bcf66dfcf` |
| `evaluate.py` file sha256 | `97d953d99f0b9136b069a764afa04536555911f9c23f8566a1563933361fc579` |

Primary metric: `rank_gain = control_rank - experiment_rank` on measurable rows, interpreted **only together with** target absolute `code_cosine`, competitor `code_cosine`, total-score movement, and component deltas. Producer `code_cosine` vs producer H1 `dense_cosine` is a correspondence comparison across representations, not a score-scale comparison of totals.

**Score-scale caution.** Control totals are `0.7 * lexical_cosine + 0.3 * jaccard + alias`. H1 totals are `0.7 * dense_cosine + 0.3 * jaccard + alias`. H-CODE totals are `0.7 * code_cosine + 0.3 * jaccard + alias`. The `0.7` weight is the same number, but the three cosine terms live in different vector spaces. Direct comparison of raw totals across experiments is not a like-for-like correspondence metric. Within-H-CODE comparisons among chunks for the same query are valid. Rank, `code_cosine` itself, Jaccard, alias, and competitor identity remain comparable.

Global hit rate is not an optimization target.

## Hypothesis (`H-CODE`)

The persistent `sem-001` producer-burial failure is caused partly by identifier/code-register representation mismatch, and an identifier-aware representation can improve **absolute correspondence** between the original query and the identifier-heavy producer chunk without query-specific lexical expansion.

More specifically: MiniLM mean-pooled cosine recovered closed-vocab synonymy (`lex-001`) and did not recover the producer whose distinctive content lives in undecomposed identifiers (`regime_stability`, `RegimeObserver.step`). If that remaining miss is a register problem rather than ordinary synonymy, replacing the cosine term with a code-oriented embedding — while holding Jaccard, aliases, blend weights, TOP_K, chunk boundaries, and the original query text fixed — should increase producer `code_cosine` relative to H1 MiniLM similarity and/or make the producer more competitive against persistent prosaic attractors (`verdict`, consumer, `question`).

This is not identifier dumping. A rank gain without increased target `code_cosine` is not support. Competitor collapse is not support. Alias is not support.

## Model selection (locked from documentation, before sealed ranks)

One model. No bake-off. No second model after seeing ranks.

Documented candidates inspected **from model cards only**:

| Candidate | Why considered | Why not selected |
| --- | --- | --- |
| `jinaai/jina-embeddings-v2-base-code` | Code-oriented sentence embedding; English + 30 programming languages including Python and Markdown; pretrained on GitHub code then trained on >150M coding QA / docstring–source pairs; mean pooling; cosine; SentenceTransformer-compatible; 161M params (CPU-feasible); 8192 max tokens so the 1022-character producer will not truncate | **Selected** |
| `flax-sentence-embeddings/st-codesearch-distilroberta-base` | NL-to-code search on CodeSearchNet | Card states max_seq_length **128** and calls the model “preliminary… neither tested nor was the training quite sophisticated.” 128 tokens would truncate the producer. Rejected on spec, not ranks. |
| `Salesforce/SFR-Embedding-Code-400M_R` | Strong CoIR code-retrieval numbers; mixed code+text | 400M, CLS pooling, CC-BY-NC. Heavier and less parallel to H1’s mean-pool symmetric encode. Not selected; not evaluated. |
| MiniLM + external identifier segmentation | Would expose `regime` inside `regime_stability` | That is still MiniLM, which already failed this row. H-CODE must test whether a **code-trained** representation differs from MiniLM. External segmentation would also confound “code model” with “query/chunk rewriting.” Rejected. |

Selected **before** any sealed-row ranks and before encoding the sealed corpus:

| Property | Locked value |
| --- | --- |
| Hub id | `jinaai/jina-embeddings-v2-base-code` |
| Hugging Face revision | `516f4baf13dec4ddddda8631e019b5737c8bc250` |
| License | Apache-2.0 |
| Parameters | 161 million |
| Local execution | CPU, `device='cpu'` |
| CUDA | unused (`torch.cuda.is_available()` is False on this machine) |
| Python | 3.14.2 |
| `sentence-transformers` | 6.1.0 |
| `torch` | 2.14.1+cpu |
| `transformers` | 5.18.0 |
| `numpy` | 2.3.5 |
| `trust_remote_code` | True (required by the published JinaBert class) |
| Embedding dimensionality | 768 |
| Max sequence length | 8192 tokens (the published `sentence_bert_config.json` default; longer inputs truncated) |
| Architecture | JinaBert with ALiBi; trained at 512, extrapolates to 8192 |
| Pooling | mean pooling of token embeddings (`pooling_mode_mean_tokens=true`; no CLS) |
| Normalization | L2 at encode time (`normalize_embeddings=True`). The published `modules.json` has Transformer + Pooling only; no Normalize module. Official card L2-normalizes after mean pooling. |
| Similarity | cosine = dot product of L2-normalized 768-d vectors |
| Query encoder | same SentenceTransformer object as chunks |
| Document encoder | same SentenceTransformer object as queries |
| Query text | original YAML `query` string, unmodified |
| Chunk text | stored `chunk.text` (the same string TF-IDF and MiniLM used; heading already prepended by the chunker) |
| Batch / determinism | `model.eval()` inference on CPU; no dropout; no sampling; encode chunks once into a frozen artifact; encode each query independently through the same encoder |
| External API | none; local Hugging Face cache under the pinned revision |

Why this model, chosen from specifications:

- It is trained to embed mixed natural language and code, which matches the producer’s mixed prose + identifiers.
- Mean pooling + L2 cosine is the published procedure, not an extra hyperparameter.
- The same encoder for queries and chunks avoids an asymmetric-instruction choice that would be a second unlocked decision.
- Sequence length 8192 removes truncation as a confounder for this 15-chunk corpus.
- Size is CPU-runnable for 15 chunks + 12 queries.

This is not a comparison among embedding models. No model will be swapped after seeing evaluation ranks.

## Locked preprocessing (none beyond the encoder)

External deterministic identifier segmentation is **off**.

| Surface | Treatment |
| --- | --- |
| snake_case | left intact in the input string (`regime_stability` is not rewritten to `regime stability`) |
| dotted identifiers | left intact (`RegimeObserver.step` is not rewritten) |
| camelCase | left intact (`RegimeObserver` is not split to `Regime Observer`) |
| filenames | left intact |
| query text | original YAML only |
| chunk text | stored `chunk.text` only |

The model’s internal tokenizer (BPE / RoBERTa-style special tokens `<s>` `</s>` `<pad>` `<unk>` `<mask>`; `do_lower_case=false`) may induce subword splits. That internal behavior is part of the locked representation. It is **not** corpus-derived identifier expansion and must not add tokens to the query string logged as `query` / `rewritten_query` / `expansions`.

Do not generate identifier candidates from the fitted vocabulary, IDF, or chunk inventory.

## Locked scoring formula

Frozen lexical hybrid (unchanged, flags off):

```
score = 0.7 * lexical_cosine + 0.3 * jaccard + alias
```

H1 (unchanged when `LUNA_DENSE_H1=1`):

```
score = 0.7 * dense_cosine + 0.3 * jaccard + alias
```

H-CODE intervention (flag on):

```
score = 0.7 * code_cosine + 0.3 * jaccard + alias
```

This is a **replacement of the cosine term**, not an added component and not a weight search. Do not blend MiniLM + code cosine. That would be H-HYBRID.

Locked constants:

| Symbol | Value | Role under H-CODE |
| --- | ---: | --- |
| `CODE_COSINE_WEIGHT` | 0.7 | weight on `code_cosine` |
| `JACCARD_WEIGHT` | 0.3 | weight on Jaccard; same implementation as control |
| alias | unchanged | `+0.5` / `+0.35`; same table |
| `lexical_cosine` | computed, **not in the blend** | attribution only |
| MiniLM `dense_cosine` | computed from the frozen H1 index + locked MiniLM encoder when that artifact is present, **not in the blend** | attribution only |

No weight sweep. No hyperparameter search. No post-result adjustment.

Logs and findings must name components as `lexical_cosine`, `dense_cosine` (MiniLM, diagnostic), `code_cosine`, `jaccard`, and `alias`. Do not call the three cosine terms merely “cosine”.

## How H-CODE enters ranking

Opt-in via `LUNA_HCODE` in `run_query_set.py`. Truthy values: `1` / `true` / `yes` / `on`. Default **off**.

When off: frozen `rank_all(original_query)` / `retrieve()`. Code model is not required. `code_cosine` is not computed.

When on: `rank_all_hcode(original_query)` using the locked formula. Original YAML query text is the only query string. No rewrite, no morphology, no identifier expansion, no function-word stripping, no synonym table, no aliases inserted into queries, no LLM rewriting.

If `LUNA_HCODE` is on **and** any of `LUNA_DENSE_H1`, `LUNA_QUERY_LOOP`, or `LUNA_MORPH_LOOP` is on, the runner must fail loud. Combining H-CODE with MiniLM or a rewrite policy would be a separate hypothesis.

`evaluate.py` stays on frozen `retrieve()`. Gold queries are checked through the H-CODE path separately as a guardrail, not by changing `evaluate.py`.

## Frozen lexical index vs code artifact

| Artifact | Role |
| --- | --- |
| `metadata/chunks.json` | frozen lexical index; must keep sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| `metadata/dense_h1_index.json` | frozen MiniLM index; diagnostic only; must remain byte-identical |
| code index (new) | 768-d L2-normalized vectors keyed by `chunk_id` / `section_id` / `content_sha256` plus model identity; hashed separately |

Do not re-ingest or alter chunk boundaries to compute code vectors. Read the existing store. If a chunk’s `content_sha256` does not match the code-index row, fail loud.

## Query rewriting remains off

For the primary H-CODE experiment:

- original YAML query text
- no function-word stripping
- no morphology
- no identifier expansion
- no synonym expansion
- no query-specific terms
- no aliases inserted into queries
- no LLM rewriting
- no appending of `regime_stability`, `regime_state`, `RegimeObserver`, filenames, or related identifiers

H-QRL, H-MORPH, and H1 remain callable when their own flags are set and `LUNA_HCODE` is off.

## Primary predictions (written before ranks)

### Primary target: `qse-docqa-sem-001`

Query: *What does the regime-related score represent when it contributes to the conviction assessment?*
Expected: `1_upstream_producer_score_definition`

| Prior evidence | Value |
| --- | --- |
| Control rank / score | 10 / 0.015352; rank 1 `verdict` 0.316521 |
| Control `lexical_cosine` / Jaccard / alias | 0.017169 / 0.011111 / 0.0 |
| H-QRL | rank 10 → 11; missed `regime_stability`; `date` rank 1 |
| H-MORPH | rank stayed 10 |
| H1 | rank 10 → 9; producer MiniLM 0.263470 vs `verdict` 0.600096 |

Diagnosed failure: identifier-register mismatch. MiniLM prefers prosaic regime/conviction chunks.

**Prediction:** If identifier/code-register mismatch explains meaningful variance, H-CODE should increase **absolute producer `code_cosine`** relative to H1 MiniLM similarity and/or make the producer more competitive against `verdict`, consumer, and `question`. Rank 1 is not required. Top-k entry would be supporting evidence, not the sole success criterion.

A rank gain caused only by prosaic competitors losing `code_cosine` is not support.

Record for this row: producer `code_cosine`, H1 MiniLM `dense_cosine`, `lexical_cosine`, Jaccard, alias, final H-CODE score, rank, margin to rank 1, margin to nearest competing chunks, competitor `code_cosine`, and a prose/identifier/mixed label for top candidates.

### Mechanism control: `qse-docqa-lex-001`

This is the positive H1 synonymy case. MiniLM improved genuine correspondence (rank 7→3, `dense_cosine` 0.284254, Jaccard frozen).

H-CODE is **not** required to outperform MiniLM. Use this row to ask whether the code-aware representation preserves ordinary language semantics reasonably or sacrifices them.

Possible outcomes: stable relative to H1; weaker than H1 but still functional; substantially degraded. Interpret as specialization evidence, not necessarily H-CODE failure.

### Mechanism control: `qse-docqa-spec-002`

This is the morphology case. H-MORPH is the matching intervention. H-CODE does not need to solve it. If it remains poor, that reinforces representation specialization. If it unexpectedly improves, investigate the mechanism without redefining H-CODE around that result.

## Guardrails

Do not declare H-CODE successful from producer rank alone.

| Guardrail | Control observation to preserve |
| --- | --- |
| `qse-docqa-sem-002` | rank 2 hit |
| `qse-docqa-sem-003` | rank 2 hit |
| `qse-docqa-lex-002` | rank 4 hit (`2_state_stamp_before_conviction`) |
| `qse-docqa-mch-001` stamp | rank 5 |
| `qse-docqa-mch-001` consumer | rank 6; conjunction still fails under control |
| `qse-docqa-spec-001` | unmeasurable underspecific; diagnostic rank-1 identity |
| frozen `evaluate.py` gold queries | question / verdict / Finding 3.5 still in top-3 on the **frozen** path |
| H-CODE gold queries | same three gold queries through `rank_all_hcode` still place each target in top-3 |

Also keep diagnostic observation of:

- near-OOD `qse-docqa-ood-002`
- far-OOD `qse-docqa-ood-001`
- alias-trap `qse-docqa-ood-003` (`verdict` rank 1 with `alias=0.5` under control, H-QRL, H-MORPH, and H1)

H-CODE must not recreate the H-QRL `date` artifact. Because no identifier expansion enters the query, generated-token alias contamination should not occur. If alias behavior changes unexpectedly, investigate and document it. Do not patch it.

Alias should remain 0.0 on the in-scope producer-target rows.

### Code-specific blast radius

Inspect whether H-CODE causes:

- identifier-heavy chunks becoming universal attractors
- code symbols dominating ordinary prose queries
- common programming tokens creating false neighbors
- chunk-title attraction
- near-OOD becoming highly similar
- arbitrary identifier similarity creating false confidence

## Code-register diagnostics (not in the score)

After the sealed run, for relevant chunks (producer, rank 1, and other persistent competitors), record whether they are prose-heavy, identifier-heavy, or mixed.

Frozen descriptive signals, applied to stored `chunk.text` only:

- snake_case count: matches of `[a-z][a-z0-9]*(?:_[a-z0-9]+)+`
- dotted-identifier count: matches of `[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]+)+`
- camelCase count: matches of `[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+`
- whitespace token count: `len(text.split())`
- identifier-like proportion: `(snake + dotted + camel) / max(1, whitespace tokens)`

These counts do **not** enter scoring. Labels are descriptive. If a chunk is ambiguous, call it mixed and say why. Do not add this diagnostic to the retrieval modules if that would expand scoring scope; compute it in analysis from frozen chunk text.

## OOD caution

Code-aware representations may create similarity between unrelated identifiers because they share structural patterns.

For near-OOD, far-OOD, and alias-trap cases, record:

- top `code_cosine`
- top-k identities
- score margin
- identifier-density of top results where available

Do **not** invent a reject threshold. Do **not** attempt OOD calibration. Document any new pathology as future work.

Do not treat high `code_cosine` as automatically meaningful.

## Success (locked before execution)

H-CODE is **supported** if:

1. `sem-001` shows meaningful absolute correspondence improvement attributable to code/identifier-aware similarity (producer `code_cosine` materially exceeds its H1 MiniLM similarity, or the producer becomes substantially more competitive relative to prose neighbors);
2. producer ranking improves meaningfully, interpreted with the score-scale caution;
3. improvement comes from target correspondence, not competitor collapse;
4. alias remains zero on the producer;
5. original query remains unchanged;
6. no corpus identifier expansion occurred;
7. guardrails remain broadly functional;
8. no severe new identifier-attractor pathology appears.

H-CODE may still be supported if `sem-001` remains outside top-k but the representation substantially improves the target-to-competitor relationship.

Do **not** require rank 1.
Do **not** require H-CODE to beat MiniLM on `lex-001`.
Do **not** require H-CODE to solve `spec-002`.
Do **not** define success as global hit rate.

Use language: supported / partially supported / weakened / rejected / inconclusive.

## Partial support (locked before execution)

Call H-CODE **partially supported** if, for example:

- `code_cosine` clearly improves `sem-001` correspondence but not enough to recover retrieval;
- some identifier-aware relationship is captured but guardrails show meaningful tradeoffs;
- improvements occur only on certain identifier structures.

Do not force binary success/failure.

## Falsification (locked before execution)

H-CODE is weakened or rejected if:

- `sem-001` remains essentially unchanged;
- producer `code_cosine` remains weak relative to prose neighbors;
- rank improves only because competitors lose score;
- generic identifier-heavy chunks become incorrect attractors;
- gains require query-specific identifiers;
- alias explains the gain;
- OOD becomes severely pathological;
- sealed ranks influence model or preprocessing selection;
- H-CODE only raises aggregate hit rate without repairing the named failure;
- query rewriting, morphology, identifier expansion, or MiniLM blending is silently applied.

`lex-001` weaker than H1 is **not** falsification by itself.
`spec-002` remaining a miss is **not** falsification.

## Mechanism labels for every important row

For every measurable/important row, report control rank, H-QRL rank, H-MORPH rank, H1 rank, H-CODE rank, `lexical_cosine`, MiniLM `dense_cosine`, `code_cosine`, Jaccard, alias, top competitor changes, and hit/miss.

Classify any rank improvement as exactly one primary mechanism, with overlays named if needed:

- **A.** target correspondence increasing (`code_cosine` on the gold)
- **B.** competitors weakening
- **C.** alias behavior
- **D.** some other mechanism

Do not label B as identifier-register improvement. Do not count B as support for H-CODE.

## Implementation requirements (after this document exists)

Keep the H-CODE path isolated and auditable. Prefer separate modules:

- code encoder (`code_embed.py`)
- code index (`code_index.py`)
- H-CODE ranker (`code_hcode.py`)
- experiment orchestration in `run_query_set.py` behind `LUNA_HCODE`

Do not contaminate frozen `retrieve()` / `rank_all()` scoring when H-CODE is disabled.

`RetrievalHit` may gain an explicit `code_cosine` field with default 0.0 so logs can name it. Frozen `rank_all()` must still compute `score = 0.7 * lexical_cosine + 0.3 * jaccard + alias` and must not load the code model.

Logs must expose at least: query, target section, `code_cosine`, `dense_cosine`, `lexical_cosine`, Jaccard, alias, total score, rank, top-k sections, component-level scores. Never collapse component scores into only one opaque final number.

## Tests before measured run

Add tests for:

- feature flag default OFF
- frozen `retrieve()` unchanged
- H1 still callable and unchanged
- H-MORPH / H-QRL modes unchanged
- H-CODE mutually exclusive with rewrite modes and with H1
- original YAML query preserved
- no identifier expansion
- scorer equation exact
- embedding dimensionality 768
- L2 normalization
- deterministic/stable embedding output within numeric tolerance
- stable section-to-vector mapping
- index/hash validation (`section_id` + `content_sha256`)
- dotted/snake/camel preprocessing exactly as preregistered (identity: no external split)
- score component logging

Run the complete suite. Record total pass count.

## Measurement protocol (after this document exists)

1. Preregistration committed (this file).
2. Implementation and tests committed.
3. Flag-off: `pytest tests` and `python run_query_set.py` still reproduce control calibration ranks.
4. Verify query-set and lexical-index hashes.
5. Build/freeze the H-CODE representation artifact; record its hash.
6. Execute sealed H-CODE pass: `LUNA_HCODE=1 python run_query_set.py` (new JSONL).
7. Preserve the trace. Do not edit YAML predictions.
8. Analyze results. Write H-CODE findings.
9. Update the comparative failure-mode map and `system_findings_hypothesis_testing.md`.
10. **STOP.** Do not begin H-HYBRID, OOD/reject, alias redesign, conjunction work, or production integration.

Do not modify the code model, pooling, weights, preprocessing, or formula after seeing results. Do not run a second representation after seeing the first result.

## Out of scope

- Query rewriting, morphology, identifier expansion
- Combining morphology + MiniLM + H-CODE + lexical cosine (H-HYBRID)
- Constrained identifier expansion (H-ID)
- Alias-contract changes (H-ALIAS)
- Embedding-model bake-off
- Weight search
- BM25, reranking, reject/OOD scoring, hop control, GraphRAG
- Changing TOP_K, golds, aliases, chunk boundaries, or query text
- Manually inserting `regime_stability` or `RegimeObserver`
- Query-specific model routing
- Expanding the query set after inspecting results and folding new cases into this experiment

## Deliberate non-actions during and after the measured test

This sprint will not:

- change query text or gold labels
- manually insert identifier bridges
- add `regime_stability` to queries
- blacklist `date`
- tune weights from sealed ranks
- test many embedding models and pick the best
- change TOP_K or chunk boundaries
- change aliases
- create query-specific boosts
- define success after seeing results
- promote a mechanism because global hit rate rose
- implement H-HYBRID
- patch `sem-001`

If the experiment exposes another failure, document it as a new hypothesis. That result is valuable.

## References

- Producer-burial forensics: `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- H-QRL / H-MORPH / H1 preregistrations and findings
- Three-hypothesis comparative findings: `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md`
- System findings: `docs/query_set_expansion/system_findings_hypothesis_testing.md`
- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Frozen three-row baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Failure-mode map: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Sealed set: `eval_sets/docqa.yaml`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
- Jina model card: https://huggingface.co/jinaai/jina-embeddings-v2-base-code (revision `516f4baf13dec4ddddda8631e019b5737c8bc250`)
