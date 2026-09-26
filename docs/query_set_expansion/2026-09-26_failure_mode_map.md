# Failure-mode map for the query-set taxonomy

**Date:** 2026-09-26
**Status:** Working map for the query-set expansion sketch
**Governs:** how rows are chosen and labeled. Does not change the pipeline.
**Schema axes:** `docs/design_notes/2026-09-24_taxonomy_schema_design.md`

This is the input to the taxonomy sketch on the query-set expansion branch.
The ADR fixes the axes (architecture under test, task, query shape, failure
mode) and leaves the growth route open. This map says, for each failure mode
in the source notes, what the named practices are, what this repo actually
does, and which sketch choice that implies.

Use it when adding a row: pick one primary mode, write the hypothesis in one
sentence, and set `current_stack` from the mapping below. A row whose
expected result the current stack cannot show is still a valid row. Mark it
`expected_miss` or `unmeasurable` so a later pass/fail is not read as
coverage.

## Architecture this map is against

Lexical + sparse hybrid over section chunks, plus exact `section_id` lookup.

| Piece | What it does | What it does not do |
| --- | --- | --- |
| `smart_chunker.py` | Splits markdown into title, bold-field, and heading chunks. Ids are slugified headings, unique within one doc by a numeric suffix. | Fixed-token windows. Log or code parsing. Cross-doc ids. |
| `embed.py` | TF-IDF on chunk text, L2-normalized. Cosine is a dot product. Unknown query tokens are dropped. | BM25. Neural dense vectors. Multi-vector / late interaction. |
| `retrieve.py` | `0.7 * cosine + 0.3 * Jaccard(heading+text) + alias_boost`. Three section ids have a `+0.5` substring list. Any chunk whose full section id appears in the query (underscores as spaces) gets `+0.35`. No score floor. | Query expansion. Reranking. A reject path. Per-term score logging (`method` is `hybrid` or `section_id`). |
| `store.py` | One JSON file. `get_by_section_id` raises if the id hits more than one doc. `chunk_id` is `doc_id::section_id`. | Doc-scoped lookup. Graphs. Filters on `kind`, line span, or provenance during ranking. |
| `evaluate.py` | Three short in-vocabulary doc-QA queries. Hit if the expected id is in the top 3. | The other five modes, long queries, logs, code files, abstention. |
| `ingest.py` | `.md` and `.txt` under `data/`. Rebuilds the whole store. | Incremental refresh. `retrieve._ensure_index` rebuilds only when the store file is missing, so a changed note can leave `chunks.json` stale until something calls `ingest_all`. |

The live corpus is one note, 15 chunks. The parent section
`code_path_producer_stamp_consumer` is stored as the heading alone
(lines 21–22). The substance of that section is in the three child chunks
`1_upstream_producer_score_definition`, `2_state_stamp_before_conviction`,
and `3_conviction_factor_entry_the_field_under_audit`.

There is no generator. Practices below that constrain an answer model
("do not hallucinate", "do not ignore context") have no runtime here. The
sketch can still label the retrieval failure that would feed that behavior.

Route tags used below:

- **Route L** — late interaction and re-ranking. Better match quality, higher cost.
- **Route S** — dense, sparse, or hybrid / multi-index / multi-vector. The cheaper family, and the multi-vector interest named in the notes.
- **Either** — the row is about the task or the corpus, and both routes still need it.
- **Now** — the current stack already has a piece of this, and the row should show the limit of that piece.

**Bias-check.** Before locking the sketch, count rows that would pass only by repeating `evaluate.py` wording or firing `SECTION_ALIASES`, and confirm that at least one row per stated Route-S interest (multi-vector embeddings, OOS classifier) could come out *against* that interest. If the set cannot contradict the author, it is confirmatory and is not ready.

## Summary

