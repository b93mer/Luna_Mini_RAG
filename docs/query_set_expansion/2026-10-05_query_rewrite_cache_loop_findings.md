# Findings: query-side rewrite/cache loop (`H-QRL`)

**Date:** 2026-10-05 (runs executed 2026-10-06T01:38Z–01:39Z UTC; the logger names run files by UTC date)
**Status:** Experiment result. Query-set bytes unchanged. Frozen hybrid scoring unchanged. Historical control traces unchanged.
**Preregistration:** `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`
**Control:** `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` / `eval_sets/runs/2026-09-29_run-004.jsonl`
**This document is observation.** Predictions stay in the preregistration. YAML queries, golds, and locked `current_stack_prediction` values were not rewritten.

H-QRL is a query-side alternative to producer-burial H1 (dense cosine). It is not H1.

## Experimental state

| Piece | Identity |
| --- | --- |
| Branch | `research/query-rewrite-cache-loop` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` (seal matched) |
| Index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` (matched the frozen control) |
| Scoring | Unchanged: `0.7 * cosine + 0.3 * Jaccard + alias_boost` |
| TOP_K | 5 |
| Flag-off sanity | `eval_sets/runs/2026-10-06_run-001.jsonl` (run UUID `efe9d4c6-8285-4732-b945-8762022be02c`); calibration ranks matched control exactly |
| Experiment pass 1 | `eval_sets/runs/2026-10-06_run-002.jsonl` (run UUID `1af5b471-f17f-4b1f-8013-7955e962270a`) |
| Tracker | `eval_sets/runs/2026-10-06_run-002_query_loop.json` |
| Frozen `evaluate.py` | PASS (section lookup + hybrid gold queries, no re-ingest in this measurement) |
| Unit tests | 32/32 pass |

`rank_gain = control_rank - experiment_rank`. Positive is movement toward rank 1.

## Verdict on H-QRL

**Weakened.** Do not accept. Do not treat the 3/7 → 6/7 measurable hit count as success.

The two halves of the locked rewriter did not share a mechanism:

1. **Morphology is supported** on the predicted spec-002 row: `threshold` → in-vocab `thresholds` moved the producer from rank 9 to rank 1. Alias stayed 0.0. Cosine, not Jaccard, carried the score (0.052 → 0.183).
2. **Identifier-segment expansion is not supported** on the predicted sem-001 row: the IDF cap selected RegimeBoss/state/filename tokens, not `regime_stability`. Producer rank 10 → 11. The same expansions injected `regime_update_interval_seconds`, whose substring `date` fired the slug-as-spaces rule (`+0.35`) on the `date` chunk. That new rank-1 winner is an alias artifact, not semantic correspondence.

The lex-001 negative control also failed its predicted “little or no gain” signature (rank 7 → 3, hit). Expansions were only `measures` / `signals` (morphology), not the forbidden `stability` / `vwap_dist`. The producer **score** slightly fell (0.037 → 0.031); rank rose because competitors collapsed after stopword stripping. That is not synonym overfitting, and it is also not the identifier-bridge the hypothesis named.

The cache claim is **supported**. The tracker claim (observe only) is **supported**.

## Measurable rank table

| row | control rank | experiment rank | rank_gain | control outcome | experiment outcome | target alias | experiment rank-1 |
| --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| sem-001 | 10 | 11 | −1 | expected_miss | expected_miss | 0.0 | `date` (`alias=0.35`) |
| sem-002 | 2 | 4 | −2 | hit | hit | 0.0 | `date` (`alias=0.35`) |
| sem-003 | 2 | 2 | 0 | hit | hit | 0.0 | `date` (`alias=0.35`) |
| lex-001 | 7 | 3 | +4 | expected_miss | hit | 0.0 | `upstream_signals_since_verdict_independent` |
| lex-002 | 4 | 3 | +1 | hit | hit | 0.0 | consumer |
| spec-002 | 9 | 1 | +8 | expected_miss | hit | 0.0 | producer (gold) |
| mch-001 stamp | 5 | 2 | +3 | expected_miss (conjunction) | hit | 0.0 | consumer |
| mch-001 consumer | 6 | 1 | +5 | expected_miss (conjunction) | hit | 0.0 | consumer |

Measurable outcomes: control `hit=3, expected_miss=4`; experiment `hit=6, expected_miss=1`. Global hit rate is still not an optimization target.

## Primary slice

### qse-docqa-sem-001 — predicted mover, missed

Identifier expansions: `10_regime_honesty_evidence_scoping.md`, `apply_regime_boss_hard_block`, `evaluate_conviction_and_ev`, `regime_boss_reason`, `regime_payload`, `regime_state`, `regime_state.get`, `regime_update_interval_seconds`. No `regime_stability`. No morphology.

Producer cosine 0.017169 → 0.013101. Rank 10 → 11. Rank 1 is `date` at score 0.350 with cosine 0, Jaccard 0, alias 0.35. Mechanism: `date` is a substring of `regime_update_interval_seconds`, so `alias_boost` treats the rewritten query as naming the `date` section.

This is the blast radius the producer-burial forensics already named for query expansion. H-QRL’s identifier half is rejected for this row.

### qse-docqa-spec-002 — predicted mover, confirmed

Expansions: `label`, `thresholds` (morphology only). No identifier dump. Alias 0.0 on every scored chunk of this row.

Producer cosine 0.051815 → 0.183381, Jaccard 0.021739 → 0.034091, rank 9 → **1**. The locked morphological miss (`threshold` / `thresholds`) is the mechanism. This is the strongest supporting row.

