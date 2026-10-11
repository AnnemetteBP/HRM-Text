"""Prepare/apply missing main-line XL Andersen jobs to the existing SQLite plan."""
import argparse
import hashlib
import json
from pathlib import Path

from eval_scheduler.model import Action, JobStatus, plan_database, write_plan
from eval_scheduler.store import SQLiteJobStore
from scripts.inventory_andersen_xl_backfill import inventory
from scripts.prepare_dfm10_andersen import EXPECTED_SHA256


def prepare(jobs, records, root, plan, after_training):
    by = {j.job_id: j for j in jobs}
    gate = by[after_training]
    assert gate.action == Action.TRAIN_UNTIL_STEP
    template = next(j for j in jobs if j.name == 'andersen_modernization'
                    and j.action == Action.EVAL_DFM)
    merge_template = next(j for j in jobs if j.name == template.name and j.action == Action.MERGE_DFM)
    additions = []
    merges = []
    for row in records:
        if row.get('existing_result'):
            continue
        step = row['step']
        key = f'andersen-xl-{step}'
        if key + '-eval' in by:
            continue
        if row.get('export_status') != 'pending':
            assert row['export_exists'], row
            assert row.get('epoch') is not None, row
        source = by[row['export_job']] if row.get('export_job') else template
        meta = {**template.metadata, **source.metadata}
        for field in ('skip_reason', 'command', 'defer_dfm_export', 'defer_euroeval_merge'):
            meta.pop(field, None)
        tag = row.get('checkpoint') or ('epoch_10' if step == 2877261 else f'step_{step}')
        log_root = root / f'logs/dfm_evals/andersen_xl_backfill/step_{step}'
        meta.update(eval_step=step, eval_epoch=row.get('epoch'), ckpt_tag=tag,
            checkpoint_tag=tag, hrm_hf_export_dir=row['export'], standard_hf_export_dir=row['export'],
            hf_export_dir=row['export'], dfm_log_root=str(log_root), no_ema=False,
            fix_mistral_regex=False, log_wandb=True, shards=1,
            plan_dir=str(plan), dfm_single_tasks_config=str(root/'config/dfm_evals_hrm_single_tasks.yaml'))
        meta['xl_boundary'] = step
        if not row.get('export_job'):
            meta['ckpt_path'] = str(root/'checkpoints/dfm11/XL-from-dfm10-epoch9')
            meta['model_prefix'] = 'hrm-dfm11-XL'
        # Match the current direct native-template server configuration, without eager.
        meta['vllm_extra_args'] = meta.get('vllm_extra_args', '').replace('--enforce-eager', '').strip()
        deps = (row['export_job'],) if row.get('export_job') else ()
        if step <= int(gate.metadata['stop_after_step']):
            deps = tuple(dict.fromkeys((*deps, after_training)))
        inference = template.with_updates(job_id=key+'-eval', deps=deps, status=JobStatus.PENDING,
            attempt=0, initial_batch=32, shard=0, shards=1,
            log_dir=str(log_root/template.name/'shard_0_of_1'/tag), metadata=meta)
        merge = merge_template.with_updates(job_id=key+'-merge', deps=(inference.job_id,),
            status=JobStatus.PENDING, attempt=0, log_dir=str(log_root/template.name), metadata=dict(meta))
        additions.extend((inference, merge))
        merges.append((step, merge.job_id))
    result = []
    # Existing terminal barriers allow exhausted eval failures without blocking training.
    for job in jobs:
        if job.action == Action.TERMINAL_BARRIER and job.job_id.endswith('-train-evals-terminal'):
            next_training = by.get(job.job_id.removesuffix('-evals-terminal'))
            if next_training and next_training.status == JobStatus.PENDING:
                before = [j for j in jobs if j.action == Action.TRAIN_UNTIL_STEP
                          and j.job_id in next_training.deps]
                lower = max((int(j.metadata.get('eval_step', 0)) for j in before), default=0)
                selected = [key for step, key in merges if step <= lower and
                            (lower == int(gate.metadata['eval_step']) or step > lower-50000)]
                if selected:
                    job = job.with_updates(deps=tuple(dict.fromkeys((*job.deps, *selected))))
        result.append(job)
    return result + additions, additions


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan-dir', type=Path, required=True)
    p.add_argument('--after-training', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    holdout = root/'evaluation/data/andersen/pairs_chunked_val.jsonl'
    assert hashlib.sha256(holdout.read_bytes()).hexdigest() == EXPECTED_SHA256['validation']
    plan = args.plan_dir.resolve()
    store = SQLiteJobStore(plan_database(plan/'plan.tsv'))
    if args.apply:
        if store.get_admin_lock():
            raise RuntimeError('Existing administrative lock; do not override it')
        store.set_admin_lock(True)
    try:
        rows = inventory(root, plan)
        jobs, added = prepare(store.load_jobs(), rows, root, plan, args.after_training)
        args.output.mkdir(parents=True, exist_ok=True)
        write_plan(args.output/'preview.tsv', jobs)
        if args.apply:
            store.backup(args.output/'before.sqlite')
            store.import_jobs(jobs, preserve_runtime=True, require_admin_lock=True)
            store.backup(plan/'state.backup.sqlite')
        receipt = dict(added_jobs=[j.job_id for j in added], applied=args.apply,
                       holdout_sha256=EXPECTED_SHA256['validation'])
        (args.output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(receipt))
    finally:
        if args.apply:
            store.set_admin_lock(False)


if __name__ == '__main__':
    main()