| Mode | In this stack | Sketch job | Route it informs |
| --- | --- | --- | --- |
| Lexical gap | Closed vocab; aliases only for three ids; exact id bypasses the gap when the caller already knows the id | Low-overlap paraphrases of a known section, kept separate from id-lookup rows | Route S (multi-vector / embeddings). Route L also changes token matching. |
| Semantic gap | One dimension per surface string. No query expansion, no complexity router | Polysemy inside this note, especially `regime`. Same-object synonymy is lexical | Route S for embeddings and expansion. A router is a later system, not a query. |
| Multi-hop | One ranking, independent chunks. No graph, no synthesis | A later query that depends on an earlier hit. Two gold chunks from one ranking are multi-chunk, not this mode | Either, once a hop layer exists. Do not treat a multi-chunk top-k as a hop. |
| Specificity mismatch | Section boundaries already; no rerank, no scope filter, no score floor. Heading-only parent chunks | Too-broad and too-narrow pairs aimed at a named section. One stale-index ops note, not a query shape | Route L if the miss is "right family, wrong chunk." Chunk shape is Now. |
| Out-of-domain | Every query is scored and top-k is returned. Alias substrings still fire | Far / near / alias-trap rejects, plus `in_scope` on every other row | Learned OOS classifier (the noted interest). The label is the sketch's job; the model is not. |
| Entity disambiguation | `section_id` and a three-row alias table. Fail-loud on cross-doc id collision. No entity layer | Surface form vs code id, and the `regime` naming collision already in the trace | Graph / agentic approaches stay deferred. The row should fail or collide before those are adopted. |

## Sketch fields

One row, one primary `failure_mode`. Other stresses go in `notes`.

| Field | Values | Why it is on the row |
| --- | --- | --- |
| `id` | `qse-{task}-{mode}-{nnn}` | Stable handle so a later runner can diff the set without depending on query wording. `{task}` is `docqa`, `log`, or `code`. `{mode}` is `lex`, `sem`, `hop`, `spec`, `ood`, or `ent`. `{nnn}` is a three-digit sequence per task+mode (start at `001`). A typo fix keeps the same `id`; a new hypothesis gets the next number. |
| `task` | `doc_qa`, `log_pattern`, `code_retrieval` | The three families from the ADR. Log and code rows stay in the set with `current_stack=unmeasurable` until ingest can see those files. |
| `text_type` | `markdown_note`, `log`, `code` | Same goal, different source. The chunker only builds the first. |
| `length` | `short`, `long` | Same target section, both lengths. The current eval is entirely `short`. |
| `specificity` | `under`, `matched`, `over` | Too general, on-scope, too narrow. |
| `domain` | `in_scope`, `out_of_scope` | Supervision for a later OOS classifier. Every row gets a label, including the ones that should hit. Out-of-scope rows also set `ood_kind`. |
| `hops` | `single`, `multi` | `multi` means hop 2's query depends on hop 1's hit. Two gold chunks from one ranking are `single` with `expected` as a set (multi-chunk). |
| `lexical_overlap` | `high`, `low` | `high` is the baseline cell. `low` is the lexical-gap cell. |
| `ambiguity` | `none`, `polysemy`, `cross_doc_section`, `code_identifier`, `alias_collision` | Which disambiguation problem the wording poses. |
| `ood_kind` | `far`, `near`, `alias_trap`, or empty | Required when `domain=out_of_scope`. Far: little or no corpus vocabulary. Near: in-corpus or adjacent model-b wording, still not a question this index may answer. Alias-trap: out of scope but contains an alias substring. Empty on in-scope rows. |
| `expected` | a `section_id`, a small set of ids, or `reject` | The hypothesis outcome. `reject` means "should not return a supporting chunk." The runner cannot express that yet. |
| `failure_mode` | one of the six | Primary axis. Do not stack modes to make a row look harder. |
| `hypothesis` | one sentence | What a pass or a miss would mean. Written so the row does not silently track the current three queries. |
| `current_stack` | `supported`, `expected_miss`, `unmeasurable` | `supported`: today's retrieve can show the outcome. `expected_miss`: it will return something, and that something is the wrong outcome for a reason named here. `unmeasurable`: no generator, no second doc, no log/code ingest, or no score components. After the first run, this field may be reclassified with a dated note; query, `expected`, and `failure_mode` may not. |
| `route_pressure` | `none`, `route_l`, `route_s`, `either` | Which open growth choice this row is evidence for. `none` if it only polices the current stack. |

Shared-structure list to reuse across broad and specific rows, taken from
this trace rather than invented as a lexicon: `regime`, `block_type`,
`disposition` / `HOLD`, `VolatilityRegimeClassifier`, `vwap_dist`,
`regime_stability`, `alias`. `regime` and `alias` are on the list because
they are **not** stable across sections. That is the connection the notes
asked for: the same surface form joins a broad ask to the wrong specific
object.

