"""Add missing accepted-v2 DaLA/GEC coverage to the live XXL-wide SQLite plan."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'eval_scheduler'))
sys.path.insert(0, str(ROOT))
from dfm12.io import load, write_json
from eval_scheduler.database_cli import validate_graph
from eval_scheduler.model import Action, JobStatus, plan_database
from eval_scheduler.plan import split_euroeval_postprocessing
from eval_scheduler.store import SQLiteJobStore
from scripts.schedule_identity_final_ema_full import canonical_log_dir


def extend(jobs, tasks):
    additions, changed = [], {}
    steps = sorted({int(j.metadata['dfm14_boundary']) for j in jobs
                    if j.job_id.startswith('xxlw-dfm14-') and j.action == Action.EXPORT_HF
                    and int(j.metadata.get('dfm14_boundary', 0)) >= 950000})
    for step in steps:
        prefix = f'xxlw-dfm14-{step}-'
        block = [j for j in jobs if j.job_id.startswith(prefix)]
        export = next(j for j in block if j.action == Action.EXPORT_HF)
        existing = {j.name for j in block if j.action == Action.EVAL_DFM}
        writers = []
        for task in tasks:
            if task['name'] in existing:
                continue
            family = 'gec_dala_ga' if task['name'].startswith('gec_') else 'dala_ga'
            seed = next(j for j in block if j.action == Action.EVAL_DFM and j.name == family)
            merge = next(j for j in block if j.action == Action.MERGE_DFM and j.name == family)
            metadata = {k:v for k,v in seed.metadata.items() if k != 'defer_dfm_export'}
            metadata.update(dfm_suite=task['suite'], dfm_single_tasks_config=task['config'],
                            language=task['language'], dfm_max_gen_toks=task['max_tokens'],
                            all50_coverage=True)
            ids = []
            for shard in range(4):
                job = seed.with_updates(job_id=prefix+task['name']+f'-{shard}',
                    name=task['name'], shard=shard, shards=4, status=JobStatus.PENDING,
                    attempt=0, metadata=metadata, deps=seed.deps)
                job = job.with_updates(log_dir=str(canonical_log_dir(job)))
                additions.append(job)
                ids.append(job.job_id)
            job = merge.with_updates(job_id=prefix+task['name']+'-merge', name=task['name'],
                status=JobStatus.PENDING, attempt=0, deps=tuple(ids),
                metadata={**metadata, 'shards':4})
            additions.append(job.with_updates(log_dir=str(canonical_log_dir(job))))
            writers.append(job.job_id)
        if not writers:
            continue
        average = next(j for j in block if j.metadata.get('multilingual_manifest')
                       and j.action == Action.AVERAGE)
        if average.status != JobStatus.PENDING:
            raise ValueError('Multilingual average already started: '+average.job_id)
        changed[average.job_id] = average.with_updates(deps=(*average.deps, *writers))
        # Terminal dependency semantics retain resume after exhausted failures.
        for job in block:
            if job.action == Action.TERMINAL_BARRIER and job.status == JobStatus.PENDING:
                changed[job.job_id] = job.with_updates(deps=tuple(dict.fromkeys(
                    (*job.deps, *writers, average.job_id))))
    result = [changed.get(j.job_id,j) for j in jobs] + split_euroeval_postprocessing(additions)
    validate_graph(result)
    for step in steps:
        prefix = f'xxlw-dfm14-{step}-'
        languages = {j.metadata.get('language') for j in result if j.job_id.startswith(prefix)
                     and j.action == Action.EVAL_DFM and j.metadata.get('language')}
        if len(languages) != 50:
            raise ValueError(f'{step}: only {len(languages)} explicitly covered languages')
    return result


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--plan-dir', type=Path, required=True)
    args = parser.parse_args()
    store = SQLiteJobStore(plan_database(args.plan_dir/'plan.tsv'))
    if not store.get_admin_lock():
        raise RuntimeError('Lock database claims before extending')
    ready = load(ROOT/'data/dfm14/evaluation/all50/ready.json')
    if not ready['exact_original_selections'] or ready['languages'] != 34:
        raise ValueError('Heldout verification incomplete')
    before = store.load_jobs()
    after = extend(before, ready['tasks'])
    # Validate every added executable row before the atomic preserving import.
    from eval_scheduler.database_runner import DatabaseRunner
    from eval_scheduler.shared_pool import SharedServerPool
    pool = SharedServerPool(args.plan_dir, list(range(8)))
    runner = DatabaseRunner(args.plan_dir, store, list(range(8)), pool)
    existing = {j.job_id for j in before}
    for job in after:
        if job.job_id not in existing:
            runner._validate(job)
    store.backup(args.plan_dir/'state.before-all50.sqlite')
    store.import_jobs(after, preserve_runtime=True, require_admin_lock=True)
    store.backup(args.plan_dir/'state.backup.sqlite')
    receipt = dict(added_rows=len(after)-len(before), languages=50, tasks_per_language=2,
                   shards_per_task=4, samples_per_task=2000, preserved_runtime=True)
    write_json(args.plan_dir/'all50-extension.json', receipt)
    store.set_admin_lock(False)
    print(receipt)


if __name__ == '__main__':
    main()
