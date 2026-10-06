# Cross-branch findings vs the current architecture

**Date:** 2026-10-06
**Status:** Synthesis on `main`. Observation only. No retrieval change.
**Branch index:** `docs/2026-10-06_branch_guide.md`

This document answers three questions from the recorded experiments:

1. What does each branch currently establish?
2. How does that evidence support keeping the architecture that is on `main`?
3. Where does the same evidence license a later, preregistered change — and which failure modes it says not to repeat?

Claims below are local to this corpus, analyzer, alias table, and sealed evaluation set. They are not universal retrieval rules. Source findings stay on their branches; this file is the `main`-side map.

**Current architecture on `main`.** Heading/bold-field markdown chunks. Closed-vocabulary TF-IDF, L2-normalized, unknown query tokens dropped. Score is `0.7 * cosine + 0.3 * Jaccard(heading+text) + alias_boost`. Three section ids get a `+0.5` substring list; any chunk whose full slug (underscores as spaces) appears in the query gets `+0.35`. Exact `section_id` lookup; collisions raise `AmbiguousSectionIdError`. No score floor, no reject path, no rewrite, no dense encoder, no hop controller. Eval is three short in-vocabulary queries.

---

## How the evidence supports keeping this architecture

The research line has **not** produced a licensed replacement retriever. It has produced a map of what this stack already does well, what it cannot show, and which “obvious” upgrades fail for named reasons.

| Architecture piece on `main` | What the evidence supports | What it does not license |
| --- | --- | --- |
| Lexical/sparse hybrid as the frozen control | High-overlap gold queries stay top-1 even when alias and Jaccard are removed, on 1-doc and two 3-doc corpora. Distinctive n-grams (`conviction_detail.factors`, `finding 3.5 disposition`) are the actual win condition. | Treating cosine sufficiency as robustness. `verdict` vs `input_fields_consumed` is a persistent thin margin. |
| Static alias table | Owns ~56–61% of winner score mass on gold queries and fires only on the intended slugs when extra docs lack those slugs. Direct-lookup fallback is redundant when queries already name the sections. | Using aliases as a semantic layer, expanding the table from eval surprises, or treating `+0.5` as relevance. Alias is a margin amplifier and an OOD trap. |
| Fail-loud `section_id` lookup | Loose-docs produced **22** colliding ids from identical heading templates. Silent first-match would have bound to an arbitrary doc. Gold targets happened to be unique. | Doc-scoped lookup or chunker-v2 prefixing as already decided. Fail-loud is the enforced invariant, not entity resolution. |
| Closed TF-IDF vocabulary / no stemmer | Producer-burial forensics: identifiers kept whole so standalone `regime` never appears in the producer vector. That is a measurable representation limit, not a scoring-weight bug. | Dumping identifier segments into the query, or assuming MiniLM will recover identifier-register chunks. |
| Independent per-chunk ranking | Control and later tests all show conjunction (`mch-001`) and true hops as unmeasurable or incidental. | Promoting incidental dual hits into a hop controller. |
| Always-return top-k | Far/near/alias-trap OOD rows always return a chunk. Alias-trap `ood-003` keeps `verdict` rank 1 with `+0.5` under lexical rewrite, morphology, MiniLM, and code cosine. | Inventing a reject threshold from current residual scores. |
| Taxonomy / change discipline | Rows that only the alias table can pass cannot tell Route L from Route S. Aggregate 3/7→6/7 hit-rate moves never decided a verdict. | Optimizing the sealed 12-row set, or mixing morphology + MiniLM + code cosine into production because each won a different row. |
| Observational instrumentation | Cache was ranking-transparent (0/12 then 12/12, identical ranks). Tracker useful when it does not mutate rules mid-run. Expected-target ranks made burial falsifiable. | Treating cache or logging as quality improvements. |

Route L and Route S stay open, as the 2026-09-24 ADR required. Misses cluster on **representation register** (closed vocab, identifiers, morphology vs prose vs code) more than on “needs a reranker for the right family.” That is pressure toward Route S experiments, not a decision.

---

## Top findings by branch

### `research/alias-boost-ablation`

**Question.** Is TF-IDF cosine enough for the three gold queries, or do Jaccard / alias / exact lookup decide?

**Result.** H0 not rejected on the 1-doc corpus. All five configs, including pure cosine, put every gold target at rank 1.

