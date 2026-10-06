# Preregistration: closed-vocabulary morphology ablation (`H-MORPH`)

**Date:** 2026-10-05
**Status:** Preregistered. Hypothesis and rewrite rules locked before the experiment run.
**Experiment name:** `morphology-only-ablation-v1`
**Branch:** `research/morphology-only-ablation`
**This document is not a result.** It records what will be measured, and why, before `LUNA_MORPH_LOOP=1` is applied to the sealed set.

H-MORPH is an **ablation of H-QRL**. It is not dense-embedding H1. It is not a second attempt to salvage identifier-segment expansion.

Prior experiment:

- Preregistration: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`
- Findings: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`
- System findings: `docs/query_set_expansion/system_findings_hypothesis_testing.md`

H-QRL as a **joint** claim was weakened. Morphology on `qse-docqa-spec-002` was the supported fragment. Identifier-segment expansion failed on `qse-docqa-sem-001` and produced `date` alias contamination via `regime_update_interval_seconds`. This experiment isolates the morphology fragment and asks whether that mechanism survives without identifier expansion.

The purpose is **not** to improve global hit rate.

## What this experiment does not change

- `eval_sets/docqa.yaml` bytes (version `docqa-expanded-v1`)
- query-set sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`
- `retrieve.py` scoring formula, `COSINE_WEIGHT=0.7`, `LEXICAL_WEIGHT=0.3`, `SECTION_ALIASES`
- chunk boundaries, analyzer (`embed.tokenize`), TF-IDF fit, TOP_K=5
- historical JSONL traces, including H-QRL `eval_sets/runs/2026-10-06_run-001.jsonl` and `eval_sets/runs/2026-10-06_run-002.jsonl`
- YAML `query` / `expected` / `failure_mode` / locked predictions
- H-QRL `qrl-v1` behavior when `LUNA_QUERY_LOOP=1` and `LUNA_MORPH_LOOP` is unset

The frozen hybrid scorer still computes `0.7 * cosine + 0.3 * Jaccard + alias`. The loop only changes the **string** that scorer sees, and may skip a later identical scoring pass via cache.

## Control

Compare against the frozen expanded control, **not** against a retrospectively modified baseline and **not** against H-QRL ranks as if they were the control. H-QRL ranks are prior mechanistic evidence used to form predictions.

| Piece | Identity |
| --- | --- |
| Control name | `expanded-control-v1` |
| Control characterization | `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` |
| Control trace | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` |
| Index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| Retriever freeze | `retrieve.py` scoring unchanged since `000e658` |
| `retrieve.py` file sha256 | `2a3401d3ea3831d39f15afceee3d382452c8a8e31c7ca39848bb674b2c4e41a5` |
| `embed.py` file sha256 | `2567d09b5da424f55f8470363a036926683b3ac6e8d6db8e1b36318bcf66dfcf` |
| `evaluate.py` file sha256 | `97d953d99f0b9136b069a764afa04536555911f9c23f8566a1563933361fc579` |

Primary metric: `rank_gain = control_rank - experiment_rank` on measurable rows, interpreted **only together with** target absolute score movement and component deltas. Global hit rate is not an optimization target.

## Hypothesis (`H-MORPH`)

Closed-vocabulary morphology can repair retrieval failures caused by simple surface-form mismatch while causing substantially less blast radius than the previous bundled rewrite.

More specifically: because the frozen analyzer stores `thresholds` rather than `threshold`, adding the in-vocabulary morphological variant of a query token should raise genuine correspondence with gold chunks whose miss is morphological, without identifier dumping, synonym invention, or alias injection.

## Function-word decision (locked before ranks)

**Choice B: keep the raw query tokens and change only morphology.**

Do **not** apply the H-QRL function-word stripping list in this experiment.

### Why B isolates the causal question

H-QRL bundled three query-side changes versus frozen control:

1. function-word stripping
2. in-vocabulary morphology
3. identifier-segment expansion

H-QRL findings already showed that (1) is a distinct ranking mechanism. On `qse-docqa-lex-001`, producer rank improved while producer absolute score fell, because competitors collapsed after stopword removal. That movement is **not** morphology.

If H-MORPH kept stripping, the comparison to `expanded-control-v1` would still have two new mechanisms. Any rank movement on lex-001, mch-001, or other function-word-heavy rows would be confounded. The only way to keep stripping and still isolate morphology would be a second, stopword-stripped control that does not exist as a frozen artifact.

Choice B makes morphology the only intended new causal mechanism relative to the frozen control:

- original query string remains the prefix of the rewritten string
- function words remain
- identifier expansion does not run
- the only added tokens are in-vocab morphological variants of original query tokens

