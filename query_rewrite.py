"""General query rewriter for H-QRL and its H-MORPH ablation.

Architecture role: rewrite the query string before frozen rank_all().
Does not change weights, aliases, analyzer, or the sealed eval set.

Policies are locked in
docs/query_set_expansion/2026-10-05_query_rewrite_cache_loop_preregistration.md
and
docs/query_set_expansion/2026-10-05_morphology_only_preregistration.md.
Do not add query-id branches, synonym tables, or alias injection.
"""

from __future__ import annotations

from dataclasses import dataclass

from embed import tokenize


# Locked function-word list (qrl-v1). Complete. Do not tune after seeing ranks.
FUNCTION_WORDS = frozenset(
    {
        "a",
        "about",
        "after",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "before",
        "being",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "for",
        "from",
        "how",
        "if",
        "in",
        "into",
        "is",
        "it",
        "itself",
        "its",
        "may",
        "might",
        "must",
        "no",
        "not",
        "of",
        "on",
        "or",
        "shall",
        "should",
        "than",
        "that",
        "the",
        "then",
        "these",
        "this",
        "those",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "why",
        "will",
        "with",
        "would",
    }
)

REWRITE_POLICY = "qrl-v1"
REWRITE_POLICY_MORPH = "morph-v1"
MIN_SEGMENT_LEN = 4
MAX_IDENTIFIER_EXPANSIONS = 8


@dataclass(frozen=True)
class RewriteResult:
    original: str
    rewritten: str
    content_tokens: list[str]
    stopwords_dropped: list[str]
    morphology: list[str]
    identifier_expansions: list[str]

    @property
    def expansions(self) -> list[str]:
        return sorted(set(self.morphology) | set(self.identifier_expansions))


def _segments(vocab_token: str) -> list[str]:
    """Split a fitted vocab token on '_' and '.' only."""
    return [part for part in vocab_token.replace(".", "_").split("_") if part]


def _morphology_candidates(token: str, vocab: dict[str, int]) -> list[str]:
    found: list[str] = []
    for variant in (token + "s", token + "es"):
        if variant != token and variant in vocab:
            found.append(variant)
    if len(token) > 3 and token.endswith("es") and token[:-2] in vocab:
        found.append(token[:-2])
    elif (
        len(token) > 3
        and token.endswith("s")
        and not token.endswith("ss")
        and token[:-1] in vocab
    ):
        found.append(token[:-1])
    return found


def _identifier_expansions(
    content_tokens: list[str],
    vocab: dict[str, int],
    idf: list[float],
) -> list[str]:
    seen_query = set(content_tokens)
    candidates: dict[str, float] = {}
    for token in dict.fromkeys(content_tokens):
        if len(token) < MIN_SEGMENT_LEN:
            continue
        for vocab_token, index in vocab.items():
            if vocab_token == token or vocab_token in seen_query:
                continue
            if token in _segments(vocab_token):
                current = candidates.get(vocab_token)
                weight = idf[index]
                if current is None or weight > current:
                    candidates[vocab_token] = weight
    ranked = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _weight in ranked[:MAX_IDENTIFIER_EXPANSIONS]]


def _morphology_from_tokens(
    tokens: list[str], vocab: dict[str, int]
) -> list[str]:
    """One-step in-vocab morphology. Does not expand generated variants."""
    original = set(tokens)
    morphology: list[str] = []
    seen_morph: set[str] = set()
    for token in dict.fromkeys(tokens):
        for variant in _morphology_candidates(token, vocab):
            if variant not in seen_morph and variant not in original:
                seen_morph.add(variant)
                morphology.append(variant)
    return sorted(set(morphology))


def _rewrite_morphology_only(query: str, vocab: dict[str, int]) -> RewriteResult:
    """Locked morph-v1: keep the original query, add in-vocab morphology only."""
    tokens = tokenize(query)
    morphology = _morphology_from_tokens(tokens, vocab)
    if morphology:
        rewritten = query + " " + " ".join(morphology)
    else:
        rewritten = query
    return RewriteResult(
        original=query,
        rewritten=rewritten,
        content_tokens=list(tokens),
        stopwords_dropped=[],
        morphology=morphology,
        identifier_expansions=[],
    )


def rewrite_query(
    query: str,
    vocab: dict[str, int],
    idf: list[float],
    policy: str = REWRITE_POLICY,
) -> RewriteResult:
    """Rewrite one query using a locked policy.

    Default remains qrl-v1 so the H-QRL experiment stays reproducible.
    morph-v1 disables identifier expansion and function-word stripping.
    vocab/idf are the fitted store model, not a second analyzer.
    """
    if policy == REWRITE_POLICY_MORPH:
        return _rewrite_morphology_only(query, vocab)
    if policy != REWRITE_POLICY:
        raise ValueError(f"unknown rewrite policy: {policy!r}")

    tokens = tokenize(query)
    content_tokens = [token for token in tokens if token not in FUNCTION_WORDS]
    stopwords_dropped = [token for token in tokens if token in FUNCTION_WORDS]
    morphology = _morphology_from_tokens(content_tokens, vocab)
    identifier_expansions = _identifier_expansions(content_tokens, vocab, idf)
    expansions = sorted(set(morphology) | set(identifier_expansions))

    if not content_tokens:
        rewritten = query
    else:
        rewritten = " ".join(content_tokens + expansions)

    return RewriteResult(
        original=query,
        rewritten=rewritten,
        content_tokens=content_tokens,
        stopwords_dropped=stopwords_dropped,
        morphology=morphology,
        identifier_expansions=identifier_expansions,
    )
