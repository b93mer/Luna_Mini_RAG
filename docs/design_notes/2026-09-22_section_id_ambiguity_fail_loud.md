# ADR: Fail loud on ambiguous section_id lookup in ChunkStore

**Date:** 2026-09-22
**Status:** Accepted (implemented in commit `534012a`)
**Deciders:** solo POC maintainer

## Context

The v1 chunker (`smart_chunker.py`) assigns `section_id` values that are unique
within a document but not across documents. The direct-lookup path in this
codebase — `store.get_by_section_id` → `retrieve_by_section_id` →
`retrieve_target_sections` — assumes section_ids are **globally unique**, but
nothing enforced that assumption: `get_by_section_id` iterated chunks and
returned the **first** match, so any lookup on a collided id silently bound to
an arbitrary doc.

This is not hypothetical. On `research/loose-docs-contrast`, the 3-doc corpus
(1 trace note + 2 session reviews) produces 74 chunks in which **22 section_id
values collide** between `data/2026-08-21_session_review.md` and
`data/2026-08-24_session_review.md` — both reviews use an identical heading
template (`1_session_summary`, `3_fire`, `cycle`, `discipline`, `draft_date`,
etc.). None of the three evaluation target ids (`question`, `verdict`,
`impact_on_finding_3_5_disposition`) are collided, so evaluation results on
that branch are valid — but only by luck of corpus composition.

Caller analysis constrained the fix shape: `retrieve_by_section_id` takes only
a `section_id` with no `doc_id` in scope, and its caller
`retrieve_target_sections` iterates a hardcoded tuple of target ids, also with
no `doc_id`. No caller layer exists that could disambiguate a collision.

## Decision

Make `ChunkStore.get_by_section_id` fail loud on ambiguity:

- Zero matches → return `None` (unchanged).
- Exactly one match → return it (unchanged).
- More than one match → raise `AmbiguousSectionIdError` (defined in
  `store.py`, subclass of `LookupError`) with a message naming the
  `section_id` and listing the `doc_id`s it appears in.

No other function in `store.py` changed; no pipeline file
(`ingest.py`, `retrieve.py`, `evaluate.py`) changed. Callers get the loud
failure for free when a collision hits a target id. Tests added in
`tests/test_store_ambiguity.py` (unique / missing / colliding cases).
`evaluate.py` still prints PASS on the current `main` corpus.

## Alternatives considered

- **Option A — Namespace by `(doc_id, section_id)`.** Deferred: it requires
  forcing `doc_id` through the public signature of `retrieve_by_section_id`,
  `retrieve_target_sections`, and into `evaluate.py`, which has no concept of
  "which doc the answer should come from."
- **Option B — Return a list and let callers disambiguate.** Deferred: it
  requires a caller layer capable of disambiguation, and no such layer exists.

## Rationale

The invariant the direct-lookup path already assumes is "section_ids are
globally unique." That assumption was unenforced. Making it
**enforced-and-loud** is the minimum change that restores the invariant
without prejudging the deeper design question of whether direct lookup should
eventually become doc-scoped.

## Consequences

### What this fixes

- A collided `section_id` lookup now raises immediately, naming the id and the
  docs involved, instead of silently returning an arbitrary chunk.

### What this does not fix

- The chunker still produces collided ids.
- The `retrieve_target_sections` path still cannot distinguish two docs with
  the same section names — it just fails loudly now instead of picking one
  arbitrarily.
- If a future corpus adds a doc with a `question` (or other target) heading,
  this fix turns a silent bug into a broken evaluation. That is better, but
  still not "handled."

### Deferred deeper fixes

Either of these would resolve the problem structurally; neither is happening
now, and this ADR records why deferring both is acceptable:

- **(a)** Chunker v2's `doc_id::` prefixing of section_ids.
- **(b)** Making the direct-lookup API doc-scoped.

## Revisit triggers

Undo the fail-loud and pick Option A or B (or a deferred deeper fix) when:

- there is a real product use case for cross-doc `section_id` queries, **or**
- chunker v2 lands and the collision goes away structurally.

Naming the trigger conditions now saves future-you from rehashing the whole
decision under time pressure.

## Principle illustrated

For any correctness fix in a shared function, **enumerate callers first**; the
fix is constrained by what information is available at the call sites, not by
what looks cleanest in the function itself.

## References

- Implementation: commit `534012a` on `main` (`store.py`,
  `tests/test_store_ambiguity.py`).
- `research/2026-09-22_loose_docs_contrast/findings.md` (branch
  `research/loose-docs-contrast`) — documents the 22 colliding section_ids
  across the two session reviews, the identical heading template, the
  first-match silent-bind behavior of `get_by_section_id`, and names this
  collision as "the strongest argument so far for the chunker-v2 `doc_id::`
  prefixing" (deferred fix (a) above). Also records that the three target ids
  are uncollided, which is why that branch's ablation results remain valid.
- `research/2026-09-22_alias_boost_ablation/findings.md` (branch
  `research/alias-boost-ablation`) — single-doc baseline (15 chunks) where the
  global-uniqueness assumption holds trivially ("there is exactly one
  `question`, one `verdict`, and one `finding 3.5` section in existence") and
  where config E confirms the `retrieve_by_section_id` direct-lookup path is
  load-bearing enough to be worth ablating. Establishes that the ambiguity
  risk appears exactly when the corpus grows past one doc — the regime this
  ADR targets.