This is a stricter replication of the spec-002 morphology claim, not a replay of H-QRL with identifiers deleted. If `thresholds` still lifts producer correspondence without stripping `the`, that is stronger evidence for morphology than the bundled H-QRL rewrite.

If function-word stripping later appears necessary, that is a **different** hypothesis. It will not be introduced after seeing H-MORPH ranks.

## Intervention (`morph-v1`)

Retain only deterministic in-vocabulary morphology from H-QRL. Extract the existing locked morphology family; do not add new transformations.

Analyzer remains `embed.tokenize`. Vocab comes from the live store (the same index `rank_all` uses). IDF is unused: there is no identifier ranking step.

### Allowed morphology (complete, frozen)

For each original query token, add a candidate only if it is already in the fitted vocab and is not already one of the original query tokens:

- `token + s`
- `token + es`
- if token ends in `es` (length > 3): stem `token[:-2]`
- else if token ends in `s` but not `ss` (length > 3): stem `token[:-1]`

Do not stem or pluralize using a linguistic library. Do not add out-of-vocab strings. Do not cascade: expand from original query tokens only, not from morphology outputs.

Apply morphology to **all original tokens**, including tokens that appear on the unused H-QRL function-word list. The function-word list is not part of `morph-v1`. If a function word has an in-vocab morphological variant, it may be emitted and must be logged. Do not add a special case to prevent that after seeing ranks.

### Identifier expansion

**Completely disabled.** Not capped at zero after candidate generation. The identifier-segment procedure must not run. `identifier_expansions` must be empty on every H-MORPH lookup.

### Emission

If any morphology variants are emitted:

`rewritten = original_query + " " + " ".join(sorted unique morphology variants)`

If none are emitted, `rewritten` is the original query string unchanged.

Preserving the original string keeps control alias matching and original token identity intact. Appended variants are space-separated fitted-vocab tokens, sorted lexicographically for determinism.

### Explicit non-actions

- no function-word stripping
- no identifier-segment expansion
- no filename / identifier dumping
- no synonym table
- no embeddings or semantic expansion
- no heading or alias injection
- no row-id, query-id, or producer-specific rules
- no analyzer / chunker / weight / TOP_K / alias-table change
- no manual injection of `thresholds`, `regime_stability`, or a `date` blacklist

## Predicted morphology fires (from locked rules + prior H-QRL tracker, not from new ranks)

These are mechanism predictions, not ranking results:

| Row | Prior H-QRL morphology | H-MORPH expectation |
| --- | --- | --- |
| `qse-docqa-spec-002` | `label`, `thresholds` | `thresholds` must fire if `threshold` remains a query token and `thresholds` remains in vocab. `label` may fire from `labels` if `label` is in vocab. |
| `qse-docqa-lex-001` | `measures`, `signals` | those same in-vocab plurals may fire from `measure` / `signal` |
| `qse-docqa-sem-001` | none | no material morphology expected; if none fire, rewritten query equals original |
| `qse-docqa-ood-003` | `scope` from `scopes` | `scope` may still fire; the control already has slug-as-spaces `scope`⊂`scopes` |

Additional fires relative to H-QRL are allowed only if they are produced by the locked one-step rules on original tokens. They are evidence to inspect, not a reason to edit the rules.

## Primary predictions

### Primary positive case: `qse-docqa-spec-002`

Control rank 9, score 0.042792, cosine 0.051815, Jaccard 0.021739, alias 0.0. Rank 1 `verdict`.

H-QRL attributed producer movement `cosine 0.052 → 0.183`, rank `9 → 1`, alias `0.0` to `threshold → thresholds`.

H-MORPH prediction:

- morphology includes `thresholds`
- producer **absolute** score increases
- producer cosine increases
- producer Jaccard ideally increases (`thresholds` is in the producer chunk)
- substantial positive rank gain
- producer alias remains `0.0`
- the gain is explained by the logged morphology tokens, not by alias and not by identifier expansion

Rank 1 on the producer is the strongest supporting pattern if it occurs. It is **not** required if absolute correspondence clearly rises and alias remains 0.0. Failure to reproduce rank 1 is not automatic falsification when `the` still inflates `verdict` because function words were deliberately retained.

This is the primary mechanistic replication.

### Mechanism-specific non-target: `qse-docqa-sem-001`

Control rank 10, score 0.015352, cosine 0.017169, Jaccard 0.011111, alias 0.0. Rank 1 `verdict`.

Diagnosed failure mode is identifier/semantic correspondence (`regime` vs `regime_stability`), not morphology. H-QRL morphology did not fire.

Prediction:

- morphology alone should **not** materially improve this row unless an actual morphology rule fires that can explain the gain
- if no morphology fires, rank and scores should match control
- do **not** reinterpret lack of movement as H-MORPH failure
- identifier expansions must be absent; `regime_update_interval_seconds` must not appear

### Negative-control / diagnostic: `qse-docqa-lex-001`

Control rank 7, score 0.037137, cosine 0.048343, Jaccard 0.010989, alias 0.0. Rank 1 `upstream_signals_since_verdict_independent`.

Closed-vocab synonymy (`consistency` / `confidence` / `market-condition`). General morphology must not invent `stability` or `vwap_dist`.

H-QRL rank 7 → 3 was **not** producer-score improvement. Competitor collapse after function-word stripping, plus weak `signals` overlap, moved rank while producer score fell (0.037 → 0.031).

H-MORPH must score this row on four separate quantities:

| Quantity | How to read it |
| --- | --- |
| target score movement | required for a correspondence claim |
| rank movement | not sufficient alone |
| competitor movement | inspect whether rank came from others falling |
| hit/miss | supporting detail only |

Prediction:

- no synonym invention
- `measures` / `signals` may fire
- a rank gain **without** increased producer correspondence is **not** evidence supporting H-MORPH
- because function words are retained, the H-QRL competitor-collapse signature is **not** expected as a stripping artifact
- if rank still moves, classify it as A/B/C/D (below) before any success language

## Guardrails

Do not declare H-MORPH successful from producer ranks alone.

| Guardrail | Control observation to preserve |
| --- | --- |
| `qse-docqa-sem-002` | rank 2 hit, margin −0.013370 vs `verdict` |
| `qse-docqa-sem-003` | rank 2 hit, margin −0.011192 vs `verdict` |
| `qse-docqa-lex-002` | rank 4 hit (`2_state_stamp_before_conviction`) |
| `qse-docqa-mch-001` stamp | rank 5 (in top-k); consumer rank 6 remains a conjunction observation |
| frozen `evaluate.py` gold queries | question / verdict / Finding 3.5 still in top-3 on the frozen path |
| loop gold queries | same three gold queries through morph-v1 still place each target in top-3 |

Also keep diagnostic observation (not scored reject metrics) of:

- near-OOD `qse-docqa-ood-002` (impact currently rank 1 at 0.164)
- far-OOD `qse-docqa-ood-001`
- alias-trap `qse-docqa-ood-003` (`verdict` rank 1 at 0.700 with `alias=0.5`)

H-MORPH must not win producer rows by stuffing aliases into in-scope queries. Alias should remain 0.0 on the in-scope producer-target rows.

### New guardrail: `date` alias contamination must disappear if identifier expansion was the cause

H-QRL injected `regime_update_interval_seconds`. Slug-as-spaces then treated substring `date` as naming the `date` section (`+0.35`). That chunk became rank 1 on multiple rewritten queries despite cosine 0 and Jaccard 0.

H-MORPH must verify **directly**:

1. `regime_update_interval_seconds` is absent from every rewritten query and every expansion list.
2. Identifier expansion lists are empty.
3. The `date` section is not rank 1 with `alias=0.35` from that generated identifier.
4. Do not merely check that `date` is no longer rank 1; inspect whether the offending generated identifier is absent and whether alias contributions behave as expected.

If `date` still wins on some row, inspect that row’s rewritten string and alias components before attributing it to residual identifier expansion. Do not blacklist `date`.

## Cache and tracker claims

Reuse the H-QRL cache/tracker infrastructure with policy `morph-v1`.

### Cache

Ranking-transparent. First pass of the 12 unique rows: all cache misses. Second identical pass in the same process: all cache hits. Pass-2 ranks match pass 1 exactly.

Serve policy unchanged: identical rewritten text + matching index hash is a hit; cosine ≥ 0.99 with a different rewritten string is a logged collision and is not served.

### Tracker

Observe only. Persist per-query original/rewritten strings, stopwords dropped (expected empty under morph-v1), morphology fired, identifier expansions (expected empty), cache hit/miss, nearest-neighbor cosine, and timing. Do **not** mutate rewrite rules from those stats during the measured runs.

Flush a **new** sibling file next to the eval JSONL, named `{jsonl_stem}_query_loop.json`. Never rewrite historical traces.

Tracker `policy` field must record `morph-v1`.

## Integration

