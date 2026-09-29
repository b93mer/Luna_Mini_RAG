# Expanded frozen-control characterization (`expanded-control-v1`)

**Date:** 2026-09-28 (run executed 2026-09-29T04:03:46Z; the logger names run files by UTC date)
**Status:** Control characterization. Retrieval behavior unchanged. Query-set bytes unchanged since preregistration.
**Preregistration:** `docs/query_set_expansion/2026-09-28_expanded_query_set_preregistration.md` (commit `ef1d33b`)
**This document is observation.** Predictions stay in the preregistration. Contradictions are recorded here; they do not rewrite `eval_sets/docqa.yaml`.

The three calibration anchors reproduced the frozen ranks exactly. That is a hard-stop check, not a new finding.

## Experimental state

| Piece | Identity |
| --- | --- |
| Control name | `expanded-control-v1` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` (matches the preregistration seal) |
| Retriever | Frozen hybrid in `retrieve.py` at `000e658`; this sprint did not edit it |
| Scoring | `0.7 * cosine(TF-IDF) + 0.3 * Jaccard(query, heading+text) + alias_boost` |
| TOP_K | 5 |
| Index | `metadata/chunks.json`, 15 chunks, sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` (matches the 2026-09-28 baseline) |
| Run UUID | `24e3b939-6aad-41e0-a47f-b8894b931d89` |
| Raw trace | `eval_sets/runs/2026-09-29_run-004.jsonl` |
| Row count | 12 |
| Measurable | 7 (`expected` non-empty; unique-target or multi-target membership is defined) |
| Unmeasurable | 5 (empty `expected`; outcome `unmeasurable`) |
| Calibration check vs `2026-09-29_run-003.jsonl` | sem-001 / sem-002 / lex-001 hits and `expected_targets` identical |

`top_margin` is derived, not logged: `expected_target_score - rank_1_score`. Zero means the target is rank 1. Negative means the target lost to rank 1. For `qse-docqa-mch-001`, margins are per target.

Future experiment comparison (not computed here, no experiment exists):

`rank_gain = control_rank - experiment_rank`

Examples: `10 → 4` is `+6`; `2 → 3` is `-1`; `2 → 2` is `0`.

## Preregistered expectations (preserved)

Locked mix from the preregistration, before this run:

| Mode | supported | expected_miss | unmeasurable |
| --- | ---: | ---: | ---: |
| semantic gap | 0 | 3 | 0 |
| lexical gap | 0 | 2 | 0 |
| specificity mismatch | 0 | 1 | 1 |
| multi-chunk | 0 | 1 | 0 |
| out-of-domain | 0 | 0 | 3 |
| multi-hop | 0 | 0 | 1 |
| **total** | **0** | **7** | **5** |

Observed measurable outcomes: `hit=3`, `expected_miss=4`, `miss=0`. Unmeasurable: 5, as predicted. Global hit rate is not an optimization target.

## Results table (measurable rows)

Scores from the JSONL (6 decimal places). `top_margin = target_score - rank_1_score`.

| row | failure_mode | prediction | outcome | target_rank | target_score | rank_1 | rank_1_score | top_margin | cosine | lexical | alias |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| qse-docqa-sem-001 | semantic gap | expected_miss | expected_miss | 10/15 | 0.015352 | verdict | 0.316521 | -0.301169 | 0.017169 | 0.011111 | 0.0 |
| qse-docqa-sem-002 | semantic gap | expected_miss | hit | 2/15 | 0.250598 | verdict | 0.263968 | -0.013370 | 0.337091 | 0.048780 | 0.0 |
| qse-docqa-sem-003 | semantic gap | expected_miss | hit | 2/15 | 0.312499 | verdict | 0.323691 | -0.011192 | 0.396006 | 0.117647 | 0.0 |
| qse-docqa-lex-001 | lexical gap | expected_miss | expected_miss | 7/15 | 0.037137 | upstream_signals_since_verdict_independent | 0.143566 | -0.106429 | 0.048343 | 0.010989 | 0.0 |
| qse-docqa-lex-002 | lexical gap | expected_miss | hit | 4/15 | 0.074985 | input_fields_consumed | 0.133715 | -0.058730 | 0.093297 | 0.032258 | 0.0 |
| qse-docqa-spec-002 | specificity mismatch | expected_miss | expected_miss | 9/15 | 0.042792 | verdict | 0.140694 | -0.097902 | 0.051815 | 0.021739 | 0.0 |
| qse-docqa-mch-001 stamp | multi-chunk | expected_miss | expected_miss | 5/15 | 0.149995 | verdict | 0.240438 | -0.090443 | 0.187905 | 0.061538 | 0.0 |
| qse-docqa-mch-001 consumer | multi-chunk | expected_miss | expected_miss | 6/15 | 0.137716 | verdict | 0.240438 | -0.102722 | 0.164129 | 0.076087 | 0.0 |