**Support for current architecture.** The hybrid is not papering over a cosine failure on these queries. Exact `section_id` lookup is load-bearing as a product path, but redundant for these wordings because the alias strings are near-verbatim section names.

**Improvement / caution.** Alias is a **confidence amplifier**, not a retrieval signal here. Removing it shrinks `question` / `verdict` margins 5–6×. Pure-cosine margins on those two are thin (`+0.0482`, `+0.0730`). Do not read “cosine passed” as “the extra terms are useless.” The predicted fragility is more documents or paraphrases, not the current gold wording.

**Source:** `research/2026-09-22_alias_boost_ablation/findings.md`

---

### `research/chunker-v2-adversarial`

**Question.** Do same-domain extra docs invert gold rankings under v2 chunking? Does alias artificially preserve the win?

**Result.** Pre-registered inversions **failed**. H0 still not rejected. Adversarial chunks appear in top-5; they do not outrank gold. Alias still owns score mass and is still not required for correctness.

**Support for current architecture.** Distinctive query n-grams beat general domain overlap. TF-IDF IDF is doing the work the gold queries were written to exploit. A larger hostile corpus of this type is the wrong next lever if the queries still name unique phrases.

**Improvement / caution.**

- v2’s size cascade emitted a **10-character fragment** (`__part4`) that became the `question` runner-up by inflated term frequency. Any later chunker needs a minimum-size or fragment-merge rule before it is compared to v1.
- `verdict` under pure cosine thinned to `+0.0222`; the competitor was still same-doc `input_fields_consumed`, not the new docs.
- Doc-prefixed ids make v1 bare-`section_id` lookup miss; that is a caller-contract issue the fail-loud ADR already flagged, not a ranking result.

**Source:** `research/2026-09-22_chunker_v2_adversarial/findings.md`

---

### `research/loose-docs-contrast`

**Question.** Does corpus growth with topical (not slug) overlap break cosine? Is alias the decisive component?

**Result.** H0 not rejected. All configs still rank-1. Best extra-doc cosine ~0.106. Alias fired **only** on the original three targets.

**Support for current architecture.** Growth alone, with shared words like `regime` / `conviction` / `EV`, does not break these gold queries. The interpretive claim “alias is the decisive component” is **not** supported: configs with alias zero still pass.

**Improvement / caution.**

- **22 colliding `section_id`s** across two session reviews with the same heading template. This is the evidence behind fail-loud lookup on `main`. Hybrid search would still rank both; lookup would now raise. Entity / cross-doc rows remain unmeasurable until that contract is revisited.
- Thinnest cosine margin in the early trio: `verdict` `+0.0167`, again vs same-doc `input_fields_consumed`. Soft spot is **trace structure**, not extra docs.
- Next falsification for this gold-query family is **paraphrase** (strip distinctive n-grams), not another hostile corpus. That is what `query-set-expansion` then did.

**Source:** `research/2026-09-22_loose_docs_contrast/findings.md`

---

### `query-set-expansion`

**Question.** What does the frozen hybrid do on a pre-registered set that is allowed to miss? Why is the producer section buried?

**Result.** Expanded control: measurable **3 hits / 4 expected misses / 5 unmeasurable**. Calibration ranks reproduced. Producer `1_upstream_producer_score_definition` at ranks 10 / 7 / 9 on sem-001 / lex-001 / spec-002. Alias 0.0 on those three probes.

**Support for current architecture.** The stack behaves as the failure-mode map said: high-overlap / alias-friendly cells can hit; lexical gap, identifier-register semantic gap, overspecific morphology, and conjunction miss for named reasons; OOD and true hops cannot be scored as hit/miss because there is no reject path and no hop controller. That honesty is the point of the taxonomy.

**Improvement / caution (diagnosis, not a patch).**

- The tokenizer does not split `regime_stability` / `RegimeObserver.step`, so the producer chunk has **no standalone `regime` dimension** while queries do.
- Burial is not one bug: OOV / closed vocab, weak overlap, identifier register, and prosaic competitors (`verdict`, `upstream_signals_since_verdict_independent`) are separable.
- Do not retarget golds or rewrite queries after seeing ranks. `current_stack` may be reclassified; `expected` and `failure_mode` may not.
- Score-component logging and expected-target ranks are justified: without them, a move from rank 10→6 is invisible at `TOP_K=5`.

