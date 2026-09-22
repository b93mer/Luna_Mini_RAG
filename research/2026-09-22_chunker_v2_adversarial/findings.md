# Chunker v2 + adversarial multi-doc ablation — findings

**Date:** 2026-09-22
**Branch:** `research/chunker-v2-adversarial`
**Baseline:** `v0.1.0-poc-baseline` (frozen; v1 pipeline files untouched)
**Prior experiment:** `research/2026-09-22_alias_boost_ablation/findings.md` (v1, 1-doc corpus)
**Scripts:** `run_ablation_v2.py`, `score_decomposition_v2.py` (this directory)

## Pre-registered prediction

*(Written before `ingest_v2` was run on the 3-doc corpus and before any
ablation output was seen.)*

Under adversarial competition from two same-domain operational docs, we predict:

1. **`question` and `verdict` margins under config D (pure cosine) will
   invert** — the retriever will pick a passage from one of the new docs,
   not the original verdict section.
2. **`finding 3.5` under D will degrade from +0.24 to under +0.05** but
   may not invert, because `impact_on_finding_3_5_disposition` is a
   distinctive slug.
3. **Alias boost (configs A, B, E) will artificially preserve the win**
   because `SECTION_ALIASES` is keyed on section_ids that only exist in
   the original doc.

**Outcome vs predictions (recorded after the run, honestly):**

1. **FAILED.** Neither `question` nor `verdict` inverted under config D. Both expected sections still ranked 1 with positive margins (+0.0854 and +0.0222 respectively). The predicted direction held only for `verdict` (margin thinned from +0.0730 to +0.0222); the `question` margin actually *widened* (+0.0482 → +0.0854).
2. **FAILED.** `finding 3.5` under D did not degrade below +0.05 — it slightly *increased* (+0.2433 → +0.2567). The distinctive vocabulary ("finding", "3.5", "disposition") still has almost no competition; the priority queue's Finding 3.5 row sits inside a long table chunk with diluted term frequency.
3. **PARTIALLY HELD.** Alias-active configs (A, C, E) did preserve large margins (+0.52 to +0.79), and the boost still owns ~58–60% of the winner's total score. But the "artificially preserve the win" framing is not supported: configs B and D (no alias at all) also passed top-3 on all three queries, so the boost is not what preserves correctness.

## Hypothesis

*(Copied from v1 findings.)*

- **H0:** TF-IDF cosine alone is sufficient to retrieve the three target sections in top-3 for their gold queries.
- **H1:** Cosine alone fails on at least one gold query and either lexical overlap or alias boost is decisive.

## Method

Same five configurations as the v1 ablation — (A) baseline `retrieve()` as written; (B) `alias_boost` monkeypatched to 0.0; (C) local wrapper with lexical weight 0; (D) pure TF-IDF cosine (alias 0 and lexical weight 0); (E) `retrieve_by_section_id` monkeypatched to `None` so `retrieve_target_sections()` must use its `retrieve()` fallback — with three changes vs v1:

1. **Chunker v2** (`smart_chunker_v2.py`): recursive splitter adding body field-run detection, a rule → paragraph → sentence size cascade (MAX_SECTION_CHARS=2000), and doc_id-prefixed corpus-unique section ids. v1 chunker untouched.
2. **Corpus grew 1 → 3 docs**: `data/system_architecture.md` and `data/priority_queue.md` added — same-domain operational docs with heavy lexical overlap with the gold queries (regime, EV, conviction, Finding 3.5, verdict-adjacent vocabulary).
3. **Index**: `metadata/chunks_v2.json` via `store_v2.py` / `ingest_v2.py`; `retrieve.load_store` monkeypatched so `retrieve()` runs as written against the v2 index. `SECTION_ALIASES` re-keyed onto doc_id-prefixed ids (suffix match) so the boost retains v1 semantics under the new id scheme.

