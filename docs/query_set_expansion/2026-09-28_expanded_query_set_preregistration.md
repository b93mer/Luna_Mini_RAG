# Preregistration: expanded diagnostic query set (`docqa-expanded-v1`)

**Date:** 2026-09-28
**Status:** Preregistered. Predictions locked before the expanded control run.
**Query-set version:** `docqa-expanded-v1`
**Sealed file:** `eval_sets/docqa.yaml`
**Sealed sha256:** `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`
**Retriever freeze:** commit `000e658` (`feat(eval): add expected-target rank and run identity telemetry`). Retrieval behavior is unchanged.
**Companion map:** `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
**This document is not a result.** It records what was predicted, and why, before `retrieve()` was called on the new rows.

The three calibration rows (`qse-docqa-sem-001`, `qse-docqa-sem-002`, `qse-docqa-lex-001`) are copied unchanged, including the dated `current_stack_after_run` note on sem-002. Their queries, expected targets, and primary failure modes are not rewritten.

## Experimental state at preregistration (Phase 0)

Inspected without modifying the retriever:

| Piece | State |
| --- | --- |
| Corpus | One note: `data/2026-08-10_regime_factor_composition_trace.md` |
| Chunk count | 15 in `metadata/chunks.json` |
| Scoring | `score = 0.7 * cosine(TF-IDF) + 0.3 * Jaccard(query, heading+text) + alias_boost` |
| TOP_K | 5 (`run_query_set.TOP_K`) |
| Aliases | `question`, `verdict`, `impact_on_finding_3_5_disposition` only; `+0.5` substring, `+0.35` if the query contains a chunk's full `section_id` with underscores as spaces |
| Query-set schema | Two-document YAML: manifest then a list of rows |
| Single-target | `expected` as a one-element list; hit iff that id is in top-k |
| Multi-target | already supported: hit iff **every** expected id is in top-k |
| Reject / OOD scoring | **does not exist**. Empty `expected` currently makes `expected_in_topk` false |
| Dependent multi-hop | **does not exist**. One independent ranking per query |
| `current_stack_prediction` vocabulary | `supported`, `expected_miss`, `unmeasurable` (map); YAML field name is `current_stack_prediction` |
| Outcome mapping before this commit | `in_topk` → `hit`; else `expected_miss` if so predicted, else `miss`. A row predicted `unmeasurable` would have been labeled `miss` |

Calibration anchors already measured against this stack (not re-predicted here):

| Row | Primary mode | Frozen target rank |
| --- | --- | ---: |
| `qse-docqa-sem-001` | semantic gap | 10/15 |
| `qse-docqa-sem-002` | semantic gap | 2/15 |
| `qse-docqa-lex-001` | lexical gap | 7/15 |

Those ranks are historical control facts. They were **not** used to word the new rows.

## Why some rows are unmeasurable

The frozen retriever always returns a ranked top-k. It has no reject path and no hop controller.

- **Out-of-domain** asks whether the query should retrieve corpus evidence **at all**. Inventing a gold section id, or treating rank-1 as the answer, would fabricate hit/miss. OOD rows therefore have `expected: []` and `current_stack_prediction: unmeasurable`. Retrieval still runs so rank-1 identity, alias fire, and score magnitude can be observed diagnostically.
- **Underspecific** `qse-docqa-spec-001` has no unique supporting section. Unique-target scoring would pick an arbitrary gold.
- **True multi-hop** requires a second query that cannot be written until hop 1 returns. A single ranking, or a pre-known multi-target list, would misrepresent the mechanism.

These rows remain in the machine-readable set so the evaluation boundary is versioned. They are not scored as miss.

## Minimal schema/runner representation (not reject, not hops)

Documentation-only OOD/hop rows would not be executed by `run_query_set.py`, so diagnostic rank-1 observation would be lost. The rows are therefore in `docqa.yaml` with empty `expected`.

Without a runner change, `outcome_for` would label them `miss`. That is a fabricated metric. Commit A therefore maps `current_stack_prediction: unmeasurable` to outcome `unmeasurable` regardless of `in_topk`. Retrieval, scoring, aliases, weights, TOP_K, and ranking are untouched.

`expected_failure_signature` and `contradiction_condition` are **not** YAML fields. They live only in this document.

## Coverage matrix (targets, not quotas)

| Primary failure mode | Target | Rows | Notes |
| --- | ---: | --- | --- |
| semantic gap | ~3 | 3 | sem-001/002 locked; sem-003 is a different sense split |
| lexical gap | ~2 | 2 | lex-001 locked; lex-002 is a different object |
| underspecific | ~1 | 1 | spec-001, unmeasurable |
| overspecific | ~1 | 1 | spec-002, measurable |
| multi-chunk | ~1 | 1 | mch-001; `hops: single` |
| far OOD | ~1 | 1 | ood-001, unmeasurable |
| near OOD | ~1 | 1 | ood-002, unmeasurable |
| alias-trap | ~1 | 1 | ood-003, unmeasurable |
| true multi-hop | ~1 | 1 | hop-001, unmeasurable |

Total rows: **12**. No entity-disambiguation primary row: alias-trap is filed as out-of-domain (`ood_kind: alias_trap`) because one side of the collision is not in the index. Empty cells left empty: log/code tasks, cross-doc entity collision, second-document hops.

## Locked prediction mix (before retrieve)

| Mode | supported | expected_miss | unmeasurable |
| --- | ---: | ---: | ---: |
| semantic gap | 0 | 3 | 0 |
| lexical gap | 0 | 2 | 0 |
| specificity mismatch | 0 | 1 | 1 |
| multi-chunk | 0 | 1 | 0 |
| out-of-domain | 0 | 0 | 3 |
| multi-hop | 0 | 0 | 1 |
| **total** | **0** | **7** | **5** |

`qse-docqa-sem-002` remains `expected_miss` in the locked prediction field. The dated after-run note (`hit`) is a map correction from the three-row baseline, not a rewritten prediction.

No new row is predicted `supported`. A later hit on a new row is a **prediction contradiction**, not a silent success.

## Seal

`docqa-expanded-v1` is the immutable experimental version of this byte snapshot.

- Identity: sha256 of `eval_sets/docqa.yaml` as hashed by `hashlib.sha256` on the file bytes the runner reads.
- Value at preregistration: `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`
- Runtime field: `query_set_sha256` on every JSONL row. Future control and experiment runs prove they used the same bytes by matching this hash.
- The manifest `sha256` field does **not** contain the digest (self-hash would move the bytes). The seal lives here and in the runtime trace.

Do not rewrite query text, expected targets, primary failure mode, or these predictions after observing retrieval.

---

## Row registry

Each new row answers: if this query fails, can we attribute the failure to the claimed mode?

Intent, expected failure signature, and contradiction condition are recorded here so the YAML schema is not expanded.

### qse-docqa-sem-001 (locked calibration)

| Field | Value |
| --- | --- |
| task / text_type / length | `doc_qa` / `markdown_note` / `short` |
| specificity / domain / hops | `matched` / `in_scope` / `single` |
| lexical_overlap / ambiguity | `high` / `polysemy` |
| expected | `1_upstream_producer_score_definition` |
| failure_mode | semantic gap |
| current_stack_prediction | `expected_miss` |
| route_pressure | `route_s` |
| query | What does the regime-related score represent when it contributes to the conviction assessment? |
| intent | Probe whether conviction-sense "regime" retrieves the producer score definition rather than the RegimeBoss sense. |
| expected failure signature | Target outside top-k; competing rank-1 in the RegimeBoss / verdict family; alias 0.0. |
| contradiction | Target in top-k without alias fire would contradict "context cannot split senses." |

Historical rank 10/15 is not a new prediction.

### qse-docqa-sem-002 (locked calibration)

| Field | Value |
| --- | --- |
| expected | `impact_on_finding_3_5_disposition` |
| failure_mode | semantic gap |
| current_stack_prediction | `expected_miss` (after-run note: `hit`, rank 2) |
| query | What does the regime control determine about the status of the existing finding? |
| intent | Probe RegimeBoss-sense "regime" toward Finding 3.5 disposition without alias vocabulary. |
| expected failure signature | As originally predicted: miss, verdict-family winner. |
| contradiction | Already observed: rank 2, margin 0.0134. Prediction field stays `expected_miss`. |

### qse-docqa-sem-003 (new)

| Field | Value |
| --- | --- |
| task / text_type / length | `doc_qa` / `markdown_note` / `short` |
| specificity / domain / hops | `matched` / `in_scope` / `single` |
| lexical_overlap / ambiguity | `high` / `polysemy` |
| expected | `3_conviction_factor_entry_the_field_under_audit` |
| failure_mode | semantic gap |
| current_stack_prediction | `expected_miss` |
| route_pressure | `route_s` |
| query | When a low regime score itself produces a hard block, is that the RegimeBoss blocking mechanism? |
| intent | Split two **hard-block** mechanisms that share "regime" vocabulary (GATE:REGIME vs RegimeBoss), not reuse the producer-vs-disposition split. |
| expected failure signature | Consumer section absent from top-k or losing to `verdict` / impact, which mention RegimeBoss hard-block without describing the 0.70 score gate; alias 0.0. |
| contradiction | Consumer section in top-k with alias 0.0 would show ordinary context tokens can separate the two block paths. |
| why one mode | Failure is sense collapse of shared tokens onto the wrong mechanism. Not lexical: overlap is intentionally high. Not Finding 3.5: that gold is sem-002. |

Source evidence (corpus, not retrieval): the consumer section states that `regime_score < 0.70` reasons `"regime"` / `GATE:REGIME` and still uses the VWAP-stability score; RegimeBoss hard block is a separate path. Verdict states independence and "not the RegimeBoss hard-block / label path" but does not describe the score-threshold gate, so verdict is not an equivalent gold.

### qse-docqa-lex-001 (locked calibration)

| Field | Value |
| --- | --- |
| expected | `1_upstream_producer_score_definition` |
| failure_mode | lexical gap |
| current_stack_prediction | `expected_miss` |
| query | Which upstream market-condition measure supplies the consistency signal used when assessing trade confidence? |
| intent | Same object as sem-001, different vocabulary. |
| expected failure signature | Target outside top-k; lexical near-miss on shared surface words. |
| contradiction | Target in top-k despite low overlap. |

Historical rank 7/15 is not a new prediction.

### qse-docqa-lex-002 (new)

| Field | Value |
| --- | --- |
| expected | `2_state_stamp_before_conviction` |
| failure_mode | lexical gap |
| current_stack_prediction | `expected_miss` |
| route_pressure | `route_s` |
| query | How frequently may the cached market-state fields be refreshed for later confidence calculation? |
| intent | Same-object substitution against the **stamp** section (refresh interval), not another producer paraphrase. |
| expected failure signature | Stamp section outside top-k; possible attraction to consumer ("confidence") or producer ("observer" not even present); closed-vocab drop of `frequently` / `cached` / `market-state` / `refreshed`. |
| contradiction | Stamp in top-k without heading leak (`state stamp`, `before conviction`) and without the `30` / throttle token. |
| why one mode | Intended object is one section; wording is a substitution for "REGIME_UPDATE_INTERVAL_SECONDS = 30" / throttled step. Not semantic: those tokens are not a second sense of the same string. Not multi-chunk: one gold. |

Source evidence: only the stamp section states the 30-second throttle (`REGIME_UPDATE_INTERVAL_SECONDS`) that answers "how frequently."

### qse-docqa-spec-001 (new, unmeasurable)

| Field | Value |
| --- | --- |
| specificity | `under` |
| expected | (empty) |
| failure_mode | specificity mismatch |
| current_stack_prediction | `unmeasurable` |
| route_pressure | `none` |
| query | What is the regime? |
| intent | Show that an underspecific in-scope query has no unique gold. |
| expected failure signature | Not scored. Diagnostically: top-k mixes conviction-factor chunks and RegimeBoss/Finding chunks; some chunk still ranks 1 with a non-zero score. |
| contradiction | Not applicable as hit/miss. A later unique-gold assignment would be a taxonomy change, not a retrieve result. |
| why one mode | Primary defect is missing scope, not a chosen sense. Polysemy is recorded on `ambiguity` as secondary. Filing this as semantic gap would require a unique expected sense it does not have. |

### qse-docqa-spec-002 (new)

| Field | Value |
| --- | --- |
| specificity | `over` |
| expected | `1_upstream_producer_score_definition` |
| failure_mode | specificity mismatch |
| current_stack_prediction | `expected_miss` |
| route_pressure | `route_l` |
| query | Which four labels can the percentile-threshold rule assign, including the in-between and missing-data cases? |
| intent | Ask only for step-3 of the producer computation (four-way label set) while the chunk also holds classifier paths, stability, and config. |
| expected failure signature | Producer outside top-k or losing to sections that mention COMPRESS (impact / verdict) or thresholds (input fields) without listing the four labels. |
| contradiction | Producer in top-k from the narrow ask alone, showing grain mismatch does not bury the step. |
| why one mode | The ask is narrower than the chunk, not a synonym of the whole producer heading, and not a second hop. Labels are not named in the query (no answer leak). |

Source evidence: only the producer section lists `COMPRESS / EXPAND / TRANSITION / UNKNOWN` as the p95-threshold label set. Upstream-signals mentions majority fraction but not those four labels. Impact mentions RegimeBoss COMPRESS, a different object.

### qse-docqa-mch-001 (new)

| Field | Value |
| --- | --- |
| hops | `single` |
| expected | `2_state_stamp_before_conviction` **and** `3_conviction_factor_entry_the_field_under_audit` |
| failure_mode | multi-chunk |
| current_stack_prediction | `expected_miss` |
| route_pressure | `either` |
| query | After the observer stores its score on the live state object, how does the conviction function copy that score into the factors map? |
| intent | Require **both** the stamp write and the consumer read in one ranking. |
| expected failure signature | At least one of the two ids missing from top-k; likely one end ranks and the other does not. Per-target ranks will be reported separately; they are not collapsed. |
| contradiction | Both ids in top-k. That would not become multi-hop success. |
| why one mode | Both golds are known before retrieval. Not multi-hop. Not lexical: overlap with observer/score/conviction/factors is intentional. |

Source evidence: stamp writes `state["regime"]["score"]` from `regime_observer.step`; consumer reads that cache into `factors["regime"]`. Neither section fully contains the other. Verdict does not describe either write.

The `mch` id token extends `qse-{task}-{mode}-{nnn}` for this coverage cell (multi-chunk is not `hop`).

### qse-docqa-ood-001 (new, unmeasurable)

| Field | Value |
| --- | --- |
| domain / ood_kind | `out_of_scope` / `far` |
| expected | (empty) |
| failure_mode | out-of-domain |
| current_stack_prediction | `unmeasurable` |
| route_pressure | `route_s` |
| query | How many innings are in a regulation baseball game? |
| intent | Far-OOD with no corpus topic and no alias substring. |
| expected failure signature | Not scored as reject. Diagnostically: some chunk still rank 1; alias 0.0; scores closer to residual Jaccard than to an in-scope hit. |
| contradiction | Not a hit. A zero-length top-k would contradict "always returns k," but that would be a retriever change, which this sprint forbids. |
| why one mode | The question is whether to retrieve at all. No gold section. |

### qse-docqa-ood-002 (new, unmeasurable)

| Field | Value |
| --- | --- |
| domain / ood_kind | `out_of_scope` / `near` |
| expected | (empty) |
| failure_mode | out-of-domain |
| current_stack_prediction | `unmeasurable` |
| query | How does RegimeBoss decide to emit COMPRESS on high realized-volatility days? |
| intent | Near-OOD: adjacent model-b / Finding 3.5 topic the index is not allowed to answer. |
| expected failure signature | Not scored. Diagnostically: impact or verdict looks like a convincing rank-1 because of RegimeBoss/COMPRESS tokens, without containing the decision procedure. |
| contradiction | Not a hit. Presence of a mention is not supporting evidence. |
| why one mode | Asking for a procedure the note only **names**. Not in-scope: the impact section lists COMPRESS-on-high-RV as what Finding 3.5 concerns; it does not explain the decision. Not the scope-field question "were fire-path changes made?" (that **is** answered: no). Avoids `finding 3.5` so attraction is near-domain tokens, not the alias table. |

### qse-docqa-ood-003 (new, unmeasurable)

| Field | Value |
| --- | --- |
| domain / ood_kind | `out_of_scope` / `alias_trap` |
| ambiguity | `alias_collision` |
| expected | (empty) |
| failure_mode | out-of-domain |
| current_stack_prediction | `unmeasurable` |
| query | What was the jury's verdict in the 1925 Scopes trial? |
| intent | Out-of-scope query that contains the `verdict` alias substring. |
| expected failure signature | Not scored as reject. Diagnostically: `verdict` ranks 1 with `alias = 0.5` and a score inflated by that constant relative to far-OOD. |
| contradiction | Not a hit on the verdict section. Alias not firing would contradict the known substring rule (and would imply the query was rewritten). |
| why one mode | Out-of-domain with alias pressure. Not entity disambiguation: the Scopes trial is not an in-corpus object. `expected` is not `verdict`. |

### qse-docqa-hop-001 (new, unmeasurable)

| Field | Value |
| --- | --- |
| hops | `multi` |
| expected | (empty) |
| failure_mode | multi-hop |
| current_stack_prediction | `unmeasurable` |
| route_pressure | `either` |
| query | Where does the number that is written into the conviction regime factor come from immediately before that write? |
| intent | Mark the evaluation boundary for **dependent** retrieval. |
| intended chain (not executed) | Hop 1: retrieve the consumer write/read site (how `factors["regime"]` is assigned). Hop 2 can be written only after hop 1 reveals `state["regime"]["score"]`; hop 2 would then ask where that cache is populated (stamp) and, if needed, what scalar the writer consumes (producer). |
| expected failure signature | Not scored. A single-pass consumer hit is hop-1 at most. A shortcut that also returns stamp is **not** hop success. |
| contradiction | Not applicable as hit/miss. Implementing a hop controller would change the architecture this row exists to bound. |
| why one mode | Hop 2 is unknown until hop 1 returns. Contrast `qse-docqa-mch-001`, which names both ends up front. Not labeled multi-chunk. |

---

## Static review (before retrieve)

Reviewed against the sprint checklist. No candidate was accepted that failed a hard-stop condition.

| Check | Result |
| --- | --- |
| Accidental target-heading leakage | New queries avoid `state stamp`, `before conviction`, `field under audit`, `upstream producer`, `score definition`, `Impact on Finding 3.5`. |
| Accidental aliases | New in-scope queries avoid `question`, `verdict`, `finding 3.5`, `finding 3_5`, `disposition`, `impact on finding`, `hold stands`. ood-003 contains `verdict` **on purpose**. No new query contains a full `section_id` with underscores as spaces. |
| Multiple simultaneous failure modes | Each row has one primary mode; secondary stresses stay in notes/`ambiguity`. spec-001 records polysemy as secondary. ood-003 records alias_collision as mechanism, primary mode out-of-domain. |
| Ambiguous expected targets | Rejected an overspecific rolling-window query that was also in `upstream_signals`. Rejected a 0.7-fallback lexical query that was also in `input_fields_consumed`. Rejected fire-path "what changed" as near-OOD because `scope` answers it. sem-003 gold is consumer, not verdict, because only consumer describes GATE:REGIME. |
| Trivial wording | Labels in spec-002 are not named. Stamp interval `30` is not named in lex-002. GATE:REGIME is not named in sem-003. |
| Expected evidence in the source | Cited from `data/2026-08-10_regime_factor_composition_trace.md` headings/bodies above, not from rankings. |
| Duplicate / paraphrase probes | sem-003 ≠ sem-001/002 (block-path split vs score-definition vs disposition). lex-002 ≠ lex-001 (stamp interval vs producer scalar). mch-001 names both ends; hop-001 does not. |
| Lexical vs semantic | Decision rule from the failure-mode map applied. |
| Multi-chunk vs multi-hop | mch-001 `hops: single` with two golds; hop-001 `hops: multi` with empty expected. |
| OOD asking in-corpus questions | Far baseball query is unsupported. Near COMPRESS procedure is mentioned, not answered. Scope/fire-path-change candidate was rejected. |
| Wording around known rankings | New queries were not adjusted using `retrieve()` output. Calibration ranks were not used to retune new wording. |
| One primary mode | All 12 assigned. |
| Fake OOD gold | None. |
| Retriever change required to represent a row | No. Unmeasurable outcome labeling only. |

Rejected candidates (not in the set):

- "What fire-path or launcher changes were made in this pass?" — answered by `scope`.
- Overspecific `vol_p95` / rolling-window ask — also in `upstream_signals_since_verdict_independent`.
- Lexical "default confidence number when state mapping is missing" — `0.7` appears in both consumer and `input_fields_consumed`.
- Multi-hop "classifier named in the independence verdict → input scalar" — verdict already names `vwap_dist`, so hop 2 is not dependent on this corpus.
- Broad "What does regime refer to in this note?" as a **semantic** gold row — no unique expected; kept only as spec-001 underspecific/unmeasurable.

## What this commit does not do

Does not implement or tune: dense embeddings, BM25, reranking, query expansion, alias changes, weight changes, thresholds, OOD rejection, score normalization, GraphRAG, entity resolution, multi-vector retrieval, hop controller, reader/LLM synthesis, learned models, new chunking, corpus changes, OOV telemetry, or extra observability beyond mapping `unmeasurable` so it is not labeled `miss`.

Does not run the expanded control. That run is a later commit, against these locked bytes.

## Future rank movement (definition only; not computed here)

When a later experiment is compared to the expanded control:

`rank_gain = control_rank - experiment_rank`

Examples: `10 → 4` is `+6`; `2 → 3` is `-1`; `2 → 2` is `0`. Rank gain is not computed until an experiment exists.

## References

- Failure-mode map and change discipline: `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
- Schema axes: `docs/design_notes/2026-09-24_taxonomy_schema_design.md`
- Section-id / multi-doc: `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md`
- Frozen baseline: `docs/query_set_expansion/2026-09-28_retrieval_baseline.md`
- Expected-target telemetry: `docs/query_set_expansion/2026-09-28_expected_target_telemetry.md`
- Source corpus: `data/2026-08-10_regime_factor_composition_trace.md`
