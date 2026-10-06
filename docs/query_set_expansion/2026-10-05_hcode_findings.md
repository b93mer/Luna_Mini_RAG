# Findings: identifier/code-register representation (`H-CODE`)

**Date:** 2026-10-05 (runs executed 2026-10-06T03:59Z–04:00Z UTC; the logger names run files by UTC date)
**Status:** Experiment result. Query-set bytes unchanged. Frozen lexical hybrid scoring unchanged when the flag is off. Historical control, H-QRL, H-MORPH, and H1 traces unchanged.
**Preregistration:** `docs/query_set_expansion/2026-10-05_hcode_preregistration.md`
**Control:** `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` / `eval_sets/runs/2026-09-29_run-004.jsonl`
**This document is observation.** Predictions stay in the preregistration. YAML queries, golds, and locked `current_stack_prediction` values were not rewritten.

H-CODE is a representation intervention: replace the TF-IDF cosine term with Jina code cosine. It is not H-QRL. It is not H-MORPH. It is not H1 MiniLM. It is not H-HYBRID. Query rewriting was off. Identifier expansion was off.

## Experimental state

| Piece | Identity |
| --- | --- |
| Branch | `research/code-register-hcode` |
| Query-set version | `docqa-expanded-v1` |
| Query-set sha256 | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` (seal matched) |
| Lexical index sha256 | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` (matched the frozen control) |
| MiniLM H1 index sha256 | `bc1cb4f3a354cf14250bcf7a41ac6edfb16e1e6f98f4d38819542129b11db3c6` (unchanged; diagnostic only) |
| Code index | `metadata/code_hcode_index.json`, 15 rows |
| Code index sha256 | `5184e90e2677f5f1a6275696d62655aed1328a0d4e20f163dd97a8f8c7a1ee20` |
| Frozen lexical scoring | Unchanged: `0.7 * lexical_cosine + 0.3 * jaccard + alias` |
| H-CODE scoring | `0.7 * code_cosine + 0.3 * jaccard + alias` |
| TOP_K | 5 |
| Code model | `jinaai/jina-embeddings-v2-base-code` revision `516f4baf13dec4ddddda8631e019b5737c8bc250` |
| Remote code | `jinaai/jina-bert-v2-qk-post-norm` revision `3baf9e3ac750e76e8edd3019170176884695fb94` |
| Encoder runtime | CPU float32; `transformers` 5.18.0 AutoModel + mean pool + L2; 768-d; max 8192 tokens; no external identifier split |
| `embed.py` sha256 | `2567d09b5da424f55f8470363a036926683b3ac6e8d6db8e1b36318bcf66dfcf` (matched preregistration) |
| `evaluate.py` sha256 | `97d953d99f0b9136b069a764afa04536555911f9c23f8566a1563933361fc579` (matched preregistration) |
| `retrieve.py` sha256 | `227a49170b417a4ec08545fa4e0d3488b3e0780f3497b02645f08430985e7bd8` (added `code_cosine` field; frozen lexical formula/weights/aliases unchanged since `000e658`) |
| Flag-off sanity | `eval_sets/runs/2026-10-06_run-007.jsonl` (run UUID `927be699-e89b-49a4-89a1-a3eb2c46bdd0`); expected-target ranks and six-decimal lexical scores matched frozen control exactly; `code_cosine` 0.0; `dense_cosine` 0.0 |
| Experiment pass | `eval_sets/runs/2026-10-06_run-008.jsonl` (run UUID `766c4e98-fda0-47ce-a367-cf7439a5d693`) |
| Frozen `evaluate.py` functions | PASS (section lookup + hybrid gold queries, no re-ingest) |
| H-CODE gold queries | question / verdict / Finding 3.5 each remain in top-3 under `rank_all_hcode` |
| Unit tests | 78/78 pass |

`rank_gain = control_rank - experiment_rank`. Positive is movement toward rank 1.

Comparison is to `expanded-control-v1`. H1 MiniLM cosine is a reference correspondence, not the H-CODE control total.

**Score-scale caution.** Control totals, H1 totals, and H-CODE totals are not like-for-like correspondence metrics. Jaccard and alias used identical implementations and, on every sealed in-scope producer row inspected, matched control to six decimals. Rank, `code_cosine` among chunks of the same query, and within-H-CODE margins are the valid comparisons. MiniLM `dense_cosine` in the H-CODE trace is diagnostic only and matched the frozen H1 values on the rows checked.

## Representation identity

Selected from model cards before sealed ranks. Not a bake-off.