`mch-001` is one row. Hit requires **both** targets in top-k. Stamp is in top-k; consumer is rank 6. Conjunction fails. Per-target numbers are not collapsed.

## Unmeasurable rows

Unique-target hit/miss is not defined. Retrieval still ran. Rank-1 is diagnostic, not a gold.

| row | why unmeasurable | rank_1 | rank_1_score | alias | diagnostic note |
| --- | --- | --- | ---: | ---: | --- |
| qse-docqa-spec-001 | underspecific; no unique gold | verdict | 0.284342 | 0.0 | top-k mixes conviction-path chunks (`verdict`, consumer) with RegimeBoss/Finding (`impact`) and the title chunk |
| qse-docqa-ood-001 | far OOD; no reject path | question | 0.152704 | 0.0 | residual non-zero top-k; short field chunks (`question`, `scope`, `triage_under_discussion`) occupy ranks 1–3 |
| qse-docqa-ood-002 | near OOD; no reject path | impact_on_finding_3_5_disposition | 0.164078 | 0.0 | mention of RegimeBoss/COMPRESS ranks first; that chunk does not contain the decision procedure |
| qse-docqa-ood-003 | alias-trap OOD; no reject path | verdict | 0.700506 | 0.5 | `verdict` substring fired `+0.5`. `scope` is rank 2 at 0.412246 with `alias=0.35` because `scope` is a substring of `scopes` |
| qse-docqa-hop-001 | no hop controller; empty expected | verdict | 0.260290 | 0.0 | consumer (hop-1 site) is rank 4; stamp is not in top-5. A single-pass consumer hit would still not be hop success |

Do not convert these rank-1 identities into a reject metric. There is still no gate.

## Prediction vs observation contradictions

Predictions were not edited. These are map corrections in this document only.

1. **`qse-docqa-sem-002`** — already contradicted on the three-row baseline (rank 2 hit). Locked prediction remains `expected_miss`. Reproduced here exactly (margin -0.013370).
2. **`qse-docqa-sem-003`** — predicted `expected_miss`; observed **hit at rank 2**. Verdict still rank 1, alias 0.0, as the failure signature expected for competition — but the consumer target was competitive, not absent. Target cosine (0.396006) even exceeded verdict cosine (0.390987); verdict won on Jaccard (0.166667 vs 0.117647).
3. **`qse-docqa-lex-002`** — predicted `expected_miss`; observed **hit at rank 4**. The stamp section was not buried outside top-k. Rank 1 is still the wrong section (`input_fields_consumed`). Closed-vocab substitution did not win; it also did not fail as a deep miss.

Matched predictions: sem-001, lex-001, spec-002, mch-001 (all `expected_miss`), and all five `unmeasurable` rows.

No measurable row produced an unpredicted `miss` (`supported` predicted, then failed). None were predicted `supported`.

## Row-level findings

### qse-docqa-sem-001 — deep miss, prediction matched

Conviction-sense query. Target producer rank **10/15**, margin **-0.301**. Rank 1 `verdict`. Alias 0.0. This is not a near-miss. The expected section is in the tail. A later top-5 reranker would not see it.

