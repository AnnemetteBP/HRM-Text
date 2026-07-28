#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval_scheduler.eval_scheduler.locking import PlanLock
from eval_scheduler.eval_scheduler.model import JobStatus, read_plan, write_plan


def replace_text(value: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        value = value.replace(old, new)
    return value


def replace_value(value: object, replacements: list[tuple[str, str]]) -> object:
    if isinstance(value, str):
        return replace_text(value, replacements)
    if isinstance(value, list):
        return [replace_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: replace_value(item, replacements)
            for key, item in value.items()
        }
    return value


def parse_replacement(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("replacement must be OLD=NEW")
    return tuple(value.split("=", 1))  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clone one checkpoint's rows into an isolated eval plan."
    )
    parser.add_argument("--source-plan-dir", type=Path, required=True)
    parser.add_argument("--dest-plan-dir", type=Path, required=True)
    parser.add_argument("--checkpoint-tag", required=True)
    parser.add_argument(
        "--replace",
        action="append",
        default=[],
        type=parse_replacement,
        metavar="OLD=NEW",
    )
    parser.add_argument(
        "--disable-wandb",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    args = parser.parse_args()

    source_plan = args.source_plan_dir / "plan.tsv"
    with PlanLock(args.source_plan_dir, exclusive=False):
        jobs = read_plan(source_plan)
    selected = [
        job
        for job in jobs
        if str(job.metadata.get("ckpt_tag", "")) == args.checkpoint_tag
    ]
    if not selected:
        raise SystemExit(f"No rows found for checkpoint {args.checkpoint_tag}")

    selected_ids = {job.job_id for job in selected}
    missing_deps = {
        dep
        for job in selected
        for dep in job.deps
        if dep not in selected_ids
    }
    if missing_deps:
        raise SystemExit(
            "Selected checkpoint has dependencies outside its row set: "
            + ", ".join(sorted(missing_deps))
        )

    replacements = [
        (str(args.source_plan_dir), str(args.dest_plan_dir)),
        *args.replace,
    ]
    cloned = []
    for job in selected:
        metadata = replace_value(job.metadata, replacements)
        assert isinstance(metadata, dict)
        if args.disable_wandb:
            metadata["log_wandb"] = False
        status = (
            JobStatus.SKIPPED
            if job.status == JobStatus.SKIPPED
            else JobStatus.PENDING
        )
        cloned.append(
            job.with_updates(
                status=status,
                attempt=0,
                log_dir=replace_text(job.log_dir, replacements),
                metadata=metadata,
            )
        )

    args.dest_plan_dir.mkdir(parents=True, exist_ok=False)
    with PlanLock(args.dest_plan_dir, exclusive=True):
        write_plan(args.dest_plan_dir / "plan.tsv", cloned)
    print(f"destination={args.dest_plan_dir}")
    print(f"checkpoint={args.checkpoint_tag}")
    print(f"rows={len(cloned)}")
    print(f"wandb_disabled={args.disable_wandb}")


if __name__ == "__main__":
    main()