## Negative control

### qse-docqa-lex-001 — predicted non-mover, unexpectedly a hit

No `stability`, no `vwap_dist`. Morphology added `measures` and `signals`. Rank 1 remains the lexical neighbor `upstream_signals_since_verdict_independent`. Producer entered top-k at rank 3 with a **lower** absolute score than control. Rank_gain came from collapsing `verdict` / impact / function-word competitors after stopword stripping, plus a small `signals` overlap with the neighbor (and weaker overlap with the producer).

The “no synonym invention” non-action held. The “little or no rank_gain” prediction did not. H-QRL is weakened on the negative-control signature.

## Guardrails

| Guardrail | Result |
| --- | --- |
| sem-002 stays a hit | Held (still in top-k) but rank 2 → 4 and a new wrong winner (`date`) |
| sem-003 stays ≤ rank 2 or in top-k | Rank 2 held; rank 1 is now `date`, not `verdict` |
| lex-002 in top-k | Held (rank 4 → 3) |
| mch-001 stamp in top-k | Held and improved; consumer also entered top-k so the conjunction flipped to hit |
| frozen `evaluate.py` PASS | Held |
| loop gold queries in top-3 | Held: question, verdict, Finding 3.5 each remain in top-3. `date` is rank 2 on the question and verdict gold queries via the same `update`/`date` substring |

Producer-target alias remained 0.0 on in-scope golds. The contamination is slug-as-spaces on **other** chunks, driven by identifier expansions, not by stuffing `SECTION_ALIASES` into the YAML queries.

## Unmeasurable / diagnostic

Not scored as hit/miss.

| row | control rank-1 | experiment rank-1 | note |
| --- | --- | --- | --- |
| spec-001 | verdict 0.284 | `date` 0.350 alias 0.35 | same `date` artifact |
| ood-001 | question 0.153 | title chunk at 0.0 | all remaining tokens OOV; ranking is ingestion order of zeros |
| ood-002 | impact 0.164 | verdict 0.115 | less attracted to impact; still no reject path |
| ood-003 | verdict 0.701 alias 0.5 | verdict 0.570 alias 0.5 | trap still fires; morphology added `scope` from `scopes`; `scope` remains rank 2 with alias 0.35 |
| hop-001 | verdict 0.260 | `date` 0.350 alias 0.35 | not hop success |

Near-OOD did not become more confidently similar to impact. Alias-trap still fires. Far-OOD collapsed to a zero vector after stopword stripping, which is a diagnostic of the rewriter, not a reject metric.

## Cache and tracker

| Claim | Observation |
| --- | --- |
| Pass 1 cache hits | 0/12 |
| Pass 2 cache hits | 12/12 |
| Pass 2 ranks identical to pass 1 | true |
| Collisions (cosine ≥ 0.99, different text) | none |
| Unique keys | 12 |
| Ranking transparency | pass-1 `rank_all(rewritten)` matches cached pass-2 section_id order |

Pass-1 `rank_ns` is ~2e6 ns per row on this machine; pass-2 `rank_ns` is 0 (served from cache). Timing is secondary evidence that the skip path ran, not a ranking-quality metric.

The tracker flushed expansion frequencies without mutating rewrite rules. Most frequent identifier expansions were `regime_state` / `regime_state.get` (7) and the RegimeBoss/filename cluster (5). `thresholds` fired once (spec-002). `regime_stability` never fired.

## Why this matches the forensics warning

Producer-burial already said a general thesaurus would not contain `regime_stability`, and that identifier recovery via query expansion is a heterogeneous, corpus-specific bridge with blast radius. The locked IDF-capped segment rule recovered **the wrong family** of `regime_*` tokens (state/boss/filenames) because those are rarer in the 15-chunk vocab than the producer’s own names in the top-8 cut. Morphology did not need that cut and hit an in-vocab plural that actually lives in the gold chunk.

## Falsification checklist (from the preregistration)

- Little or no movement on sem-001 **and** spec-002 → **not triggered** (spec-002 moved)
- lex-001 is the only large gainer → **not triggered** (spec-002 was larger)
- Alias/slug fire explains a producer win → **not for spec-002**; **yes for several rank-1 `date` events**
- Guardrail rows leave top-k → **not triggered**, but sem-002/003 acquired a new wrong winner
- Cache changes first-pass ranks → **not triggered**
- TOP_K / golds / weights / chunks changed → **not triggered**

H-QRL as a **joint** claim (morphology **and** identifier expansion help producer burial without guardrail damage) is weakened. Split into two later hypotheses rather than patching qrl-v1 against these ranks.

## Deliberate non-actions after seeing results

This sprint did not:

- retune the function-word list, IDF cap, or segment rule
- add `regime_stability` by hand
- disable `date` slug-as-spaces
- rewrite YAML queries or golds
- implement dense embeddings (H1)
- mutate rewrite rules from tracker stats

## What a next experiment could ask (not implemented)

- Morphology-only ablation of qrl-v1 (keep spec-002, drop identifier dump).
- Identifier expansion that forbids filename tokens and tokens whose substrings match short `section_id` slugs.
- Existing H1: dense cosine with Jaccard/aliases/weights held fixed.

## References

- Preregistration: `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md`
- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Producer-burial forensics: `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
- Flag-off sanity: `eval_sets/runs/2026-10-06_run-001.jsonl`
- Experiment trace: `eval_sets/runs/2026-10-06_run-002.jsonl`
- Tracker: `eval_sets/runs/2026-10-06_run-002_query_loop.json`