### qse-docqa-sem-002 — competitive hit, prediction already contradicted

RegimeBoss-sense query. Target rank **2/15**, margin **-0.013370**. Same structure as the baseline: `verdict` barely ahead, no alias. Representation already has the gold in the candidate set.

### qse-docqa-sem-003 — competitive hit, new contradiction

GATE:REGIME vs RegimeBoss. Target rank **2/15**, margin **-0.011192**. Structurally the same as sem-002, different gold (consumer vs impact). Cosine favored the gold; the blend did not. Failure signature **partially** matched (verdict default, alias 0) and **failed** on “target outside top-k.”

### qse-docqa-lex-001 — lexical near-miss, prediction matched

Producer gold rank **7/15**, margin **-0.106**. Rank 1 is `upstream_signals_since_verdict_independent` (shared “upstream” / “signals” surface, wrong section). Matches the preregistered lexical-neighbor signature. Outside top-k; a top-5 reranker would not see the gold.

### qse-docqa-lex-002 — shallow hit, new contradiction

Stamp gold rank **4/15**, margin **-0.058730**. In top-k, not rank 1. Rank 1 `input_fields_consumed`. Lexical gap is not one depth. This probe is a ranking/separation miss inside top-k, not a tail miss.

### qse-docqa-spec-001 — unmeasurable mix, diagnostic matched

“What is the regime?” Rank 1 `verdict` (0.284). Top-5 includes both conviction-path and Finding/RegimeBoss chunks, plus the title. No unique gold was invented.

### qse-docqa-spec-002 — deep-ish miss, prediction matched

Overspecific producer ask. Target rank **9/15**, margin **-0.098**. Rank 1 `verdict`, not the COMPRESS-mention impact section that was the main feared attractor (impact is rank 4). The narrow ask did not surface the step-3 label set. Grain mismatch here looks like **the same producer-chunk burial** seen in sem-001 and lex-001, not like a right-family/wrong-child rerank problem. That is an observation about where the miss landed, not a relabel of the row.

### qse-docqa-mch-001 — conjunction miss at the cutoff

Stamp rank 5 (in top-k), consumer rank 6 (one below cutoff). Rank 1 `verdict`. Evidence for both ends is near the cutoff, not in the tail. Failure is **all-in-topk**, not “neither chunk exists.” If TOP_K were 6 this would flip to hit; that cutoff sensitivity is recorded, not used to change TOP_K.

### qse-docqa-ood-001 — far OOD still fills top-k

Rank 1 `question` at 0.153, alias 0. Short metadata chunks dominate. Not a confident in-domain-looking hit compared with ood-003.

### qse-docqa-ood-002 — near OOD looks more on-topic

Rank 1 is the impact section (0.164), which *mentions* RegimeBoss COMPRESS-on-high-RV and does not explain it. Near-OOD is more convincing than far-OOD without being a valid answer. Scores are only slightly above far-OOD in this pair (0.164 vs 0.153). N=1 each; do not generalize the delta.

### qse-docqa-ood-003 — alias trap, plus an extra `scope` fire

Rank 1 `verdict` at **0.700506** with `alias=0.5`. Reconstructs as `0.7*0.268945 + 0.3*0.040816 + 0.5`. Far-OOD rank-1 was 0.153. The trap makes an irrelevant chunk look like a high-confidence hit.

Additional observation, not in the preregistration: rank 2 `scope` has `alias=0.35` because `section_id.replace("_"," ")` is `scope`, which is a substring of `scopes` in “Scopes trial.” The `+0.35` rule is not limited to the three-row alias table. This is extra trap surface, not a reason to edit aliases in this sprint.

### qse-docqa-hop-001 — boundary holds

Consumer (the hop-1 write site) is rank 4. Stamp is absent from top-5. Even if this row were mis-scored as multi-chunk, it would miss. It is still **unmeasurable as multi-hop**: a single ranking cannot be hop success. No hop controller was added.

