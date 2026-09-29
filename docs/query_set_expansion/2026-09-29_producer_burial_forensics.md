# Producer-section burial forensics (`producer-burial-v1`)

**Date:** 2026-09-29
**Status:** Forensic diagnosis. Retrieval behavior unchanged. Query-set bytes unchanged. Index bytes unchanged. Historical control traces unchanged.
**Control characterization:** `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` (commit `1a29488`)
**Preregistration:** `docs/query_set_expansion/2026-09-28_expanded_query_set_preregistration.md` (commit `ef1d33b`)
**Retriever freeze:** `retrieve.py` at `000e658`
**This document is diagnosis, not an intervention.** It records what the frozen retriever actually computes on three producer-target misses, then names one falsifiable next experiment. Nothing here was used to rewrite queries, golds, aliases, weights, or chunk boundaries.

The control already showed that three differently labeled probes bury the same section. It could not separate OOV, weak IDF, identifier tokenization, and competitor attraction. This sprint adds that separation from a one-off read-only reconstruction of the frozen TF-IDF/Jaccard path. No OOV fields were added to the logger.

## 1. Research question

Why does `1_upstream_producer_score_definition` remain buried at ranks 7–10 across semantic-gap, lexical-gap, and specificity probes?

More specifically: what evidence does each query provide for that producer chunk, what evidence do outranking chunks receive, which scoring components create the separation, and is the producer losing because relevant query information is absent from the TF-IDF representation, present but weakly weighted, or overpowered by generic shared vocabulary?

## 2. Frozen experimental state

Verified before analysis by hashing the files on disk and by reconstructing `rank_all()` against the live store. Live ranks and six-decimal scores matched `eval_sets/runs/2026-09-29_run-004.jsonl`. The control JSONL was not rewritten.

