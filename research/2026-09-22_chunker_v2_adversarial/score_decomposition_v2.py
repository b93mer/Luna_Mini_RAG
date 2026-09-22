"""Score decomposition v2: baseline formula over the v2 adversarial index.

Same as the v1 decomposition but reading metadata/chunks_v2.json via the
shared v2 helpers in run_ablation_v2 (store swap + re-keyed alias map).
Top-5 hits per gold query, components as WEIGHTED contributions
(0.7*cosine, 0.3*lexical, alias) so columns sum to the total.

Read-only: never writes either index. No pipeline files modified.
"""

from __future__ import annotations

import sys
from pathlib import Path

# NOTE (added helper): research scripts live two levels below repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import retrieve  # noqa: E402
from embed import cosine_similarity, model_from_store  # noqa: E402
from evaluate import QUERIES  # noqa: E402
from store_v2 import load_store_v2  # noqa: E402

# NOTE (added helper reuse): install_v2_store patches retrieve.load_store
# and retrieve.SECTION_ALIASES for the v2 id scheme; ids_match handles
# doc_id-prefixed section ids when marking the expected row.
from run_ablation_v2 import ids_match, install_v2_store  # noqa: E402

W_COSINE = 0.7  # must match retrieve.retrieve()
W_LEXICAL = 0.3
TOP_N = 5


def _configure_stdout() -> None:
    """NOTE (added helper): match retrieve.py's Windows encoding guard."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def decompose(query: str) -> list[dict]:
    store = load_store_v2()
    if store is None:
        raise RuntimeError(
            "metadata/chunks_v2.json missing or empty; run ingest_v2.py first"
        )
    model = model_from_store(store.vocab, store.idf)
    query_vec = model.transform([query])[0]
    rows = []
    for chunk in store.chunks:
        cosine = cosine_similarity(query_vec, chunk.embedding)
        lexical = retrieve.lexical_overlap(query, chunk)
        alias = retrieve.alias_boost(query, chunk)
        rows.append(
            {
                "chunk_id": chunk.chunk_id,
                "section_id": chunk.section_id,
                "cosine_raw": cosine,
                "cosine_w": W_COSINE * cosine,
                "lexical_raw": lexical,
                "lexical_w": W_LEXICAL * lexical,
                "alias": alias,
                "total": W_COSINE * cosine + W_LEXICAL * lexical + alias,
            }
        )
    rows.sort(key=lambda row: row["total"], reverse=True)
    return rows[:TOP_N]


def print_table(query: str, expected_id: str, rows: list[dict]) -> None:
    print(f"\n### Query: \"{query}\"  (expected: `{expected_id}`)\n")
    print("| Rank | chunk_id | cosine (x0.7) | lexical (x0.3) | alias | total |")
    print("|---|---|---|---|---|---|")
    for index, row in enumerate(rows, start=1):
        marker = " *" if ids_match(row["section_id"], expected_id) else ""
        print(
            f"| {index}{marker} | {row['chunk_id']} "
            f"| {row['cosine_w']:.4f} (raw {row['cosine_raw']:.4f}) "
            f"| {row['lexical_w']:.4f} (raw {row['lexical_raw']:.4f}) "
            f"| {row['alias']:.2f} | {row['total']:.4f} |"
        )
    print("\n\\* = expected gold section")


def main() -> None:
    _configure_stdout()
    install_v2_store()
    for query, expected_id in QUERIES:
        rows = decompose(query)
        print_table(query, expected_id, rows)


if __name__ == "__main__":
    main()