- Hub id: `jinaai/jina-embeddings-v2-base-code`
- Revision: `516f4baf13dec4ddddda8631e019b5737c8bc250`
- Same encoder for queries and chunks
- Mean pooling, L2 normalization, CPU float32
- Query text: original YAML
- Chunk text: stored `chunk.text`
- External snake/dot/camel segmentation: **off**
- Loader shims locked before the sealed run: prune-helper import, BERT-era config defaults, historical attention-mask helpers, all-zero `token_type_ids` (the RoBERTa-style tokenizer does not emit them; transformers 5.18 left Jina’s buffer uninitialized)

Rejected from documentation, not from ranks: CodeSearchNet DistilRoBERTa (128-token truncation), SFR-Embedding-Code-400M (heavier CLS path), MiniLM+external identifier split (still MiniLM).

## Hashes

| Artifact | sha256 |
| --- | --- |
| Query set | `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` |
| Lexical index | `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` |
| MiniLM index | `bc1cb4f3a354cf14250bcf7a41ac6edfb16e1e6f98f4d38819542129b11db3c6` |
| Code index | `5184e90e2677f5f1a6275696d62655aed1328a0d4e20f163dd97a8f8c7a1ee20` |

## Tests

78/78 passed (`pytest tests`). Prior H1 suite was 61/61. New H-CODE tests cover flag default off, frozen `retrieve()`, H1/H-QRL/H-MORPH still callable, mutual exclusion with rewrite and H1, original query preservation, no identifier expansion, exact scorer equation, 768-d L2 vectors, deterministic encode, section/`content_sha256` index validation, identity preprocessing, and named score-component logging.

## Scoring formula

```
score = 0.7 * code_cosine + 0.3 * jaccard + alias
```

`lexical_cosine` and MiniLM `dense_cosine` were logged for attribution and were **not** in the blend.

## Verdict

**Partially supported.** Do not treat the 3/7 → 6/7 measurable hit count as the result.

H-CODE increased **absolute identifier-register correspondence** on `qse-docqa-sem-001` without query expansion, and it did **not** fully recover that producer into top-k. The remaining nearest neighbor is another identifier-bearing regime/conviction chunk (the consumer), not the short prosaic `verdict` field that buried the producer under control and MiniLM.

1. **Primary correspondence improved; retrieval was not recovered.** `sem-001` moved rank 10 → 6 and stayed a miss. Producer `code_cosine` is **0.519607** versus H1 MiniLM **0.263470**. Versus `verdict`, the MiniLM gap was 0.600096 − 0.263470 = 0.336626; the code gap is 0.565467 − 0.519607 = 0.045860. Jaccard, alias, and `lexical_cosine` matched control. Rank +4 is mechanism **A**, not competitor collapse.
2. **The producer is now in an identifier-bearing neighborhood, not a prose neighborhood.** Rank 1 is the consumer (`code_cosine` 0.665044). Stamp is rank 5. `verdict` fell from rank 1 (control/H1) to rank 3. `date` is rank 15 with alias 0.0. H-CODE did not recreate the H-QRL `date` artifact.
3. **lex-001 was not sacrificed.** Producer rank 7 → **1**. Producer `code_cosine` 0.507600 exceeds H1 MiniLM 0.284254. The previously invariant signals neighbor fell to rank 7 (`code_cosine` 0.393939 vs its MiniLM 0.379759). This is stronger than the preregistered “preserve semantics reasonably” bar. It is specialization evidence that a code-trained encoder can still recover mixed NL/identifier synonymy; it is not a reason to declare H-CODE a general retriever.
4. **spec-002 improved unexpectedly and is not H-CODE’s defining mechanism.** Rank 9 → 3, `code_cosine` 0.304967 vs MiniLM 0.107786. The query still contains `threshold`, not `thresholds`. H-MORPH remains the matching morphological repair. Investigate as overlay: the producer’s label-set identifiers (`COMPRESS` / `EXPAND` / `TRANSITION` / `UNKNOWN`) are code-register content MiniLM treated as weak.
5. **Guardrails stayed hits and several strengthened.** `sem-002` rank 1. `sem-003` rank 1. `lex-002` rank 1. Frozen and H-CODE gold queries still place each target in top-3.
6. **mch-001 conjunction hit is incidental.** Consumer rank 1, stamp rank 2. Not a hop controller.
7. **Near-OOD identifier attraction is real.** `ood-002` ranks the producer first (`code_cosine` 0.527452) because the query names `RegimeBoss` / `COMPRESS`. Far-OOD top `code_cosine` ~0.36 is higher than MiniLM’s ~0.15. Do not invent a reject threshold.
8. **Alias-trap holds.** `ood-003` keeps `verdict` rank 1 with alias 0.5. No generated-token `date` overlay.

