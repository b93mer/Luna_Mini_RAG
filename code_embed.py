"""Locked Jina code encoder for the H-CODE experiment.

Architecture role: turn query/chunk strings into 768-d L2-normalized
vectors using one pinned code-oriented embedding model. Does not rank.
Does not rewrite queries. Does not expand identifiers. Does not touch
the frozen TF-IDF analyzer or the MiniLM H1 encoder.

Identity is locked in
docs/query_set_expansion/2026-10-05_hcode_preregistration.md.
Do not swap models after seeing sealed ranks.

The published SentenceTransformer wrapper cannot construct JinaBert
under transformers 5.18.0. Encoding therefore follows the model card's
AutoModel + mean-pool + L2 procedure on the same pinned weights.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import torch
import torch.nn.functional as F
import transformers.pytorch_utils as _pytorch_utils
from transformers import AutoConfig, AutoModel, AutoTokenizer


def _shim_find_pruneable_heads_and_indices() -> None:
    """Restore a helper removed in transformers 5.x.

    JinaBert remote code still imports find_pruneable_heads_and_indices
    from transformers.pytorch_utils. The function is unused during
    encode(); this shim is loader glue, not a representation change.
    """
    if hasattr(_pytorch_utils, "find_pruneable_heads_and_indices"):
        return

    def find_pruneable_heads_and_indices(
        heads: list[int],
        n_heads: int,
        head_size: int,
        already_pruned_heads: set[int],
    ) -> tuple[set[int], torch.LongTensor]:
        mask = torch.ones(n_heads, head_size)
        remaining = set(heads) - already_pruned_heads
        for head in remaining:
            adjusted = head - sum(1 if h < head else 0 for h in already_pruned_heads)
            mask[adjusted] = 0
        mask = mask.view(-1).contiguous().eq(1)
        index = torch.arange(len(mask))[mask].long()
        return remaining, index

    _pytorch_utils.find_pruneable_heads_and_indices = (
        find_pruneable_heads_and_indices
    )


_shim_find_pruneable_heads_and_indices()

# BERT-era PretrainedConfig defaults that JinaBert still reads, but
# transformers 5.18 no longer provides on the base config.
_JINA_CONFIG_DEFAULTS = {
    "is_decoder": False,
    "add_cross_attention": False,
    "chunk_size_feed_forward": 0,
    "output_attentions": False,
    "output_hidden_states": False,
    "use_return_dict": True,
}


MODEL_ID = "jinaai/jina-embeddings-v2-base-code"
MODEL_REVISION = "516f4baf13dec4ddddda8631e019b5737c8bc250"
EMBEDDING_DIM = 768
MAX_SEQ_LENGTH = 8192
POOLING = "mean"
DEVICE = "cpu"
LIBRARY = "transformers"
LIBRARY_VERSION = "5.18.0"
TORCH_VERSION = "2.14.1+cpu"
TRANSFORMERS_VERSION = "5.18.0"
NUMPY_VERSION = "2.3.5"
PYTHON_VERSION = "3.14.2"
TRUST_REMOTE_CODE = True
REMOTE_CODE_REPO = "jinaai/jina-bert-v2-qk-post-norm"
REMOTE_CODE_REVISION = "3baf9e3ac750e76e8edd3019170176884695fb94"
TORCH_DTYPE = "float32"

_ENCODER: "CodeEncoder | None" = None


@dataclass
class CodeEncoder:
    tokenizer: object
    model: object
    max_seq_length: int = MAX_SEQ_LENGTH

    def eval(self) -> "CodeEncoder":
        self.model.eval()
        return self


def prepare_text(text: str) -> str:
    """Identity preprocessing. No snake_case, dotted, or camelCase split."""
    return text


def _patch_jina_config(config: object) -> None:
    """Fill BERT-era config attrs missing under transformers 5.18."""
    for name, value in _JINA_CONFIG_DEFAULTS.items():
        if not hasattr(config, name):
            setattr(config, name, value)


def _bind_bert_mask_helpers(model: torch.nn.Module) -> None:
    """Restore PreTrainedModel mask helpers removed in transformers 5.x."""

    def get_extended_attention_mask(self, attention_mask, input_shape, device=None, dtype=None):
        if dtype is None:
            dtype = self.dtype
        if attention_mask.dim() == 3:
            extended = attention_mask[:, None, :, :]
        elif attention_mask.dim() == 2:
            extended = attention_mask[:, None, None, :]
        else:
            raise ValueError(
                f"Wrong shape for attention_mask (shape {tuple(attention_mask.shape)})"
            )
        extended = extended.to(dtype=dtype)
        return (1.0 - extended) * torch.finfo(dtype).min

    def get_head_mask(self, head_mask, num_hidden_layers, is_attention_chunked=False):
        if head_mask is None:
            return [None] * num_hidden_layers
        if head_mask.dim() == 1:
            head_mask = head_mask.unsqueeze(0).unsqueeze(0).unsqueeze(-1).unsqueeze(-1)
            head_mask = head_mask.expand(num_hidden_layers, -1, -1, -1, -1)
        elif head_mask.dim() == 2:
            head_mask = head_mask.unsqueeze(1).unsqueeze(-1).unsqueeze(-1)
        if is_attention_chunked:
            head_mask = head_mask.unsqueeze(-1)
        return head_mask.to(dtype=self.dtype)

    if not hasattr(model, "get_extended_attention_mask"):
        model.get_extended_attention_mask = get_extended_attention_mask.__get__(
            model, type(model)
        )
    if not hasattr(model, "get_head_mask"):
        model.get_head_mask = get_head_mask.__get__(model, type(model))


def mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Official Jina mean pooling: mask-averaged token embeddings."""
    expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    summed = torch.sum(last_hidden_state * expanded, dim=1)
    counts = torch.clamp(expanded.sum(dim=1), min=1e-9)
    return summed / counts