**Sources:** `docs/query_set_expansion/2026-09-28_expanded_control_characterization.md`, `docs/query_set_expansion/2026-09-29_producer_burial_forensics.md`, plus baseline / trace-validation / telemetry docs on that branch.

---

### `research/query-rewrite-cache-loop` (H-QRL)

**Question.** Can query-side morphology + identifier-segment expansion + stripping recover producer burial, with a transparent cache?

**Result.** **Weakened. Do not accept.** Measurable hits 3/7→6/7 is not success.

- Morphology on spec-002: `threshold → thresholds`, producer cosine ~0.052→0.183, rank 9→1, alias 0. **Supported fragment.**
- Identifier expansion on sem-001: selected RegimeBoss/state/filename tokens, **not** `regime_stability`. Rank 10→11.
- `regime_update_interval_seconds` fired slug-as-spaces `date` at `+0.35` (cosine 0, Jaccard 0). New rank-1 winner on multiple rows.
- lex-001 rank 7→3 while producer **score fell** — stopword stripping collapsed competitors.
- Cache 0/12 then 12/12, identical ranks: **supported** as execution optimization.

**Support for current architecture.** Putting a generic rewrite loop in front of the frozen scorer is worse than leaving queries alone for identifier-register misses, and it silently violates alias assumptions that were written for human queries. The frozen hybrid plus observational traces remain the right control.

**Improvement / caution.** Separate morphology from identifier expansion. Do not rank expansions by IDF. Do not let generated tokens participate in substring aliases without a new contract. Rank ≠ correspondence. Global hit rate is not the objective.

**Sources:** `docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_findings.md`, `system_findings_hypothesis_testing.md` on that branch.

---

### `research/morphology-only-ablation` (H-MORPH)

**Question.** Does closed-vocabulary morphology still repair spec-002 when stripping and identifier expansion are off?

**Result.** **Supported on a small surface.** Hits 3/7→4/7 from the predicted spec-002 row only.

- spec-002 rank 9→3, cosine 0.052→0.145, Jaccard up, alias 0. Rank 1 did not recur because `the` was kept and `verdict` retained that leftover.
- Identifier lists empty; `date` alias 0.0 on previously contaminated rows — isolates the H-QRL artifact.
- sem-001 stayed rank 10 (not a morphology miss).
- lex-001 stayed rank 7; H-QRL’s rank-only “win” disappeared.
- Short incidental fires (`a → as`, `does → do`) documented, not patched.

**Support for current architecture.** The frozen analyzer’s lack of a stemmer is a **real, local** miss class. Repairing it with a tiny in-vocab `+s`/`+es` rule is compatible with “do not invent synonyms.” Bundling that rule with identifier dumping is what made H-QRL unsafe.

**Improvement / caution.** Morphology is a specialized mechanism, not a production default from one sealed row. Coverage (`H-MORPH-N`) and a minimum token length are open. Do not blacklist `date`. Do not promote morph-v1 because hit rate ticked up.

**Sources:** `docs/query_set_expansion/2026-10-05_morphology_only_findings.md`

---

### `research/dense-cosine-h1` (H1)

**Question.** Does replacing TF-IDF cosine with MiniLM recover producer burial without rewriting the query?

**Result.** **Partially supported.** Hits 3/7→5/7 is not the result.

- lex-001 rank 7→3 as mechanism A (`dense_cosine` 0.284; Jaccard/alias/lexical cosine frozen). Synonymy (`consistency` / `market-condition` vs `stability` / `vwap_dist`).
- sem-001 rank 10→9, still a miss. Producer dense 0.263 vs `verdict` 0.600. MiniLM prefers prosaic regime/conviction fields over the identifier-heavy score definition.
- spec-002 rank 9→10. Morphology remains the matching repair.
- Title chunks can enter top-k with Jaccard 0. Near-OOD dense ~0.37 vs far-OOD ~0.15. No reject threshold chosen.
- `ood-003` still `verdict` +0.5. Alias is independent of the encoder.
- Incidental `mch-001` hit (consumer dense attraction) is not a conjunction design.

