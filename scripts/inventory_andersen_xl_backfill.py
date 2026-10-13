"""Inventory missing Andersen evaluations without changing the live scheduler.

Scope: the main XL lineage's 50K evaluation checkpoints and epoch endpoints
since DFM10 introduced Andersen training. Identity-only branches are excluded.
"""
import argparse
import json
from pathlib import Path


def inventory(root, plan):
    from eval_scheduler.model import Action, read_plan

    records = {}
    # DFM10 ran from the DFM9 endpoint 2127489 through 2482084.
    for step in [*range(2150000, 2450001, 50000), 2482084]:
        export = root / f"exports/dfm10_XL_step{step}_ema_hf"
        metrics = root / f"logs/andersen-xl-backfill/remote/dfm10_XL_epoch9/step_{step}/standard_shards/ARC/merged_metrics.json"
        epoch = json.loads(metrics.read_text()).get("epoch") if metrics.is_file() else None
        records[step] = dict(step=step, dataset="dfm10", export=str(export), epoch=epoch,
                             status="needs holdout and eval")
        result = root / f"logs/andersen-xl-backfill/remote/dfm10_XL_epoch9_dfm/step_{step}/andersen_modernization/merged_metrics.json"
        if result.is_file():
            records[step].update(existing_result=str(result), status="existing historical result")
    for step in [*range(2500000, 2850001, 50000), 2877261]:
        tag = "epoch_10" if step == 2877261 else f"step_{step}"
        export = root / f"exports/dfm11_XL_epoch10_{tag}_ema_hf"
        metrics = root / f"logs/eval/dfm11_XL_epoch10/{tag}/standard_shards/ARC/merged_metrics.json"
        epoch = json.loads(metrics.read_text()).get("epoch") if metrics.is_file() else None
        records[step] = dict(step=step, dataset="dfm11", export=str(export),
                             epoch=epoch, status="needs holdout and eval")
    jobs = read_plan(plan / "plan.tsv")
    for job in jobs:
        m = job.metadata
        step = m.get("eval_step")
        if (job.action != Action.EXPORT_HF or not isinstance(step, int)
                or step < 2900000 or str(job.status) == "skipped"
                or "XL" not in str(m.get("ckpt_path", ""))):
            continue
        records[step] = dict(step=step, checkpoint=m.get("ckpt_tag"),
            export=m.get("hrm_hf_export_dir") or m.get("hf_export_dir"),
            epoch=m.get("eval_epoch"), export_job=job.job_id,
            status="needs holdout and eval", export_status=str(job.status))
    for job in jobs:
        step = job.metadata.get("eval_step")
        if (job.name == "andersen_modernization" and step in records
                and job.action == Action.MERGE_DFM):
            result = root / job.log_dir / "merged_metrics.json"
            if result.is_file():
                records[step]["existing_result"] = str(result)
                records[step]["status"] = "inspect existing result and sync before scheduling"
    for row in records.values():
        export = row.get("export")
        row["export_exists"] = bool(export and (Path(export) / "config.json").is_file())
    return [records[s] for s in sorted(records)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--plan-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = inventory(args.root, args.plan_dir)
    report = dict(scope="main XL lineage, EMA, 50K eval cadence plus epoch endpoints",
        training_introduction="DFM10 after step 2127489",
        holdout=str(args.root / 'evaluation/data/andersen/pairs_chunked_val.jsonl'),
        holdout_available=(args.root / 'evaluation/data/andersen/pairs_chunked_val.jsonl').is_file(),
        expected_rows=119, checkpoints=rows, live_plan_changed=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(checkpoints=len(rows), local_exports=sum(r['export_exists'] for r in rows),
                         output=str(args.output), live_plan_changed=False)))


if __name__ == "__main__":
    main()
