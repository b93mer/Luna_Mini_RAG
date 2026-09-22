"""Local TF-IDF embeddings for the Luna retrieval pipeline.

Architecture role: turn chunk text into vectors for hybrid search.

No embedding service, model weights, or third-party vector library is
configured in this repo, so this module is a stdlib stand-in. Extra
helpers below are documented as such.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    """NOTE (added helper): local tokenizer.

    Substitutes for an NLP tokenizer / embedding preprocessor that is not
    present in the provided files. Keeps dotted ids (`3.5`) and snake_case.
    """
    return TOKEN_RE.findall(text.lower())


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """NOTE (added helper): cosine of two equal-length vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


def _l2_normalize(vector: list[float]) -> list[float]:
    """NOTE (added helper): unit-length scaling so cosine is a dot product."""
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


@dataclass
class TfidfModel:
    """Fitted vocabulary + IDF weights persisted in metadata/chunks.json."""

    vocab: dict[str, int]
    idf: list[float]

    def transform(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def _vectorize(self, text: str) -> list[float]:
        tokens = tokenize(text)
        counts = Counter(tokens)
        total = float(len(tokens)) or 1.0
        dim = len(self.vocab)
        vector = [0.0] * dim
        for token, count in counts.items():
            index = self.vocab.get(token)
            if index is None:
                continue
            tf = count / total
            vector[index] = tf * self.idf[index]
        return _l2_normalize(vector)


def fit_transform(texts: list[str]) -> tuple[TfidfModel, list[list[float]]]:
    """Fit IDF on a corpus and return normalized vectors for each text.

    NOTE (added helper): `fit_transform` replaces a hosted embedding API.
    """
    tokenized = [tokenize(text) for text in texts]
    df: Counter[str] = Counter()
    for tokens in tokenized:
        df.update(set(tokens))

    vocab = {token: index for index, token in enumerate(sorted(df))}
    n_docs = max(len(texts), 1)
    idf = [0.0] * len(vocab)
    for token, index in vocab.items():
        idf[index] = math.log((n_docs + 1) / (df[token] + 1)) + 1.0

    model = TfidfModel(vocab=vocab, idf=idf)
    return model, model.transform(texts)


def model_from_store(vocab: dict[str, int], idf: list[float]) -> TfidfModel:
    """NOTE (added helper): rebuild the vectorizer from chunks.json."""
    return TfidfModel(vocab=vocab, idf=idf)
