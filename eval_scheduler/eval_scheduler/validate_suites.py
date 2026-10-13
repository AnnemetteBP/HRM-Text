"""Isolated production-client score/timing comparison. Never syncs to W&B."""
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import zipfile

import typer

from .model import Action, JobStatus, read_plan, write_plan
from .runtime import Runner, gpu_snapshot, vllm_model_path
from .database_runner import DatabaseRunner
from .shared_pool import SharedServerPool
from .store import SQLiteJobStore


SUPPORTED = {Action.EVAL_STANDARD, Action.EVAL_DFM, Action.EVAL_EUROEVAL}


def clone_job(source, directory, index):
    if source.action not in SUPPORTED:
        raise ValueError('Only inference jobs are allowed, never sync or training')
    metadata = dict(source.metadata)
    metadata.update(log_wandb=False, defer_dfm_export=False, defer_euroeval_merge=False,
                    plan_dir=str(directory), min_gpu_free_mib=0)
    for field in ('log_root', 'dfm_log_root', 'euroeval_log_root'):
        metadata[field] = str(directory / field)
    for field in list(metadata):
        if field.startswith('wandb_'):
            del metadata[field]
    return source.with_updates(job_id=f'canary-{index}', deps=(), status=JobStatus.PENDING,
        attempt=0, max_retries=0, log_dir=str(directory / f'task-{index}'), metadata=metadata)


def scores(job):
    root = Path(job.log_dir)
    if job.action == Action.EVAL_STANDARD:
        from scripts.merge_standard_eval_shards import parse_metrics
        return parse_metrics(root / f'{job.name}_shard_{job.shard or 0}_of_{job.shards or 1}.log', job.name)
    if job.action == Action.EVAL_DFM:
        archives = list((root / 'inspect').glob('*.eval'))
        if len(archives) != 1:
            raise ValueError(f'Expected exactly one Inspect archive: {archives}')
        with zipfile.ZipFile(archives[0]) as archive:
            header = json.loads(archive.read('header.json'))
        if header['status'] != 'success':
            raise ValueError('Inspect evaluation did not succeed')
        results = header['results']
        result = {k: results[k] for k in ('total_samples', 'completed_samples')}
        for score in results['scores']:
            for name, metric in score['metrics'].items():
                result[f'{score["name"]}/{name}'] = metric['value']
            result[f'{score["name"]}/scored_samples'] = score['scored_samples']
        return result
    result = json.loads((root / 'merged_metrics.json').read_text())
    return {k: v for k, v in result.items() if isinstance(v, (float, int))
            and not k.endswith(('/epoch', '/step'))}


def compare(left, right):
    if not left or not right:
        raise ValueError('Empty score artifacts are not parity')
    return {key: {'legacy': left.get(key), 'shared': right.get(key)}
            for key in left.keys() | right.keys() if left.get(key) != right.get(key)}


def main(plan: Path, output: Path, job_id: list[str] = typer.Option(...),
         gpus: str = '0,1,2', shared_first: bool = False, resume: bool = False,
         reference_legacy: Path | None = None):
    if output.exists() and not resume:
        raise ValueError('Use a new directory; production results must not be overwritten')
    gpu_ids = [int(x) for x in gpus.split(',')]
    if len(set(gpu_ids)) != len(gpu_ids) or not gpu_ids:
        raise ValueError('Unique GPU IDs required')
    by_id = {j.job_id: j for j in read_plan(plan)}
    sources = [by_id[key] for key in job_id]
    for source in sources:
        if source.action not in SUPPORTED or source.status != JobStatus.DONE:
            raise ValueError('Choose completed inference rows')
        if not (Path(vllm_model_path(source)) / 'config.json').is_file():
            raise ValueError('Missing local export')
    for gpu in gpu_ids:
        free, _, total = gpu_snapshot(gpu)
        if float(free) < .98 * float(total):
            raise RuntimeError(f'GPU {gpu} is not idle; refusing to disturb other work')
    output.mkdir(parents=True, exist_ok=resume)
    os.environ['WANDB_MODE'] = 'disabled'
    report = {'source_jobs': [j.to_row() for j in sources], 'gpus': gpu_ids,
              'passed': False, 'modes': {}, 'note': 'Representative tasks, not a full benchmark campaign; exact score gate.'}
    if resume:
        saved = json.loads((output / 'result.json').read_text())
        if saved['source_jobs'] != report['source_jobs'] or saved['gpus'] != gpu_ids:
            raise ValueError('Resume must use identical source definitions and GPUs')
        report = saved
        report.pop('error', None)
    if reference_legacy:
        saved = json.loads(reference_legacy.read_text())
        if saved['source_jobs'] != report['source_jobs'] or saved['gpus'] != gpu_ids:
            raise ValueError('Reference must have identical source jobs and GPUs')
        legacy = saved['modes']['legacy']
        if not legacy['jobs'] or any(j['status'] != 'done' for j in legacy['jobs']):
            raise ValueError('Legacy reference did not complete')
        report['modes']['legacy'] = {**legacy, 'artifact_dir': str(reference_legacy.parent / 'legacy')}
        report['reference_legacy'] = str(reference_legacy)
    try:
        for mode in (('shared', 'legacy') if shared_first else ('legacy', 'shared')):
            directory = output / mode
            jobs = [clone_job(j, directory, i) for i, j in enumerate(sources)]
            if mode in report['modes'] and all(j['status'] == 'done' for j in report['modes'][mode]['jobs']):
                artifact_dir = Path(report['modes'][mode].get('artifact_dir', directory))
                report['modes'][mode]['scores'] = [scores(clone_job(j, artifact_dir, i)) for i, j in enumerate(sources)]
                continue
            directory.mkdir()
            write_plan(directory / 'plan.tsv', jobs)
            start = time.monotonic()
            if mode == 'legacy':
                runner = Runner(directory, gpu_ids, persistent_vllm=True)
                runner.run()
                final = read_plan(directory / 'plan.tsv')
            else:
                with tempfile.TemporaryDirectory(prefix='suite-parity-db-') as local:
                    store = SQLiteJobStore(Path(local) / 'jobs.sqlite')
                    store.import_jobs(jobs)
                    event_lock = threading.Lock()
                    def event(message):
                        with event_lock, (directory / 'events.log').open('a') as handle:
                            handle.write(f'{time.time():.3f} {message}\n')
                    pool = SharedServerPool(directory, gpu_ids, event=event)
                    try:
                        DatabaseRunner(directory, store, gpu_ids, pool, event=event).run()
                        final = store.load_jobs()
                        store.export_tsv(directory / 'final.tsv')
                    finally:
                        pool.shutdown()
            report['modes'][mode] = {'wall_seconds': time.monotonic() - start, 'artifact_dir': str(directory),
                'jobs': [j.to_row() for j in final]}
            if any(j.status != JobStatus.DONE for j in final):
                raise RuntimeError(f'{mode} has incomplete/failed jobs; inspect isolated logs')
            report['modes'][mode]['scores'] = [scores(j) for j in jobs]
            (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        report['differences'] = [compare(a, b) for a, b in zip(
            report['modes']['legacy']['scores'], report['modes']['shared']['scores'])]
        report['passed'] = not any(report['differences'])
    except BaseException as exc:
        report['error'] = repr(exc)
        raise
    finally:
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    typer.echo(str(output / 'result.json'))
    if not report['passed']:
        raise typer.Exit(1)


if __name__ == '__main__':
    typer.run(main)
