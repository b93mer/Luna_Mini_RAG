# Retrieval baseline: frozen stack vs the three-row docqa set

**Date:** 2026-09-28 (run executed 2026-09-29T03:05:19Z; the logger names run
files by UTC date)
**Status:** Frozen baseline. Comparison point for all future retrieval
hypotheses and architecture changes on this branch line.
**Governs:** what "the current system" means numerically. Does not change the
pipeline.
**Change discipline:** `docs/query_set_expansion/2026-09-26_failure_mode_map.md`
("Query set change discipline") — this document follows it; it is not
restated here.

## Role of this baseline

This run establishes the empirical behavior of the frozen current stack. It
is the comparison point for future retrieval hypotheses and architecture
changes. Future experiments should be able to answer, relative to this
document:

1. What changed relative to this baseline?
2. Which failure modes improved or regressed?
3. Did the change behave according to its hypothesis?
4. Did it improve one slice while damaging another?
5. Is the evidence strong enough to justify retaining the architectural
   change?

Predictions below are the pre-registered `current_stack_prediction` values
from the query set. Observations are what the frozen stack did. The two are
kept separate deliberately: a prediction that disagrees with an observation
is a map correction (dated reclassification), never a retrofitted prediction.

## State under test

| Piece | Identity |
| --- | --- |
| Branch | `query-set-expansion` |
| Code at run time | HEAD `bc94ba8` (`feat(query_logger): append-only per-run JSONL trace...`) plus two working-tree changes committed alongside this document: the dated `current_stack_after_run` reclassification on `qse-docqa-sem-002` in `eval_sets/docqa.yaml` (a map correction, allowed by the change discipline), and a `metadata/chunks.json` rebuild that changed only `built_at` / `captured_at` timestamps (verified: no non-timestamp diff lines) |
| Freeze commit | The commit containing this document is the freeze point for the evaluation sequence |
| Query set | `eval_sets/docqa.yaml`, 3 rows, sha256 as run `F70CC5A77D1451A4355C823125A34C760A37E37BFBF8FB644FF68C2D38452B4E` |
| Index | `metadata/chunks.json`, 15 chunks from `data/2026-08-10_regime_factor_composition_trace.md`, `built_at` 2026-09-29T03:05:10Z, sha256 as run `B4CFF81DECBFBBE5CEDBDFB3133BF66EFF3EBAEB6E77D124B937A6B296C4690C` |
| Retrieval path | `retrieve.retrieve()` hybrid only. The exact `section_id` lookup path is not exercised by this runner |
| Scoring formula | `score = 0.7 * cosine(TF-IDF) + 0.3 * Jaccard(query, heading+text) + alias_boost`; alias `+0.5` for three section ids' substring lists, `+0.35` when the query contains a chunk's full section id with underscores as spaces; no score floor; full scan over all 15 chunks |
| TOP_K | 5 (`run_query_set.TOP_K`) |
| Runner / trace | `run_query_set.py` → `query_logger.py`; raw record `eval_sets/runs/2026-09-29_run-001.jsonl` |
| Checks at freeze | `pytest tests` 4/4 pass; `python evaluate.py` PASS (run immediately before the baseline run; it re-ingests, which is why `built_at` is 2026-09-29T03:05:10Z) |

**Freeze note.** For purposes of this evaluation sequence the retriever
(`retrieve.py` scoring, weights, alias table) and the three-row query set are
frozen as of the freeze commit. This is a recorded convention, not enforced
machinery: the repo's mechanism for such records is dated documents like this
one, plus a pointer note in the `retrieve.py` module docstring. Unfreezing
happens only through a pre-registered hypothesis measured against this
baseline.

## Results

Observed top-k per row, scores from the JSONL trace (6dp). `alias` was 0.0 on
every hit in every row and is omitted from the tables.

### qse-docqa-sem-001 — semantic gap — route_s

Query: "What does the regime-related score represent when it contributes to
the conviction assessment?"
Expected: `1_upstream_producer_score_definition`
Pre-registered prediction: `expected_miss`

| Rank | section_id | score | cosine | lexical |
| --- | --- | --- | --- | --- |
| 1 | `verdict` | 0.316521 | 0.398602 | 0.125000 |
| 2 | `question` | 0.211679 | 0.241174 | 0.142857 |
| 3 | `impact_on_finding_3_5_disposition` | 0.186431 | 0.238455 | 0.065041 |
| 4 | `2_state_stamp_before_conviction` | 0.150369 | 0.177867 | 0.086207 |
| 5 | `3_conviction_factor_entry_the_field_under_audit` | 0.149853 | 0.184519 | 0.068966 |

Observed: expected section **not in top-k** → outcome `expected_miss`.
Prediction and observation agree.

### qse-docqa-sem-002 — semantic gap — route_s

Query: "What does the regime control determine about the status of the
existing finding?"
Expected: `impact_on_finding_3_5_disposition`
Pre-registered prediction: `expected_miss`