Gold queries unchanged (`evaluate.QUERIES`). Metrics unchanged: rank of expected section, top-1/top-3 membership, margin over runner-up.

## Results

Corpus: 3 docs → 90 chunks (trace note 15, system_architecture 46, priority_queue 29). All five configurations PASS (expected section top-3 — in fact top-1 — on all three gold queries).

| Config | Query (gold) | Expected section | Rank | Top-1? | Top-3? | Margin over runner-up |
|---|---|---|---|---|---|---|
| A baseline | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.6318 |
| A baseline | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.5524 |
| A baseline | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7643 |
| B no alias boost | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.1318 |
| B no alias boost | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.0524 |
| B no alias boost | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.2643 |
| C no lexical overlap | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.5854 |
| C no lexical overlap | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.5222 |
| C no lexical overlap | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7567 |
| D pure cosine only | What is the question about conviction_detail.factors regime? | question | 1 | yes | yes | +0.0854 |
| D pure cosine only | What is the verdict on whether the regime factor is independent of block_type? | verdict | 1 | yes | yes | +0.0222 |
| D pure cosine only | Does this change Finding 3.5 disposition? | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.2567 |
| E no section_id lookup | (fallback alias query) | question | 1 | yes | yes | +0.6787 |
| E no section_id lookup | (fallback alias query) | verdict | 1 | yes | yes | +0.5468 |
| E no section_id lookup | (fallback alias query) | impact_on_finding_3_5_disposition | 1 | yes | yes | +0.7920 |

## Delta vs v1

Margins per config per query, v1 (1 doc) → v2 (3 adversarial docs). **Scale caveat:** the two runs use separately fitted TF-IDF models (the v2 corpus changed the vocabulary and IDF), so directions are meaningful but magnitudes are not calibrated against each other.

| Query | Config | v1 margin | v2 margin | Direction |
|---|---|---|---|---|
| question | A | +0.5924 | +0.6318 | up |
| question | B | +0.0924 | +0.1318 | up |
| question | C | +0.5482 | +0.5854 | up |
| question | D | +0.0482 | +0.0854 | **up** (predicted: invert) |
| verdict | A | +0.6031 | +0.5524 | down |
| verdict | B | +0.1031 | +0.0524 | down |
| verdict | C | +0.5730 | +0.5222 | down |
| verdict | D | +0.0730 | +0.0222 | **down, thin** (predicted: invert — direction only) |
| finding 3.5 | A | +0.7508 | +0.7643 | up |
| finding 3.5 | B | +0.2508 | +0.2643 | up |
| finding 3.5 | C | +0.7433 | +0.7567 | up |
| finding 3.5 | D | +0.2433 | +0.2567 | **up** (predicted: under +0.05) |
| question | E | +0.7113 | +0.6787 | down |
| verdict | E | +0.5305 | +0.5468 | up |
| finding 3.5 | E | +0.8456 | +0.7920 | down |

## Score decomposition summary

Under baseline, the alias boost remains a flat +0.50 on the expected chunk and still dominates the winner's total (~58–60% on all three queries). The v2-specific observations:

- **Adversarial chunks now occupy runner-up slots.** For the `question` query, rank 2 is `system_architecture::three_ev_objects...__part4` (raw cosine 0.2928 vs winner 0.4148). For `finding 3.5`, `priority_queue::now_active_focus__part2` takes rank 3 (raw 0.0871). Competition is visible; it is just not decisive yet.
- **The `question`-query runner-up is a chunker artifact.** `...__part4` is a **10-character fragment** ("**Direction**" plus table separator residue) produced by the v2 size cascade splitting around bold subheadings and tables. Tiny chunks get inflated raw cosine because one matching term dominates their term frequency. This is a v2 chunker weakness, not a retrieval signal.
- **`verdict`'s real competitor is still same-doc.** `input_fields_consumed` (raw 0.4278 vs winner 0.4595 — a raw gap of only 0.0317) outranks every adversarial chunk. The thin config-D margin (+0.0222) is driven by the trace note's own table section, not the new docs.
- Lexical overlap remains a minor, never-decisive term (weighted ≤ 0.0714; removing it changes margins by ≤ 0.046).