**Support for current architecture.** A generic sentence embedding is not a drop-in upgrade to the TF-IDF term. Closed-vocab synonymy is a **different** miss from identifier-register burial and from morphology. Jaccard and alias remaining identical to control is why H1 movement is attributable — keep those terms as attribution tools even if a later cosine term changes.

**Improvement / caution.** MiniLM is a candidate for the **prose-synonymy** cell (Route S), not for undecomposed identifiers. Dense overgeneralization to titles and more-confident near-OOD are blast radius, not a reason to ship H1 as default.

**Sources:** `docs/query_set_expansion/2026-10-05_dense_cosine_h1_findings.md`, comparative findings on that branch.

---

### `research/code-register-hcode` (H-CODE)

**Question.** Does a code-trained mean-pooled embedding raise identifier-register correspondence without query-side identifier dumping?

**Result.** **Partially supported.** Hits 3/7→6/7 is not the result.

- sem-001 rank 10→6, still a miss. Producer `code_cosine` 0.520 vs MiniLM 0.263. Gap to `verdict` collapsed (~0.337 dense → ~0.046 code). Rank 1 is the **identifier-heavy consumer** (0.665), not prose `verdict`. Correspondence A; retrieval not recovered.
- lex-001 rank 7→**1**; previously invariant signals neighbor fell to rank 7. Stronger synonymy recovery than MiniLM on this row.
- spec-002 rank 9→3 **without** `threshold→thresholds` — overlay via label-set identifiers, not a morphology substitute.
- Near-OOD `ood-002` can rank the producer first (code 0.527) because the query names `RegimeBoss` / `COMPRESS`. Far-OOD top code ~0.36 > MiniLM ~0.15.
- No generated tokens; `date` not rank 1. Alias-trap still holds.

**Support for current architecture.** Generic identifier expansion was the **wrong tool** for this miss: correspondence moved without dumping `regime_*` into the query. The remaining problem is competition among identifier-bearing chunks (producer vs consumer), which neither TF-IDF nor MiniLM posed this way. Exact-term gold queries still land in top-3.

**Improvement / caution.** Code cosine is a candidate for the **identifier-register** cell, not a general retriever and not an OOD gate. Combining it with morphology and MiniLM is a **new** hypothesis (`H-HYBRID` / `H-ROUTE`), not licensed as a mix from this map. Producer vs consumer disambiguation (`H-ID` in a constrained form, or a later entity/scope rule) is still open.

**Sources:** `docs/query_set_expansion/2026-10-05_hcode_findings.md`, five-way map and `system_findings_hypothesis_testing.md` on that branch.

---

## Specialized mechanism map (sealed set only)

| Failure class | Matching evidence | Status |
| --- | --- | --- |
| Distinctive in-vocab n-grams (gold `evaluate.py` queries) | Cosine alone, 1-doc and 3-doc | Supported on those wordings; thin `verdict` margin |
| Morphological surface form (`threshold` / `thresholds`) | H-MORPH (H-QRL mixed it with stripping) | Supported, one row |
| Prose / closed-vocab synonymy | MiniLM H1; H-CODE also recovered lex-001 | Supported as specialized |
| Identifier-register correspondence | H-CODE on sem-001 (rank 6, still miss) | Partial; not top-k recovery |
| Generic identifier-segment expansion | H-QRL | Unsupported; alias contamination |
| Conjunction / multi-chunk / hop | None designed | Unresolved; incidental hits only |
| OOD reject | None | Unresolved; trap invariant |
| Cross-doc `section_id` | Fail-loud on `main`; 22 collisions on loose-docs | Enforced refusal, not resolution |
| Tiny chunker fragments | v2 cascade | Documented artifact |

A mechanism that wins more sealed rows is not therefore the general retriever.

---

## Failure modes to avoid

These are recorded behaviors, not style preferences.

