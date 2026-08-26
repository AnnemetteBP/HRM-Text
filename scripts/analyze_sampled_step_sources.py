#!/usr/bin/env python3
"""Attribute optimizer-step windows in a sampled V1 corpus to source tasks."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from multipack_sampler import MultipackDistributedBatchSampler


def parse_window(value: str) -> tuple[str, int, int]:
    try:
        name, bounds = value.split("=", 1)
        start, end = (int(part) for part in bounds.split(":", 1))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected NAME=START:END") from exc
    if start > end:
        raise argparse.ArgumentTypeError("window start must not exceed end")
    return name, start, end


def npy_length(path: Path) -> int:
    return int(np.load(path, mmap_mode="r").shape[0])


def task_boundaries(tokenized_path: Path) -> tuple[np.ndarray, list[str]]:
    names: list[str] = []
    ends: list[int] = []
    cursor = 0
    for task_dir in sorted(tokenized_path.iterdir()):
        if not task_dir.is_dir():
            continue
        cursor += npy_length(task_dir / "tokens.npy")
        names.append(task_dir.name)
        ends.append(cursor)
    return np.asarray(ends, dtype=np.int64), names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sampled-path", type=Path, required=True)
    parser.add_argument("--tokenized-path", type=Path, required=True)
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--checkpoint-state", type=Path, required=True)
    parser.add_argument("--window", action="append", type=parse_window, required=True)
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    state = json.loads(args.checkpoint_state.read_text())
    checkpoint_step = int(state["step"])
    row_cursor = int(state["global_row_cursor_in_epoch"])
    gas = int(state["gradient_accumulation_steps"])
    local_batch_size = int(state["local_batch_size"])

    epoch_path = args.sampled_path / f"epoch_{args.epoch}"
    inst_start = np.load(epoch_path / "inst_start.npy", mmap_mode="r")
    inst_len = np.load(epoch_path / "inst_len.npy", mmap_mode="r")
    resp_len = np.load(epoch_path / "resp_len.npy", mmap_mode="r")
    lengths = inst_len + resp_len - 1

    windows = {name: (start, end) for name, start, end in args.window}
    first_step = min(start for start, _ in windows.values())
    last_step = max(end for _, end in windows.values())
    if first_step <= checkpoint_step:
        raise SystemExit("all windows must start after the checkpoint step")

    sampler = MultipackDistributedBatchSampler(
        batch_max_length=local_batch_size,
        lengths=lengths,
        num_replicas=8,
        rank=0,
        drop_last_batch=True,
    )
    selected: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for microbatch_index, (_, info) in enumerate(
        sampler.iter_with_info(start_index=row_cursor), start=1
    ):
        optimizer_step = checkpoint_step + (microbatch_index + gas - 1) // gas
        for name, (start, end) in windows.items():
            if start <= optimizer_step <= end:
                selected[name].append((info["global_row_start"], info["global_row_end"]))
        if optimizer_step >= last_step and microbatch_index % gas == 0:
            break

    boundaries, task_names = task_boundaries(args.tokenized_path)
    result: dict[str, object] = {
        "checkpoint_step": checkpoint_step,
        "checkpoint_row_cursor": row_cursor,
        "gradient_accumulation_steps": gas,
        "windows": {},
    }
    baseline_name = next(iter(windows))
    baseline_shares: dict[str, float] = {}

    for name in windows:
        row_ranges = selected[name]
        rows = np.concatenate([np.arange(start, end, dtype=np.int64) for start, end in row_ranges])
        offsets = np.asarray(inst_start[rows], dtype=np.int64)
        task_ids = np.searchsorted(boundaries, offsets, side="right")
        counts = Counter(task_names[int(task_id)] for task_id in task_ids)
        lens = np.asarray(lengths[rows], dtype=np.int64)
        token_counts: Counter[str] = Counter()
        for task_id in np.unique(task_ids):
            mask = task_ids == task_id
            token_counts[task_names[int(task_id)]] = int(lens[mask].sum())
        total_rows = int(rows.size)
        total_tokens = int(lens.sum())
        shares = {task: count / total_rows for task, count in counts.items()}
        if name == baseline_name:
            baseline_shares = shares
        def task_record(task: str, count: int) -> dict[str, object]:
            share = count / total_rows
            base_share = baseline_shares.get(task, 0.0)
            return {
                "task": task,
                "rows": count,
                "row_share": share,
                "tokens": token_counts[task],
                "token_share": token_counts[task] / total_tokens,
                "share_vs_baseline": None if base_share == 0 else share / base_share,
            }

        top_tasks = []
        for task, count in counts.most_common(args.top):
            top_tasks.append(task_record(task, count))
        overrepresented = sorted(
            (task_record(task, count) for task, count in counts.items() if count >= 20),
            key=lambda record: (
                float("inf") if record["share_vs_baseline"] is None else record["share_vs_baseline"],
                record["rows"],
            ),
            reverse=True,
        )[: args.top]

        family_rows: Counter[str] = Counter()
        family_tokens: Counter[str] = Counter()
        for task, count in counts.items():
            family = task.split("__", 1)[0]
            family_rows[family] += count
            family_tokens[family] += token_counts[task]
        result["windows"][name] = {
            "step_start": windows[name][0],
            "step_end": windows[name][1],
            "microbatches": len(row_ranges),
            "rows": total_rows,
            "tokens": total_tokens,
            "length_percentiles": {
                str(p): float(np.percentile(lens, p)) for p in (0, 25, 50, 75, 90, 95, 99, 100)
            },
            "top_tasks": top_tasks,
            "top_overrepresented_tasks": overrepresented,
            "top_families": [
                {
                    "family": family,
                    "rows": count,
                    "row_share": count / total_rows,
                    "tokens": family_tokens[family],
                    "token_share": family_tokens[family] / total_tokens,
                }
                for family, count in family_rows.most_common(args.top)
            ],
        }

    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
