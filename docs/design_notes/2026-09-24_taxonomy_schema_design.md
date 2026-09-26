# ADR: Taxonomy schema for query-set expansion

**Date:** 2026-09-24
**Status:** Proposed (notes structured into this ADR on 2026-09-26; no pipeline change)
**Deciders:** solo POC maintainer

## Context

Luna's retrieval work is aimed at three task families: question-answering over
documentation, log-pattern retrieval, and code retrieval. The nearer jobs
inside that — text retrieval, research for model-b diagnosis and analysis,
and the data behind model-b documentation, logging, and code — are uses of
those families, not extra architectures.

The comparison set for how the retriever might grow is five families:
lexical, sparse, dense, late interaction, and re-ranking. Late interaction
and re-ranking retrieve better and cost more. Dense and sparse run cheaper
and often underperform. BM25 is the strong zero-shot baseline in the
lexical/sparse family. This repo does not run BM25.

What actually runs, on one markdown trace
(`data/2026-08-10_regime_factor_composition_trace.md`, 15 section chunks in
`metadata/chunks.json`):

- **Chunking** (`smart_chunker.py`). Heading- and bold-field units (`title`,
  `field`, `section`), not fixed token windows. A heading whose body is only
  the next child heading becomes a heading-only chunk. That is already true
  of `code_path_producer_stamp_consumer`: stored text is the heading line.
- **Representation** (`embed.py`). Corpus TF-IDF, L2-normalized, scored by
  cosine. The vocabulary is closed over ingested chunk text. A query token
  absent from that vocabulary adds nothing to the vector.
- **Ranking** (`retrieve.py`). Full scan, one blended score:
  `0.7 * cosine + 0.3 * Jaccard(query, heading + text) + alias_boost`.
  The alias table is a static substring list for three section ids
  (`question`, `verdict`, `impact_on_finding_3_5_disposition`), worth
  `+0.5`. Any other chunk whose full `section_id` (underscores as spaces)
  appears in the query gets `+0.35`. There is no score floor. Top-k is
  always returned when the store has chunks.
- **Direct path.** `retrieve_target_sections` looks up those three ids.
  `ChunkStore.get_by_section_id` returns the single match, or raises
  `AmbiguousSectionIdError` when the id exists in more than one doc
  (ADR `2026-09-22_section_id_ambiguity_fail_loud.md`). `chunk_id` is
  already `doc_id::section_id`; the lookup key is the bare `section_id`.
- **Store.** One JSON file. No inverted index, dense index, graph, or
  reranker. Ingest reads `.md` and `.txt` only.
- **Eval** (`evaluate.py`). Three short queries. A query passes when the
  expected `section_id` is in the top 3. The direct-lookup check asks that
  the chunk contain a gold phrase. All three queries reuse surface forms
  from the targets (`conviction_detail.factors`, `verdict`, `block_type`,
  `Finding 3.5`).

That is a **lexical + sparse hybrid**, plus an exact-id side path. It is
not a dense embedding model, not late interaction, and not a learned
reranker. TF-IDF cosine sits in the sparse family; it is not BM25. The
pipeline's **build corpus** is that one ingested trace (the text that
fitted TF-IDF and that `retrieve` ranks today); the taxonomy's **target
corpus** is documentation, logs, and code for model-b diagnosis, which
first-wave rows may name but this index does not yet contain.

There is no answer generator in this repo. The pipeline returns chunks.
Effects the notes describe as hallucination, ignored evidence, or a
confident wrong answer appear only if a later reader treats a bad hit as
support. Query-set expansion can still define those rows; it cannot observe
generation here.

Versatility is the constraint on the schema. Queries will vary in length
for the same goal. Sources will not stay one research note: logs and code
are named tasks, and the current trace already quotes code paths, config
files, and finding ids inside markdown. Some terms keep a structure across
broad and specific asks (`regime`, `block_type`, `disposition`) and some
only look shared (`regime` the conviction factor vs `regime` the
RegimeBoss label — the trace itself calls this a naming collision).
Difficulty has to run past the three direct prompts. The set can start as
a baseline. It has to stay interpretable after the corpus and the
retriever change, which means each row states the hypothesis it is testing.
Otherwise the set drifts toward whatever the current note and the current
alias table already pass.

## Decision

The next branch sketches a query set on four axes. Failure-mode definitions,
the practices named for each, and the mapping onto this pipeline live in
`docs/query_set_expansion/2026-09-26_failure_mode_map.md`. This ADR fixes
the axes and the choices left open.

1. **Architecture under test.** Every row is against the current
   lexical/sparse hybrid unless the row says otherwise. Describe that
   system as TF-IDF cosine + heading Jaccard + static alias boost +
   exact `section_id`. Leave "BM25", "dense", and "late interaction" for
   the comparison set.

2. **Task.** Labels for the sketch: `doc_qa`, `log_pattern`,
   `code_retrieval`. Model-b diagnosis, documentation structure, logging,
   and code structure file under those three. They do not add a fourth
   retrieval family.

