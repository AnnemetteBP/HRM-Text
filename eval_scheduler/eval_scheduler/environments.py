"""Prepare project environments before dispatch, never on the GPU client path."""
from pathlib import Path
import subprocess

from .model import Action, JobStatus


DFM_ACTIONS = frozenset((Action.EVAL_DFM, Action.EVAL_DFM_IFEVAL, Action.EXPORT_DFM_RESULTS))


def sync_project_environments(jobs, plan_dir):
    projects = sorted({str(Path(j.metadata.get('dfm_evals_dir', 'dfm-evals')).resolve())
                       for j in jobs if j.status == JobStatus.PENDING and j.action in DFM_ACTIONS})
    for index, project in enumerate(projects):
        log = Path(plan_dir) / f'environment-sync-{index}.log'
        with log.open('a') as handle:
            # Retain installed optional scoring packages; do not rewrite uv.lock.
            subprocess.run(['uv', 'sync', '--verbose', '--locked', '--inexact', '--project', project],
                           stdout=handle, stderr=subprocess.STDOUT, check=True)


def without_project_sync(argv):
    if (len(argv) >= 2 and Path(argv[0]).name == 'uv' and argv[1] == 'run'
            and '--project' in argv and '--no-sync' not in argv):
        return [*argv[:2], '--no-sync', *argv[2:]]
    return argv