1. **Optimize 3/7, 4/7, 5/7, or 6/7.** Those counts appeared under four different mechanisms, including artifacts. Prefer preregistered mechanistic agreement and guardrails.
2. **Treat rank movement as correspondence.** Same lex-001 delta 7→3 was competitor collapse (H-QRL) and dense synonymy (H1). H-MORPH sem-003 became rank 1 while gold score **fell**.
3. **Bundle rewrite families.** Morphology + stripping + identifier dump hid the only supported fragment and imported `date`.
4. **Use IDF (or rarity) as semantic relevance** for expansion candidates.
5. **Assume identifier segment overlap is meaning.** `regime_state` and `regime_stability` are not interchangeable.
6. **Run human-query alias matching on generated tokens.** Slug-as-spaces substring `date` ⊂ `update` ⊂ `regime_update_interval_seconds`.
7. **Patch `SECTION_ALIASES` from the current eval set** (do not blacklist `date` to hide the trap).
8. **Assume MiniLM (or any one dense space) recovers identifier-heavy chunks.**
9. **Assume code cosine is a morphology substitute or a reject path.** Near-OOD identifier attraction is the opposite of a gate.
10. **Ship a composite of morphology + MiniLM + Jina because each won a different probe.** That mix was not measured.
11. **Use v2-style size cascades without a fragment floor.** Tiny heading/table residues inflate cosine.
12. **Rely on silent first-match lookup** once two docs share a heading template.
13. **Add more hostile documents instead of harder queries** when gold wording still contains unique n-grams.
14. **Mutate rewrite rules from tracker frequencies in the same measured run.**
15. **Invent an OOD threshold** from residual MiniLM ~0.15 / code ~0.36 / near-OOD ~0.37. That is a later `H-OOD` experiment.

---

## Where further work is actually supported

Work that would **change `main`** still needs its own preregistration. The evidence only names the cell.

| Area | Why the evidence points here | Do not do yet |
| --- | --- | --- |
| Isolated closed-vocab morphology (`H-MORPH-N`) | spec-002 replicated under ablation; incidental short-token fires exist | Default-on rewrite; length exceptions invented during a measured test |
| Alias contract (`H-ALIAS`) | Trap holds across every representation; generated tokens can fire slug-as-spaces | Narrowing aliases to “fix” ood-003 or the `date` artifact |
| Code-register representation vs producer/consumer (`H-ID` / later ranker) | H-CODE raised sem-001 correspondence; consumer still wins | Query-side identifier dumping; declaring burial solved |
| Prose synonymy encoder (MiniLM or better) | lex-001 mechanism A under H1 | Replacing TF-IDF for identifier-register or morphology rows |
| Routing / hybrid (`H-HYBRID` / `H-ROUTE`) | Failure classes do not share a repair | Production blend from the 12-row map |
| Reject / calibration (`H-OOD`) | Always-return top-k; near-OOD confidence rises under dense/code | A cutoff chosen from this residual table |
| Chunker fragment policy | v2 `__part4` | Replacing v1 on `main` without that rule and without a new eval |
| Doc-scoped lookup or prefixed ids | 22 collisions; fail-loud ADR revisit triggers | Silent disambiguation |
| Conjunction / hop controller | mch-001 incidental only | Counting QRL/H1/H-CODE dual hits as a planner |
| Paraphrased gold queries (early-line leftover) | Distinctive n-grams kept cosine alive on 3 corpora | Another same-template extra-doc ablation as the primary stress |

Instrumentation that already earned its keep: expected-target ranks, named score components, observational trackers, flag-off sanity traces that reproduce control to six decimals.

---

## Evaluation invariants to carry forward

- Sealed YAML sha256 `0760edeaa29b0496f288309464d26d0564f1e65b6c39afed94e3b47bf1a244a8` and lexical index sha256 `b4cff81decbfbbe5cedbdfb3133bf66eff3ebaeb6e77d124b937a6b296c4690c` are the comparison identity for the hypothesis line.
- Decompose every rank change into target score, cosine/Jaccard/alias, competitor scores, and top-k membership.
- Control vs rewrite totals are comparable; control vs H1 vs H-CODE totals are not. Ranks and frozen Jaccard/alias are.
- Alias-trap `ood-003` remaining rank-1 `verdict` is a **stable architecture fact**, not a representation bug.
- Exact-term gold queries staying in top-3 is a guardrail, not coverage of the six failure modes.

---

## References

- Architecture on `main`: `docs/design_notes/2026-09-24_taxonomy_schema_design.md`, `docs/query_set_expansion/2026-09-26_failure_mode_map.md`, `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md`.
- Per-branch reading list: `docs/2026-10-06_branch_guide.md`.
- Most complete hypothesis-line file (not on `main`): `docs/query_set_expansion/system_findings_hypothesis_testing.md` on `research/code-register-hcode`.