## Interpretation

- **No ablation broke retrieval, again.** All five configs returned all three targets at rank 1. The adversarial docs are visible in top-5 (rank 2 for `question`) but never outrank a target.
- **The pre-registered inversion predictions failed.** The corpus grew 3× with deliberately hostile vocabulary and pure cosine still held. Where the predicted *direction* appeared (`verdict` under D), the driver was same-doc competition, not the adversarial docs.
- **Why the predictions missed:** the gold queries contain near-unique n-grams (`conviction_detail.factors`, `independent of block_type`, `finding 3.5 disposition`) that exist verbatim only in the trace note. Lexical overlap of *general domain vocabulary* (regime, EV, conviction) turned out not to compete with exact distinctive phrases. TF-IDF's IDF term actively rewards this: rare query terms get high weight, and they are rare precisely because the adversarial docs don't contain them.
- **Alias boost: same verdict as v1, stronger evidence.** It owns the score mass (~58–60% of winner totals) but is decisive for correctness nowhere. It is a margin amplifier.
- **New failure mode found (chunker-side):** the v2 size cascade emits tiny fragments (6–10 chars) around bold subheadings/tables, and those fragments are spuriously competitive on raw cosine. On a larger corpus this class of fragment could take top-1 by accident.

## Falsification outcome

**H0 was not rejected** on the 3-doc adversarial corpus: pure TF-IDF cosine (config D) retrieved all three target sections at rank 1 for all three gold queries. H1's condition did not occur.

Honest framing: this is now *two* corpora on which H0 survives, but the `verdict` config-D margin (+0.0222) is a soft pass, and the `question` runner-up being a 10-char artifact means the measured margin overstates the real robustness of that ranking. The pre-registered predictions were mostly wrong — the adversarial docs stress general vocabulary overlap, while the gold queries win on distinctive exact phrases. H1 may need queries that *lack* distinctive n-grams (paraphrased gold queries) rather than a more hostile corpus.

## Caveats

This test uses adversarial docs specifically chosen for lexical overlap with the gold queries — `system_architecture.md` and `priority_queue.md` discuss the same regime/EV/conviction subsystem vocabulary as the trace note, so they are near-worst-case competitors, not a representative sample of a growing corpus. A loose-docs contrast test (branch `research/loose-docs-contrast`) is queued as the paired experiment. Corpus is still small (3 docs); margins at this scale indicate direction, not magnitude, of the effect.

Additional v2-specific caveats:

1. Chunker v2's doc_id-prefixed section ids mean the v1 direct `section_id` lookup path (`retrieve_by_section_id`) cannot match anything on the v2 index — config E's fallback is the de facto path under the v2 id scheme, not just an ablation.
2. The v1↔v2 delta table compares scores from two separately fitted TF-IDF models; IDF rescaling means only directions, not magnitudes, should be read across corpora.
3. The v2 cascade's tiny-fragment chunks (e.g. a 10-char `__part4`) inflate cosine competition artificially and contaminate the runner-up margin measurement for at least the `question` query.

## Next hypothesis

*(Stub — to be filled after the loose-docs contrast.)* Outcomes of the loose-docs contrast, and what design change would address whichever failure mode dominates. Candidate questions: if pure cosine fails under adversarial competition but holds under loose docs, is the fix query-side (better alias coverage), index-side (document-aware boosting), or chunk-side (heading-path context in chunk text)?

Early candidates informed by this run: (a) a minimum-chunk-size or fragment-merge rule in chunker v2 to kill the tiny-part artifact; (b) a paraphrased-gold-query variant of this ablation, since distinctive-n-gram queries appear to be the reason cosine keeps surviving.
