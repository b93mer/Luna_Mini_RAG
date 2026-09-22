# Loose-docs contrast — findings

**Date:** 2026-09-22
**Branch:** `research/loose-docs-contrast` (off main = `v0.1.0-poc-baseline`)
**Chunker:** v1 (`smart_chunker.py`), unchanged
**Paired experiment:** `research/chunker-v2-adversarial` (adversarial docs, chunker v2)
**Scripts:** `run_ablation.py`, `score_decomposition.py` (this directory; logic unchanged from the v1 ablation)

## Pre-registered prediction

*(Written before `ingest` was run on the 3-doc corpus and before any
ablation output was seen.)*

Because the new docs share topical vocabulary but not the exact section_id slugs, we predict:

1. **Alias boost still fires only for the original doc's sections.**
2. **Cosine margins in config D will shrink but not invert.**
3. **Overall pass/fail unchanged from v1.**

If this prediction holds, it confirms the alias table is the decisive component and that lexical adversarial pressure is what breaks it — not corpus growth alone.

**Outcome vs predictions:** recorded in the Interpretation section below, after the Results.

## Hypothesis

*(Copied from v1 findings.)*

- **H0:** TF-IDF cosine alone is sufficient to retrieve the three target sections in top-3 for their gold queries.
- **H1:** Cosine alone fails on at least one gold query and either lexical overlap or alias boost is decisive.

## Method

Same five configurations as the v1 ablation — (A) baseline `retrieve()` as written; (B) `alias_boost` monkeypatched to 0.0; (C) local wrapper with lexical weight 0; (D) pure TF-IDF cosine; (E) `retrieve_by_section_id` monkeypatched to `None`. What changed vs v1: **only the corpus** — `data/session_review_1.md` and `data/session_review_2.md` added (loose docs: shared topical vocabulary, no hardcoded section_id slugs), and `metadata/chunks.json` regenerated with the v1 chunker (restored to frozen bytes after the run). Chunker, gold queries, metrics, and scripts are unchanged from the v1 ablation.

## Results

Corpus: 3 docs → 74 chunks via the v1 chunker (trace note 15, session reviews 59 combined). All five configurations PASS (expected section top-3 — in fact top-1 — on all three gold queries). Full stdout: `ablation_stdout.txt` (committed).

| Config | Query (gold) | Expected section | Rank | Top-1? | Top-3? | Margin over runner-up |
|---|---|---|---|---|---|---|
| A baseline | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.6746 |
| A baseline | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.5468 |
| A baseline | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7550 |
| B no alias boost | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.1746 |
| B no alias boost | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.0468 |
| B no alias boost | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.2550 |
| C no lexical overlap | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.6304 |
| C no lexical overlap | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.5167 |
| C no lexical overlap | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7540 |
| D pure cosine only | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.1304 |
| D pure cosine only | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.0167 |
| D pure cosine only | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.2540 |
| E no section_id lookup | (fallback alias query) | question | 1 | yes | yes | +0.7439 |
| E no section_id lookup | (fallback alias query) | verdict | 1 | yes | yes | +0.5468 |
| E no section_id lookup | (fallback alias query) | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.8195 |

## Delta vs v1

Margins per config per query, v1 (1 doc) → loose-docs (3 docs). **Scale caveat:** the two runs use separately fitted TF-IDF models (the 3-doc corpus changed the vocabulary and IDF), so directions are meaningful but magnitudes are not calibrated against each other.

| Query | Config | v1 margin | loose-docs margin | Direction |
|---|---|---|---|---|
| question | A | +0.5924 | +0.6746 | up |
| question | B | +0.0924 | +0.1746 | up |
| question | C | +0.5482 | +0.6304 | up |
| question | D | +0.0482 | +0.1304 | **up** (predicted: shrink) |
| verdict | A | +0.6031 | +0.5468 | down |
| verdict | B | +0.1031 | +0.0468 | down |
| verdict | C | +0.5730 | +0.5167 | down |
| verdict | D | +0.0730 | +0.0167 | **down, thinnest margin recorded in any experiment so far** |
| finding 3.5 | A | +0.7508 | +0.7550 | up |
| finding 3.5 | B | +0.2508 | +0.2550 | up |
| finding 3.5 | C | +0.7433 | +0.7540 | up |
| finding 3.5 | D | +0.2433 | +0.2540 | **up** (predicted: shrink) |
| question | E | +0.7113 | +0.7439 | up |
| verdict | E | +0.5305 | +0.5386 | up |
| finding 3.5 | E | +0.8456 | +0.8195 | down |

## Score decomposition summary

Full tables: `decomposition.md` (committed). Under baseline:

- Alias boost remains a flat +0.50 on the expected chunk and the largest single component (~57–59% of the winner's total). It fired **only** on the trace doc's three target sections; every session-review chunk scored 0.00 alias.
- Loose docs are visible but weak competitors: the best session-review chunk is `2026-08-24_session_review::0_scorer_attention_analysis_paste` at rank 2 for the `finding 3.5` query (raw cosine 0.1061 vs winner 0.4690). No session-review chunk reaches top-5 for the `question` or `verdict` queries.
- `verdict`'s runner-up is again same-doc `input_fields_consumed` (raw 0.3587 vs winner 0.3826 — a raw gap of 0.0239). The thin config-D margin (+0.0167) is driven by the trace note's own table section, not by the new docs.
- Lexical overlap remains minor and never decisive (weighted ≤ 0.0714).

## Interpretation

- **No ablation broke retrieval.** All five configs returned all three targets at rank 1, matching v1 pass/fail exactly.
- **Corpus growth with topical overlap did not stress the retriever.** Session-review chunks barely enter the top-5. The loose docs share vocabulary (regime, conviction, EV) but lack the distinctive query n-grams, and TF-IDF's IDF discounts exactly the shared terms.
- **`verdict` under pure cosine is the consistent soft spot across all three experiments**: +0.0730 (v1) → +0.0222 (adversarial v2) → +0.0167 (loose docs). The driver in both multi-doc runs is same-doc competition from `input_fields_consumed`, not the added docs. This is a property of the trace doc's structure, not of corpus composition.
- **Section_id collisions (v1 chunker, surfaced per task item 5):** 22 section_ids are shared across the two session reviews — the reviews use an identical heading template (`1_session_summary`, `3_fire`, `cycle`, `discipline`, `draft_date`, etc.). None of the three target ids (`question`, `verdict`, `impact_on_finding_3_5_disposition`) are collided, so this experiment is unaffected. But `store.get_by_section_id` returns the FIRST match, so any direct lookup or alias keyed on a collided id would silently bind to an arbitrary doc. This is the v1 chunker's per-doc-uniqueness weakness made concrete, and it is the strongest argument so far for the chunker-v2 `doc_id::` prefixing.
- **The pre-registered interpretive framing overreaches.** The prediction block says that if the predictions hold, "it confirms the alias table is the decisive component." The results do not support that clause: configs B and D (alias fully removed) pass on every corpus tested so far, so the alias table is decisive for *score mass*, not for *correctness*. What these results do support: corpus growth alone (1 → 3 docs, topical overlap) does not break cosine retrieval of these three targets.

## Falsification outcome

**H0 was not rejected** on the loose-docs 3-doc corpus: pure TF-IDF cosine (config D) retrieved all three target sections at rank 1 for all three gold queries. This is the third corpus on which H0 survives. The `verdict` pass is soft (+0.0167, the thinnest margin recorded); the other two are comfortable.

## Prediction outcome

1. **"Alias boost still fires only for the original doc's sections" — HELD.** Decomposition shows +0.50 alias only on the trace doc's three target chunks; all 59 session-review chunks scored 0.00.
2. **"Cosine margins in config D will shrink but not invert" — PARTIALLY HELD.** Nothing inverted (held). But only `verdict` shrank (+0.0730 → +0.0167); `question` (+0.0482 → +0.1304) and `finding 3.5` (+0.2433 → +0.2540) margins *grew*. The blanket "will shrink" did not hold for 2 of 3 queries.
3. **"Overall pass/fail unchanged from v1" — HELD.** Identical pass pattern: all configs, all queries, top-1.

The closing interpretive clause of the prediction ("confirms the alias table is the decisive component") is **not supported** by the results — see Interpretation. Stated plainly: the predictions about behavior mostly held; the prediction about what the behavior would *mean* did not.

## Caveats

3-doc corpus is still small, and the two added docs are session reviews with topical but not structural overlap — a middle-difficulty competitor between the v1 single-doc baseline and the adversarial branch. Cross-corpus margin comparisons carry the IDF-rescaling caveat (separately fitted models; directions meaningful, magnitudes not calibrated). The 22 colliding section_ids mean this corpus would be unsafe for any lookup keyed on non-target ids; results here are valid only because the three target ids happen to remain unique.

## Review footnotes

1. The pre-registered prediction and Method sections reference placeholder filenames `session_review_1.md` / `session_review_2.md`; the landed files are `data/2026-08-21_session_review.md` and `data/2026-08-24_session_review.md`. Same role, final names. (The run_ablation.py / score_decomposition.py docstrings carry the same placeholder names; scripts were frozen per task constraints.)
2. The prediction block was committed (e900d4d) before ingest ran; it had been written-but-uncommitted at branch setup, and was committed as-is to make the pre-registration real. No text was changed in that commit or after.

## Synthesis across experiments

Both multi-doc branches now have results. Factual summary:

| Experiment | Corpus | Chunker | All configs pass? | Thinnest D margin |
|---|---|---|---|---|
| v1 ablation | 1 doc | v1 | yes | +0.0482 (question) |
| chunker-v2-adversarial | 3 docs, hostile vocabulary | v2 | yes | +0.0222 (verdict) |
| loose-docs-contrast | 3 docs, topical vocabulary | v1 | yes | +0.0167 (verdict) |

Across all three: no config ever failed; alias boost was never decisive for correctness; `verdict` is the persistent soft spot and its competitor is always the same-doc `input_fields_consumed` table. Neither corpus growth nor adversarial vocabulary broke cosine retrieval, because the gold queries carry distinctive exact n-grams. The two structural findings for a future cross-experiment doc: (a) v1 chunker section_id collisions (22 here) make direct lookup unsafe in multi-doc regimes — chunker v2's prefixing addresses it; (b) the next falsification lever is paraphrased gold queries that strip the distinctive n-grams, not a larger or more hostile corpus.
