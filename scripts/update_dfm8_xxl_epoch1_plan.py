#!/usr/bin/env python3
"""Repair and complete the stopped DFM8 XXL epoch-one scheduler campaign."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

TRAIN_ENV = (
    "CC=/usr/bin/gcc CXX=/usr/bin/g++ AS=/usr/bin/as "
    "COMPILER_PATH=/usr/libexec/gcc/x86_64-linux-gnu/13:"
    "/usr/lib/gcc/x86_64-linux-gnu/13:/usr/bin "
    "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "
    "PATH=/home/ucloud/miniforge3/envs/hrm/bin:/usr/local/cuda/bin:"
    "/usr/local/bin:/usr/bin:/bin"
)
BARE_TORCHRUN = "torchrun --nproc_per_node=8"
EXPLICIT_TORCHRUN = "/home/ucloud/miniforge3/envs/hrm/bin/torchrun --nproc_per_node=8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-tag", default="ephemeral_step_151000")
    parser.add_argument("plan_tsv", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = args.plan_tsv
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit(f"missing TSV header: {path}")

    expected = {
        "campaign-train-200000",
        "campaign-train-250000",
        "campaign-train-268857",
    }
    found: set[str] = set()
    for row in rows:
        if row["job_id"] not in expected:
            continue
        found.add(row["job_id"])
        metadata = json.loads(row["metadata_json"])
        command = str(metadata["command"])
        if BARE_TORCHRUN in command:
            command = command.replace(BARE_TORCHRUN, EXPLICIT_TORCHRUN, 1)
        torchrun_index = command.index(EXPLICIT_TORCHRUN)
        command = f"{TRAIN_ENV} {command[torchrun_index:]}"
        explicit_fast_path = {
            "fsdp_shard_degree": "null",
            "fsdp_reshard_after_forward": "false",
            "fsdp_accumulation_sync_mode": "no_sync",
        }
        for key, value in explicit_fast_path.items():
            if f"{key}=" not in command:
                command += f" {key}={value}"
        metadata["command"] = command

        if row["job_id"] == "campaign-train-200000":
            metadata["resume_from_tag"] = args.resume_tag
            resume_step = args.resume_tag.rsplit("_", 1)[-1]
            row["log_dir"] = f"logs/training/dfm8_XXL_1epoch/step_{resume_step}_to_200000"
            row["status"] = "pending"
            row["attempt"] = "0"
        elif row["job_id"] == "campaign-train-268857":
            metadata["completion_checkpoint_tag"] = "epoch_1"
        row["metadata_json"] = json.dumps(metadata, separators=(",", ":"), sort_keys=True)

    missing = expected - found
    if missing:
        raise SystemExit(f"missing expected training rows: {sorted(missing)}")

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
