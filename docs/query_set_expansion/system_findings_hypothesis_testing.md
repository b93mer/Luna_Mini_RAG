# Luna Retrieval System Findings

## Purpose

This document records empirical knowledge about the retrieval system derived from controlled experiments. It distinguishes mechanisms that are supported, unsupported, or still uncertain.

These findings describe the current corpus, analyzer, vocabulary, scoring architecture, alias behavior, and evaluation set. They should not be treated as universal retrieval rules.

---

## 1. Closed-vocabulary morphology can repair lexical representation misses

**Status:** Supported, narrow evidence.

A query token may fail to match a relevant chunk when the corpus contains only a nearby morphological form. In H-QRL, `threshold` did not correspond strongly enough with the gold producer while `thresholds` already existed in the fitted vocabulary.

Adding the in-vocabulary morphological variant increased producer cosine from approximately 0.052 to 0.183 and moved the producer from rank 9 to rank 1. Alias contribution remained zero.

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

One positive row is not enough to establish morphology as a permanent retrieval policy. Additional morphological cases are required to estimate its generality and blast radius.

---

## 2. Generic identifier-segment expansion is not a reliable semantic bridge

**Status:** Unsupported in H-QRL v1.

Expanding a query token into identifiers that contain that token as a `_` or `.` delimited segment did not reliably recover the relevant producer terminology.

For the `regime` query case, the expansion mechanism selected RegimeBoss, state, filename, and update-related identifiers but did not recover `regime_stability`. Producer rank moved from 10 to 11.

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

H-QRL ranked candidate identifier expansions by IDF. The resulting top candidates were rare but not necessarily useful to the target query.

### What does not work

Do not equate corpus rarity with semantic relevance.

### Why

IDF measures discriminativeness within the corpus, not whether an identifier preserves the meaning or intent of the query.

A high-IDF expansion may therefore be highly distinctive while pointing toward the wrong concept.

---

## 4. Machine-generated rewrite tokens can violate assumptions made by the alias layer

**Status:** Supported failure mechanism.

Identifier expansion introduced `regime_update_interval_seconds`. The substring `date` inside `update` caused the slug-as-spaces alias mechanism to apply a `+0.35` alias score to the `date` section.

The `date` section consequently became rank 1 on multiple rewritten queries despite zero cosine and zero Jaccard evidence.

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

In the H-QRL negative-control row, the producer moved from rank 7 to rank 3 even though its absolute score decreased.

The apparent improvement came primarily from competing chunks losing score after stopword removal.

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

H-QRL changed the measurable hit count from 3/7 to 6/7, but the joint hypothesis was still weakened.

Some additional hits arose from mechanisms different from those predicted, and several queries acquired an incorrect `date` winner.

### Evaluation rule

Do not accept retrieval changes because aggregate top-k hit rate increases.

Prefer mechanistic agreement with preregistered predictions and preservation of guardrails.

---

## 7. Cache behavior is ranking-transparent under the tested conditions

**Status:** Supported.

The first pass produced 0/12 cache hits and the second identical pass produced 12/12 hits. Cached rankings were identical to first-pass rankings, and no ≥0.99 cosine collisions occurred between different rewritten queries.

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

The tracker exposed which expansions fired, how frequently they occurred, cache behavior, and ranking effects without mutating rewrite rules during the measured experiment.

### What works

Instrumentation that records mechanism-level behavior without adapting the system during evaluation.

### Why

It allows failed hypotheses to produce reusable system knowledge while preserving the independence of the experiment.

Tracker statistics may motivate a later preregistered hypothesis but should not directly modify rules during the same evaluation cycle.

---

# Current retrieval design principles

Based on the evidence so far:

1. Prefer minimal transformations whose mechanism can be directly attributed.
2. Separate morphological normalization from semantic expansion.
3. Treat identifier overlap as structural evidence, not automatically semantic evidence.
4. Do not use IDF alone as a proxy for semantic relevance.
5. Keep machine-generated query tokens from silently changing the assumptions of downstream scoring components.
6. Inspect score components and competitors, not rank alone.
7. Preserve frozen controls and guardrails when testing retrieval changes.
8. Do not optimize aggregate hit rate against a small sealed evaluation set.
9. Keep caching and instrumentation orthogonal to retrieval-quality hypotheses.
10. Convert surprising failures into new hypotheses rather than immediately patching the benchmark.

# Open hypotheses

The current evidence motivates separate future experiments:

- **H-MORPH:** closed-vocabulary morphology improves genuine morphological misses with low guardrail damage.
- **H-ID:** constrained identifier expansion can recover useful identifier relationships without alias contamination.
- **H-ALIAS:** alias matching requires different semantics for natural-language query tokens and machine-generated tokens.
- **H1:** dense cosine may provide the semantic correspondence needed for producer-burial cases that cannot be solved safely through lexical rewriting.

These hypotheses should be tested independently rather than bundled into a single rewrite intervention.