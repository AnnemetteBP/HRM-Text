#!/usr/bin/env python3
"""Build the selected DFM8 tokenized union tree."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


DFM8_SPECIAL_WRAPPER_PREFIX = "dfm8_special_sources__"
DFM8_TRANSFORM_EXPANSION_WRAPPER_PREFIX = "dfm8_transform_expansion__"
DFM8_EXPORT_UPLOAD_WRAPPER_PREFIX = "export-upload__"
DFM8_TARGETED_SYNTHETIC_WRAPPER_PREFIX = "export-upload-dfm8-synthetic__"
DFM8_REPAIRED_OPENHERMES_WRAPPER_PREFIX = "export-upload-dfm8-openhermes-repaired__"
EXPORT_UPLOAD_STRIP_PREFIXES = (
    "common-pile-",
    "danish-dynaword-",
    "transformations-",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-tokenized", type=Path, default=Path("data/tokenized_dfm8_jinja"))
    parser.add_argument("--base-tokenized", type=Path, default=Path("data/tokenized_dfm7"))
    parser.add_argument("--output", type=Path, default=Path("data/tokenized_dfm8"))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def task_dirs(root: Path) -> list[Path]:
    tasks: list[Path] = []
    if not root.exists():
        return tasks
    for dirpath, _, filenames in os.walk(root, followlinks=True):
        if "metadata.json" in filenames:
            tasks.append(Path(dirpath))
    return sorted(tasks)


def link_task(src: Path, dst_root: Path, name: str) -> None:
    dst = dst_root / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(dst)
    dst.symlink_to(src.resolve(), target_is_directory=True)


def selected_name(raw_name: str) -> str | None:
    if raw_name.startswith(DFM8_SPECIAL_WRAPPER_PREFIX):
        return raw_name.removeprefix(DFM8_SPECIAL_WRAPPER_PREFIX)
    if raw_name.startswith(DFM8_TRANSFORM_EXPANSION_WRAPPER_PREFIX):
        return raw_name.removeprefix(DFM8_TRANSFORM_EXPANSION_WRAPPER_PREFIX)
    if raw_name.startswith(DFM8_EXPORT_UPLOAD_WRAPPER_PREFIX):
        name = raw_name.removeprefix(DFM8_EXPORT_UPLOAD_WRAPPER_PREFIX)
        if name.startswith(EXPORT_UPLOAD_STRIP_PREFIXES):
            return name
    if raw_name.startswith(DFM8_TARGETED_SYNTHETIC_WRAPPER_PREFIX):
        name = raw_name.removeprefix(DFM8_TARGETED_SYNTHETIC_WRAPPER_PREFIX)
        if name.startswith("dfm8-synthetic-"):
            return name
    if raw_name.startswith(DFM8_REPAIRED_OPENHERMES_WRAPPER_PREFIX):
        name = raw_name.removeprefix(DFM8_REPAIRED_OPENHERMES_WRAPPER_PREFIX)
        if name.startswith(("dfm8-openhermes-en__", "dfm8-openhermes-da__")):
            return name
    return None


def main() -> None:
    args = parse_args()
    if args.output.exists():
        if not args.force:
            raise SystemExit(f"{args.output} exists; pass --force to rebuild")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    info = args.raw_tokenized / "tokenizer_info.json"
    if not info.exists():
        raise SystemExit(f"Missing tokenizer info: {info}")
    (args.output / "tokenizer_info.json").symlink_to(info.resolve())

    base_selected = 0
    if args.base_tokenized.exists():
        base_info = args.base_tokenized / "tokenizer_info.json"
        if not base_info.exists():
            raise SystemExit(f"Missing base tokenizer info: {base_info}")
        if base_info.read_text() != info.read_text():
            raise SystemExit(
                "Base tokenized tree and DFM8 additions use different tokenizer/template info. "
                f"base={base_info}, additions={info}"
            )
        for src in sorted(args.base_tokenized.iterdir()):
            if src.name == "tokenizer_info.json" or not src.is_dir():
                continue
            link_task(src, args.output, src.name)
            base_selected += 1

    selected = 0
    skipped = 0
    duplicate_skipped = 0
    for src in task_dirs(args.raw_tokenized):
        raw_name = src.relative_to(args.raw_tokenized).as_posix()
        name = selected_name(raw_name)
        if name is None:
            skipped += 1
            continue
        if (args.output / name).exists() or (args.output / name).is_symlink():
            duplicate_skipped += 1
            continue
        link_task(src, args.output, name)
        selected += 1

    manifest = {
        "raw_tokenized": str(args.raw_tokenized),
        "base_tokenized": str(args.base_tokenized),
        "output": str(args.output),
        "base_selected_tasks": base_selected,
        "dfm8_selected_tasks": selected,
        "duplicate_skipped_tasks": duplicate_skipped,
        "skipped_tasks": skipped,
    }
    (args.output / "union_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
