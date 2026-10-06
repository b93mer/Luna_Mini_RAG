# Preregistration: query-side rewrite/cache loop (`H-QRL`)

**Date:** 2026-10-05
**Status:** Preregistered. Hypothesis and rewrite rules locked before the experiment run.
**Experiment name:** `query-rewrite-cache-loop-v1`
**Branch:** `research/query-rewrite-cache-loop`
**This document is not a result.** It records what will be measured, and why, before `LUNA_QUERY_LOOP=1` is applied to the sealed set.

This is a **query-side** intervention. It is not the dense-embedding H1 named in `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`. That document already rejected query-specific expansion as overfitting. H-QRL uses general locked rules only.

## What this experiment does not change

- `eval_sets/docqa.yaml` bytes (version `docqa-expanded-v1`)
- query-set sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`
- `retrieve.py` scoring formula, `COSINE_WEIGHT=0.7`, `LEXICAL_WEIGHT=0.3`, `SECTION_ALIASES`
- chunk boundaries, analyzer (`embed.tokenize`), TF-IDF fit, TOP_K=5
- historical JSONL traces
- YAML `query` / `expected` / `failure_mode` / locked predictions

The frozen hybrid scorer still computes `0.7 * cosine + 0.3 * Jaccard + alias`. The loop only changes the **string** that scorer sees, and may skip a later identical scoring pass via cache.

## Control

| Piece | Identity |
| --- | --- |
| Control name | `expanded-control-v1` |
| Control characterization | `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` |
| Control trace | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| Query-set version | `docqa-expanded-v1` |
| Index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| Retriever freeze | `retrieve.py` scoring unchanged since `000e658` |

Primary metric: `rank_gain = control_rank - experiment_rank` on measurable rows. Global hit rate is not an optimization target.

## Hypothesis (`H-QRL`)

Because the frozen scorer sees the raw query string, a general rewrite that (1) drops a locked function-word list and (2) expands remaining tokens to in-vocab morphological variants and identifier-segment superstrings should raise overlap with gold chunks whose miss is identifier-bound or morphological.

### Predicted movers (primary slice)

| Row | Control rank | Why a general rewrite could move it |
| --- | ---: | --- |
| `qse-docqa-sem-001` | 10 | Standalone `regime` is absent from the producer vector; identifier-segment expansion can add `regime_stability` / similar `_`/`.`-delimited tokens. |
| `qse-docqa-spec-002` | 9 | `threshold` vs `thresholds` is a morphological miss; `thresholds` is already in the fitted vocab. |

### Predicted non-mover (negative control)

| Row | Control rank | Why little or no gain is expected |
| --- | ---: | --- |
| `qse-docqa-lex-001` | 7 | Closed-vocab synonymy (`consistency` / `confidence` / `market-condition`). General rules must not invent `stability` or `vwap_dist`. A large gain here would suggest hidden overfitting. |

### Cache claim

Ranking-transparent. First pass of the 12 unique rows: all cache misses. Second identical pass in the same process: all cache hits. Pass-2 ranks match pass 1 exactly.

### Tracker claim

Observe only. Persist per-query rewrite diffs, expansions fired, nearest-neighbor cosine, and timing. Do **not** mutate rewrite rules from those stats during the measured runs. Learning in this PoC is the findings document plus a flushable aggregate.

## Locked rewriter policy (`qrl-v1`)

Single implementation: `query_rewrite.py`. Analyzer remains `embed.tokenize`. Vocab and IDF come from the live store (the same index `rank_all` uses).

### 1. Function-word list (complete, frozen)

Drop these tokens after tokenize. This is the entire list. Do not add or remove members after seeing experiment ranks.

```
a about after an and are as at be been before being but by can could did do
does for from how if in into is it itself its may might must no not of on or
shall should than that the then these this those to was were what when where
which who whom whose why will with would
```

### 2. Morphology

For each remaining content token, add a candidate only if it is already in the fitted vocab:

- `token + s`
- `token + es`
- if token ends in `es` (length > 3): stem `token[:-2]`
- else if token ends in `s` but not `ss` (length > 3): stem `token[:-1]`

Do not stem or pluralize using a linguistic library. Do not add out-of-vocab strings.

### 3. Identifier-segment expansion

For each remaining content token with length ≥ 4, collect vocab tokens in which that token is a `_` or `.` delimited segment (example: `regime` matches `regime_stability`, not `regimeboss` or `regimeobserver.step` as a single unsplit identifier).

- Skip the token equal to the query token itself.
- Cap at **8** identifier expansions per query.
- Prefer highest IDF, then lexicographic token name for ties.
- Do not cascade: expand from original content tokens only, not from morphology outputs.

### 4. Emission

Rewritten text = original content tokens in order (function words removed) plus the unique expansion tokens (morphology ∪ identifier) sorted lexicographically, space-joined.

If every token was a function word, keep the original query (do not emit an empty string).

### Explicit non-actions

- no synonym table
- no heading or alias injection
- no row-id or query-id branches
- no producer-specific boosts
- no analyzer / chunker / weight / TOP_K change

## Semantic cache policy

Module: `query_cache.py`. In-memory for the process.

- Key: L2-normalized TF-IDF vector of the **rewritten** query + `index_sha256`.
- Serve iff the rewritten query string is identical and `index_sha256` matches. Identical-string hits include all-OOV queries whose TF-IDF vectors are all zeros (`cosine_similarity` of zeros is 0.0, so cosine-only serving would miss pass 2).
- Cosine ≥ **0.99** with a **different** rewritten string is a collision: log it, do not serve. This keeps the cache from mixing golds across rows (near-dup ranking reuse was rejected for this PoC).
- On miss, run frozen `rank_all(rewritten)`.
- Store serializable ranking (section_id + score components) and rehydrate from the live store.
- Invalidate the entire cache when `index_sha256` changes.
- Always record nearest-neighbor cosine, including on a miss.

A unit test will check that pairwise cosine of the 12 rewritten sealed queries stays below 0.99. If a pair collides, the test fails and the cache must not serve that pair.

## Tracker policy

Module: `query_tracker.py`. Does not change ranking.

Per lookup: original query, rewritten query, stopwords dropped, expansions applied, cache hit/miss, nearest cosine, `perf_counter` duration in nanoseconds for cache lookup and for `rank_all` (zero `rank_ns` on a hit).

Per run: flush a **new** sibling file next to the eval JSONL, named `{jsonl_stem}_query_loop.json`. Never rewrite historical traces.

## Integration

- Orchestrator: `query_loop.py` (`rank_with_loop`).
- `run_query_set.py` calls it only when `LUNA_QUERY_LOOP` is `1` / `true` / `yes` / `on`. Default off.
- JSONL `query` field remains the original YAML string. New optional fields: `rewritten_query`, `cache_hit`, `expansions`, `config.loop_enabled`.
- `evaluate.py` stays on frozen `retrieve()`. Gold queries are checked through the loop separately as a guardrail, not by changing `evaluate.py`.
- `retrieve.py` scoring path unchanged; docstring may point at this experiment.

## Measurement protocol (after this document exists)

1. Flag-off: `pytest tests` and `python run_query_set.py` still reproduce control calibration ranks.
2. Pass 1: `LUNA_QUERY_LOOP=1 python run_query_set.py` (new JSONL + tracker file).
3. Pass 2: same process replays the 12 queries against the same cache; tracker records hit rate and rank identity. Pass 2 does not append a second JSONL copy of the rows.
4. Findings document compares pass 1 to `2026-09-29_run-004.jsonl`. Do not edit YAML predictions.

## Guardrails

Do not declare H-QRL successful from producer ranks alone.

| Guardrail | Control observation to preserve |
| --- | --- |
| `qse-docqa-sem-002` | rank 2 hit, margin −0.013370 vs `verdict` |
| `qse-docqa-sem-003` | rank 2 hit, margin −0.011192 vs `verdict` |
| `qse-docqa-lex-002` | rank 4 hit (`2_state_stamp_before_conviction`) |
| `qse-docqa-mch-001` stamp | rank 5 (in top-k); consumer rank 6 remains a conjunction observation |
| `evaluate.py` gold queries on the frozen path | still PASS |
| `evaluate.py` gold queries through the loop | question / verdict / Finding 3.5 still in top-3 |

Also keep diagnostic observation (not scored reject metrics) of:

- near-OOD `qse-docqa-ood-002` (impact currently rank 1 at 0.164)
- alias-trap `qse-docqa-ood-003` (`verdict` rank 1 at 0.700 with `alias=0.5`)

H-QRL must not win producer rows by stuffing aliases into in-scope queries. Alias should remain 0.0 on the in-scope producer-target rows.

## Expected signature

Evidence that would support H-QRL:

- Positive rank_gain on **both** primary-slice rows (sem-001 and spec-002), not one lucky row.
- lex-001 shows little or no rank_gain (negative-control signature).
- Cosine and/or Jaccard movement on the producer is explained by logged expansions (`regime_*` segments and/or `thresholds`), not by alias.
- Guardrail rows stay hits at comparable ranks; frozen `evaluate.py` still PASSes; loop gold queries still place each target in top-3.
- Pass 1 cache hit rate is 0/12; pass 2 is 12/12 with identical ranks.

Entry into TOP_K=5 is supporting detail, not the definition of success.

## Falsification

H-QRL is weakened or rejected if:

- Little or no rank movement on sem-001 **and** spec-002.
- lex-001 is the only large gainer.
- Alias or slug-as-spaces fire explains a producer “win.”
- Guardrail rows regress substantially (sem-002/003 leave top-k; lex-002 leaves top-k; frozen or loop gold queries fail).
- Near-OOD or alias-trap become materially more pathological.
- Cache changes first-pass ranks relative to `rank_all(rewritten)` (cache must be transparent).
- Observed gains come from changing TOP_K, golds, aliases, 0.7/0.3, or chunk boundaries.

Do not define success as “more hits” globally. The control hit rate is not an optimization target.

## Out of scope

- Dense embeddings (existing H1)
- Learned expansion overlay that mutates rules from tracker stats
- LLM rewriter, new dependencies, argparse
- Analyzer/chunker changes, BM25, reranking, reject/OOD scoring, hop control

## References

- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Producer-burial forensics (H1, not implemented here): `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- Frozen three-row baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Failure-mode map: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Sealed set: `eval_sets/docqa.yaml`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