## Slice-level findings

N is 1–3 per slice. This is diagnostic structure, not statistical confidence.

### Semantic gap (N=3)

Not homogeneous. Two competitive rank-2 hits (sem-002, sem-003) with ~0.01 margins and a **verdict** winner; one deep miss (sem-001, rank 10, margin -0.30) on the **producer** gold. Alias never fired. Cosine dominates the competitive pair; on sem-003 cosine actually preferred the gold and Jaccard reversed it.

The slice supports “miss is not one state.” It does **not** support a single embedding swap as the obvious fix for all three.

### Lexical gap (N=2)

Not homogeneous. lex-001 is a tail miss (rank 7) with a lexical neighbor at rank 1. lex-002 is a top-k hit (rank 4) with a different wrong winner (`input_fields_consumed`). Closed vocabulary hurt both; it did not bury both.

### Specificity (N=2, one unmeasurable)

Underspecific: mix of families, as hypothesized. Overspecific: producer rank 9, similar depth to other producer-target misses. Route L (rerank right-family/wrong-grain) is weakly supported here because the gold never entered the family at the top; impact was not the winner.

### Multi-chunk (N=1)

Both targets are near TOP_K (5 and 6). This looks like cutoff/conjunction, not missing representation of either chunk. Do not call it multi-hop.

### OOD diagnostics (N=3, all unmeasurable)

Far: low residual scores, short-chunk residue. Near: on-topic wrong section. Alias-trap: order-of-magnitude higher score from a constant boost. The three slices are distinguishable in this run. They still cannot be scored as reject.

### Multi-hop (N=1, unmeasurable)

Marks an evaluation boundary. The originating query retrieved a plausible hop-1 chunk at rank 4. That must not be read as hop coverage.

## Global findings

- Calibration anchors did not move: 10 / 2 / 7.
- Query-set and index hashes matched the seal and the frozen baseline.
- 3 measurable hits, 4 expected misses, 0 unexpected misses, 5 unmeasurable.
- 2 of 3 hits were predicted misses (plus the already-known sem-002).
- Rank 1 is `verdict` on 7 of 12 rows (sem-001/002/003, spec-001/002, mch-001, hop-001), and on ood-003 via alias. Verdict-default is the most repeated rank-1 event in this set.
- Every **measurable miss** either targets `1_upstream_producer_score_definition` at ranks 7–10, or fails multi-chunk conjunction at ranks 5–6.
- Alias was 0.0 on every in-scope measurable row. It dominated only the alias-trap OOD row (and `scope` via the `+0.35` slug rule).

Do not treat 3/7 as system accuracy.

## Candidate generation vs ranking

**Competitive targets (ranks 2–5):** sem-002 (2), sem-003 (2), lex-002 (4), mch-001 stamp (5). The gold is already in the scored set near the top. Failure, when it still exists, is separation from rank 1 (usually `verdict`) or conjunction at the cutoff. A mechanism that only reorders a shortlist **can** see these.

**Deep targets (well outside top-k):** sem-001 (10), spec-002 (9), lex-001 (7). All three golds are the **producer** section. A top-5 reranker **cannot** see them. That points upstream: representation, vocabulary, chunk grain, or candidate generation — not a shortlist reorder.

**Boundary:** mch-001 consumer at rank 6 is one place outside TOP_K. Not “deep” in the rank-10 sense.

Do not assign a solution from this split. It constrains **where** a later intervention could act.

## Candidate load-bearing mechanisms

No numerical load-bearing score. Tiny N. These are qualitative candidates for the next hypothesis sprint.

### Verdict-default on in-scope “regime” queries

- **Frequency:** rank 1 on both competitive semantic hits, both specificity rows, multi-chunk, hop-001, and the deep semantic miss.
- **Severity:** tiny when the gold is rank 2 (~0.01); huge when the gold is the producer (~0.30).
- **Architectural reach:** core hybrid path (TF-IDF + Jaccard over a chunk that densely uses `regime`). Not an edge-case alias.
- **Collateral-risk:** `evaluate.py` gold includes a verdict query. Down-weighting verdict globally could damage a currently successful slice.