Baseline cell, already implemented, do not duplicate as if it were expansion:
the three `QUERIES` in `evaluate.py` (`question`, `verdict`,
`impact_on_finding_3_5_disposition`), all `doc_qa` / `short` / `matched` /
`in_scope` / `single` / `high` / `ambiguity=none` / `current_stack=supported`.
Those three keep their `evaluate.py` identity; new rows start at
`qse-docqa-*-001` and do not reuse the baseline wording.

**Decision rule (lexical vs semantic).** File as lexical gap when the
intended object is one section (one sense) and the query uses different
words for that same object — a substitution of the target section's tokens
would make TF-IDF or Jaccard fire. File as semantic gap when the same
surface tokens can attach to more than one object, or the query and the
chunk share tokens but not sense. If both stresses are present, pick the
one named in `hypothesis`; do not dual-tag the same wording.

## Query set change discipline

The sketch is a pre-registered set, not a working list of prompts that
can be tuned toward a pass.

- **Add** a row only to fill an empty cell or to record a split this map
  now names (far / near / alias-trap OOD, multi-chunk vs multi-hop). Do
  not add another high-overlap paraphrase of `evaluate.py`.
- **Do not rewrite** query text, `expected`, or `failure_mode` after
  seeing retrieve output. That fit is the bias the original notes asked
  the set to prevent.
- **May reclassify** `current_stack` after the first run, with a dated
  note. That is a map correction, not a test-set edit. Clustered
  reclassification is an ADR revisit trigger.
- **Keep ids stable.** A typo fix keeps the same `id`. A new hypothesis
  takes the next `{nnn}`. Withdrawn rows stay in the file marked
  withdrawn; they are not deleted to improve the score.
- **Do not change the retriever** to make a row pass until that row has
  been run against the current stack.

## Lexical gap

**What it is.** The query and the chunk use different words for the same
ask, so exact overlap fails. The notes' bar for high precision is that the
retriever understand the wording, not that the user repeat the heading.

**Practices named in the notes.** Explicit linguistic resources. Dynamic
synonym management. Embedding-based retrieval. Episodic memory for rare
terms. Interactive feedback. The interest recorded for this mode is
hybrid / multi-index retrieval, specifically multi-vector embeddings.

**Where this stack stands.**

- TF-IDF cannot match a synonym. If the query token is outside the fitted
  vocabulary, `_vectorize` skips it. Jaccard uses the same tokenizer
  (`[a-z0-9]+` with dotted and snake_case ids preserved, no stemmer).
- The alias table is a static synonym list for three section ids (`+0.5`).
  It is not dynamic, it does not cover body concepts (`vwap_dist`,
  `independent-of-block_type`, `RegimeObserver`), and it matches by
  substring, so it is also an alias-trap for out-of-domain rows. A second
  boost (`+0.35`) fires when the query contains the chunk's full
  `section_id` with underscores turned into spaces. That helps short ids
  (`question`, `verdict`, `date`, `scope`) and almost never long ones
  (`1 upstream producer score definition`), because the whole slug has to
  appear.
- Exact `section_id` lookup does not have a lexical gap. It also does not
  answer a user who does not already know the id. Keep those rows in a
  separate `method` expectation (`section_id` vs `hybrid`) so a lookup pass
  is not counted as gap closure.
- The three eval queries are `lexical_overlap=high`. They are the control,
  not the test.

**Sketch choice.** Add low-overlap paraphrases whose expected id is still
one of the 15 current sections. Example hypothesis: a query that says
"volatility stability score" and "boss block label" without saying
`verdict`, `independent-of-block_type`, or `VolatilityRegimeClassifier`
is still about `verdict`. `current_stack=expected_miss` until embeddings
or a real synonym layer exist. `route_pressure=route_s` for the
multi-vector interest; a Route L row is the same wording if the question
is whether late interaction matches the tokens a bag-of-words drops.
Rare-term rows (a code id that appears once) test the "episodic memory"
practice only as a label: nothing in the store remembers a term that was
not in the last `fit_transform`.

Do not add linguistic resources, a synonym service, or a second index on
this branch. The row is the decision to leave that practice measurable.

## Semantic gap

**What it is.** The machine's representation of the query and the chunk
does not match a human reading of either. The notes name vocabulary
mismatch, synonymy, and polysemy as the usual causes. Vocabulary mismatch
overlaps lexical gap; keep synonymy and polysemy here so the two modes
stay separable in the set.

