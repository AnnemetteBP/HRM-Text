#!/usr/bin/env python3
"""Sample broad DFM8 transformation rows from generated export/data files.

This keeps the existing judged/accepted export-upload rows unchanged and writes
additional broadly sampled candidate rows under data/dfm8_transform_expansion.
The rows are sampled from export/<family>/data files whose shard names are not
already present in export-upload/<family>/data, so DFM8 is not limited to the
small uploaded shard set.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
import shutil
from pathlib import Path
from typing import Any, Iterable


FAMILIES = (
    "common-pile-denoising",
    "common-pile-paragraph-reordering",
    "common-pile-prefix-continuation",
    "common-pile-span-filling",
    "danish-dynaword-denoising",
    "danish-dynaword-paragraph-reordering",
    "danish-dynaword-prefix-continuation",
    "danish-dynaword-span-filling",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-root", type=Path, default=Path("export"))
    parser.add_argument("--accepted-root", type=Path, default=Path("export-upload"))
    parser.add_argument("--output-root", type=Path, default=Path("data/dfm8_transform_expansion"))
    parser.add_argument("--target-multiplier", type=float, default=1.0, help="Additional rows per currently accepted row.")
    parser.add_argument("--seed", type=int, default=20260709)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def jsonl_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and (p.suffix == ".jsonl" or p.name.endswith(".jsonl.gz")))


def iter_lines(path: Path) -> Iterable[str]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield line


def line_key(line: str) -> str:
    # Normalize through JSON so gzip chunking/whitespace cannot create false
    # negatives when comparing export/data with export-upload rows.
    try:
        obj = json.loads(line)
        payload = json.dumps(obj.get("messages", obj), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        payload = line.strip()
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def accepted_hashes(files: list[Path]) -> set[str]:
    hashes: set[str] = set()
    for path in files:
        for line in iter_lines(path):
            hashes.add(line_key(line))
    return hashes


def count_lines(path: Path) -> int:
    return sum(1 for _ in iter_lines(path))


def sample_family(family: str, args: argparse.Namespace) -> dict[str, Any]:
    source_data = args.export_root / family / "data"
    accepted_data = args.accepted_root / family / "data"
    accepted_files = jsonl_files(accepted_data)
    accepted_names = {p.name for p in accepted_files}
    accepted_rows = sum(count_lines(p) for p in accepted_files)
    target_rows = math.ceil(accepted_rows * args.target_multiplier)
    source_files = [p for p in jsonl_files(source_data) if p.name not in accepted_names]
    if not source_files:
        return {
            "family": family,
            "accepted_rows": accepted_rows,
            "target_rows": target_rows,
            "source_files": 0,
            "sampled_rows": 0,
            "reason": "no non-upload source files",
        }

    hashes = accepted_hashes(accepted_files)
    rng = random.Random(f"{args.seed}:{family}")
    rng.shuffle(source_files)
    per_file_target = math.ceil(target_rows / len(source_files))
    out_data = args.output_root / family / "data"
    out_data.mkdir(parents=True, exist_ok=True)
    sampled_rows = 0
    sampled_files = 0
    file_summaries: list[dict[str, Any]] = []

    for src in source_files:
        seen = 0
        duplicate = 0
        chosen: list[str] = []
        for line in iter_lines(src):
            seen += 1
            if line_key(line) in hashes:
                duplicate += 1
                continue
            chosen.append(line)
            if len(chosen) >= per_file_target:
                break
        if not chosen:
            file_summaries.append({"source": str(src), "seen": seen, "duplicates": duplicate, "sampled": 0})
            continue
        take = min(len(chosen), max(0, target_rows - sampled_rows))
        if take <= 0:
            break
        if take < len(chosen):
            chosen = chosen[:take]
        out = out_data / f"dfm8-extra-{src.name}"
        with gzip.open(out, "wt", encoding="utf-8", compresslevel=1) as handle:
            for line in chosen:
                row = json.loads(line)
                if isinstance(row, dict):
                    row["dfm8_transform_expansion"] = True
                    row["dfm8_transform_family"] = family
                    row["dfm8_transform_source_file"] = src.name
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        sampled_rows += take
        sampled_files += 1
        file_summaries.append({"source": str(src), "seen": seen, "duplicates": duplicate, "sampled": take, "output": str(out)})
        if sampled_rows >= target_rows:
            break

    return {
        "family": family,
        "accepted_rows": accepted_rows,
        "target_rows": target_rows,
        "source_files": len(source_files),
        "sampled_source_files": sampled_files,
        "sampled_rows": sampled_rows,
        "per_file_target": per_file_target,
        "files": file_summaries,
    }


def main() -> None:
    args = parse_args()
    if args.output_root.exists():
        if not args.force:
            raise SystemExit(f"{args.output_root} exists; pass --force to rebuild")
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True)
    manifest: dict[str, Any] = {
        "output_root": str(args.output_root),
        "target_multiplier": args.target_multiplier,
        "families": {},
    }
    for family in FAMILIES:
        manifest["families"][family] = sample_family(family, args)
    manifest["accepted_rows"] = sum(v.get("accepted_rows", 0) for v in manifest["families"].values())
    manifest["target_rows"] = sum(v.get("target_rows", 0) for v in manifest["families"].values())
    manifest["sampled_rows"] = sum(v.get("sampled_rows", 0) for v in manifest["families"].values())
    (args.output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "families"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
