# Branch guide: purpose and reading list

**Date:** 2026-10-06
**Status:** Index for `main`. This document does not change retrieval behavior.
**Companion:** `docs/2026-10-06_cross_branch_findings.md` (what the evidence currently supports).

Most research writing lives only on its branch. Checkout that branch, or read a file with `git show <branch>:<path>`. Paths below are branch-local unless marked **on main**.

---

## How the branches relate

Two families, both off `main`. They have not been merged back.

```
main
  POC pipeline + ADRs that define the current architecture

  research/alias-boost-ablation          (fork of initial POC; 1-doc hybrid ablation)
  research/chunker-v2-adversarial        (fork of initial POC; v2 chunker + hostile docs)
  research/loose-docs-contrast           (fork of initial POC; v1 chunker + topical extra docs)

  query-set-expansion                    (off current main; sealed diagnostic set + frozen control)
    research/query-rewrite-cache-loop    (H-QRL)
      research/morphology-only-ablation  (H-MORPH)
        research/dense-cosine-h1         (H1 MiniLM)
          research/code-register-hcode   (H-CODE)
```

The three `research/*` ablations from 2026-09-22 fork the **initial POC commit**, not current `main`. They predate fail-loud `section_id` lookup and the taxonomy ADR. `query-set-expansion` and the later hypothesis branches fork **current `main`**.

None of these research branches is a production retriever. Opt-in code on the later line is measurement machinery. Default scoring on those branches remains the frozen lexical hybrid when flags are unset.

---

## `main`

**What it is.** The current architecture: heading-based markdown chunking, closed-vocabulary TF-IDF cosine, heading Jaccard, a static alias table, exact `section_id` lookup, and fail-loud lookup on collided ids. One ingested note, 15 chunks. Three short in-vocabulary eval queries. No query rewrite, no dense encoder, no reject path, no hop controller.

**Use it for.** The live pipeline; the ADRs that constrain later experiments; this index.

**Read first (on main)**

| Document | Why |
| --- | --- |
| `docs/design_notes/2026-09-24_taxonomy_schema_design.md` | Axes for query-set growth. Route L vs Route S left open. |
| `docs/query_set_expansion/2026-09-26_failure_mode_map.md` | How the six failure modes map onto this stack. |
| `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md` | Why lookup raises instead of silently picking a doc. |
| `docs/2026-10-06_cross_branch_findings.md` | Cross-branch evidence vs this architecture. |

**Code on main:** `smart_chunker.py`, `embed.py`, `retrieve.py`, `store.py`, `ingest.py`, `evaluate.py`. Corpus: `data/2026-08-10_regime_factor_composition_trace.md`. Index: `metadata/chunks.json`.

---

## `query-set-expansion`

**What it is.** Measurement infrastructure and the sealed diagnostic set. Retrieval scoring is frozen. The branch adds a YAML query set, JSONL traces, expected-target rank telemetry, score-component fields on hits, and the 12-row `docqa-expanded-v1` characterization. It does not pick Route L or Route S.

**Use it for.** What the frozen hybrid actually does on the expanded set; producer-burial diagnosis; the control every later hypothesis compares to.

**Read first**

| Document | Role |
| --- | --- |
| `docs/query_set_expansion/2026-09-28_expanded_query_set_preregistration.md` | Locked predictions before the 12-row run. |
| `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md` | Observed control: 3/7 measurable hits; producer buried at ranks 7–10. |
| `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md` | Why `1_upstream_producer_score_definition` loses: identifiers kept whole, OOV `regime`, competitor attraction. |

**Then**