**Practices named in the notes.** Knowledge-enhanced embeddings. Query
expansion from external resources, graphs, and neural models. Choosing the
retriever by query complexity. A shared semantic frame if more than one
agent reads the same hits. Evaluation that measures whether the query and
the relevant chunk actually communicated, not only whether a string
matched.

**Where this stack stands.**

- One vocabulary dimension per surface string. `regime` in the conviction
  factor and `regime` in RegimeBoss are the same token. IDF down-weights
  tokens that are common across chunks; it does not split senses. The
  trace states the collision directly: the conviction "regime" factor is
  the `VolatilityRegimeClassifier` / `RegimeObserver` stability score, and
  Finding 3.5 is about RegimeBoss, a different instrument.
- No expansion step sits in front of `retrieve`. The alias boost is not
  expansion; it adds a constant when a section name is mentioned.
- Every hybrid query uses the same weights. There is no complexity router.
  A long compositional query and "verdict section" take one code path.
- One pipeline, one store. No multi-agent frame to align.
- Eval checks section id in the top 3 and, on the direct path, gold phrase
  presence. It does not check that the hit's sense matches the query's
  sense. Heading text is part of the chunk, so a query that repeats the
  heading can pass while the body sense is wrong.
- `RetrievalHit` does not break out cosine vs Jaccard vs alias. A semantic
  row can name which term *should* have fired. Attributing it is
  `unmeasurable` until score components are logged. That logging is a
  deferred instrumentation choice in the ADR, not part of the sketch's
  first pass.

**Sketch choice.** Polysemy rows whose two senses are already two sections.
Broad: "What does regime refer to in this note?" — under-specified, see
specificity. Specific, sense A: the conviction factor / `vwap_dist` /
`1_upstream_producer_score_definition` or `verdict`. Specific, sense B:
RegimeBoss / Finding 3.5 / `impact_on_finding_3_5_disposition`. Same token,
different `expected`. `route_pressure=route_s` if the hypothesis is that
knowledge-enhanced or multi-vector embeddings would split the senses.
Query-expansion and "pick a model by complexity" are labels on the row
(`length` + `difficulty`), not components to build. Synonymy with one
intended object is lexical; see the decision rule above. Do not file the
same wording under both modes.

## Multi-hop

**What it is.** The answer is assembled from more than one retrieval, with
a reasoning step between searches: first hit, intermediate check, further
hops, then synthesis. Needing two chunks in one top-k is **multi-chunk**,
not multi-hop. Multi-chunk is `hops=single` with `expected` as a set.
Multi-hop is `hops=multi`: hop 2 cannot be written until hop 1 returns.
The notes' risks (broken dependency, dropped hop, split context, shortcut
that cites one chunk and skips the chain) apply to the hop case. A
retriever that returns both gold chunks in one ranking has not executed a
hop.

**Practices named in the notes.** Map dependencies as entity links or
causal chains. Mitigate position bias (attention steering, absolute
indexing). Retrieve with both vectors and a graph so evidence stays
connected. Check intermediate steps. Route on confidence so uncertain hops
are flagged without always paying for a heavy model. Test hub overload and
semantic drift. Use a heavier reasoning pass only for chains that cross
documents.

**Where this stack stands.**

- `retrieve` scores every chunk independently and returns top-k. Nothing
  reads a hit and issues another query. Nothing stitches hits.
- The product path fetches Question, Verdict, and Finding 3.5 as three
  separate lookups. They are bundled for display. They are not a chain.
- Several real questions in this note are still single-hop because one
  section already holds the conclusion. `impact_on_finding_3_5_disposition`
  states both the HOLD and that the conviction factor is a different
  instrument. A query answered entirely by that chunk is `hops=single`.
  Calling it multi-hop because the prose mentions another finding inflates
  the axis.
- A real **multi-chunk** split already exists. The independence claim is
  in `verdict`. The input scalar and the stability computation are in
  `1_upstream_producer_score_definition`. A query that asks which scalar
  the independent-of-block_type factor consumes needs both chunks in one
  ranking. That is `hops=single`, `expected` as the pair,
  `current_stack=expected_miss` because nothing requires both. It is not
  a hop: the second id is known before retrieve runs.
- A **multi-hop** row on this corpus uses the first hit as the next
  query. Example: retrieve the verdict, then search with the classifier
  it names to get the input scalar. Today's path cannot issue that second
  search. `hops=multi`, `current_stack=expected_miss`.