| Piece | Identity |
| --- | --- |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` (matches preregistration seal) |
| Index | `metadata/chunks.json`, 15 chunks, sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| Vocab size | 383 |
| Scoring | `0.7 * cosine(TF-IDF) + 0.3 * Jaccard(query, heading+text) + alias_boost` |
| Aliases | `question`, `verdict`, `impact_on_finding_3_5_disposition` only; `+0.5` substring, `+0.35` full slug-as-spaces |
| TOP_K | 5 |
| Analyzer | `embed.tokenize`: `[a-z0-9]+(?:[._][a-z0-9]+)*`; no stopwords, no stemmer, no camelCase split, snake_case and dotted ids kept whole |
| TF-IDF | Fitted on chunk `text` only; `tf = count / n_tokens`; IDF = `log((N+1)/(df+1)) + 1`; L2-normalized; OOV query tokens dropped |
| Control run | `eval_sets/runs/2026-09-29_run-004.jsonl` (run UUID `24e3b939-6aad-41e0-a47f-b8894b931d89`) |

`retrieve.py` scoring, weights, and alias table are unchanged since `000e658`. `run_query_set.py` later gained an `unmeasurable` outcome label; that does not change ranking.

### Target slice (frozen)

| Row | Failure-mode label | Control rank | Control score | Rank 1 |
| --- | --- | ---: | ---: | --- |
| `qse-docqa-sem-001` | semantic gap | 10/15 | 0.015352 | `verdict` (0.316521) |
| `qse-docqa-lex-001` | lexical gap | 7/15 | 0.037137 | `upstream_signals_since_verdict_independent` (0.143566) |
| `qse-docqa-spec-002` | specificity mismatch | 9/15 | 0.042792 | `verdict` (0.140694) |

Expected target for all three: `1_upstream_producer_score_definition`. Alias was 0.0 on every scored chunk of these three rows.

No fourth producer row was added after seeing results. No row was dropped because it behaved differently from the others.

## 3. Producer representation

Heading: `1. Upstream producer (score definition)`
Section id: `1_upstream_producer_score_definition`
Kind: `section`
Source: `data/2026-08-10_regime_factor_composition_trace.md` lines 23–42
`content_sha256`: `02de14342cbc6de21c04c3275fb31effc7f170a0c271a52b1d163fd4c01ff41a`

The human-readable chunk defines how the conviction regime score is computed: `vwap_dist` → rolling p95 → four labels `COMPRESS` / `EXPAND` / `TRANSITION` / `UNKNOWN` → `regime_stability` returned by `RegimeObserver.step`. That is the gold answer for all three probes.

What retrieval actually stores:

| Property | Value |
| --- | ---: |
| Characters | 1022 |
| Tokens in `text` | 98 |
| Unique tokens in `text` | 78 |
| Non-zero TF-IDF dimensions | 78 / 383 |
| Length rank in the 15-chunk corpus | 4th (behind impact, input_fields, consumer) |

Chunker `text` already prepends the heading, so Jaccard on `heading + text` does not add unique heading tokens for this section. The extra five heading tokens only repeat `1 / upstream / producer / score / definition`.

### What the source contains vs what the vector contains

The source mentions “regime” constantly, but almost always inside identifiers. The tokenizer does **not** split those identifiers. The fitted vocabulary therefore never sees a standalone `regime` token in this chunk.

Producer tokens that a human would read as “regime”:

| Surface in the note | Token actually stored | Standalone `regime`? |
| --- | --- | --- |
| `RegimeObserver.step` | `regimeobserver.step` | no |
| `regime_stability` | `regime_stability` | no |
| `config/regime_observer.yaml` | `regime_observer.yaml` | no |
| `VolatilityRegimeClassifier.update` | `volatilityregimeclassifier.update` | no |
| `RegimeBoss` | `regimeboss` | no |
| `utils/vol_regime.py` | `vol_regime.py` | no |

Standalone `regime` **does** occur in eight other chunks, including `verdict` (2), the consumer (6), impact (6), and `input_fields_consumed` (4). It is one of the two lowest-IDF terms in the fitted model (df=8, idf≈1.575), tied with `the`.

The producer’s highest TF-IDF raw weights are code-path tokens the three queries never use: `utils`, `vol_regime.py`, `window`, `regimeobserver.step`, `expand`, `p95`, line-number fragments (`l86`, `l133`, …). Distinctive content that *would* answer spec-002 (`compress`, `expand`, `transition`, `unknown`, `thresholds`, `p95`) is present in the vector and, for `expand` / `transition` / `unknown`, is unique to this chunk. None of the three queries emit those tokens.

Three layers must be kept separate:

1. **In the original chunk:** the definition of the upstream score, including the four-way label rule.
2. **In the retrieval representation:** a bag of undecomposed identifiers, table chrome (`item`, `location`), and a few prose words (`score`, `upstream`, `labels`, `stability`).
3. **Shared with each query:** one or two of those prose words. Not `regime`. Not the label set. Not `p95`.

The retriever does not see conceptual similarity. It sees token identity after this analyzer.

## 4. Per-row forensic analysis

### qse-docqa-sem-001

Query: *What does the regime-related score represent when it contributes to the conviction assessment?*

| Query evidence | Value |
| --- | --- |
| Tokens | `what does the regime related score represent when it contributes to the conviction assessment` (`the` twice) |
| Unique tokens | 13 |
| OOV unique | `assessment`, `contributes`, `related`, `represent` (4/13) |
| TF-IDF-active unique | `conviction`, `does`, `it`, `regime`, `score`, `the`, `to`, `what`, `when` |
| Exact intersection with producer | `{score}` |
| In-vocab query terms absent from producer | `conviction`, `does`, `it`, `regime`, `the`, `to`, `what`, `when` |
| Jaccard | 1/90 = 0.011111 |
| Cosine | 0.017169 (100% from `score`) |
| Alias | 0.0 |
| Final score | 0.015352 = `0.7*0.017169 + 0.3*0.011111` |
| Rank | 10/15; cosine rank 10; Jaccard rank 10 |

`regime` is the query’s load-bearing content word. It is in the fitted vocabulary (df=8) and is simply not in the producer vector. Cosine on the producer is a one-dimension match on heading `score` (df=5, one occurrence in 98 tokens). The OOV terms are conceptually central (*represent*, *contributes*, *related*, *assessment*) and are also absent from the producer, so putting them into the vocabulary without putting them into the chunk would not create a bridge.

This is not a near-miss. Nine chunks score higher. Five chunks score 0.0.

### qse-docqa-lex-001

Query: *Which upstream market-condition measure supplies the consistency signal used when assessing trade confidence?*

| Query evidence | Value |
| --- | --- |
| Unique tokens | 14 |
| OOV unique | `assessing`, `condition`, `confidence`, `consistency`, `market`, `measure`, `signal`, `supplies`, `trade`, `which` (10/14) |
| TF-IDF-active unique | `the`, `upstream`, `used`, `when` |
| Exact intersection with producer | `{upstream}` |
| In-vocab query terms absent from producer | `the`, `used`, `when` |
| Jaccard | 1/91 = 0.010989 |
| Cosine | 0.048343 (100% from `upstream`) |
| Alias | 0.0 |
| Final score | 0.037137 |
| Rank | 7/15; cosine rank 7; Jaccard rank 8 |

The lexical-gap design worked as a closed-vocab stress: the semantic payload of the query is almost entirely OOV. The producer *does* contain `stability` (2), `vwap_dist` (2), `score` (1), and `p95` (2) — the note’s own names for “consistency signal” and “market-condition measure” — but the query does not use those names. The only surviving bridge is heading `upstream` (df=2). That token also occurs once in the rank-1 neighbor `upstream_signals_since_verdict_independent`.

Preserving the OOV terms in the vectorizer would not connect this query to the producer. Those strings are not in the chunk. The missing information is correspondence, not coverage of an already-present token.

### qse-docqa-spec-002

Query: *Which four labels can the percentile-threshold rule assign, including the in-between and missing-data cases?*

| Query evidence | Value |
| --- | --- |
| Unique tokens | 16 |
| OOV unique | `assign`, `between`, `cases`, `data`, `four`, `including`, `percentile`, `rule`, `threshold`, `which` (10/16) |
| TF-IDF-active unique | `and`, `can`, `in`, `labels`, `missing`, `the` |
| Exact intersection with producer | `{and, labels}` |
| In-vocab query terms absent from producer | `can`, `in`, `missing`, `the` |
| Jaccard | 2/92 = 0.021739 |
| Cosine | 0.051815 (`labels` 0.033456 + `and` 0.018359) |
| Alias | 0.0 |
| Final score | 0.042792 |
| Rank | 9/15; cosine rank 9; Jaccard rank 8 |

The producer is the only chunk that contains the four-way set `COMPRESS` / `EXPAND` / `TRANSITION` / `UNKNOWN` and the only chunk with `expand`, `transition`, and `unknown`. The query never names them. Hyphen splitting yields `percentile` / `threshold` / `between` / `data`, all OOV. The corpus has `thresholds` (plural, df=3, two of them in the producer) and `p95`, not `threshold` or `percentile`. Analyzer mismatch is real here, but even a stemmer would not map `in-between` → `TRANSITION` or `missing-data` → `UNKNOWN`.

`labels` is a genuine shared content word (df=2). It also occurs once in `upstream_signals_since_verdict_independent` (“ticker labels”), which is not the four-way percentile rule. Shared `labels` is therefore not a unique pointer at the producer.

## 5. Competitor analysis

### sem-001 — why `verdict` beats the producer

| Evidence | Producer | `verdict` (rank 1) |
| --- | ---: | ---: |
| rank | 10 | 1 |
| final score | 0.015352 | 0.316521 |
| cosine | 0.017169 | 0.398602 |
| Jaccard | 0.011111 | 0.125000 |
| alias | 0.0 | 0.0 |
| exact shared terms | `{score}` | `{conviction, does, it, regime, score, the}` |
| TF-IDF terms that actually contribute | `score` only | `the` (0.181), `it` (0.083), `does` (0.041), `regime` (0.036), `conviction` (0.029), `score` (0.029) |
| OOV query terms | 4 | same query OOV; unused by both |

Score gap 0.301169 ≈ `0.7*(0.381432) + 0.3*(0.113889)`. Cosine accounts for 0.267 of the gap (89%); Jaccard 0.034 (11%). Alias 0.

The frozen scorer prefers `verdict` because that chunk contains the query’s standalone `regime` (quoted as the conviction factor name), plus `the` five times in 51 tokens, plus `conviction` / `score` / `does` / `it`. The producer contains none of `regime` / `the` / `conviction`. This is not “verdict is semantically closer to the definition.” It is token co-occurrence with a shorter, more prosaic chunk.

`question` at rank 2 is the same mechanism on a 19-token field: Jaccard 0.142857 from `{does, it, regime, the}`. Ranks 3–9 all share some of `{regime, the, conviction, score}` that the producer lacks. The parent heading-only chunk `code_path_producer_stamp_consumer` scores 0.0.

### lex-001 — why `upstream_signals_since_verdict_independent` beats the producer

| Evidence | Producer | Signals chunk (rank 1) |
| --- | ---: | ---: |
| rank | 7 | 1 |
| final score | 0.037137 | 0.143566 |
| cosine | 0.048343 | 0.189788 |
| Jaccard | 0.010989 | 0.035714 |
| alias | 0.0 | 0.0 |
| exact shared terms | `{upstream}` | `{the, upstream, used}` |
| TF-IDF terms that actually contribute | `upstream` only | `used` (0.092), `upstream` (0.058), `the` (0.040) |

Score gap 0.106429 ≈ `0.7*0.141445 + 0.3*0.024725`. Cosine 93% of the gap; Jaccard 7%.

Rank 1 is the lexical neighbor predicted at preregistration. Both chunks contain `upstream` once. The signals chunk also contains `used` twice and `the` twice; the producer contains neither. Cosine therefore prefers the neighbor even on the one distinctive surviving term’s family of leftovers. `verdict` at rank 2 is almost entirely `the` (cosine contribution 0.140 from five occurrences; no `upstream`).

### spec-002 — why `verdict` beats the producer, and why other leftovers outrank it

| Evidence | Producer | `verdict` (rank 1) |
| --- | ---: | ---: |
| rank | 9 | 1 |
| final score | 0.042792 | 0.140694 |
| cosine | 0.051815 | 0.193338 |
| Jaccard | 0.021739 | 0.017857 |
| alias | 0.0 | 0.0 |
| exact shared terms | `{and, labels}` | `{the}` |
| TF-IDF terms that actually contribute | `labels` + `and` | `the` only (0.193) |

Score gap 0.097901 ≈ `0.7*0.141523 + 0.3*(-0.003882)`. Cosine over-explains the gap (0.099). **Jaccard slightly prefers the producer over `verdict`.** The blend still ranks `verdict` first because 0.7 × “`the` in a short chunk” dominates 0.3 × a two-token Jaccard edge.

Other material competitors are incidental in-vocab leftovers, not COMPRESS-family attractors:

- Rank 2 `input_fields_consumed`: unique-corpus token `can` (df=1) plus `and` / `in` / `the`. Hypothesis fear that the impact COMPRESS mention would win is not what happened; impact is rank 4.
- Rank 4 `impact_on_finding_3_5_disposition`: cosine from `the` (5×), `missing` (the triage file “missing at write time”), and `in`. `missing` here is not the UNKNOWN label.
- Rank 5 signals chunk: `labels` + `the`, same `labels` token the producer has, in a slightly shorter bag, so `labels` contributes *more* cosine to the neighbor (0.040 vs 0.033).

The overspecific probe did not fail as right-family / wrong-child ranking. The gold never entered the top of the family. Impact was not rank 1.

## 6. Score decomposition

`cosine_contribution = 0.7 * cosine`, `lexical_contribution = 0.3 * Jaccard`, `alias_contribution = 0`.

| Row | Producer 0.7·cos | Producer 0.3·Jac | Rank-1 0.7·cos | Rank-1 0.3·Jac | Cosine gap vs rank 1 | Jaccard gap vs rank 1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sem-001 | 0.012019 | 0.003333 | 0.279021 | 0.037500 | +0.267003 to rank 1 | +0.034167 to rank 1 |
| lex-001 | 0.033840 | 0.003297 | 0.132851 | 0.010714 | +0.099011 to rank 1 | +0.007418 to rank 1 |
| spec-002 | 0.036270 | 0.006522 | 0.135336 | 0.005357 | +0.099066 to rank 1 | **−0.001165 (producer)** |

Ordering agreement:

- **sem-001:** cosine and Jaccard agree. Both put the producer at rank 10. Jaccard does not reverse a correct cosine order; it reinforces the burial.
- **lex-001:** cosine rank 7, Jaccard rank 8. Jaccard slightly worsens producer position. Both components put the signals chunk first. No reversal of rank 1.
- **spec-002:** cosine rank 9, Jaccard rank 8. Jaccard slightly helps the producer and **does reverse `verdict` vs producer** (verdict Jaccard rank 11). The 0.7 cosine weight restores `verdict` to rank 1. Jaccard’s own rank 1 is `question` (0.060606), still not the producer.

These are representation failures, not blend failures. The producer is not competitive on cosine in any of the three rows (cosines 0.017 / 0.048 / 0.052 vs rank-1 cosines 0.399 / 0.190 / 0.193). Reweighting 0.7 / 0.3 cannot lift ranks 7–10 into top-5 on this evidence: even 100% Jaccard would leave sem-001 and lex-001 at ~0.011, far below current rank-5 scores, and spec-002’s Jaccard rank is already 8.

Alias never participates.

## 7. Vocabulary / OOV analysis

| Row | Unique query terms | OOV | OOV are central? | In-vocab overlap with producer | Distinctive producer terms the query did not use |
| --- | ---: | ---: | --- | --- | --- |
| sem-001 | 13 | 4 | yes (`represent`, `contributes`, `related`, `assessment`) | `{score}` | `regime_stability`, `regimeobserver.step`, `vwap_dist`, identifier-bound `regime*` |
| lex-001 | 14 | 10 | yes (almost the whole ask) | `{upstream}` | `stability`, `vwap_dist`, `score`, `p95` |
| spec-002 | 16 | 10 | yes (`percentile`, `threshold`, `four`, `between`, `data`) | `{labels, and}` | `compress`, `expand`, `transition`, `unknown`, `thresholds`, `p95` |

OOV is not one story:

### Vocabulary coverage

Real for spec-002’s `threshold` vs stored `thresholds`, and for sem-001’s standalone `regime` vs stored `regime_stability` / `regimeobserver.step`. Those tokens exist in the producer under a different analyzer segmentation. A stemmer or identifier splitter would recover some of that without a new embedding space.

Not sufficient for lex-001: `consistency` / `market` / `confidence` are not alternate segmentations of producer tokens.

### Weighting

Not the primary burial. The shared terms that exist (`score`, `upstream`, `labels`) are used. They are too few, and on spec-002 `labels` is shared with a neighbor. The spec-002 `the`-driven verdict win is a secondary length/TF effect on a leftover function word, not a failure to upweight a strong producer match.

### Semantic correspondence

Load-bearing for all three, strongest for lex-001:

| Query wording | Producer wording | Same tokenizer token? |
| --- | --- | --- |
| regime-related score | `regime_stability` / `RegimeObserver.step` | no |
| conviction assessment | heading “score definition”; no `conviction` | no |
| consistency signal | `stability` / `regime_stability` | no |
| market-condition measure | `vwap_dist` / p95 window | no |
| trade confidence | conviction factor (not in this chunk) | no |
| percentile-threshold rule | `p95` vs compress/expand `thresholds` | no |
| in-between / missing-data cases | `TRANSITION` / `UNKNOWN` | no |
| four labels | `COMPRESS` / `EXPAND` / `TRANSITION` / `UNKNOWN` | no |

### Competition

Also present on all three, using whatever in-vocab residue remains:

- sem-001: high-df prose `regime` and `the` in `verdict` / `question` / impact / consumer.
- lex-001: `upstream` + `used` + `the` in the signals neighbor.
- spec-002: `the` in `verdict`; `can` in input_fields; `missing` in impact; `labels` in the signals chunk.

**Would restoring OOV terms alone plausibly connect query to producer?** No. The OOV strings are not in the producer bag. Connection requires either (a) exposing identifier pieces already in the chunk, (b) mapping query synonyms onto producer tokens, or (c) a representation that scores correspondence without token identity.

## 8. Cross-row mechanism

**Outcome D, with a shared Outcome A core.**

The shared property is not the YAML `failure_mode` label. It is:

> After the frozen analyzer, these three queries and the producer chunk have essentially no usable token identity. Cosine and Jaccard both see one or two weak leftover words. Other chunks, written in prose, own the leftover in-vocab terms (`regime`, `the`, `used`, `can`, `missing`).

That is a **common representation failure** (absent lexical/TF-IDF bridge), not a common weighting failure. The producer is not a competitive cosine document that Jaccard then buries.

Row-specific overlays are evidence, not noise:

| Row | Overlay on the shared core |
| --- | --- |
| sem-001 | Identifier non-decomposition: the note’s “regime” lives in bound tokens; competing chunks use standalone `regime`. OOV verbs cannot help. Deep miss (rank 10, margin −0.30). |
| lex-001 | Closed-vocab synonymy: query payload is 10/14 OOV; producer’s own names (`stability`, `vwap_dist`) are unused. Lexical neighbor wins the one surviving content token plus `used`. Rank 7. |
| spec-002 | Morphological miss (`threshold`/`thresholds`) plus label-set paraphrase, plus function-word competition (`the`, `can`, `missing`). Jaccard would slightly prefer producer to `verdict`; cosine does not. Rank 9. |

Contrast with other semantic-gap rows in the same control: `sem-002` and `sem-003` also say “regime”, but their gold chunks (`impact_on_finding_3_5_disposition`, `3_conviction_factor_entry_the_field_under_audit`) contain standalone `regime` six times each. Those rows hit at rank 2. Semantic-gap as a label is not one mechanism; producer burial is specifically this chunk’s token form.

**Strongest competing explanation:** common competitor attraction to `verdict` via `regime`/`the`. It is real for sem-001 and spec-002 rank 1, and it is the control’s most frequent rank-1 event overall. It does **not** explain lex-001 (rank 1 is the signals neighbor, not `verdict`), and it does not explain why the producer’s own distinctive tokens never enter the query vectors. Verdict-default is the overlay when leftover query tokens are generic prose; it is not the reason the producer scores ~0.02–0.05.

## 9. Intervention-family comparison

Evaluated only after the row-level evidence. None implemented.

### BM25 / alternative sparse weighting

**Partially supported, not as the first hypothesis for this slice.**

Supported fragment: spec-002’s rank-1 is saturated TF of `the` in a short `verdict` chunk. Length-normalized sparse scoring could shrink that artifact.

Unsupported as the shared fix: BM25 cannot invent tokens. sem-001 would still match only `score`; lex-001 only `upstream`. The neighbor that already contains `upstream`+`used` would likely remain preferred. Blast radius would be all sparse ranking, including current `evaluate.py` high-overlap queries, without a demonstrated producer bridge.

An **analyzer change** (split snake_case/camelCase; light stemming) is a related sparse-representation move, not a reweighting. It is the narrowest way to recover sem-001 `regime` from `regime_stability` / `RegimeObserver` and spec-002 `threshold` from `thresholds`. It still leaves lex-001’s `consistency`/`confidence`/`market-condition` unmapped. Because the target slice is all three rows, analyzer-only is not the first experiment.

### Dense semantic representation

**Supported as the family that matches the shared core.**

All three queries are conceptually aligned with the producer: score definition, upstream market-condition stability measure, four-way percentile label set. Correspondence uses different surface vocabulary. The lexical bridge is absent or one leftover word. A representation that can score that correspondence can in principle move all three ranks.

Blast radius is wide: every query’s candidate scores change. Near-domain OOD (`ood-002`, RegimeBoss/COMPRESS wording) may become more confidently similar to impact. Exact-term strengths on `evaluate.py` and on the rank-2 semantic hits must be guarded, not assumed.

### Query expansion

**Supported only as heterogeneous, corpus-specific bridges — poor first experiment under the no-overfit rule.**

A small bridge *would* connect each row *separately*:

- sem-001: `regime` → identifier pieces / `regime_stability`
- lex-001: `consistency` → `stability`; `market-condition` → `vwap_dist`
- spec-002: `percentile-threshold` → `p95`/`thresholds`; in-between/missing → `TRANSITION`/`UNKNOWN`

That is three different expansions, two of which encode this note’s private names. Phase 11 forbids query-specific rules and manually added vocabulary. A general thesaurus is unlikely to contain `regime_stability` or `vwap_dist`. Blast radius: false positives from broader queries, plus leakage of corpus knowledge into the retriever.

### Scoring-weight adjustment

**Not supported.** The producer is not competitive on component scores. spec-002 is the only row where Jaccard disagrees with cosine on `verdict`, and even there Jaccard rank of the producer is 8. Tuning 0.7/0.3 to pass these three rows would overfit the diagnostic set.

### Late reranking

**Incapable of observing the target.** Control ranks 10, 7, 9 with TOP_K=5. A top-5 reranker never sees the producer. Do not propose it for this slice. (It remains relevant later for sem-002/sem-003 rank-1 vs rank-2, which is a different locus.)

## 10. Selected experimental hypothesis

**H1:** Because the three producer probes share an absent token-level bridge — conceptually aligned wording that the frozen analyzer/TF-IDF/Jaccard path does not share with `1_upstream_producer_score_definition` — introducing a dense semantic representation for the cosine term, while holding Jaccard, aliases, blend weights, TOP_K, chunk boundaries, and the query set fixed, should cause positive rank movement for sem-001, lex-001, and spec-002 while preserving high-overlap exact-term behavior on the guardrail slice.

This tests representation of correspondence, not a new alias, not a producer boost, and not a weight search.

## 11. Target slice

| Row | Frozen control rank | Frozen control score | Frozen rank 1 |
| --- | ---: | ---: | --- |
| `qse-docqa-sem-001` | 10 | 0.015352 | `verdict` |
| `qse-docqa-lex-001` | 7 | 0.037137 | `upstream_signals_since_verdict_independent` |
| `qse-docqa-spec-002` | 9 | 0.042792 | `verdict` |

Primary evidence is rank movement (`rank_gain = control_rank - experiment_rank`), not hit-rate. Movement into TOP_K=5 is the strongest supporting pattern but is not required to treat a consistent upward move as evidence for H1.

## 12. Guardrails

Do not declare H1 successful from producer ranks alone.

| Guardrail | Control observation to preserve |
| --- | --- |
| `qse-docqa-sem-002` | rank 2 hit, margin −0.013370 vs `verdict` |
| `qse-docqa-sem-003` | rank 2 hit, margin −0.011192 vs `verdict` |
| `qse-docqa-lex-002` | rank 4 hit (`2_state_stamp_before_conviction`) |
| `qse-docqa-mch-001` stamp | rank 5 (in top-k); consumer rank 6 remains a conjunction observation |
| `evaluate.py` gold queries | question / verdict / Finding 3.5 still in top-3 |

Also keep **diagnostic observation** (not scored reject metrics) of:

- near-OOD `qse-docqa-ood-002` (impact currently rank 1 at 0.164)
- alias-trap `qse-docqa-ood-003` (`verdict` rank 1 at 0.700 with `alias=0.5`; `scope` rank 2 with `alias=0.35`)

H1 must not “win” producer rows by stuffing aliases into in-scope queries, and must not be judged solely by making near-OOD look more like an in-domain hit.

## 13. Expected signature

Evidence that would support H1:

- Positive rank gain on **all three** producer-target rows, not one lucky row.
- Ideally all three enter TOP_K=5, so a later reranker could even see them; entry into top-5 is supporting detail, not the definition of success.
- Guardrail rows stay hits at comparable ranks (sem-002/003 remain ≤ rank 2 or still in top-k with no large margin collapse against a new wrong winner; lex-002 remains in top-k; `evaluate.py` still PASSes).
- Alias remains 0.0 on the in-scope measurable producer rows (improvement is not an accidental slug/alias fire).
- Cosine, not a new Jaccard artifact, should be the component that moves the producer if the hypothesized mechanism is semantic correspondence.

## 14. Falsification criteria

H1 is weakened or rejected if:

- Producer rows show little or no rank movement (dense cosine still ~0 relative to competitors).
- Only one row improves, especially if that row is spec-002 via incidental down-weighting of `the` rather than correspondence to the label set — that would support a weighting story, not H1’s shared mechanism.
- Analyzer-like side effects (stopword dropping, identifier splitting) are introduced alongside dense vectors and are the actual source of movement; that would be a different hypothesis.
- Guardrail rows regress substantially (sem-002/003 leave top-k; lex-002 leaves top-k; `evaluate.py` FAILs).
- Near-OOD becomes materially more pathological (much higher confident scores on impact/RegimeBoss wording without a reject path).
- Alias-trap scores inflate further in a way that contaminates in-scope ranking.
- Observed “gains” come from an unrelated scoring artifact (changed TOP_K, changed gold, changed aliases, changed 0.7/0.3, rebuilt chunks with different boundaries).

Do not define success as “more hits” globally. The control hit rate is not an optimization target.

## 15. Deliberate non-actions

This sprint did not:

- modify query wording, expected targets, or primary failure-mode labels
- add synonyms to the corpus or rewrite the producer chunk
- alter chunk boundaries, aliases, 0.7/0.3 weights, TOP_K, or TF-IDF parameters
- add query-specific rules or producer-specific boosts
- implement BM25, dense embeddings, query expansion, reranking, OOD rejection, hop control, or GraphRAG
- run parameter searches or bake-off several retrievers against these three rows
- add OOV/token-overlap fields to the production logger
- rerun `run_query_set.py` (that would append a new JSONL); control traces were read, not replaced
- commit the disposable forensic reconstruction scripts used to compute the tables above

The diagnostic rows remain evidence, not a leaderboard. H1 is not implemented here.

## References

- Control characterization: `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`
- Preregistration: `docs/query_set_expansion/2026-09-28_expanded_query_set_preregistration.md`
- Frozen baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Failure-mode map: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Raw control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
- Retriever: `retrieve.py` (`COSINE_WEIGHT=0.7`, `LEXICAL_WEIGHT=0.3`, `SECTION_ALIASES`)
- Analyzer / TF-IDF: `embed.py`
