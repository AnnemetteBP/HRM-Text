#!/usr/bin/env python3
"""Convert selected giannor TV2R instruction datasets for DFM8."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from datasets import load_dataset


DATASETS = {
    "giannor_dala_tv2r_it": "giannor/dala_tv2r_it",
    "giannor_gec_dala_tv2r_it": "giannor/gec_dala_tv2r_it",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-root", type=Path, default=Path("data/downloads/datasets"))
    parser.add_argument("--output-root", type=Path, default=Path("data/dfm8_special_sources/giannor_tv2r_instruction"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-rows-per-split", type=int, default=None)
    return parser.parse_args()


def dataset_ref(download_root: Path, name: str, repo_id: str) -> str:
    local = download_root / name
    return str(local) if local.exists() else repo_id


def sample_dict(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("samples")
    return value if isinstance(value, dict) else {}


def converted_row(source_name: str, split: str, idx: int, row: dict[str, Any]) -> dict[str, Any] | None:
    direction = row.get("direction")
    samples = sample_dict(row)
    content = samples.get("content")
    response = samples.get("response")
    if not isinstance(direction, str) or not direction.strip():
        return None
    if not isinstance(content, str) or not content.strip():
        return None
    if not isinstance(response, str) or not response.strip():
        return None
    user = f"{direction.strip()}\n\n{content.strip()}"
    record: dict[str, Any] = {
        "messages": [
            {"role": "user", "content": user},
            {"role": "assistant", "content": response.strip()},
        ],
        "source": source_name,
        "split": split,
        "row_id": f"{source_name}:{split}:{idx}",
        "dfm8_category": "danish_gec_acceptability",
        "language": "da",
    }
    for key in ("corruption_type", "affected_token_1", "affected_token_2"):
        if key in samples and samples[key] is not None:
            record[key] = samples[key]
    return record


def write_dataset(name: str, repo_id: str, args: argparse.Namespace) -> dict[str, Any]:
    source = dataset_ref(args.download_root, name, repo_id)
    out_dir = args.output_root / name
    if out_dir.exists() and args.force:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {"repo_id": repo_id, "source": source, "splits": {}, "rows": 0, "skipped": 0}
    dataset = load_dataset(source)
    for split in sorted(dataset.keys()):
        out = out_dir / f"{split}.jsonl"
        if out.exists() and not args.force:
            raise SystemExit(f"{out} exists; pass --force to rebuild")
        rows = 0
        skipped = 0
        with out.open("w", encoding="utf-8") as handle:
            for idx, row in enumerate(dataset[split]):
                if args.max_rows_per_split is not None and rows >= args.max_rows_per_split:
                    break
                record = converted_row(name, split, idx, dict(row))
                if record is None:
                    skipped += 1
                    continue
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                rows += 1
        summary["splits"][split] = {"path": str(out), "rows": rows, "skipped": skipped}
        summary["rows"] += rows
        summary["skipped"] += skipped
    return summary


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"output_root": str(args.output_root), "datasets": {}}
    for name, repo_id in DATASETS.items():
        manifest["datasets"][name] = write_dataset(name, repo_id, args)
    (args.output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