def model_identity() -> dict[str, object]:
    """Exact encoder identity recorded beside code vectors."""
    return {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "embedding_dim": EMBEDDING_DIM,
        "max_seq_length": MAX_SEQ_LENGTH,
        "pooling": POOLING,
        "normalized": True,
        "device": DEVICE,
        "library": LIBRARY,
        "library_version": LIBRARY_VERSION,
        "torch_version": TORCH_VERSION,
        "transformers_version": TRANSFORMERS_VERSION,
        "numpy_version": NUMPY_VERSION,
        "python_version": PYTHON_VERSION,
        "torch_dtype": TORCH_DTYPE,
        "trust_remote_code": TRUST_REMOTE_CODE,
        "remote_code_repo": REMOTE_CODE_REPO,
        "remote_code_revision": REMOTE_CODE_REVISION,
        "transformers_prune_helper_shim": True,
        "jina_config_attr_shim": True,
        "bert_mask_helper_shim": True,
        "zero_token_type_ids": True,
        "loader": "AutoModel+mean_pool",
        "same_encoder_for_query_and_chunks": True,
        "external_identifier_segmentation": False,
        "prepare_text": "identity",
    }


def get_encoder() -> CodeEncoder:
    """Load the pinned Jina code encoder once. CPU float32 inference only."""
    global _ENCODER
    if _ENCODER is None:
        hub = {
            "revision": MODEL_REVISION,
            "code_revision": REMOTE_CODE_REVISION,
            "trust_remote_code": TRUST_REMOTE_CODE,
        }
        config = AutoConfig.from_pretrained(MODEL_ID, **hub)
        _patch_jina_config(config)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, **hub)
        model = AutoModel.from_pretrained(
            MODEL_ID,
            config=config,
            torch_dtype=torch.float32,
            **hub,
        )
        model.to(DEVICE)
        model.eval()
        _bind_bert_mask_helpers(model)
        _ENCODER = CodeEncoder(tokenizer=tokenizer, model=model)
    return _ENCODER


def l2_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in vector))


def encode_texts(texts: list[str]) -> list[list[float]]:
    """Encode strings with mean pooling and L2 normalization.

    The same encoder is used for queries and chunks. Inputs longer than
    MAX_SEQ_LENGTH tokens are truncated by the tokenizer. Strings are
    not identifier-segmented before encoding.
    """
    if not texts:
        return []
    encoder = get_encoder()
    prepared = [prepare_text(text) for text in texts]
    encoded = encoder.tokenizer(
        prepared,
        padding=True,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        return_tensors="pt",
    )
    if "token_type_ids" not in encoded:
        encoded["token_type_ids"] = torch.zeros_like(encoded["input_ids"])
    encoded = {key: value.to(DEVICE) for key, value in encoded.items()}
    with torch.no_grad():
        output = encoder.model(**encoded)
        pooled = mean_pool(output.last_hidden_state, encoded["attention_mask"])
        normalized = F.normalize(pooled, p=2, dim=1)
    vectors: list[list[float]] = []
    for row in normalized:
        vector = [float(value) for value in row.detach().cpu().tolist()]
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(
                f"expected {EMBEDDING_DIM}-d code vector, got {len(vector)}"
            )
        vectors.append(vector)
    return vectors


def encode_query(query: str) -> list[float]:
    """Encode one original query string. No rewriting or identifier dump."""
    return encode_texts([query])[0]
