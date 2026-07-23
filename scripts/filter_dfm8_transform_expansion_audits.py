#!/usr/bin/env python3
"""Filter DFM8 transform-expansion candidates using all available audit files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_FAMILIES = (
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
    parser.add_argument("--expansion-root", type=Path, default=Path("data/dfm8_transform_expansion"))
    parser.add_argument("--export-root", type=Path, default=Path("export"))
    parser.add_argument("--output-root", type=Path, default=Path("data/dfm8_transform_expansion_filtered"))
    parser.add_argument("--family", action="append", choices=DEFAULT_FAMILIES, help="Filter only this family. Repeatable.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def audit_files(family_root: Path) -> list[Path]:
    # The final dynamic pass used earlier audit files as skip lists, so a
    # complete accepted set is the union of these roots. They are expected to be
    # disjoint by row_id because later passes skipped previously judged rows.
    known_roots = (
        family_root / "audit_full",
        family_root / "audit_shards",
        family_root / "audit_shards_c64",
        family_root / "audit_shards_c64_u070",
    )
    files: list[Path] = []
    for root in known_roots:
        if root.exists():
            files.extend(sorted(root.rglob("audit.jsonl")))
    if not files:
        files = sorted(family_root.rglob("audit.jsonl"))
    return [p for p in files if p.is_file() and p.stat().st_size > 0]


def main() -> None:
    args = parse_args()
    families = tuple(args.family) if args.family else DEFAULT_FAMILIES
    if args.output_root.exists() and args.force and not args.dry_run:
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    summary: dict[str, object] = {
        "expansion_root": str(args.expansion_root),
        "output_root": str(args.output_root),
        "families": {},
    }
    for family in families:
        family_root = args.expansion_root / family
        data_root = family_root / "data"
        recreate = args.export_root / family / "recreate_dataset.py"
        output_root = args.output_root / family
        audits = audit_files(family_root)
        if not data_root.exists():
            raise SystemExit(f"Missing data root for {family}: {data_root}")
        if not recreate.exists():
            raise SystemExit(f"Missing recreate script for {family}: {recreate}")
        if not audits:
            raise SystemExit(f"No audit files found for {family} under {family_root}")

        cmd = [
            sys.executable,
            str(recreate.resolve()),
            "filter",
            "--data-root",
            str(data_root.resolve()),
            "--glob",
            "*.jsonl.gz",
            "--output-root",
            str(output_root.resolve()),
            "--force",
        ]
        for audit in audits:
            cmd.extend(["--audit", str(audit.resolve())])
        summary["families"][family] = {
            "audit_files": [str(p) for p in audits],
            "output_root": str(output_root),
            "command": cmd,
        }
        print(f"{family}: {len(audits)} audit files -> {output_root}")
        if not args.dry_run:
            subprocess.run(cmd, check=True)

    manifest_path = args.output_root / "filter_manifest.json"
    if not args.dry_run:
        manifest_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
