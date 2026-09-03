import hashlib
import json
from pathlib import Path

import numpy as np

from moe_tokenizer_contract import (
    CHAT_TEMPLATE_PATH,
    CORE_SPECIAL_TOKEN_IDS,
    TOKENIZER_FAMILY,
    TOKENIZER_NAME,
    TOKENIZER_REVISION,
    TOKENIZER_VOCAB_SIZE,
)
from scripts.validate_moe_pilot import validate


def test_validate_complete_moe_pilot(tmp_path: Path) -> None:
    root = tmp_path / "pilot"
    tokenizer = root / "tokenizer"
    epoch = root / "epoch_0"
    tokenizer.mkdir(parents=True)
    epoch.mkdir()
    for filename in ("tokenizer.json", "tokenizer_config.json"):
        (tokenizer / filename).write_text("{}")
    (tokenizer / "chat_template.jinja").write_text(
        CHAT_TEMPLATE_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    np.save(root / "tokens.npy", np.asarray([1, 10, 11, 2, 1, 20, 21, 22, 2], dtype=np.uint32))
    np.save(epoch / "inst_start.npy", np.asarray([0, 4], dtype=np.uint64))
    np.save(epoch / "inst_len.npy", np.asarray([2, 2], dtype=np.uint32))
    np.save(epoch / "resp_start.npy", np.asarray([2, 6], dtype=np.uint64))
    np.save(epoch / "resp_len.npy", np.asarray([2, 3], dtype=np.uint32))

    metadata = {
        "tokenizer_info": {
            "vocab_size": TOKENIZER_VOCAB_SIZE,
            "name_or_path": TOKENIZER_NAME,
            "tokenizer_path": str(tokenizer),
            "tokenizer_revision": TOKENIZER_REVISION,
            "tokenizer_family": TOKENIZER_FAMILY,
            "template_mode": "jinja_chat_template",
            "chat_template_sha256": hashlib.sha256(CHAT_TEMPLATE_PATH.read_bytes()).hexdigest(),
            "special_token_ids": CORE_SPECIAL_TOKEN_IDS,
        },
        "total_length": 7,
        "max_seq_len": 5,
        "domains": {
            "danish": {"rows": 1, "train_tokens": 3},
            "math": {"rows": 1, "train_tokens": 2},
            "code": {"rows": 1, "train_tokens": 2},
        },
    }
    (root / "metadata.json").write_text(json.dumps(metadata))

    result = validate(root)

    assert result["status"] == "valid"
    assert result["rows"] == 2
    assert result["train_tokens"] == 7