### Producer-section burial

- **Frequency:** three measurable misses, three failure-mode labels, one section id (`1_upstream_producer_score_definition`).
- **Severity:** ranks 7, 9, 10; margins about -0.10 to -0.30.
- **Architectural reach:** that chunk is large (paths, five-step computation, config). Burial may be representation, grain, or vocabulary — not yet separable (OOV telemetry was not added).
- **Collateral-risk:** a global representation or chunking change would move every row, including current rank-2 hits.

These two mechanisms can co-exist. Semantic-gap as a **label** is not one mechanism.

### Alias substring boost on OOD (and slug `+0.35`)

- **Frequency:** one dedicated trap row; mechanism is always-on.
- **Severity:** 0.70 vs ~0.15 far-OOD rank-1; the boost is larger than the entire far-OOD top score.
- **Architectural reach:** ranking additive, not a gate. Also fired `scope` on `scopes`.
- **Collateral-risk:** the same table is load-bearing for `evaluate.py` Finding 3.5 / verdict wording. Do not remove aliases to “fix” this row.

### Multi-chunk conjunction at TOP_K

- **Frequency:** N=1.
- **Severity:** mild (ranks 5 and 6).
- **Reach:** evaluation rule (`all` expected in top-k) plus a hard cutoff, not missing chunks.
- **Collateral-risk:** raising TOP_K would manufacture a hit without testing aggregation. Not a recommended sneak change.

### Absent reject path

- **Frequency:** all three OOD rows returned a full top-k, as architecture requires.
- **Severity:** high only when alias fires; far/near scores stay modest in this pair.
- **Reach:** there is no gate anywhere in `retrieve()`.
- **Collateral-risk:** adding reject now would be a new mechanism, not a local fix, and would change frozen control behavior.

## Candidate intervention map (implement none)

| Observed mechanism | Candidate family | Expected blast radius | Why not automatic |
| --- | --- | --- | --- |
| Rank 2 golds, ~0.01 behind `verdict` | Downstream rerank / separation on an already-retrieved shortlist | Narrow if it only reorders top-k; still touches every query that currently puts `verdict` first | Cannot move producer ranks 7–10. sem-002/003 are already hits at TOP_K=5 |
| Producer ranks 7–10 | Representation / candidate generation (dense, multi-vector, chunk split, or a sparse method that actually ranks that chunk) | Wide: every query’s vector/token path | Three labels, one chunk; OOV vs weak-IDF is still unlogged |
| lex-001 lexical neighbor at rank 1 | Stronger sparse matching (e.g. BM25) or query expansion | Wide on all lexical surface forms; could help lex-001 and hurt alias-free in-scope wording | lex-002 already in top-k without BM25; N=2 |
| ood-003 alias fire | Constrain/gate `SECTION_ALIASES` and/or the `+0.35` slug rule | High: `evaluate.py` uses those aliases | Must not be done until measured as its own experiment; this sprint forbids it |
| Far/near OOD always returns k | Future reject / confidence / OOS classifier | New pathway beside ranking | Unmeasurable today; scores of far vs near barely differ in this pair |
| mch-001 ranks 5–6 | Aggregation/reader, or ranking that lifts consumer one place | Medium; cutoff games would fake a hit | N=1; not multi-hop |
| hop-001 | Hop controller / staged retrieval | New architecture | Current eval cannot score it; building it to pass this row would be circular |

Narrowest-intervention rule for the next sprint:

> Fix a failure at the latest/narrowest layer capable of correcting the observed mechanism.

If the gold is already rank 2, do not replace candidate generation because a more sophisticated retriever exists. If the gold is rank 10 and a reranker only sees top-5, a top-5 reranker cannot solve that failure.

## Guardrails for a future experiment