| Document | Role |
| --- | --- |
| `docs/query_set_expansion/2026-09-28_retrieval_baseline.md` | Three-row freeze; comparison point for later changes. |
| `docs/query_set_expansion/2026-09-28_trace_validation.md` | JSONL is truthful but censored below top-k and inside score components. |
| `docs/design_notes/2026-09-28_observability_scoping.md` | What to log next; implements nothing by itself. |
| `docs/query_set_expansion/2026-09-28_expected_target_telemetry.md` | Rank/score of the gold chunk in the full ranking; run identity. |
| `eval_sets/docqa.yaml` | Sealed rows. sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8`. |
| `eval_sets/runs/2026-09-29_run-004.jsonl` | Frozen expanded control. |

Also inherits the three **on-main** ADRs/map.

---

## `research/alias-boost-ablation`

**What it is.** Five-config ablation of the hybrid formula on the **1-doc, 15-chunk** corpus. Pipeline files untouched (monkeypatch / local wrappers). Tests whether TF-IDF cosine alone retrieves the three gold `evaluate.py` targets.

**Use it for.** Score-mass vs correctness of the alias table; thin cosine margins on high-overlap gold queries.

**Read first**

| Document | Role |
| --- | --- |
| `research/2026-09-22_alias_boost_ablation/findings.md` | H0 not rejected; alias owns score mass, not top-k; thin D margins on `question` / `verdict`. |

**Then:** `run_ablation.py`, `score_decomposition.py` in the same directory.

---

## `research/chunker-v2-adversarial`

**What it is.** Parallel v2 chunker (doc-prefixed ids, size cascade) plus two same-domain operational docs. Same five-config ablation as alias-boost. v1 pipeline left untouched.

**Use it for.** Whether hostile vocabulary inverts gold rankings; whether alias “saves” them; chunker-v2 fragment artifacts.

**Read first**

| Document | Role |
| --- | --- |
| `research/2026-09-22_chunker_v2_adversarial/findings.md` | Pre-registered inversions failed; H0 still not rejected; 10-char `__part4` fragment is a chunker artifact. |

**Then:** `run_ablation_v2.py`, `score_decomposition_v2.py`; v2 helpers `smart_chunker_v2.py`, `store_v2.py`, `ingest_v2.py`.

---

## `research/loose-docs-contrast`

**What it is.** Paired contrast to the adversarial branch: **v1 chunker**, two session-review docs that share topical vocabulary but not the gold slugs. Same five-config ablation.

**Use it for.** Corpus growth without distinctive n-gram competition; the 22 colliding `section_id` values that motivated the fail-loud ADR on `main`.

**Read first**

| Document | Role |
| --- | --- |
| `research/2026-09-22_loose_docs_contrast/findings.md` | H0 not rejected; thinnest cosine margin recorded (`verdict` +0.0167); 22 collisions; alias not decisive for correctness. |

**Then:** `decomposition.md`, `ablation_stdout.txt`, `run_ablation.py`, `score_decomposition.py`.

The fail-loud ADR on `main` cites this branch as the collision evidence.

---

## `research/query-rewrite-cache-loop` (H-QRL)

**What it is.** Query-side rewrite/cache loop in front of the **frozen** hybrid: function-word stripping, closed-vocabulary morphology, IDF-capped identifier-segment expansion, plus an observational tracker and ranking-transparent cache. Not a dense-encoder experiment.

**Use it for.** Why bundling those rewrite families is unsafe; the `date` alias artifact; the reusable evaluation rules later branches keep.

**Read first**

| Document | Role |
| --- | --- |
| `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md` | Locked predictions. |
| `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md` | Joint hypothesis weakened. Morphology worked; identifier expansion did not; 6/7 hits are not the verdict. |
| `docs/query_set_expansion/system_findings_hypothesis_testing.md` | First extraction of reusable system claims (later branches extend this file). |

**Traces:** `eval_sets/runs/2026-10-06_run-001.jsonl` (flag off), `..._run-002.jsonl` (experiment), `..._run-002_query_loop.json` (tracker).

---

## `research/morphology-only-ablation` (H-MORPH)

**What it is.** Ablation of H-QRL: `morph-v1` only. Function words kept. Identifier expansion off. Same cache/tracker. Isolates whether spec-002 was morphology or a bundled rewrite.

**Use it for.** Supported closed-vocabulary morphology; causal isolation of the H-QRL `date` artifact; proof that H-QRL’s lex-001 rank gain was competitor collapse.

**Read first**

| Document | Role |
| --- | --- |
| `docs/query_set_expansion/2026-10-05_morphology_only_preregistration.md` | Locked predictions. |
| `docs/query_set_expansion/2026-10-05_morphology_only_findings.md` | spec-002 repaired as mechanism A (rank 9→3); sem-001 unchanged; `date` gone. |
| `docs/query_set_expansion/system_findings_hypothesis_testing.md` | Updated with H-MORPH evidence. |

**Traces:** `eval_sets/runs/2026-10-06_run-003.jsonl` (flag off), `..._run-004.jsonl` (experiment). Also keep the H-QRL docs on this branch; they are the parent experiment.

---

## `research/dense-cosine-h1` (H1)

**What it is.** Representation swap: replace the TF-IDF cosine **term** with MiniLM `dense_cosine` (`all-MiniLM-L6-v2`). Jaccard, aliases, 0.7/0.3 weights, original query text, and chunks frozen. No rewrite.

**Use it for.** Prose synonymy vs identifier-register burial; why MiniLM is not a general producer-burial fix; the first four-way comparative audit.

**Read first**

| Document | Role |
| --- | --- |
| `docs/query_set_expansion/2026-10-05_dense_cosine_h1_preregistration.md` | Locked predictions. |
| `docs/query_set_expansion/2026-10-05_dense_cosine_h1_findings.md` | lex-001 recovered as A; sem-001 still buried; spec-002 not repaired. |
| `docs/query_set_expansion/2026-10-05_three_hypothesis_comparison_plan.md` | Comparative audit protocol (observation only). |
| `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md` | Control vs QRL vs MORPH vs H1 (later extended with H-CODE on the next branch). |
| `docs/query_set_expansion/system_findings_hypothesis_testing.md` | Cross-experiment claims after H1. |

**Traces:** `eval_sets/runs/2026-10-06_run-005.jsonl` (flag off), `..._run-006.jsonl` (experiment). Dense index: `metadata/dense_h1_index.json`.

---

## `research/code-register-hcode` (H-CODE)

**What it is.** Representation swap: replace the cosine term with Jina `code_cosine` (`jina-embeddings-v2-base-code`). Same freeze as H1. No identifier expansion. MiniLM cosine is logged only as a diagnostic.

**Use it for.** Identifier-register correspondence on sem-001; the five-way mechanism map; current best statement of what is supported vs still open.

**Read first**

| Document | Role |
| --- | --- |
| `docs/query_set_expansion/2026-10-05_hcode_preregistration.md` | Locked predictions. |
| `docs/query_set_expansion/2026-10-05_hcode_findings.md` | sem-001 rank 10→6 still a miss; lex-001 rank 1; not a morphology substitute. |
| `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md` | Five-way map including H-CODE. |
| `docs/query_set_expansion/system_findings_hypothesis_testing.md` | Current system-findings file (most complete on this branch). |

**Traces:** `eval_sets/runs/2026-10-06_run-007.jsonl` (flag off), `..._run-008.jsonl` (experiment). Code index: `metadata/code_hcode_index.json`.

If you need one file that already consolidates H-QRL through H-CODE, read `system_findings_hypothesis_testing.md` on this branch. The companion on `main` restates the architecture implications without requiring that checkout.

---

## Suggested reading order

1. On `main`: taxonomy ADR → failure-mode map → fail-loud ADR.
2. Early robustness: alias-boost findings → chunker-v2 findings → loose-docs findings.
3. Measurement line: query-set preregistration → expanded control → producer-burial forensics.
4. Interventions, one mechanism at a time: H-QRL → H-MORPH → H1 → H-CODE.
5. Synthesis: `system_findings_hypothesis_testing.md` on `research/code-register-hcode`, or `docs/2026-10-06_cross_branch_findings.md` on `main`.

Do not treat later branches as replacements for earlier ones. Each later file assumes the sealed YAML, control JSONL, and evaluation rules from `query-set-expansion`.
