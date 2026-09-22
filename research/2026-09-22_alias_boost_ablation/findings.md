# Alias-boost ablation — findings

**Date:** 2026-09-22
**Branch:** `research/alias-boost-ablation`
**Baseline:** `v0.1.0-poc-baseline` (frozen; pipeline files untouched)
**Scripts:** `run_ablation.py`, `score_decomposition.py` (this directory)

## Hypothesis

- **H0:** TF-IDF cosine alone is sufficient to retrieve the three target sections in top-3 for their gold queries.
- **H1:** Cosine alone fails on at least one gold query and either lexical overlap or alias boost is decisive.

## Method

For each of the 3 gold queries in `evaluate.QUERIES`, retrieval was run under 5 configurations: (A) baseline `retrieve()` as written; (B) `retrieve.alias_boost` monkeypatched to return 0.0; (C) local scoring wrapper with the lexical-overlap weight set to 0 (0.7·cosine + alias); (D) pure TF-IDF cosine (alias monkeypatched to 0 **and** lexical weight 0); (E) `retrieve_by_section_id` monkeypatched to `None` so `retrieve_target_sections()` must resolve targets through its `retrieve()` fallback path. For each configuration and query we recorded the rank of the expected `section_id`, top-1/top-3 membership, and the margin between the expected chunk's score and the best-scoring non-expected chunk (runner-up). A sanity check confirmed the local wrapper with baseline weights reproduces `retrieve()`'s top-3 ordering exactly, so C/D measure the same retriever. The index (`metadata/chunks.json`) was read-only throughout; no pipeline file was edited.

## Results

| Config | Query (gold) | Expected section | Rank | Top-1? | Top-3? | Margin over runner-up |
|---|---|---|---|---|---|---|
| A baseline | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.5924 |
| A baseline | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.6031 |
| A baseline | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7508 |
| B no alias boost | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.0924 |
| B no alias boost | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.1031 |
| B no alias boost | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.2508 |
| C no lexical overlap | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.5482 |
| C no lexical overlap | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.5730 |
| C no lexical overlap | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7433 |
| D pure cosine only | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.0482 |
| D pure cosine only | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.0730 |
| D pure cosine only | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.2433 |
| E no section_id lookup | (fallback alias query) | question | 1 | yes | yes | +0.7113 |
| E no section_id lookup | (fallback alias query) | verdict | 1 | yes | yes | +0.5305 |
| E no section_id lookup | (fallback alias query) | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.8456 |

All five configurations PASS (expected section in top-3 — in fact top-1 — for all three gold queries).

## Score decomposition summary

Under baseline, the **alias boost dominates the total score** for every gold query: a flat +0.50 on the expected chunk, versus weighted cosine contributions of 0.27–0.34 and weighted lexical contributions of 0.02–0.07. Alias accounts for roughly 56–61% of the winning chunk's total on all three queries.

However, the decomposition also shows the expected chunk already has the **highest raw cosine** before any boost:

| Query | Expected raw cosine | Runner-up raw cosine | Cosine-only gap |
|---|---|---|---|
| question | 0.3907 | 0.3218 (verdict) | +0.0689 |
| verdict | 0.4854 | 0.3812 (input_fields_consumed) | +0.1042 |
| finding 3.5 | 0.4301 | 0.0826 (verification_this_pass) | +0.3475 |

Lexical overlap is a minor term everywhere (weighted ≤ 0.0714) and is never decisive: removing it (config C) changes margins by ≤ 0.044.

## Interpretation

- **No ablation broke retrieval.** Every configuration, including pure cosine (D), returned the expected section at rank 1 for all three gold queries.
- **Alias boost is not decisive for correctness on this corpus, but it is doing most of the margin work.** Removing it (B) shrinks margins by 5–6× on `question` (+0.5924 → +0.0924) and `verdict` (+0.6031 → +0.1031). The boost is a confidence amplifier, not a retrieval signal, on these queries.
- **Pure-cosine margins on `question` (+0.0482) and `verdict` (+0.0730) are thin.** These are soft passes. The runner-up in both cases is a thematically adjacent section of the same document (`verdict`, `input_fields_consumed`), so a small perturbation — more documents, a rechunk, a paraphrased query — could plausibly flip the ranking. The `finding 3.5` query is the only comfortable cosine-only pass (+0.2433), because "Finding 3.5 disposition" is distinctive vocabulary with no competitor in the corpus.
- **The section_id fallback (E) is fully redundant on this corpus** — the alias-query fallback path retrieves all three targets at rank 1 with the largest margins observed, because the alias strings are near-verbatim section names.

## Falsification outcome

**H0 was not rejected.** Pure TF-IDF cosine (config D) retrieved all three target sections in top-3 — specifically at rank 1 — for all three gold queries. H1's condition (cosine alone failing at least one gold query) did not occur.

This should be read narrowly: H0 survives **on this corpus with these queries**, and two of the three cosine-only passes rest on margins under 0.08. The evidence supports "cosine is sufficient here," not "the hybrid terms are useless" — the alias boost clearly owns the score mass under baseline, and its value would likely appear first as robustness (margin) rather than correctness (top-k) exactly when the corpus gets more competitive.

## Caveats

This ablation runs on a **single-document corpus** (15 chunks, all from one note). Margins may be artificially inflated because there is no competition for top-k — there is exactly one `question`, one `verdict`, and one `finding 3.5` section in existence, and the gold queries name them nearly verbatim. Results establish a **baseline for comparison against multi-doc expansion**, not a general claim about retriever quality. Additionally, config D's margins are reported on the 0.7·cosine scale (kept for comparability with A–C); raw-cosine margins are larger by a factor of 1/0.7 but identically ranked.

## Next hypothesis

*(Stub — to be filled after multi-doc expansion.)* Does the ablation result hold when the corpus grows from 1 doc to 3 (`system_architecture.md`, `priority_queue.md` added)? Specifically: do configurations that passed on 1 doc still pass when there are additional sections competing for top-k? The thin pure-cosine margins on `question` (+0.0482) and `verdict` (+0.0730) are the predicted failure points; if H1 is going to show anywhere, it is there.
