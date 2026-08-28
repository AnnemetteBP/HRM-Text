#!/usr/bin/env python3
"""Materialize a deterministic quality-audit sample from accepted Folketing rows."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_ROOT = ROOT / "logs/dfm10_folketing_audit_8gpu_vllm/workers"
DEFAULT_SOURCE_ROOT = ROOT / "data/dfm10_folketing_transform_sources"
DEFAULT_OUTPUT = ROOT / "logs/data_audits/dfm10_folketing_quality_a4b_20260827/samples.jsonl"
SOURCE_ID = "dfm-agreement/rigsarkivet-folketinget-14004"
TASKS = (
    "folketingets-dokumenter-denoising",
    "folketingets-dokumenter-error-correction",
    "folketingets-dokumenter-prefix-continuation",
    "folketingets-dokumenter-span-filling",
)


def atomic_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def reservoir_decisions(paths: list[Path], per_task: int, seed: int) -> tuple[dict[str, list[dict]], dict[str, int]]:
    rng = {task: random.Random(f"{seed}:{task}") for task in TASKS}
    reservoirs: dict[str, list[dict]] = {task: [] for task in TASKS}
    accepted = defaultdict(int)
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                task = str(row.get("dataset", ""))
                if task not in reservoirs or row.get("keep") is not True:
                    continue
                accepted[task] += 1
                current = reservoirs[task]
                if len(current) < per_task:
                    current.append(row)
                else:
                    replacement = rng[task].randrange(accepted[task])
                    if replacement < per_task:
                        current[replacement] = row
    for task, rows in reservoirs.items():
        if len(rows) != per_task:
            raise ValueError(f"{task}: expected {per_task} accepted rows, found {len(rows)}")
    return reservoirs, dict(accepted)


def materialize_task(source_root: Path, task: str, decisions: list[dict]) -> list[dict]:
    by_line = {int(str(row["row_id"]).rsplit(":", 1)[1]): row for row in decisions}
    source = source_root / task / "data/train-00000.jsonl.gz"
    found: list[dict] = []
    with gzip.open(source, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle):
            decision = by_line.get(line_number)
            if decision is None:
                continue
            row = json.loads(line)
            messages = row.get("messages")
            if not isinstance(messages, list):
                raise ValueError(f"{task}:{line_number} has no messages list")
            assistant_positions = [idx for idx, message in enumerate(messages) if message.get("role") == "assistant"]
            if not assistant_positions:
                raise ValueError(f"{task}:{line_number} has no assistant target")
            target = assistant_positions[-1]
            found.append(
                {
                    "source_id": SOURCE_ID,
                    "generation": "dfm10",
                    "form": "generated and acceptance-audited",
                    "task_name": task,
                    "row_index": line_number,
                    "prompt": json.dumps(messages[:target], ensure_ascii=False),
                    "response": json.dumps(messages[target], ensure_ascii=False),
                    "acceptance_audit": {
                        "row_id": decision["row_id"],
                        "judge": decision.get("judge"),
                    },
                }
            )
            if len(found) == len(by_line):
                break
    if len(found) != len(by_line):
        raise ValueError(f"{task}: materialized {len(found)} of {len(by_line)} selected rows")
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-root", type=Path, default=DEFAULT_DECISION_ROOT)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--completed-partitions", default="0,1,2,3,4,5")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260827)
    args = parser.parse_args()
    if args.samples % len(TASKS):
        raise ValueError(f"--samples must be divisible by {len(TASKS)}")

    partitions = [int(value) for value in args.completed_partitions.split(",")]
    decision_paths = [
        args.decision_root / f"partition_{partition}/export_judge.audit.jsonl" for partition in partitions
    ]
    missing = [path for path in decision_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)

    reservoirs, accepted = reservoir_decisions(decision_paths, args.samples // len(TASKS), args.seed)
    samples: list[dict] = []
    for task in TASKS:
        samples.extend(materialize_task(args.source_root, task, reservoirs[task]))
    samples.sort(key=lambda row: (row["task_name"], row["row_index"]))
    for ordinal, sample in enumerate(samples):
        sample["sample_ordinal"] = ordinal
        sample["sample_id"] = hashlib.blake2b(
            f"{SOURCE_ID}\0{sample['task_name']}\0{sample['row_index']}".encode(), digest_size=16
        ).hexdigest()
        sample["source_available_rows"] = sum(accepted.values())
        sample["accepted_pool_partitions"] = partitions
    atomic_jsonl(args.output, samples)
    print(json.dumps({"output": str(args.output), "samples": len(samples), "accepted_pool": accepted}, indent=2))


if __name__ == "__main__":
    main()
