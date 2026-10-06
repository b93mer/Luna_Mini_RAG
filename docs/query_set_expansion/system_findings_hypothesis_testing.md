# Luna Retrieval System Findings

## Purpose

This document records empirical knowledge about the retrieval system derived from controlled experiments. It distinguishes mechanisms that are supported, unsupported, or still uncertain.

These findings describe the current corpus, analyzer, vocabulary, scoring architecture, alias behavior, and evaluation set. They should not be treated as universal retrieval rules.

---

## 1. Closed-vocabulary morphology can repair lexical representation misses

**Status:** Supported across controlled ablation, still limited by small evaluation coverage.

**Evidence lineage:** first observed in H-QRL; isolated/replicated in H-MORPH; H1 did not repair `spec-002` (rank 9→10, `dense_cosine` 0.108). Current confidence after three experiments: **strengthened as a specialized mechanism**, not as a general retriever. H1 missing this row does not weaken morphology.

A query token may fail to match a relevant chunk when the corpus contains only a nearby morphological form. In H-QRL, `threshold` did not correspond strongly enough with the gold producer while `thresholds` already existed in the fitted vocabulary.

Adding the in-vocabulary morphological variant increased producer cosine from approximately 0.052 to 0.183 and moved the producer from rank 9 to rank 1. Alias contribution remained zero.

H-MORPH isolated that mechanism. Identifier expansion and function-word stripping were removed. The same row, `qse-docqa-spec-002`, still improved:

- predicted: `threshold → thresholds` should raise producer correspondence, with alias remaining 0.0
- observed: morphology emitted `label` and `thresholds`; producer cosine 0.051815 → 0.145072; Jaccard 0.021739 → 0.043478; rank 9 → 3; alias 0.0
- why supported: absolute producer score rose (+0.072) more than competitors; the gain is cosine/Jaccard from an in-vocab plural, not alias and not identifier dumping
- remaining uncertainty: this is still one sealed morphological miss. Rank 1 did not recur because function words were retained, so `verdict` kept a leftover-`the` advantage. Short tokens such as `a → as` and `does → do` also fire under the locked rules and slightly dilute unrelated queries.

### What works

Deterministic morphological expansion when:

- the generated form already exists in the fitted vocabulary;
- the transformation is small and mechanically defined;
- no semantic synonym is invented;
- the target's absolute correspondence increases;
- the gain can be attributed to cosine/Jaccard rather than an alias.

### Why it works

The intervention repairs a representation mismatch rather than inferring a new concept. `threshold` and `thresholds` encode essentially the same lexical concept but were represented as different vocabulary items by the frozen analyzer.

### What remains unknown

One positive row, now replicated under ablation, is still not enough to establish morphology as a permanent retrieval policy. Additional morphological cases are required to estimate its generality. A minimum token-length constraint was not tested; incidental `do`/`as` fires are documented, not patched.

H1 later showed that mean-pooled MiniLM cosine does not substitute for this repair. That is additional evidence of specialization, not a reason to drop morphology.

---

## 2. Generic identifier-segment expansion is not a reliable semantic bridge

**Status:** Unsupported in H-QRL v1. H-MORPH did not retest identifier expansion as a positive intervention.

**Evidence lineage:** first observed in H-QRL; isolated by H-MORPH (identifiers off, `sem-001` still rank 10); H1 also left `sem-001` buried (rank 9) without dumping identifiers. Current confidence after three experiments: **strengthened**. MiniLM cosine failing this row does **not** rehabilitate generic identifier expansion. It narrows the earlier hope that “semantic correspondence” in the MiniLM sense was the missing piece.

Expanding a query token into identifiers that contain that token as a `_` or `.` delimited segment did not reliably recover the relevant producer terminology.

For the `regime` query case, the expansion mechanism selected RegimeBoss, state, filename, and update-related identifiers but did not recover `regime_stability`. Producer rank moved from 10 to 11.

H-MORPH disabled this family entirely. `regime_stability` still did not appear, as expected, because morphology cannot construct identifier superstrings. Producer rank on `qse-docqa-sem-001` stayed 10. That is consistent with the original diagnosis: this miss is not morphological. It is not new evidence that a *constrained* identifier rule would also fail.

### What does not work

Do not assume that identifiers sharing one segment are semantically interchangeable.

Examples such as:

`regime_state`

`regime_update_interval_seconds`

`regime_stability`

share the token `regime`, but represent different relationships and system concepts.

### Why it fails

