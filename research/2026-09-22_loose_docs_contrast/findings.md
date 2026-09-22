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

PENDING — filled after the run.

## Delta vs v1

PENDING — filled after the run.

## Score decomposition summary

PENDING — filled after the run.

## Interpretation

PENDING — filled after the run.

## Falsification outcome

PENDING — filled after the run.

## Caveats

PENDING — filled after the run (baseline: 3-doc corpus is still small; the two added docs are session reviews with topical but not structural overlap; v1↔v2-style cross-corpus margin comparisons carry the same IDF-rescaling caveat as the adversarial branch).

## Synthesis across experiments

*(Stub — to be filled once both `research/chunker-v2-adversarial` and this branch have results.)* The paired design: adversarial docs (heavy lexical overlap, no shared slugs) vs loose docs (topical overlap only). If both branches pass all configs, the alias table's decisiveness remains untested at this corpus scale and the next lever is paraphrased gold queries; if loose passes and adversarial fails, lexical pressure is the breaker; if loose fails, corpus growth alone is sufficient and the alias table is load-bearing sooner than predicted.