- Position bias in the attention sense does not apply: there is no
  attention. What does apply is chunk position as structure. Line spans
  are stored and unused at rank time. The heading-only parent
  `code_path_producer_stamp_consumer` will compete with its children on
  heading tokens and contains none of the path.
- Cross-doc hops are `unmeasurable` on this corpus (one doc). When a second
  doc arrives, a hop that looks up a shared `section_id` raises
  `AmbiguousSectionIdError` instead of traversing. That interaction with
  the 2026-09-22 ADR should be an explicit row, not a surprise.

**Sketch choice.** Write the multi-chunk pair and the multi-hop chain as
separate rows, not a graph in code. Multi-chunk: `verdict` +
`1_upstream_producer_score_definition`, `hops=single`, `expected` as the
pair. Multi-hop: verdict, then a second query built from the named
classifier; `hops=multi`. Both `current_stack=expected_miss`,
`route_pressure=either`. A second pair that collapses into the impact
section is still single-hop — do not file it as either. Hub overload,
semantic drift, and System-2 chains are deferred until a traversal exists;
do not add rows that only those practices can fail. Absolute indexing is
already on the chunk (`start_line`, `end_line`) and unused — a row may
*name* the line span as the expected evidence location, which gives a
future graph something to attach to.

## Specificity mismatch

**What it is.** The query is broader or narrower than the chunk that gets
returned. The notes' downstream symptoms are a hallucinated answer, ignored
evidence, and an off-topic answer. Causes named: chunking artifacts,
semantic gap, no rerank, a stale or mismatched index, context
misalignment.

**Practices named in the notes.** Chunk on semantic boundaries rather than
fixed token counts. Rerank when the architecture needs it, so the
right-scoped chunk outranks a loose match. Filter hits by query scope,
using metadata. Constrain the reader so it cannot answer off-context.

**Where this stack stands.**

- Chunking is already boundary-based (title, bold field, heading). That
  practice is in place for markdown. It is not "adaptive" inside a long
  section: `1_upstream_producer_score_definition` is one chunk covering
  the classifier, the stability function, the config, and the five-step
  computation. A query about only `vwap_dist` still retrieves that whole
  section or misses it. There is no smaller unit.
- The heading-only parent is a chunking artifact. A broad query that
  shares "code path" or "producer" can rank a chunk with no body.
- No reranker. Order is the blended score alone.
- Metadata that could express scope (`doc_id`, `section_id`, `heading`,
  `kind`, line span, provenance) is not a filter. Hybrid search never
  consults it. Exact lookup consults `section_id` only.
- No score floor, so an over-broad query still fills top-k.
- Stale index is real and is not a query shape. `evaluate.py` calls
  `ingest_all` first. `retrieve` does not. A sketch row cannot catch a
  stale store. Record it as an ops limit in the hypothesis, not as
  `failure_mode` padding.
- Reader constraints are `unmeasurable`. The retrieval symptom the sketch
  can grade is the wrong section in top-k, or the right family with the
  wrong grain (parent heading vs child section).

**Sketch choice.** For each high-value target, three rows: `specificity=under`,
`matched`, `over`, same sense, `hops=single`. Under-specific example:
"What is the regime?" with no expected single id (the hypothesis is that
top-k mixes conviction-factor chunks and Finding 3.5). Over-specific
example: a query that names only step 2 of the computation (`abs(v)` on
`vwap_dist`) and expects `1_upstream_producer_score_definition`, knowing
the chunk is larger than the step. `route_pressure=route_l` only when the
hypothesis is that a reranker would promote the child over the heading-only
parent. Chunk-boundary rows are `route_pressure=none` (the practice is
already the chunker). Do not file stale-index as a query.

## Out-of-domain

**What it is.** The question is outside the corpus the index is allowed to
answer from. The notes' risk is a confident answer anyway, which loses
trust and, if the domain is safety-relevant, is worse than a refusal.
This pipeline does not answer. The matching failure is returning a chunk
as if it supported an out-of-scope query.

**Practices named in the notes.** Lightweight detection aligned to the
knowledge base. A learned out-of-scope classifier — this is the approach
the notes single out. Rule-based hybrids. A pipeline shaped as preprocess,
gate, in-scope path, feedback. The gate is the piece the current retrieve
path does not have.