Identifier membership supplies structural overlap, not sufficient semantic correspondence.

The identifier vocabulary is heterogeneous, so segment overlap produces a broad candidate family rather than a reliable bridge to the intended concept.

---

## 3. High IDF is not a sufficient relevance criterion for query expansion

**Status:** Unsupported as a generic identifier-selection heuristic.

**Evidence lineage:** first observed in H-QRL. H-MORPH and H1 did not rank expansions by IDF. Current confidence after three experiments: **unchanged** (still untested outside H-QRL).

H-QRL ranked candidate identifier expansions by IDF. The resulting top candidates were rare but not necessarily useful to the target query.

### What does not work

Do not equate corpus rarity with semantic relevance.

### Why

IDF measures discriminativeness within the corpus, not whether an identifier preserves the meaning or intent of the query.

A high-IDF expansion may therefore be highly distinctive while pointing toward the wrong concept.

---

## 4. Machine-generated rewrite tokens can violate assumptions made by the alias layer

**Status:** Supported failure mechanism.

**Evidence lineage:** first observed in H-QRL; isolated/replicated in H-MORPH (offending token absent, `date` alias 0.0 on previously contaminated rows); H1 generated no rewrite tokens and did not recreate rank-1 `date`. Current confidence after three experiments: **strengthened**.

Identifier expansion introduced `regime_update_interval_seconds`. The substring `date` inside `update` caused the slug-as-spaces alias mechanism to apply a `+0.35` alias score to the `date` section.

The `date` section consequently became rank 1 on multiple rewritten queries despite zero cosine and zero Jaccard evidence.

H-MORPH removed identifier expansion and kept the alias table unchanged. Direct inspection found:

- `regime_update_interval_seconds` absent from every rewritten query and expansion list;
- identifier-frequency empty;
- `date` score 0.0 and alias 0.0 on the previously contaminated in-scope rows.

That is evidence consistent with the H-QRL causal explanation. It is not a proof that alias matching is safe for all future generated tokens, and it is not a reason to blacklist `date`.

### What does not work

Do not assume that alias matching designed for human-written queries remains valid when applied unchanged to machine-generated rewrite tokens.

### Why

Generated identifiers have different lexical structure from natural-language queries. Substring relationships inside identifiers may accidentally resemble valid section aliases without expressing user intent.

### Design implication

Query rewriting and alias matching require an explicit interface contract. Future experiments should determine whether generated tokens should participate in alias detection, and under what matching semantics.

Do not patch individual aliases based only on the current evaluation set.

---

## 5. Rank gain is not equivalent to improved semantic correspondence

**Status:** Supported.

**Evidence lineage:** first observed in H-QRL; isolated/replicated in H-MORPH; H1 produced the same `lex-001` rank 7→3 as H-QRL but as mechanism A (`dense_cosine` 0.284254, Jaccard identical to control). Current confidence after three experiments: **strengthened**. Identical rank deltas can be A or B depending on the intervention.

In the H-QRL negative-control row, the producer moved from rank 7 to rank 3 even though its absolute score decreased.

The apparent improvement came primarily from competing chunks losing score after stopword removal.

H-MORPH kept function words and still emitted `measures` / `signals` on that row. Rank stayed 7. Producer score fell further (0.037 → 0.028) while the lexical neighbor rose (0.144 → 0.188) because `signals` is that neighbor’s token. The H-QRL rank gain therefore does not survive once stripping is removed.

H-MORPH also produced the complementary pattern on `qse-docqa-sem-003`: gold rank 2 → 1 while gold score *fell* (0.312 → 0.302), because `verdict` fell more. That rank gain is competitor weakening, not improved correspondence.

### Evaluation rule

For retrieval experiments, inspect separately:

- target absolute score change;
- cosine/Jaccard/alias component changes;
- target rank change;
- competitor score changes;
- top-k hit/miss outcome.

A better rank alone is insufficient evidence that an intervention improved query-to-document correspondence.

---

## 6. Global hit rate is not a valid optimization target for this evaluation stage

**Status:** Reinforced.

**Evidence lineage:** first observed in H-QRL (3/7→6/7, joint claim weakened); H-MORPH 3/7→4/7 from predicted spec-002; H1 3/7→5/7 from lex-001 A plus incidental mch-001. Current confidence after three experiments: **strengthened**.

H-QRL changed the measurable hit count from 3/7 to 6/7, but the joint hypothesis was still weakened.