## Measurable rank table

| row | control rank | QRL | MORPH | H1 | H-CODE | rank_gain vs C | control outcome | H-CODE outcome | target alias | H-CODE rank-1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| sem-001 | 10 | 11 | 10 | 9 | **6** | +4 | expected_miss | expected_miss | 0.0 | consumer |
| sem-002 | 2 | 4 | 1 | 1 | 1 | +1 | hit | hit | 0.0 | gold |
| sem-003 | 2 | 2 | 1 | 3 | 1 | +1 | hit | hit | 0.0 | gold |
| lex-001 | 7 | 3 | 7 | 3 | **1** | +6 | expected_miss | hit | 0.0 | **producer** |
| lex-002 | 4 | 3 | 4 | 4 | 1 | +3 | hit | hit | 0.0 | gold |
| spec-002 | 9 | 1 | 3 | 10 | **3** | +6 | expected_miss | hit | 0.0 | impact |
| mch-001 stamp | 5 | 2 | 5 | 5 | 2 | +3 | expected_miss (conjunction) | hit (conjunction) | 0.0 | consumer |
| mch-001 consumer | 6 | 1 | 6 | 1 | 1 | +5 | expected_miss (conjunction) | hit (conjunction) | 0.0 | consumer (gold) |

Measurable outcomes: control `hit=3, expected_miss=4`; experiment `hit=6, expected_miss=1`. Global hit rate is still not an optimization target.

## Score-component table

Raw totals are **not** directly comparable across representations. Jaccard and alias matched control on the in-scope producer rows below. MiniLM `dense_cosine` is the H1 reference, not part of the H-CODE score.

| row | C rank | QRL | MORPH | H1 | H-CODE | lexical cos | MiniLM cos | code cos | Jaccard | alias | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sem-001 | 10 | 11 | 10 | 9 | 6 | 0.017169 | 0.263470 | **0.519607** | 0.011111 | 0.0 | A; correspondence up; still miss; consumer 0.665 |
| sem-002 | 2 | 4 | 1 | 1 | 1 | 0.337091 | 0.476763 | 0.461929 | 0.048780 | 0.0 | stable/stronger guardrail |
| sem-003 | 2 | 2 | 1 | 3 | 1 | 0.396006 | 0.410560 | 0.573172 | 0.117647 | 0.0 | guardrail; gold now rank 1 |
| lex-001 | 7 | 3 | 7 | 3 | 1 | 0.048343 | 0.284254 | **0.507600** | 0.010989 | 0.0 | A; stronger than H1; signals neighbor rank 7 |
| lex-002 | 4 | 3 | 4 | 4 | 1 | 0.093297 | 0.256891 | 0.500254 | 0.032258 | 0.0 | stable guardrail became rank 1 |
| spec-002 | 9 | 1 | 3 | 10 | 3 | 0.051815 | 0.107786 | 0.304967 | 0.021739 | 0.0 | unexpected A overlay; not morphology |
| mch stamp | 5 | 2 | 5 | 5 | 2 | 0.187905 | 0.357366 | 0.469759 | 0.061538 | 0.0 | incidental conjunction |
| mch consumer | 6 | 1 | 6 | 1 | 1 | 0.164129 | 0.515935 | 0.565190 | 0.076087 | 0.0 | incidental; identifier-mixed consumer |

## sem-001 primary result

Original YAML query. Rewritten query empty. Expansions empty. Alias 0.0 on the producer. `date` rank 15, alias 0.0.

| Quantity | Control | H1 MiniLM | H-CODE |
| --- | ---: | ---: | ---: |
| producer rank | 10 | 9 | **6** |
| Jaccard / alias / lexical_cosine | 0.011111 / 0.0 / 0.017169 | identical | identical |
| producer cosine term | lexical 0.017169 | dense 0.263470 | **code 0.519607** |
| rank-1 identity | `verdict` 0.316521 | `verdict` dense 0.600096 | **consumer** code 0.665044 |
| producer vs verdict cosine | lexical leftover | 0.263 vs 0.600 | **0.520 vs 0.565** |
| producer vs consumer cosine | n/a (consumer not the MiniLM issue) | 0.263 vs 0.552 | 0.520 vs 0.665 |
| margin to rank 1 (total) | −0.301 | n/a across spaces | −0.119163 |

