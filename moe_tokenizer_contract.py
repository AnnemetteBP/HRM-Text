"""Pinned tokenizer and chat-format contract for from-scratch HRM-MoE runs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


TOKENIZER_NAME = "openeurollm/tokenizer-128k-v2"
TOKENIZER_REVISION = "5c1fc6c70779ec84580c2a68d75c6b569b3381f5"
TOKENIZER_VOCAB_SIZE = 131_072
TOKENIZER_FAMILY = "openeurollm_v2"
CORE_SPECIAL_TOKEN_IDS = {"<unk>": 0, "<bos>": 1, "<eos>": 2, "<pad>": 3}
CHAT_SPECIAL_TOKENS = ("<|im_start|>", "<|im_end|>")
CHAT_TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "evaluation"
    / "chat_templates"
    / "hrm_moe_chatml.jinja"
)


def load_chat_template() -> str:
    return CHAT_TEMPLATE_PATH.read_text(encoding="utf-8")


def configure_tokenizer(tokenizer: Any) -> str:
    """Validate the pinned tokenizer and install the repository-owned template."""
    if len(tokenizer) != TOKENIZER_VOCAB_SIZE:
        raise ValueError(
            f"Expected {TOKENIZER_VOCAB_SIZE:,} tokenizer entries, got {len(tokenizer):,}"
        )
    for token, expected_id in CORE_SPECIAL_TOKEN_IDS.items():
        actual_id = tokenizer.convert_tokens_to_ids(token)
        if actual_id != expected_id:
            raise ValueError(f"Expected {token}={expected_id}, got {actual_id}")
    for token in CHAT_SPECIAL_TOKENS:
        token_id = tokenizer.convert_tokens_to_ids(token)
        encoded = tokenizer.encode(token, add_special_tokens=False)
        if token_id == tokenizer.unk_token_id or encoded != [token_id]:
            raise ValueError(f"Required ChatML marker is not atomic: {token}")

    template = load_chat_template()
    tokenizer.chat_template = template
    return hashlib.sha256(template.encode("utf-8")).hexdigest()
