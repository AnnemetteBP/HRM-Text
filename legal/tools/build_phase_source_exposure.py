#!/usr/bin/env python3
"""Attribute the released Mimir checkpoint's sampled rows to source tasks."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REGISTERS = ROOT / "legal" / "registers"
CHUNK_ROWS = 2_000_000


@dataclass(frozen=True)
class Phase:
    phase_id: str
    recipe: str
    slices: tuple[tuple[int, int | None], ...]


PHASES = (
    Phase("PHASE-001", "dfm6", ((0, None), (1, None), (2, None))),
    Phase("PHASE-002", "dfm7", ((3, None), (4, None))),
    Phase("PHASE-003", "dfm8", ((5, None), (6, 122_594_633))),
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty register: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def task_inventory(recipe: str) -> tuple[list[str], np.ndarray, list[dict[str, object]]]:
    root = ROOT / "data" / f"tokenized_{recipe}"
    names: list[str] = []
    ends: list[int] = []
    manifest: list[dict[str, object]] = []
    cursor = 0
    for task_path in sorted(root.iterdir()):
        if not task_path.is_dir():
            continue
        inst_len = np.load(task_path / "inst_len.npy", mmap_mode="r")
        resp_len = np.load(task_path / "resp_len.npy", mmap_mode="r")
        token_count = int(np.sum(inst_len, dtype=np.int64) + np.sum(resp_len, dtype=np.int64))
        cursor += token_count
        names.append(task_path.name)
        ends.append(cursor)
        link_target = str(task_path.resolve().relative_to(ROOT))
        manifest.append(
            {
                "dataset_recipe": recipe,
                "task_name": task_path.name,
                "source_prefix": task_path.name.split("__", 1)[0],
                "tokenized_target": link_target,
                "rows_before_sampling": len(inst_len),
                "tokens_before_sampling": token_count,
                "inst_len_sha256": sha256(task_path / "inst_len.npy"),
                "resp_len_sha256": sha256(task_path / "resp_len.npy"),
            }
        )
    sampled_tokens = np.load(ROOT / "data" / f"sampled_{recipe}" / "tokens.npy", mmap_mode="r")
    if cursor != sampled_tokens.shape[0]:
        raise RuntimeError(
            f"{recipe}: reconstructed token store length {cursor} != sampled store {sampled_tokens.shape[0]}"
        )
    return names, np.asarray(ends, dtype=np.int64), manifest


def attribute_phase(
    phase: Phase,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    names, task_ends, manifest = task_inventory(phase.recipe)
    task_rows = np.zeros(len(names), dtype=np.int64)
    task_inst = np.zeros(len(names), dtype=np.int64)
    task_resp = np.zeros(len(names), dtype=np.int64)
    sampled_root = ROOT / "data" / f"sampled_{phase.recipe}"

    for epoch, requested_stop in phase.slices:
        epoch_root = sampled_root / f"epoch_{epoch}"
        inst_start = np.load(epoch_root / "inst_start.npy", mmap_mode="r")
        inst_len = np.load(epoch_root / "inst_len.npy", mmap_mode="r")
        resp_len = np.load(epoch_root / "resp_len.npy", mmap_mode="r")
        stop = len(inst_start) if requested_stop is None else requested_stop
        if stop > len(inst_start):
            raise RuntimeError(f"{phase.recipe} epoch {epoch}: stop {stop} exceeds {len(inst_start)} rows")
        for start in range(0, stop, CHUNK_ROWS):
            end = min(stop, start + CHUNK_ROWS)
            task_ids = np.searchsorted(task_ends, np.asarray(inst_start[start:end]), side="right")
            if np.any(task_ids >= len(names)):
                raise RuntimeError(f"{phase.recipe} epoch {epoch}: sampled offset outside task ranges")
            task_rows += np.bincount(task_ids, minlength=len(names))
            task_inst += np.bincount(
                task_ids, weights=np.asarray(inst_len[start:end], dtype=np.float64), minlength=len(names)
            ).astype(np.int64)
            task_resp += np.bincount(
                task_ids, weights=np.asarray(resp_len[start:end], dtype=np.float64), minlength=len(names)
            ).astype(np.int64)

    manifest_by_name = {row["task_name"]: row for row in manifest}
    task_output: list[dict[str, object]] = []
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "rows": 0,
            "instruction_tokens": 0,
            "response_tokens": 0,
            "task_count": 0,
            "tokenized_roots": set(),
        }
    )
    for index, name in enumerate(names):
        if task_rows[index] == 0:
            continue
        prefix = name.split("__", 1)[0]
        target = str(manifest_by_name[name]["tokenized_target"])
        target_root = "/".join(Path(target).parts[:2])
        task_output.append(
            {
                "phase_id": phase.phase_id,
                "dataset_recipe": phase.recipe,
                "task_name": name,
                "source_prefix": prefix,
                "tokenized_target": target,
                "sampled_rows_consumed": int(task_rows[index]),
                "instruction_tokens_consumed": int(task_inst[index]),
                "response_tokens_consumed": int(task_resp[index]),
                "source_tokens_consumed": int(task_inst[index] + task_resp[index]),
            }
        )
        group = grouped[prefix]
        group["rows"] = int(group["rows"]) + int(task_rows[index])
        group["instruction_tokens"] = int(group["instruction_tokens"]) + int(task_inst[index])
        group["response_tokens"] = int(group["response_tokens"]) + int(task_resp[index])
        group["task_count"] = int(group["task_count"]) + 1
        group["tokenized_roots"].add(target_root)  # type: ignore[union-attr]

    source_output: list[dict[str, object]] = []
    for prefix, values in sorted(grouped.items()):
        source_output.append(
            {
                "phase_id": phase.phase_id,
                "dataset_recipe": phase.recipe,
                "source_prefix": prefix,
                "sampled_rows_consumed": values["rows"],
                "instruction_tokens_consumed": values["instruction_tokens"],
                "response_tokens_consumed": values["response_tokens"],
                "source_tokens_consumed": int(values["instruction_tokens"]) + int(values["response_tokens"]),
                "task_count": values["task_count"],
                "tokenized_roots": ";".join(sorted(values["tokenized_roots"])),  # type: ignore[arg-type]
            }
        )
    return task_output, source_output, manifest


def main() -> None:
    all_tasks: list[dict[str, object]] = []
    all_sources: list[dict[str, object]] = []
    all_manifest: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for phase in PHASES:
        tasks, sources, manifest = attribute_phase(phase)
        all_tasks.extend(tasks)
        all_sources.extend(sources)
        all_manifest.extend({"phase_id": phase.phase_id, **row} for row in manifest)
        summaries.append(
            {
                "phase_id": phase.phase_id,
                "dataset_recipe": phase.recipe,
                "index_slices": ";".join(
                    f"epoch_{epoch}[0:{stop if stop is not None else 'end'}]" for epoch, stop in phase.slices
                ),
                "source_prefixes_consumed": len(sources),
                "tasks_consumed": len(tasks),
                "sampled_rows_consumed": sum(int(row["sampled_rows_consumed"]) for row in sources),
                "source_tokens_consumed": sum(int(row["source_tokens_consumed"]) for row in sources),
            }
        )
        print(json.dumps(summaries[-1], sort_keys=True))

    write_csv(REGISTERS / "phase-task-exposure-register.csv", all_tasks)
    write_csv(REGISTERS / "phase-source-exposure-register.csv", all_sources)
    write_csv(REGISTERS / "phase-tokenized-source-manifest.csv", all_manifest)
    write_csv(REGISTERS / "phase-exposure-summary.csv", summaries)


if __name__ == "__main__":
    main()