H-MORPH changed it from 3/7 to 4/7 because spec-002 entered top-k. That extra hit is mechanistically the predicted morphology repair. It is still not an optimization target, and it does not license promoting morph-v1 to default production retrieval.

Some additional hits arose from mechanisms different from those predicted, and several queries acquired an incorrect `date` winner.

### Evaluation rule

Do not accept retrieval changes because aggregate top-k hit rate increases.

Prefer mechanistic agreement with preregistered predictions and preservation of guardrails.

---

## 7. Cache behavior is ranking-transparent under the tested conditions

**Status:** Supported.

**Evidence lineage:** first observed in H-QRL; isolated/replicated in H-MORPH. H1 did not use the rewrite cache. Current confidence after three experiments: **unchanged** for rewrite loops; **still untested** on the dense path.

The first H-QRL pass produced 0/12 cache hits and the second identical pass produced 12/12 hits. Cached rankings were identical to first-pass rankings, and no ≥0.99 cosine collisions occurred between different rewritten queries.

H-MORPH reused the same cache under `morph-v1` rewritten strings: again 0/12 then 12/12, identical ranks, no collisions. This is a replication of ranking transparency, not a new cache design.

### What works

The current cache can avoid repeated ranking of identical rewritten queries without changing retrieval results, provided that:

- rewritten text is identical;
- index SHA matches;
- different rewritten strings are not served merely because vectors are highly similar.

### Interpretation

Caching is an execution optimization, not a retrieval-quality improvement.

Its correctness should continue to be evaluated independently from ranking quality.

---

## 8. Tracker instrumentation is useful when it remains observational

**Status:** Supported.

**Evidence lineage:** first observed in H-QRL; isolated/replicated in H-MORPH. H1 had no rewrite tracker. Current confidence after three experiments: **unchanged** for rewrite loops; **still untested** on the dense path.

The tracker exposed which expansions fired, how frequently they occurred, cache behavior, and ranking effects without mutating rewrite rules during the measured experiment.

H-MORPH used the same observational tracker with policy `morph-v1`. It recorded empty identifier lists, `thresholds` once, and incidental short-token morphology (`do`, `as`) without using those frequencies to change rules during the run.

### What works

Instrumentation that records mechanism-level behavior without adapting the system during evaluation.

### Why

It allows failed hypotheses to produce reusable system knowledge while preserving the independence of the experiment.

Tracker statistics may motivate a later preregistered hypothesis but should not directly modify rules during the same evaluation cycle.

---

## 9. Dense cosine can recover closed-vocab synonymy and does not recover identifier-register producer burial

**Status:** Partially supported under H1. New after the dense-cosine experiment.

