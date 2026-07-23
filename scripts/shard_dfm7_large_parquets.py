#!/usr/bin/env python3
"""Shard large DFM7 Parquet sources for safer chat-template tokenization."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pyarrow.parquet as pq


DEFAULT_INPUT = Path("data/downloads/datasets/dfm_dyna_instruct/data/apertus-sft-mixture/apertus-sft-mixture.parquet")
DEFAULT_OUTPUT = Path("data/dfm7_special_sources/dfm_dyna_instruct_apertus_sft_mixture_shards")
DEFAULT_COLUMNS = ("messages",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--columns", nargs="+", default=list(DEFAULT_COLUMNS))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Missing input Parquet: {args.input}")
    if args.output.exists():
        if not args.force:
            raise SystemExit(f"{args.output} exists; pass --force to rebuild")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    parquet_file = pq.ParquetFile(args.input)
    available = set(parquet_file.schema_arrow.names)
    columns = [column for column in args.columns if column in available]
    if not columns:
        raise SystemExit(f"None of the requested columns exist in {args.input}: {args.columns}")

    shards = []
    for row_group_idx in range(parquet_file.num_row_groups):
        table = parquet_file.read_row_group(row_group_idx, columns=columns)
        shard = args.output / f"part-{row_group_idx:04d}.parquet"
        pq.write_table(table, shard, compression="zstd")
        shards.append(
            {
                "path": shard.name,
                "rows": table.num_rows,
                "bytes": shard.stat().st_size,
                "source_row_group": row_group_idx,
            }
        )

    manifest = {
        "source": str(args.input),
        "columns": columns,
        "num_source_row_groups": parquet_file.num_row_groups,
        "num_source_rows": parquet_file.metadata.num_rows,
        "shards": shards,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps({k: v for k, v in manifest.items() if k != "shards"} | {"shard_count": len(shards)}, indent=2))


if __name__ == "__main__":
    main()
