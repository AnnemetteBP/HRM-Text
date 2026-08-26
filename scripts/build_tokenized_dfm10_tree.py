#!/usr/bin/env python3
"""Build DFM10 as the DFM9 tokenized tree plus DFM10 additions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("data/tokenized_dfm9"))
    parser.add_argument(
        "--andersen", type=Path, default=Path("data/tokenized_dfm10_andersen")
    )
    parser.add_argument(
        "--alexandra", type=Path, default=Path("data/tokenized_dfm10_alexandra")
    )
    parser.add_argument(
        "--folketing", type=Path, default=Path("data/tokenized_dfm10_folketing")
    )
    parser.add_argument(
        "--deepdive", type=Path, default=Path("data/tokenized_dfm10_deepdive")
    )
    parser.add_argument("--output", type=Path, default=Path("data/tokenized_dfm10"))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def link(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.symlink_to(source.resolve(), target_is_directory=source.is_dir())


def task_directories(root: Path) -> list[Path]:
    tasks: list[Path] = []
    for directory, _, files in os.walk(root, followlinks=True):
        path = Path(directory)
        if path != root and "metadata.json" in files:
            tasks.append(path)
    return sorted(tasks)


def main() -> None:
    args = parse_args()
    for root in (
        args.base,
        args.andersen,
        args.alexandra,
        args.folketing,
        args.deepdive,
    ):
        if not (root / "tokenizer_info.json").is_file():
            raise FileNotFoundError(root / "tokenizer_info.json")
    for addition in (args.andersen, args.alexandra, args.folketing, args.deepdive):
        if (args.base / "tokenizer_info.json").read_bytes() != (
            addition / "tokenizer_info.json"
        ).read_bytes():
            raise ValueError(
                f"DFM9 and {addition} use different tokenizer/template metadata"
            )

    if args.output.exists() or args.output.is_symlink():
        if not args.force:
            raise FileExistsError(f"{args.output} exists; pass --force to rebuild")
        if args.output.is_symlink() or args.output.is_file():
            args.output.unlink()
        else:
            shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    link(args.base / "tokenizer_info.json", args.output / "tokenizer_info.json")

    counts: dict[str, int] = {}
    for label, root in (
        ("dfm9", args.base),
        ("andersen", args.andersen),
        ("alexandra", args.alexandra),
        ("folketing", args.folketing),
        ("deepdive", args.deepdive),
    ):
        count = 0
        for source in task_directories(root):
            name = source.relative_to(root).as_posix()
            link(source, args.output / name)
            count += 1
        counts[label] = count

    manifest = {
        "base": str(args.base),
        "andersen": str(args.andersen),
        "alexandra": str(args.alexandra),
        "folketing": str(args.folketing),
        "deepdive": str(args.deepdive),
        "output": str(args.output),
        "task_counts": counts,
        "total_tasks": sum(counts.values()),
    }
    (args.output / "union_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
