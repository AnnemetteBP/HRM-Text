#!/usr/bin/env python3
"""Validate a sampled HRM-MoE pilot before spending GPU time on it."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from moe_tokenizer_contract import (
    CHAT_TEMPLATE_PATH,
    CORE_SPECIAL_TOKEN_IDS,
    TOKENIZER_FAMILY,
    TOKENIZER_NAME,
    TOKENIZER_REVISION,
    TOKENIZER_VOCAB_SIZE,
)


INDEX_DTYPES = {
    "inst_start": np.dtype(np.uint64),
    "inst_len": np.dtype(np.uint32),
    "resp_start": np.dtype(np.uint64),
    "resp_len": np.dtype(np.uint32),
}


def load_array(path: Path, expected_dtype: np.dtype[Any]) -> np.ndarray:
    if not path.is_file():
        raise ValueError(f"Missing array: {path}")
    array = np.load(path, mmap_mode="r")
    if array.ndim != 1:
        raise ValueError(f"{path} must be one-dimensional, got {array.shape}")
    if array.dtype != expected_dtype:
        raise ValueError(f"{path} must use {expected_dtype}, got {array.dtype}")
    return array


def validate_tokenizer_info(root: Path, info: dict[str, Any]) -> None:
    expected = {
        "vocab_size": TOKENIZER_VOCAB_SIZE,
        "name_or_path": TOKENIZER_NAME,
        "tokenizer_revision": TOKENIZER_REVISION,
        "tokenizer_family": TOKENIZER_FAMILY,
        "template_mode": "jinja_chat_template",
        "special_token_ids": CORE_SPECIAL_TOKEN_IDS,
    }
    for key, value in expected.items():
        if info.get(key) != value:
            raise ValueError(f"tokenizer_info.{key}: expected {value!r}, got {info.get(key)!r}")

    template_digest = hashlib.sha256(CHAT_TEMPLATE_PATH.read_bytes()).hexdigest()
    if info.get("chat_template_sha256") != template_digest:
        raise ValueError("Dataset chat-template digest does not match the repository template")

    tokenizer_path = Path(str(info.get("tokenizer_path", "")))
    if not tokenizer_path.is_absolute():
        tokenizer_path = Path(__file__).resolve().parents[1] / tokenizer_path
    if tokenizer_path.resolve() != (root / "tokenizer").resolve():
        raise ValueError(f"Tokenizer snapshot does not belong to this dataset: {tokenizer_path}")
    for filename in ("tokenizer.json", "tokenizer_config.json"):
        if not (tokenizer_path / filename).is_file():
            raise ValueError(f"Tokenizer snapshot is missing {filename}")
    saved_template_path = tokenizer_path / "chat_template.jinja"
    if saved_template_path.is_file():
        saved_template = saved_template_path.read_text(encoding="utf-8")
    else:
        tokenizer_config = json.loads(
            (tokenizer_path / "tokenizer_config.json").read_text(encoding="utf-8")
        )
        saved_template = tokenizer_config.get("chat_template")
    if not isinstance(saved_template, str):
        raise ValueError("Tokenizer snapshot does not contain the HRM-MoE chat template")
    saved_digest = hashlib.sha256(saved_template.encode("utf-8")).hexdigest()
    if saved_digest != template_digest:
        raise ValueError("Tokenizer snapshot contains a different chat template")


def validate_epoch(root: Path, epoch_dir: Path, token_count: int) -> dict[str, int]:
    arrays = {
        name: load_array(epoch_dir / f"{name}.npy", dtype)
        for name, dtype in INDEX_DTYPES.items()
    }
    rows = len(arrays["inst_start"])
    if rows == 0 or any(len(array) != rows for array in arrays.values()):
        raise ValueError(f"{epoch_dir} has empty or unequal-length index arrays")
    if np.any(arrays["inst_len"] == 0) or np.any(arrays["resp_len"] < 2):
        raise ValueError(f"{epoch_dir} contains an empty instruction or truncated response")

    inst_end = arrays["inst_start"] + arrays["inst_len"]
    resp_end = arrays["resp_start"] + arrays["resp_len"]
    if np.any(inst_end > token_count) or np.any(resp_end > token_count):
        raise ValueError(f"{epoch_dir} contains offsets beyond tokens.npy")
    if np.any(inst_end != arrays["resp_start"]):
        raise ValueError(f"{epoch_dir} has non-contiguous instruction/response pairs")

    lengths = arrays["inst_len"].astype(np.uint64) + arrays["resp_len"]
    return {
        "rows": rows,
        "max_sequence_tokens": int(lengths.max()),
        "train_tokens": int((lengths - 1).sum()),
    }


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    metadata_path = root / "metadata.json"
    if not metadata_path.is_file():
        raise ValueError(f"Missing metadata: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    validate_tokenizer_info(root, metadata.get("tokenizer_info", {}))

    tokens = load_array(root / "tokens.npy", np.dtype(np.uint32))
    if len(tokens) == 0:
        raise ValueError("tokens.npy is empty")
    if int(tokens.max()) >= TOKENIZER_VOCAB_SIZE:
        raise ValueError("tokens.npy contains a token outside the declared vocabulary")

    epoch_dirs = sorted(path for path in root.glob("epoch_*") if path.is_dir())
    if not epoch_dirs:
        raise ValueError("No epoch directories found")
    epoch_summaries = [validate_epoch(root, path, len(tokens)) for path in epoch_dirs]
    reference = epoch_summaries[0]
    if any(summary != reference for summary in epoch_summaries[1:]):
        raise ValueError("Epoch index sets disagree on row or token totals")
    if metadata.get("total_length") != reference["train_tokens"]:
        raise ValueError("metadata.total_length disagrees with sampled indices")
    if metadata.get("max_seq_len") != reference["max_sequence_tokens"]:
        raise ValueError("metadata.max_seq_len disagrees with sampled indices")

    domains = metadata.get("domains", {})
    if not isinstance(domains, dict) or not domains:
        raise ValueError("Dataset metadata must contain non-empty domain counts")
    expected_domains = metadata.get("expected_domains")
    if expected_domains is not None and set(domains) != set(expected_domains):
        raise ValueError(
            f"Unexpected pilot domains: {sorted(domains)}; "
            f"expected {sorted(expected_domains)}"
        )
    domain_tokens = sum(int(value["train_tokens"]) for value in domains.values())
    if domain_tokens != reference["train_tokens"]:
        raise ValueError("Per-domain train-token counts do not match the sampled total")

    return {
        "dataset": str(root),
        "epochs": len(epoch_dirs),
        "stored_tokens": len(tokens),
        **reference,
        "domains": domains,
        "tokenizer_revision": TOKENIZER_REVISION,
        "status": "valid",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    summary = validate(args.dataset)
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        if args.receipt.exists():
            raise SystemExit(f"Refusing to overwrite validation receipt: {args.receipt}")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