Identifier-density counts on stored `chunk.text` (analysis only; not scored):

| section | snake | dotted | camel | whitespace tokens | qualitative |
| --- | ---: | ---: | ---: | ---: | --- |
| producer | 16 | 9 | 5 | 116 | identifier-heavy score definition |
| consumer | 17 | 6 | 2 | 116 | identifier-heavy mixed consumer |
| stamp | 15 | 4 | 0 | 72 | identifier-heavy stamp |
| verdict | 8 | 1 | 4 | 48 | mixed short field (prose + identifiers) |
| title | 0 | 0 | 0 | 4 | prose-heavy |

The preregistered numeric cut (`≥4` matches or proportion `≥0.08`) over-labels this technical note; almost every content chunk trips it. Labels above are qualitative from the counts plus chunk role.

Classification: **A**. Count as support for the correspondence claim. Do not count as retrieval recovery. The remaining miss is competition among identifier-bearing regime/conviction chunks, not MiniLM-style prosaic burial.

## lex-001 mechanism control

No `stability`. No `vwap_dist`. Query text identical to YAML. Jaccard and `lexical_cosine` identical to control.

| Quantity | Control | H1 | H-CODE |
| --- | ---: | ---: | ---: |
| producer rank | 7 | 3 | **1** |
| producer MiniLM | — | 0.284254 | 0.284254 (diagnostic) |
| producer code | — | — | **0.507600** |
| signals neighbor rank | 1 | 1 | **7** |

The four-experiment invariant “signals neighbor is always rank 1 on lex-001” **breaks** under H-CODE. Producer `code_cosine` 0.507600 exceeds the neighbor’s 0.393939. MiniLM had the reverse order (0.284 vs 0.379). Rank 1 is target correspondence, not stripping (function words were never removed) and not alias.

H-CODE did not have to outperform MiniLM here. It did. Interpret as: the code-trained space preserved mixed NL/identifier synonymy and even inverted the neighbor that MiniLM could not dethrone. Do not promote H-CODE as the synonymy specialist; MiniLM remains the isolated H1 mechanism. This row is not H-CODE failure.

## spec-002 mechanism control

H-MORPH repaired this row with `threshold → thresholds`. H-CODE used the original query.

Producer rank 9 → 3. Producer `code_cosine` 0.304967 vs MiniLM 0.107786. Rank 1 is impact (`code_cosine` 0.329704), not the four-way label set. Alias 0.0.

This is unexpected **A** on identifier/label content, not a replication of morphology. The query still lacks `thresholds`. Do not redefine H-CODE as a morphology substitute. H-MORPH remains the matching intervention for surface-form mismatch.

## Guardrails

| Guardrail | Result |
| --- | --- |
| sem-002 stays a hit | Held and remained rank 1. Title chunk rank 5. |
| sem-003 in top-k | Held and became rank 1 (`code_cosine` 0.573172). |
| lex-002 in top-k | Held and became rank 1. |
| mch-001 stamp in top-k | Held at rank 2. Conjunction flipped to hit via consumer rank 1. Not counted as producer-burial support. |
| frozen `evaluate.py` PASS | Held (no re-ingest) |
| H-CODE gold queries in top-3 | Held: question, verdict, Finding 3.5 each rank 1 on their gold queries |

Producer-target alias remained 0.0 on in-scope golds. No rewrite tokens existed to fire slug-as-spaces `date`.

## OOD diagnostics

| Row | Control rank-1 | H1 rank-1 | H-CODE rank-1 | note |
| --- | --- | --- | --- | --- |
| ood-001 far | question 0.153 | stamp dense 0.150 | question code **0.363** | residual ranking; more confident than MiniLM far-OOD; still no reject |
| ood-002 near | impact 0.164 | verdict dense 0.370 | **producer code 0.527** | identifier attraction (`RegimeBoss` / `COMPRESS`); predicted pathology |
| ood-003 trap | verdict alias 0.5 | verdict alias 0.5 | verdict alias 0.5 | HOLDS; `scope` has higher code cosine (0.399) than verdict (0.346), alias restores verdict |

Do not invent a reject threshold. Near-OOD producer rank 1 is future H-OOD / identifier-attractor work.

## Alias behavior

- In-scope producer alias 0.0
- No `regime_update_interval_seconds` in any query
- `date` is not rank 1 on any H-CODE row
- Alias-trap `ood-003` unchanged

H-CODE did not recreate the H-QRL `date` artifact. That is consistent with “no identifier expansion enters the query.”