- Orchestrator: `query_loop.py` (`rank_with_loop`), policy-selectable.
- `run_query_set.py` enables morph-v1 only when `LUNA_MORPH_LOOP` is `1` / `true` / `yes` / `on`. Default off.
- `LUNA_QUERY_LOOP` continues to mean H-QRL `qrl-v1` when morph-v1 is unset, so the previous experiment remains runnable.
- JSONL `query` field remains the original YAML string. Optional fields remain: `rewritten_query`, `cache_hit`, `expansions`, `config.loop_enabled`. Record rewrite policy so traces distinguish morph-v1 from qrl-v1.
- `evaluate.py` stays on frozen `retrieve()`. Gold queries are checked through the loop separately as a guardrail, not by changing `evaluate.py`.
- `retrieve.py` scoring path unchanged.

## Measurement protocol (after this document exists)

1. Flag-off: `pytest tests` and `python run_query_set.py` still reproduce control calibration ranks.
2. Pass 1: `LUNA_MORPH_LOOP=1 python run_query_set.py` (new JSONL + tracker file).
3. Pass 2: same process replays the 12 queries against the same cache; tracker records hit rate and rank identity. Pass 2 does not append a second JSONL copy of the rows.
4. Findings document compares pass 1 to `2026-09-29_run-004.jsonl`. Do not edit YAML predictions.
5. Do not modify rewrite rules after seeing results. Do not add special cases if a prediction fails.

## Mechanism labels for every important row

For every measurable/important row, report control rank, experiment rank, rank_gain, control total score, experiment total score, cosine delta, Jaccard delta, alias delta, morphology expansions fired, top competitor changes, and hit/miss.

Classify any rank improvement as exactly one primary mechanism, with overlays named if needed:

- **A.** target correspondence increasing (cosine and/or Jaccard on the gold)
- **B.** competitors weakening
- **C.** alias behavior
- **D.** some other mechanism

Do not label B as semantic improvement. Do not count B as support for H-MORPH.

## Expected signature (success)

H-MORPH is **supported** if evidence resembles:

1. `spec-002` reproduces a meaningful improvement attributable specifically to morphology (`thresholds` present in the rewrite).
2. Producer **absolute** correspondence improves, not merely relative rank.
3. Alias does not explain the gain.
4. Identifier-related contamination from H-QRL disappears (`regime_update_interval_seconds` absent; `date` alias artifact from that token gone).
5. Guardrail rows remain broadly stable (still hits at comparable ranks; frozen `evaluate.py` still PASSes; loop gold queries still place each target in top-3).
6. Non-morphological misses (especially sem-001) do not suddenly appear “solved” without a plausible morphology mechanism.
7. Cache remains ranking-transparent if retained.

Entry into TOP_K=5 is supporting detail, not the definition of success. Global hit-rate increase is not success.

## Falsification

H-MORPH is **weakened** or **rejected** if:

- `spec-002` fails to reproduce the morphology effect (no `thresholds` fire, or they fire but producer cosine/score do not rise).
- apparent spec-002 gain comes from competitor collapse rather than target-score improvement (mechanism B).
- morphology introduces significant unrelated ranking damage (guardrail hits leave top-k; gold queries fail).
- alias artifacts remain despite removal of identifier expansion, in a way that still depends on generated identifiers.
- unrelated rows gain substantially through mechanisms not named in the hypothesis (synonym invention, alias stuffing, identifier leakage).
- cache changes first-pass ranks relative to `rank_all(rewritten)`.
- observed gains come from changing TOP_K, golds, aliases, 0.7/0.3, or chunk boundaries.

sem-001 non-movement is **not** falsification. lex-001 rank-only movement is **not** support.

Use language: supported / weakened / rejected / inconclusive. Do not say the experiment “worked” because hit rate increased.

## Out of scope

- Dense embeddings (existing H1)
- Constrained identifier expansion (future H-ID)
- Alias-contract changes for generated tokens (future H-ALIAS)
- Re-introducing function-word stripping
- Learned expansion overlay that mutates rules from tracker stats
- LLM rewriter, new dependencies, argparse
- Analyzer/chunker changes, BM25, reranking, reject/OOD scoring, hop control
- Expanding the query set after inspecting results and folding new cases into this experiment

## Deliberate non-actions during and after the measured test

This sprint will not:

- add new morphology exceptions because a sealed row missed
- manually inject `thresholds`
- add `regime_stability`
- blacklist `date`
- retune aliases, TOP_K, or scoring weights
- rewrite expected answers or gold labels
- change chunk boundaries
- patch qrl-v1 against H-MORPH ranks
- start the next hypothesis on this same branch as part of the measured experiment

If the experiment exposes another failure, document it as a new hypothesis.

## References

- H-QRL preregistration: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`
- H-QRL findings: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`
- System findings: `docs/query_set_expansion/system_findings_hypothesis_testing.md`
- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Producer-burial forensics (H1, not implemented here): `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- Frozen three-row baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Failure-mode map: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Sealed set: `eval_sets/docqa.yaml`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