Compare at row, slice, and global levels. Track transitions: hit→hit, miss→hit, hit→miss, miss→miss with positive rank movement, miss→miss with negative rank movement. Preserve raw rank and score movement. Do not pick a universal regression threshold yet.

If the next hypothesis targets **producer burial** (sem-001, lex-001, spec-002):

- Target slices: those three producer-gold misses.
- Guardrail slices: sem-002, sem-003 (rank-2 hits), lex-002 (rank-4 hit), mch-001 stamp already in top-k, `evaluate.py` three gold queries (not in this YAML, still production behavior).

If the next hypothesis targets **verdict-vs-neighbor separation** (sem-002, sem-003 rank 1):

- Target slices: those two competitive semantic rows.
- Guardrail slices: producer misses must not get worse; lex-002; alias-trap diagnostic (do not “win” by stuffing aliases into in-scope queries); mch-001.

If the next hypothesis targets **alias-trap / OOD**:

- Target: ood-003 diagnostic (and maybe ood-001/002 score/rank-1 character), still without fabricating reject accuracy.
- Guardrail: in-scope measurable rows where alias is currently 0.0 must not start passing via new alias hits.

Research question for that experiment:

> Did the intervention improve its target failure mode without materially degrading non-target behavior?

## Open questions

- Is producer burial one mechanism (chunk grain / weak TF-IDF on that section) or three (sense, vocabulary, overspecific step)? This run cannot separate them without OOV-token or term-level traces, which were not added.
- Would a reranker that sees top-5 ever need to exist if the remaining misses are mostly outside top-5? The competitive semantic rows are already hits; rank-1 vs rank-2 may not be the next bottleneck.
- Is `verdict` winning because it is the right *family* heading, because it repeats `regime` densely, or because it is short and Jaccard-friendly? sem-003 says Jaccard, not cosine, decided rank 1.
- How much of ood-003 is the intended `verdict` `+0.5` vs the accidental `scope`⊂`scopes` `+0.35`? Both fired. Gating only `SECTION_ALIASES` would leave the slug rule.
- Near vs far OOD score gap was ~0.01 in this pair. Is near-OOD “more convincing” generally, or only because impact contains COMPRESS/RegimeBoss?
- mch-001 at 5 and 6: is conjunction-at-cutoff a real product failure, or an eval-cutoff artifact? Unknown; N=1.
- True multi-hop remains an evaluation-architecture question, not a ranking question.

## What was deliberately not implemented

Dense embeddings, BM25, reranking, query expansion, alias changes, weight changes, thresholds, OOD rejection, score normalization, GraphRAG, entity resolution, multi-vector retrieval, hop controller, reader/LLM synthesis, learned models, new chunking, corpus changes, OOV telemetry, extra logger fields (margins derived offline), and any third commit that “fixes” an observed problem.

Query text, expected targets, primary failure modes, and locked predictions were not edited after this run. `docqa-expanded-v1` bytes are the same as commit `ef1d33b`.

## Is the evidence sufficient to formulate the first retrieval intervention hypothesis?

**Yes, as a choice between loci, not as a technology pick.**

The next experiment can be formulated from this control rather than from architectural preference:

1. **Late/narrow locus:** verdict-vs-neighbor separation on competitive semantic rows (gold already rank 2; top-5 rerank could see it). This cannot fix producer ranks 7–10.
2. **Early/wide locus:** producer-section retrieval (the repeated measurable miss). This is where remaining `expected_miss` rows concentrate. A top-5 rerank cannot see those golds.

The set is small and constructed. It is sufficient to **choose which locus to test first** and to name guardrail slices. It is **not** sufficient to conclude that dense embeddings, BM25, GraphRAG, or query expansion is required.

Do not implement either hypothesis in this sprint.

## References

- Preregistration / seal: `docs/query_set_expansion/2026-09-28_expanded_query_set_preregistration.md`
- Frozen three-row baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Expected-target telemetry: `docs/query_set_expansion/2026-09-28_expected_target_telemetry.md`
- Failure-mode map: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Raw control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
