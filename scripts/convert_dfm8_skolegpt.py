#!/usr/bin/env python3
"""Convert kobprof/skolegpt-instruct rows for DFM8."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from datasets import load_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-root", type=Path, default=Path("data/downloads/datasets"))
    parser.add_argument("--output-root", type=Path, default=Path("data/dfm8_special_sources/kobprof_skolegpt_instruct"))
    parser.add_argument("--source-name", default="kobprof_skolegpt_instruct")
    parser.add_argument("--repo-id", default="kobprof/skolegpt-instruct")
    parser.add_argument("--shard-size", type=int, default=100_000)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def dataset_ref(download_root: Path, name: str, repo_id: str) -> str:
    local = download_root / name
    return str(local) if local.exists() else repo_id


def clean(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def converted_row(source_name: str, split: str, idx: int, row: dict[str, Any]) -> dict[str, Any] | None:
    system_prompt = clean(row.get("system_prompt"))
    question = clean(row.get("question"))
    response = clean(row.get("response"))
    upstream_source = clean(row.get("source"))
    upstream_id = clean(row.get("id"))
    if not question or not response:
        return None

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(
        [
            {"role": "user", "content": question},
            {"role": "assistant", "content": response},
        ]
    )
    return {
        "messages": messages,
        "source": source_name,
        "skolegpt_source": upstream_source,
        "skolegpt_id": upstream_id,
        "split": split,
        "row_id": f"{source_name}:{split}:{idx}",
        "dfm8_category": classify(upstream_source),
        "language": "da",
    }


def classify(upstream_source: str) -> str:
    source = upstream_source.lower()
    if source == "niv":
        return "danish_education_natural_instructions"
    if source == "flan":
        return "danish_education_flan"
    if source:
        return f"danish_education_{source.replace('-', '_')}"
    return "danish_education_instruction"


def main() -> None:
    args = parse_args()
    if args.output_root.exists() and args.force:
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    source = dataset_ref(args.download_root, args.source_name, args.repo_id)
    dataset = load_dataset(source, split="train")
    manifest: dict[str, Any] = {
        "repo_id": args.repo_id,
        "source": source,
        "output_root": str(args.output_root),
        "shard_size": args.shard_size,
        "files": [],
        "rows": 0,
        "skipped": 0,
        "by_upstream_source": {},
    }

    shard_idx = -1
    shard_rows = 0
    handle = None
    out = None
    try:
        for idx, row in enumerate(dataset):
            if args.max_rows is not None and manifest["rows"] >= args.max_rows:
                break
            record = converted_row(args.source_name, "train", idx, dict(row))
            if record is None:
                manifest["skipped"] += 1
                continue
            if handle is None or shard_rows >= args.shard_size:
                if handle is not None:
                    handle.close()
                    manifest["files"].append({"path": str(out), "rows": shard_rows})
                shard_idx += 1
                shard_rows = 0
                out = args.output_root / f"train-{shard_idx:05d}.jsonl"
                if out.exists() and not args.force:
                    raise SystemExit(f"{out} exists; pass --force to rebuild")
                handle = out.open("w", encoding="utf-8")
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            shard_rows += 1
            manifest["rows"] += 1
            upstream = record.get("skolegpt_source") or "unknown"
            by_source = manifest["by_upstream_source"]
            assert isinstance(by_source, dict)
            by_source[upstream] = int(by_source.get(upstream, 0)) + 1
    finally:
        if handle is not None:
            handle.close()
            manifest["files"].append({"path": str(out), "rows": shard_rows})

    (args.output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