**Where this stack stands.**

- No gate. Any string is embedded, scored against every chunk, and cut to
  top-k.
- A query whose tokens are all unknown collapses toward a zero TF-IDF
  vector. Jaccard is then the lexical residue, and `alias_boost` still
  adds 0.5 if the string contains `verdict`, `question`, `finding 3.5`,
  `disposition`, or `hold stands`. An out-of-scope sentence that mentions
  "verdict" is an in-scope-looking hit. That is the alias trap, and it is
  the same table the lexical-gap section relies on. Do not narrow
  `SECTION_ALIASES` or add a gate to "fix" the trap until those rows have
  been run against the current table; changing the boost first would
  erase the failure the sketch is supposed to measure.
- There is no feedback loop and no classifier to train. The sketch's
  `domain` and `ood_kind` labels are the supervision those practices would
  consume later.
- Safety policy for a future reader is out of scope for this map. The
  retrieval obligation is narrower: an out-of-scope row's `expected` is
  `reject`.

**Sketch choice.** Split out-of-domain into three `ood_kind` values.
Label `domain` on every row, including in-scope controls, so a later
classifier is not trained on rejects alone.

- **Far** (`ood_kind=far`): little or no vocabulary from this trace and
  no alias substring. Hypothesis: top-k still returns a chunk.
- **Near** (`ood_kind=near`): wording from this note or adjacent model-b
  topics (other findings, fire path, launcher, config change) that the
  index is not allowed to answer. The trace header says this pass did not
  change fire-path, launcher, or config behavior; a query that asks for
  those changes is near-OOD relative to this note, not "missing from the
  index" in the abstract.
- **Alias-trap** (`ood_kind=alias_trap`): out of scope but contains
  `verdict`, `finding 3.5`, `disposition`, or `hold stands`. This is the
  high-scoring reject.

All three have `expected=reject` and `current_stack=expected_miss`,
because top-k will still return chunks. The trap slice is the one that
will look in-scope. `route_pressure=route_s` only in the weak sense that
the noted interest is a classifier beside the retriever, not a different
embedding. The classifier itself is not this branch. Rule-based detection
("no alias and near-zero cosine") can be a hypothesis in `notes` without
implementing the gate. Do not implement the gate, and do not edit
`SECTION_ALIASES`, until the three slices have been run.

## Entity disambiguation

**What it is.** Map an ambiguous mention onto the intended object, and
keep that mapping stable as docs are added or revised. The notes' approaches
are GraphRAG, RAGED, query-time graph disambiguation, and agentic RAG with
entity grounding. Challenges named: context, cost, ambiguity when the
graph has many nodes, and a frequent entity overshadowing a rare one.

**Where this stack stands.**

- There is no entity layer. The objects retrieval can point at are chunks.
  `chunk_id` (`doc_id::section_id`) is unique. `section_id` is not unique
  across docs. On collision, lookup fails loud rather than picking an
  entity. That is the 2026-09-22 decision, and it is the current
  disambiguation policy: refuse, do not resolve.
- Aliases bind surface forms to section ids, not to objects in the trace.
  `disposition` boosts Finding 3.5. A later note that uses "disposition"
  for something else inherits that boost. `alias` in the trace means the
  2.30 honesty-gap chain and the 5.7 `macro_compress_pct` alias, which is
  a different object from `SECTION_ALIASES`.
- Code identifiers are tokens. The tokenizer keeps `conviction_detail.factors`
  and `3.5` intact, so an exact id query can overlap. "The classifier" does
  not link to `VolatilityRegimeClassifier`. Nothing tracks that the class
  is the same entity across `verdict` and `1_upstream_producer_score_definition`.
- Provenance stores content hashes and line spans. Retrieval does not
  prefer a newer hash or a specific revision. Stability over time is
  unmeasured. With one doc it is also `unmeasurable`.
- GraphRAG, RAGED, and agentic grounding are not in the repo. Adopting
  them because the notes list them would skip the evidence the sketch is
  supposed to collect: a row that shows two chunks competing for one
  mention.

**Sketch choice.** Four row kinds, all `failure_mode=entity disambiguation`,
distinguished by `ambiguity`:

1. `polysemy` — "regime" as conviction factor vs RegimeBoss. Overlaps
   semantic gap; file it here when the hypothesis is "which object," and
   under semantic gap when the hypothesis is "the embedding collapsed the
   senses." Do not file both for the same wording.
