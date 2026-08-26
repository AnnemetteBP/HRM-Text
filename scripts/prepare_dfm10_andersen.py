#!/usr/bin/env python3
"""Validate the Andersen modernization split and expose training rows only."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


EXPECTED_COUNTS = {"all": 1187, "train": 1068, "validation": 119}
EXPECTED_SHA256 = {
    "all": "91b914082f389b79a3389379108a6c033f09126056b905393574dcef43b512e3",
    "train": "5dd4f2b67e3e1e358266a8e5e834531abf2630f7eda313588216430f7a683408",
    "validation": "7d635eb87ecab1fd88be0e290fe029d4af183fbafc0097f516fce0e7c60e91bf",
}
EXPECTED_ROLES = ("system", "user", "assistant")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("/work/dfm/andersen"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/dfm10_andersen_sources")
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            validate_row(row, path=path, line_number=line_number)
            rows.append(row)
    return rows


def validate_row(row: dict[str, Any], *, path: Path, line_number: int) -> None:
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) != 3:
        raise ValueError(f"{path}:{line_number}: expected exactly three messages")
    roles = tuple(message.get("role") for message in messages)
    if roles != EXPECTED_ROLES:
        raise ValueError(f"{path}:{line_number}: unexpected roles {roles}")
    for message in messages:
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            raise ValueError(f"{path}:{line_number}: empty message content")
    if not isinstance(row.get("id"), str) or not row["id"].strip():
        raise ValueError(f"{path}:{line_number}: missing id")
    if not isinstance(row.get("chunk_idx"), int):
        raise ValueError(f"{path}:{line_number}: missing integer chunk_idx")


def row_key(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["id"]), int(row["chunk_idx"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    paths = {
        "all": args.source_dir / "pairs_chunked.jsonl",
        "train": args.source_dir / "pairs_chunked_train.jsonl",
        "validation": args.source_dir / "pairs_chunked_val.jsonl",
    }
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    rows = {name: load_jsonl(path) for name, path in paths.items()}
    counts = {name: len(items) for name, items in rows.items()}
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"unexpected split counts: {counts}, expected {EXPECTED_COUNTS}")
    hashes = {name: sha256(path) for name, path in paths.items()}
    if hashes != EXPECTED_SHA256:
        raise ValueError(f"unexpected source hashes: {hashes}")

    keys = {name: {row_key(row) for row in items} for name, items in rows.items()}
    if len(keys["train"]) != counts["train"] or len(keys["validation"]) != counts["validation"]:
        raise ValueError("duplicate (id, chunk_idx) keys within a split")
    if keys["train"] & keys["validation"]:
        raise ValueError("training and validation keys overlap")
    if keys["train"] | keys["validation"] != keys["all"]:
        raise ValueError("training and validation are not an exact partition of all rows")

    if args.output_dir.exists() or args.output_dir.is_symlink():
        if not args.force:
            raise FileExistsError(f"{args.output_dir} exists; pass --force to rebuild")
        if args.output_dir.is_symlink() or args.output_dir.is_file():
            args.output_dir.unlink()
        else:
            shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)

    # The validation file is deliberately not linked into the tokenization tree.
    train_link = args.output_dir / "andersen_modernization__pairs_chunked_train.jsonl"
    train_link.symlink_to(paths["train"].resolve())

    train_titles = {str(row["id"]) for row in rows["train"]}
    validation_titles = {str(row["id"]) for row in rows["validation"]}
    manifest = {
        "source_dir": str(args.source_dir.resolve()),
        "training_file": str(paths["train"].resolve()),
        "validation_file": str(paths["validation"].resolve()),
        "training_link": str(train_link),
        "counts": counts,
        "sha256": hashes,
        "key_overlap": 0,
        "validation_rows_exposed_to_tokenizer": 0,
        "training_titles": len(train_titles),
        "validation_titles": len(validation_titles),
        "title_overlap": len(train_titles & validation_titles),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