H1 replaced the frozen TF-IDF cosine term with MiniLM `dense_cosine` (`sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) while holding Jaccard, aliases, 0.7/0.3 weights, TOP_K, chunks, and original query text fixed.

On `qse-docqa-lex-001`, producer rank moved 7→3 and entered top-k. Jaccard, alias, and `lexical_cosine` matched control. Producer `dense_cosine` was 0.284254 versus the signals neighbor 0.379759. That is mechanism A for synonymy (`consistency`/`market-condition` versus `stability`/`vwap_dist`), not H-QRL-style competitor collapse.

On `qse-docqa-sem-001`, the primary identifier-register miss, the producer moved only 10→9. Producer `dense_cosine` 0.263470 remained far below prosaic neighbors (`verdict` 0.600096, consumer 0.552181). MiniLM preferred natural-language regime/conviction chunks over the identifier-heavy score definition.

On `qse-docqa-spec-002`, H1 moved the producer 9→10. Morphology remains the matching repair.

### What works

Dense cosine as a replacement similarity, without query rewriting, when the miss is conceptual synonymy expressed in prose-like language.

### What does not work

Do not assume a general sentence embedding recovers chunks whose distinctive content lives in undecomposed identifiers and code-register tokens.

### Blast radius

Title and other generic chunks can become neighbors with Jaccard 0. Near-OOD `dense_cosine` (~0.37) is closer to in-scope scores than far-OOD (~0.15). Do not treat high dense similarity as automatically meaningful. Do not invent a reject threshold from this experiment.

**Evidence lineage:** first observed in H1. H-QRL and H-MORPH did not implement dense cosine. Current confidence: **narrow** (one synonymy row, one failed identifier-register row, one morphology diagnostic).

---

# Cross-Experiment Findings

These conclusions are supported only by the combined evidence from frozen control, H-QRL, H-MORPH, and H1. Details: `docs/query_set_expansion/2026-10-05_three_hypothesis_comparative_findings.md`.

## Representation-specific repairs

Failure classes in this corpus do not share one repair.

- Closed-vocabulary morphology repairs spec-002 and does not repair sem-001 or lex-001.
- MiniLM dense cosine repairs lex-001 synonymy and does not repair spec-002 or sem-001.
- Generic identifier-segment expansion repairs none of the three producer probes and imports alias contamination.

A mechanism that wins more rows is not therefore the general retriever.

## Unsafe transformations

- Function-word stripping changes competitor ranks without raising target correspondence (H-QRL lex-001).
- IDF-capped identifier dumping selects structurally related, semantically heterogeneous tokens and can fire slug-as-spaces aliases (`date`).
- Dense cosine can promote broad conceptual neighbors, including title chunks with no lexical overlap.

## Evaluation invariants

- Rank movement must be decomposed into target correspondence, competitor change, alias, or other every time. The lex-001 rank 7→3 occurred twice with opposite mechanisms.
- Aggregate hit rate moved 3/7 → 6/7 → 4/7 → 5/7 across the three tests and never decided the verdict.
- The signals neighbor remains lex-001 rank 1 under every intervention.
- Alias-trap ood-003 keeps verdict rank 1 with +0.5 after lexical rewrite, morphology, and dense replacement.
- No experiment implemented a reject path.

## Scorer interactions

- Jaccard and alias were stable attribution tools: H1 in-scope producer rows matched control Jaccard/alias/`lexical_cosine` exactly, so movement could be assigned to `dense_cosine`.
- Alias matching is an independent architecture surface. Representation changes do not remove substring traps designed for human queries.
- Combining morphology, dense cosine, identifier expansion, and new alias rules would be a fourth hypothesis. It was not implemented.

## Unresolved architecture failures

- Identifier-register producer burial (`sem-001`) survives identifier expansion, morphology, and MiniLM cosine.
- Conjunction/multi-chunk (`mch-001`) has no designed controller. Incidental hits under H-QRL and H1 are not a solution.
- Near-OOD calibration under dense similarity is an open reject hypothesis, not a threshold chosen here.

---

# Current retrieval design principles

Based on the evidence so far:

1. Prefer minimal transformations whose mechanism can be directly attributed.
2. Separate morphological normalization from semantic expansion. Isolated closed-vocabulary morphology can repair a genuine surface-form miss; bundling it with identifier expansion hides that fact and imports alias risk.
3. Treat identifier overlap as structural evidence, not automatically semantic evidence.
4. Do not use IDF alone as a proxy for semantic relevance.
5. Keep machine-generated query tokens from silently changing the assumptions of downstream scoring components.
6. Inspect score components and competitors, not rank alone. Rank can improve while target score falls, and target score can rise without reaching rank 1. The same rank delta can be artifact in one experiment and correspondence in another.
7. Preserve frozen controls and guardrails when testing retrieval changes.
8. Do not optimize aggregate hit rate against a small sealed evaluation set.
9. Keep caching and instrumentation orthogonal to retrieval-quality hypotheses.
10. Convert surprising failures into new hypotheses rather than immediately patching the benchmark. Incidental short-token morphology (`a → as`, `does → do`) is in this category: document it, do not add an exception during the measured test. Dense overgeneralization to title chunks and near-OOD confidence belong here too.
11. Map failure classes to mechanisms instead of promoting a composite retriever from a small sealed set. Morphology, dense synonymy, and identifier expansion are different tools.
12. Do not treat dense similarity as automatically meaningful, especially for OOD queries or code-register chunks.

# Open hypotheses

H-QRL, H-MORPH, and H1 have been tested independently. Remaining questions should stay independent:

- **H-MORPH-N / coverage:** whether additional sealed morphological misses behave like spec-002, and whether a minimum token length should constrain `+s`/`+es`.
- **H-ID:** constrained identifier expansion can recover useful identifier relationships without alias contamination.
- **H-ALIAS:** alias matching requires different semantics for natural-language query tokens and machine-generated tokens.
- **H-CODE:** an identifier-aware or code-register representation for producer-burial cases MiniLM left buried (`regime` vs `regime_stability`).
- **H-HYBRID:** whether morphology + dense cosine, without identifier expansion, should be preregistered as a new intervention. Not licensed as a production mix from the current audit.
- **H-OOD:** reject/calibration, now that near-OOD dense scores approach in-scope values.

These hypotheses should be tested independently rather than bundled into a single rewrite or hybrid intervention on a measured branch.