## Important competitor analysis

On `sem-001`, H-CODE moved similarity **toward identifier-bearing chunks** rather than merely reshuffling unrelated competitors:

- Producer `code_cosine` doubled MiniLM’s 0.263.
- `verdict` lost rank-1 status; its remaining lead over the producer is 0.046 on code cosine versus 0.337 on MiniLM.
- Consumer and stamp, both identifier-heavy, occupy ranks 1 and 5.
- Title chunk is rank 7 (`code_cosine` 0.470, Jaccard 0.0625), not a MiniLM-style Jaccard-0 overgeneralization into top-k on this row.
- The miss is now “wrong identifier-mixed neighbor,” not “no correspondence.”

On `lex-001`, the signals neighbor is no longer an invariant. That is a real representation effect, not an alias effect.

## Falsification checklist (from the preregistration)

- `sem-001` remains essentially unchanged → **not triggered** (rank 10→6; code cosine 0.520 vs MiniLM 0.263)
- producer `code_cosine` remains weak relative to prose neighbors → **partially triggered vs consumer** (0.520 vs 0.665); **not triggered vs verdict** (gap collapsed)
- rank improves only because competitors lose score → **not triggered** (Jaccard/`lexical_cosine` frozen; producer code cosine is the moving term)
- generic identifier-heavy chunks become incorrect attractors → **triggered as overlay** on near-OOD (`ood-002` producer rank 1) and as the remaining `sem-001` consumer neighbor
- gains require query-specific identifiers → **not triggered**
- alias explains the gain → **not triggered**
- OOD becomes severely pathological → **far-OOD more confident, not in-domain-confident; near-OOD identifier attraction documented; no reject invented**
- sealed ranks influenced model or preprocessing selection → **not triggered**
- only aggregate hit rate improves → **hit rate rose to 6/7, but sem-001 A and lex-001 A are real; do not accept 6/7**
- rewrite / morphology / identifier expansion / MiniLM blending silently applied → **not triggered**

`lex-001` weaker than H1 is **not** falsification; the row was stronger.
`spec-002` remaining a miss is **not** falsification; the row became a hit by a non-morphology overlay.

H-CODE as the claim “an identifier-aware representation can improve absolute correspondence for the surviving producer-burial failure without query-specific expansion” is **partially supported**: correspondence improved and the prosaic burial collapsed; top-k recovery failed because another identifier-bearing chunk won.

## Deliberate non-actions

This sprint did not:

- swap Jina for a second model after seeing ranks
- retune 0.7 / 0.3 or blend MiniLM + code cosine
- add `regime_stability` or `RegimeObserver` to queries
- blacklist `date` or retune aliases
- rewrite YAML queries or golds
- change TOP_K or chunk boundaries
- turn morphology or identifier expansion on
- invent an OOD reject threshold
- implement H-HYBRID
- patch `sem-001`

## Implications for system architecture

Semantic similarity is **representation-dependent**. MiniLM recovers closed-vocab synonymy and fails identifier-register burial. A code-trained mean-pooled cosine recovers much of that burial’s missing correspondence and still loses to a neighboring identifier-mixed consumer. Morphology remains a third, non-interchangeable tool.

A production mix of morphology + MiniLM + code cosine would be a new hypothesis about routing or combination. It is not licensed by this result.

## Next hypotheses — not implemented

- **H-HYBRID / H-ROUTE:** detect failure class and choose morphology vs MiniLM vs code cosine, or combine them, without tuning on these sealed rows.
- **H-OOD:** reject/calibration now that code cosine on near-OOD identifiers can match in-scope values.
- **H-ID:** constrained identifier expansion remains a different mechanism; H-CODE reduced the need for dumping `regime_stability` into the query but did not make consumer-vs-producer disambiguation automatic.
- **H-ALIAS:** unchanged; alias-trap still fires from human query text.

Do not start those experiments on this branch as part of this measurement.

## References

- Preregistration: `docs/query_set_expansion/2026-10-05_hcode_preregistration.md`
- H1 findings: `docs/query_set_expansion/2026-10-05_dense_cosine_h1_findings.md`
- Three-hypothesis comparative findings: `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md`
- Control trace: `eval_sets/runs/2026-09-29_run-004.jsonl`
- Flag-off sanity: `eval_sets/runs/2026-10-06_run-007.jsonl`
- Experiment trace: `eval_sets/runs/2026-10-06_run-008.jsonl`
- Code index: `metadata/code_hcode_index.json`
