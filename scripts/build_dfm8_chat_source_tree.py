#!/usr/bin/env python3
"""Build a DFM8 chat-tokenization source tree."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DFM8_EXTRA_ROOTS = (
    Path("data/dfm8_special_sources"),
    Path("data/dfm8_transform_expansion_filtered"),
    Path("export-upload"),
    Path("export-upload-dfm8-synthetic"),
    Path("export-upload-dfm8-openhermes-repaired"),
)

DFM8_EXPORT_UPLOAD_PREFIXES = (
    "common-pile-",
    "danish-dynaword-",
    "transformations-",
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dfm7-source-tree", type=Path, default=Path("data/dfm7_chat_sources"))
    parser.add_argument("--output", type=Path, default=Path("data/dfm8_chat_sources"))
    parser.add_argument("--new-only", action="store_true", help="Only link DFM8 additions; reuse data/tokenized_dfm7 for inherited sources.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def link_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(dst)
    dst.symlink_to(src.resolve(), target_is_directory=src.is_dir())


def link_children(src_root: Path, dst_root: Path, *, prefixes: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    linked: list[dict[str, str]] = []
    if not src_root.exists():
        return linked
    for src in sorted(src_root.iterdir()):
        if prefixes is not None and not src.name.startswith(prefixes):
            continue
        dst = dst_root / src.name
        if dst.exists() or dst.is_symlink():
            continue
        link_tree(src, dst)
        linked.append({"src": str(src), "dst": str(dst)})
    return linked


def main() -> None:
    args = parse_args()
    if args.output.exists():
        if not args.force:
            raise SystemExit(f"{args.output} exists; pass --force to rebuild")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    manifest: dict[str, object] = {
        "output": str(args.output),
        "new_only": args.new_only,
        "dfm7_source_tree": str(args.dfm7_source_tree),
        "linked": [],
    }
    linked = manifest["linked"]
    assert isinstance(linked, list)

    if not args.new_only:
        linked.extend(
            {"mode": "dfm7_inherited", **item}
            for item in link_children(args.dfm7_source_tree, args.output)
        )

    for root in DFM8_EXTRA_ROOTS:
        prefixes = DFM8_EXPORT_UPLOAD_PREFIXES if root.name == "export-upload" else None
        dst_root = args.output / root.name
        linked.extend(
            {"mode": "dfm8_extra_root", **item}
            for item in link_children(root, dst_root, prefixes=prefixes)
        )

    (args.output / "dfm8_chat_source_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in manifest.items() if k != "linked"} | {"linked_count": len(linked)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