3. **Query shape.** Each row records length (short / long), domain grain
   (broad / specific), text type (markdown note / log / code), and
   difficulty (direct / compositional). The current three queries occupy
   one cell: short, specific, markdown, direct, high token overlap.

4. **Failure mode.** Each row has one primary mode from the six in the
   source notes: lexical gap, semantic gap, multi-hop, specificity
   mismatch, out-of-domain, entity disambiguation. A row that only
   paraphrases `evaluate.py` does not cover an axis.

**Growth route is not chosen.** Two routes stay open:

- **Route L** — late interaction and re-ranking.
- **Route S** — stay in the cheap family: dense embeddings, sparse
  retrieval, or the hybrid / multi-index / multi-vector design called out
  in the notes.

The sketch should contain rows that would move a later choice between L
and S. Rows that only the current alias table can pass do not do that.

Two interests are recorded and not adopted: hybrid / multi-index retrieval
with multi-vector embeddings (lexical gap), and a learned out-of-scope
classifier (out-of-domain). The taxonomy should be able to score both
later. Neither interest is a change to `retrieve.py` on the expansion
branch.

## Alternatives considered

- **Commit to Route L now.** Deferred. The quality claim for late
  interaction and re-ranking is general. The only measurements in repo are
  three in-vocabulary queries. Cost is the reason the cheap path stays open.
- **Commit to Route S, including multi-vector embeddings, now.** Deferred
  for the same measurement gap. The interest is recorded under lexical gap
  in the companion map, where the current stack's closed vocabulary and
  static aliases are the concrete limit.
- **Grow the set by paraphrasing the three gold queries.** Rejected as the
  expansion policy. Those queries share vocabulary with the targets, so
  they do not expose lexical gap, out-of-domain, multi-hop, or entity
  collision. More of them would bias the set toward this note.
- **Write the taxonomy as a catalog of five families with no tie to this
  pipeline.** Rejected. The next branch expands the query set for this
  system. The five families stay the comparison set. Rows say what this
  pipeline can retrieve, what it will miss for a known reason, and what it
  cannot measure yet.

## Rationale

The schema exists so expansion is a set of labeled hypotheses, not a longer
list of prompts that already work. Query length, text type, domain grain,
and difficulty will move independently of which retriever is in the loop.
A row that names its failure mode, its expected section or its expected
reject, and whether today's stack can even show the outcome, stays useful
after a retriever swap. A row that only restates "What is the verdict…"
does not.

Keeping Route L and Route S open is deliberate. The notes already state the
cost/quality split. Choosing a route before the set can tell the routes
apart would make the set confirm the choice.

## Consequences

### What this frames

- A place to file a query before any new retriever exists.
- Today's `evaluate.py` result stays the baseline cell (short, specific,
  in-vocabulary doc QA). It is not coverage of the six modes.
- Log and code rows can be sketched now, marked unsupported until ingest
  can see those texts. A miss on them is a corpus limit, not a ranking bug.

### What this does not do

- No change to chunker, embedder, store, retriever, or evaluator.
- No selection of Route L or Route S.
- No log parser and no code parser. The chunker splits markdown headings
  and bold fields. Code in the trace is still a markdown section.

### Deferred deeper fixes

These would change the architecture or the measurement, not the sketch.
None of them is this branch:

- ~~Breaking `RetrievalHit` into cosine, Jaccard, and alias components.~~
  ~~Today `method` is `hybrid` or `section_id` and `score` is one float, so
  a row cannot yet say which term fired.~~
- A reject path for out-of-domain queries. Top-k currently always returns
  chunks.
- A hop controller or a graph. Retrieval is one ranking over independent
  chunks.
- Doc-scoped `section_id` lookup, already deferred in the 2026-09-22 ADR.
  Cross-doc entity rows will collide with that deferral on purpose.

## Revisit triggers

Reopen this ADR when any of these is true:

- The sketch has a query that cannot be filed on the four axes.
- A second retriever is prototyped, so "architecture under test" is no
  longer one stack.
- The corpus is more than one note, or ingest accepts logs or code.
- A multi-vector index or an out-of-scope classifier is actually proposed.
  That proposal is a new ADR. This schema should already hold the rows
  that justify it.
- `current_stack` labels need reclassification after the first sketch run.
  A single disagreement is a dated field correction in the map (query,
  `expected`, and `failure_mode` stay locked). Reopen this ADR if those
  reclassifications cluster, because the architecture claims in Context
  would then be wrong.

## Principle illustrated

Classify the retriever you have before you expand the set that will judge
the retriever you might build. A query set that only the current aliases
can pass cannot tell late interaction from TF-IDF.

## References

- Companion map (definitions, practices, current-system mapping, sketch
  fields): `docs/query_set_expansion/2026-09-26_failure_mode_map.md`.
- Prior decision this schema assumes: `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md`.
- Pipeline the axes describe: `smart_chunker.py`, `embed.py`, `retrieve.py`,
  `store.py`, `evaluate.py`, `ingest.py`.
- Corpus the first rows should be written against:
  `data/2026-08-10_regime_factor_composition_trace.md`.
- Deferred deeper fixes first task is resolved. Fixed on 9/26/26 before query tests.