| Rank | section_id | score | cosine | lexical |
| --- | --- | --- | --- | --- |
| 1 | `verdict` | 0.263968 | 0.341383 | 0.083333 |
| 2 | `impact_on_finding_3_5_disposition` | 0.250598 | 0.337091 | 0.048780 |
| 3 | `question` | 0.161431 | 0.182996 | 0.111111 |
| 4 | `input_fields_consumed` | 0.131249 | 0.173214 | 0.033333 |
| 5 | `3_conviction_factor_entry_the_field_under_audit` | 0.117338 | 0.147921 | 0.045977 |

Observed: expected section **in top-k at rank 2** → outcome `hit`.
Prediction and observation **disagree**. This row was already reclassified
on 2026-09-26 (`current_stack_after_run: hit` with dated `after_run_note` in
`docqa.yaml`), the correction the change discipline allows; the prediction
field stays `expected_miss`. The margin to rank 1 is 0.013370 of blended
score. The note's numbers match this trace.

### qse-docqa-lex-001 — lexical gap — route_s

Query: "Which upstream market-condition measure supplies the consistency
signal used when assessing trade confidence?"
Expected: `1_upstream_producer_score_definition`
Pre-registered prediction: `expected_miss`

| Rank | section_id | score | cosine | lexical |
| --- | --- | --- | --- | --- |
| 1 | `upstream_signals_since_verdict_independent` | 0.143566 | 0.189788 | 0.035714 |
| 2 | `verdict` | 0.103335 | 0.139685 | 0.018519 |
| 3 | `impact_on_finding_3_5_disposition` | 0.080765 | 0.105412 | 0.023256 |
| 4 | `3_conviction_factor_entry_the_field_under_audit` | 0.072138 | 0.088926 | 0.032967 |
| 5 | `2_state_stamp_before_conviction` | 0.059904 | 0.071752 | 0.032258 |

Observed: expected section **not in top-k** → outcome `expected_miss`.
Prediction and observation agree.

### Aggregate

| outcome | count |
| --- | --- |
| hit | 1 |
| miss | 0 |
| expected_miss | 2 |

Predictions matched observations on 2 of 3 rows. No row produced an
unpredicted `miss` (a hit predicted `supported` that failed — none exist in
this set).

## Reproducibility

The same three rows were run on 2026-09-27 (`eval_sets/runs/2026-09-27_run-001.jsonl`,
committed in `bc94ba8`) and again for this baseline. Excluding `ts_utc` and
`query_uuid`, the two traces are identical row-for-row and hit-for-hit:
TF-IDF + Jaccard + alias over an unchanged corpus is deterministic, and the
index rebuild between the runs changed only timestamps. This run therefore
confirms the 2026-09-27 record rather than replacing it.

## Surprising observations

Recorded as observed; none of these is reinterpreted to fit a prediction.

- **The polysemy row that was supposed to miss, hit.** sem-002 was designed
  so the RegimeBoss sense of "regime" would lose to the conviction sense.
  Instead the expected section ranked 2nd, 0.0134 behind `verdict`, with no
  alias help and with the deliberately avoided anchor vocabulary absent.
  Whatever disambiguates the two senses here lives in ordinary context
  tokens, and it was enough for top-5 (though not for rank 1).
- **`verdict` is rank 1 on both semantic-gap rows regardless of sense.** The
  conviction-sense query (sem-001) and the RegimeBoss-sense query (sem-002)
  both put `verdict` first. The sense split these rows probe is happening —
  or failing — below rank 1, and top-1 accuracy would hide it entirely.
- **The expected target is absent from the top-k on both rows that target
  it.** `1_upstream_producer_score_definition` does not appear at any rank
  1–5 for sem-001 or lex-001. Where it actually ranks (6th? 15th?) is not
  observable from a top-k trace; see the trace-validation document for what
  that means diagnostically.
- **The alias boost never fired.** All 15 logged hits across the three rows
  have `alias = 0.0`. Every outcome above is pure `0.7*cosine + 0.3*Jaccard`.
  The rows were designed that way; the baseline confirms the design held.
- **lex-001's rank 1 is a lexical near-miss, not a random one.**
  `upstream_signals_since_verdict_independent` shares the query's surface
  vocabulary ("upstream", "signals") but is the wrong section — the exact
  shape the lexical-gap hypothesis predicts for a closed-vocabulary stack.

## What this baseline is not

- Not coverage: 3 rows, 2 failure modes (semantic gap, lexical gap), 1
  document, 15 chunks. The `not_list` in the query-set manifest applies.
- Not a retriever change: nothing in this commit alters ranking behavior.
- Not the observation-mechanism check: validation of the JSONL trace itself
  is a separate document (`2026-09-28_trace_validation.md`).

## References

- Query set: `eval_sets/docqa.yaml` (manifest `governs` the failure-mode map).
- Change discipline, failure-mode definitions, route tags:
  `docs/query_set_expansion/2026-09-26_failure_mode_map.md`.
- Schema axes and growth-route deferral:
  `docs/design_notes/2026-09-24_taxonomy_schema_design.md`.
- Lookup-path decision this runner does not exercise:
  `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md`.
- Raw trace: `eval_sets/runs/2026-09-29_run-001.jsonl` (and its deterministic
  twin `eval_sets/runs/2026-09-27_run-001.jsonl`).
