#!/usr/bin/env python3
"""Repair and complete the stopped DFM8 XXL epoch-one scheduler campaign."""

from __future__ import annotations

import csv
import json
import os
import sys
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


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: update_dfm8_xxl_epoch1_plan.py PLAN_TSV")
    path = Path(sys.argv[1])
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
        metadata["command"] = command

        if row["job_id"] == "campaign-train-200000":
            metadata["resume_from_tag"] = "ephemeral_step_151000"
            row["log_dir"] = "logs/training/dfm8_XXL_1epoch/step_151000_to_200000"
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