2. `code_identifier` — query uses `VolatilityRegimeClassifier` vs query
   uses "the stability classifier." Expected chunk is the producer section
   or `verdict`, stated in the hypothesis. Exact-id wording may be
   `current_stack=supported` because the token survives TF-IDF. Descriptive
   wording is `expected_miss`.
3. `cross_doc_section` — `question` / `verdict` once a second note uses the
   same template. `current_stack=unmeasurable` until that doc is ingested.
   The expected behavior of *lookup* is the existing exception, not a
   silent choice of doc. Hybrid search would rank both and return top-k
   with no doc constraint. Write that as the hypothesis so the sketch does
   not assume the fail-loud path and the hybrid path agree.
4. `alias_collision` — two in-corpus objects could claim `disposition` /
   `hold stands`. Prefer this tag when both objects are in the index;
   prefer `ood_kind=alias_trap` when one side is not in the corpus at all.

`route_pressure=none` until those rows fail for a reason a graph would
fix. Entity overshadowing (a common heading crowding out a rare id) can be
one `code_identifier` row; it does not justify a graph implementation by
itself.

## What the first sketch should decide

These are the choices the map is for. They are taxonomy choices. They are
not retriever work.

1. **Coverage before paraphrase.** The first new rows fill empty cells:
   `lexical_overlap=low`, `domain=out_of_scope` with all three `ood_kind`
   values, `specificity=under|over`, the verdict/producer **multi-chunk**
   pair, one **multi-hop** chain that uses the verdict as the next query,
   and one `regime` sense split. More wording variants of the three eval
   queries wait until those cells exist.

2. **One mode per row.** Alias-trap as `ood_kind` is first-wave
   out-of-domain, not a second mode. Interactions that remain second wave:
   `regime` that is also a hop, alias-trap that is also entity collision.
   The first wave has to stay attributable.

3. **Mark the stack honestly.** `expected_miss` and `unmeasurable` are
   successful sketch outcomes. A set that is all `supported` has collapsed
   back to the baseline cell.

4. **Leave the growth route open.** Rows carry `route_pressure` so a later
   ADR can see whether the misses cluster on Route S (synonyms, sense,
   multi-vector) or Route L (right family, wrong chunk, needs a rerank).
   The sketch does not pick the route.

5. **Log and code stay labeled and unscored.** `task=log_pattern` and
   `task=code_retrieval` rows are allowed. `text_type` is `log` or `code`,
   `current_stack=unmeasurable`. They record the versatility requirement
   without pretending `smart_chunker.py` ingested a log line or a `.py`
   file. Code *mentions inside the trace* are `text_type=markdown_note`
   and `ambiguity=code_identifier`.

6. **Shared-structure list stays short and tied to this note.** Extend it
   only when a new row needs a term that already points at two objects.
   A general synonym list is the lexical-gap practice, and it is deferred.

7. **Pre-register per-category predictions.** Before retrieve runs on the
   new rows, write the predicted `current_stack` mix for each of the six
   modes (how many `supported` / `expected_miss` / `unmeasurable`). Lock
   those counts. After the run, compare. Do not add or rewrite rows to
   close the gap; only `current_stack` may move, with a dated note.

## Deferred with the route

Not sketch fields, and not this branch: multi-vector indexes, a learned
OOS model, query expansion, a reranker, a hop controller, GraphRAG-style
entity linking, score-component logging, doc-scoped lookup, log/code
ingest, and a reader that could hallucinate. The map's job is to make
those absences visible on the rows that would justify them.

## References

- Schema axes: `docs/design_notes/2026-09-24_taxonomy_schema_design.md`.
- Prior lookup decision: `docs/design_notes/2026-09-22_section_id_ambiguity_fail_loud.md`.
- Pipeline and build corpus read for this map: `smart_chunker.py`,
  `embed.py`, `retrieve.py`, `store.py`, `evaluate.py`, `ingest.py`,
  `data/2026-08-10_regime_factor_composition_trace.md`,
  `metadata/chunks.json` (15 chunks).
- **Reading-pass provenance.** Claims about what this stack does and does
  not do come from a 2026-09-26 reading of those files and of the
  unstructured notes that became the 2026-09-24 ADR. They are not from
  running an expanded query set. A later `current_stack` reclassification
  should cite a retrieve run, not a second reading pass.
