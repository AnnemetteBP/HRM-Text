"""Fill epoch-10 evaluation coverage before the production 3600K evaluation.

Reuses checkpoint-bound historical summaries, never inference from another model.
The SQLite authority is edited transactionally while current training continues.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from eval_scheduler.database_cli import validate_graph
from eval_scheduler.model import Action, Job, JobStatus, plan_database, read_plan, write_plan
from eval_scheduler.store import SQLiteJobStore

ROOT = Path(__file__).resolve().parents[1]
STEP = 2877261
PREFIX = "epoch10-comparable-"
TRAIN = "dfm14-xl-step_3600000-train"
TEMPLATE = "dfm14-xl-step_3600000"
PYTHON = "/home/ucloud/miniforge3/envs/hrm/bin/python"


def prepare(jobs, plan, output):
    by = {j.job_id: j for j in jobs}
    assert by[TRAIN].status in (JobStatus.RUNNING, JobStatus.PENDING)
    assert not any(j.job_id.startswith(PREFIX) for j in jobs), "Already installed"
    state = ROOT / "checkpoints/dfm11/XL-from-dfm10-epoch9/checkpoint_state_epoch_10.json"
    checkpoint = json.loads(state.read_text())
    assert (checkpoint['step'], checkpoint['epoch']) == (STEP, 10)
    export = ROOT / "exports/dfm11_XL_epoch10_multilingual_ema_hf"
    assert (export / 'model.safetensors').is_file()
    old_plan = ROOT / 'logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725/plan.tsv'
    old = read_plan(old_plan)
    history = [j for j in [*old, *jobs] if j.status == JobStatus.DONE
               and j.metadata.get('ckpt_tag') == 'epoch_10'
               and j.metadata.get('eval_epoch') == 10
               and j.metadata.get('no_ema') is False]
    candidates = {}
    for j in history:
        if j.family in ('dfm', 'euroeval', 'standard', 'dfm_ifeval'):
            candidates.setdefault((j.family, j.name), []).append(j)
    templates = [j for j in jobs if j.job_id.startswith(TEMPLATE + '-')
                 and j.status == JobStatus.PENDING
                 and j.action not in (Action.TRAIN_UNTIL_STEP, Action.WAIT_CHECKPOINT,
                                      Action.EXPORT_HF, Action.REPORT,
                                      Action.TERMINAL_BARRIER, Action.TEARDOWN_EVAL)]
    infer = [j for j in templates if j.action.value.startswith('eval_')]
    groups = {(j.family, j.name) for j in infer}
    roots = {k: output / k for k in ('standard', 'dfm', 'euroeval')}
    reuse, copies = {}, []
    for family, name in sorted(groups):
        paths = []
        for j in candidates.get((family, name), []):
            if family == 'standard':
                paths.append(Path(j.metadata['log_root']) / 'standard_shards' / name / 'merged_metrics.json')
            elif family == 'dfm':
                paths.append(Path(j.metadata['dfm_log_root']) / name / 'merged_metrics.json')
            elif family == 'dfm_ifeval':
                paths.append(Path(j.metadata['dfm_log_root']) / 'merged_ifeval_da_metrics.json')
            else:
                paths.append(Path(j.log_dir) / 'merged_metrics.json')
        valid = []
        for p in dict.fromkeys(paths):
            if not p.is_file():
                continue
            doc = json.loads(p.read_text())
            metrics = doc.get('metrics', doc)
            if not metrics:
                continue
            stamps = [v for k, v in metrics.items() if k.endswith('/epoch')]
            if doc.get('epoch', 10) != 10 or any(v != 10 for v in stamps):
                continue
            # Old core EuroEval wrote zero as its train step. Its completed
            # epoch-10 job/export and checkpoint state supply the real binding.
            steps = [v for k, v in metrics.items() if k.endswith('/train_step')]
            if any(v not in (0, STEP) for v in steps):
                continue
            if name == 'generative_talemaader' and not any('model_graded_fact_v2' in k for k in metrics):
                v2 = p.with_name('merged_metrics_v2.json')
                if not v2.is_file():
                    continue
                doc = json.loads(v2.read_text()); p = v2
                metrics = doc.get('metrics', doc)
                if not any('model_graded_fact_v2' in k for k in metrics):
                    continue
            valid.append((p, doc))
        if not valid:
            continue
        p, doc = valid[-1]
        metrics = doc.get('metrics', doc)
        if family == 'euroeval':
            metrics['euroeval/train_step'] = STEP
            dest = roots['euroeval'] / 'epoch_10' / name / 'merged_metrics.json'
        elif family == 'standard':
            dest = roots['standard'] / 'standard_shards' / name / 'merged_metrics.json'
        elif family == 'dfm_ifeval':
            dest = roots['dfm'] / 'merged_ifeval_da_metrics.json'
        else:
            dest = roots['dfm'] / name / 'merged_metrics.json'
        reuse[family, name] = p
        copies.append((dest, doc, dict(source=str(p.resolve()), destination=str(dest),
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(), family=family, name=name)))

    allowed = []
    for j in templates:
        if (j.family, j.name) in reuse and j.action != Action.AVERAGE:
            continue
        # The current expanded headline supersedes this historical wrapper.
        if j.metadata.get('todo5_talemaader_future'):
            continue
        allowed.append(j)
    ids = {j.job_id: PREFIX + str(i).zfill(4) for i, j in enumerate(allowed)}
    clones = []
    for j in allowed:
        m = dict(j.metadata)
        for k in ('command', 'dfm13_cursor_epoch_pending', 'dfm14_cursor_epoch_pending',
                  'source_pins', 'legacy_template_job_id'):
            m.pop(k, None)
        m.update(ckpt_path=str(state.parent), ckpt_tag='epoch_10', checkpoint_tag='epoch_10',
                 eval_step=STEP, eval_epoch=10.0, xl_boundary=STEP,
                 model_prefix='hrm-dfm11-XL-epoch10', no_ema=False,
                 hf_export_dir=str(export), hrm_hf_export_dir=str(export),
                 standard_hf_export_dir=str(export), log_root=str(roots['standard']),
                 dfm_log_root=str(roots['dfm']), euroeval_log_root=str(roots['euroeval']),
                 python_bin=PYTHON, fix_mistral_regex=False, plan_dir=str(plan))
        m['additional_standard_roots'] = [str(roots['standard'])]
        m['additional_dfm_roots'] = []
        m['additional_euroeval_roots'] = []
        m.pop('expanded_roots', None)
        m['backfill_template_job'] = j.job_id
        if j.action == Action.AVERAGE:
            log_dir = output / 'averages' / ids[j.job_id]
        else:
            key = 'euroeval_log_root' if j.family == 'euroeval' else ('log_root' if j.family == 'standard' else 'dfm_log_root')
            original = Path(j.metadata[key]).resolve()
            relative = Path(j.log_dir).resolve().relative_to(original)
            log_dir = Path(m[key]) / str(relative).replace('step_3600000', 'epoch_10')
        deps = tuple(dict.fromkeys([TRAIN, *(ids[d] for d in j.deps if d in ids)]))
        clones.append(j.with_updates(job_id=ids[j.job_id], deps=deps, status=JobStatus.PENDING,
                                     attempt=0, metadata=m, log_dir=str(log_dir)))
    # Every average sees all missing tasks and publication jobs, not just the
    # subset used by its former 3600K template dependency graph.
    publications = [j.job_id for j in clones if j.action not in
                    (Action.AVERAGE, Action.TERMINAL_BARRIER, Action.TEARDOWN_EVAL)]
    clones = [j.with_updates(deps=tuple(dict.fromkeys((*j.deps, *publications))))
              if j.action == Action.AVERAGE else j for j in clones]
    finish = Job(job_id=PREFIX+'complete', action=Action.TERMINAL_BARRIER,
                 family='control', name='epoch10-comparable-complete',
                 deps=tuple(j.job_id for j in clones), deps_mode='terminal',
                 log_dir=str(output/'complete'), metadata={'eval_step': STEP, 'eval_epoch': 10.0})
    updated = []
    for j in jobs:
        if j.job_id.startswith(TEMPLATE + '-') and j.action == Action.EXPORT_HF:
            assert j.status == JobStatus.PENDING
            j = j.with_updates(deps=tuple(dict.fromkeys((*j.deps, finish.job_id))))
        updated.append(j)
    result = updated + clones + [finish]
    validate_graph(result)
    receipt = dict(reused=[c[2] for c in copies], missing=sorted([list(g) for g in groups-reuse.keys()]),
                   added=Counter(str(j.action) for j in clones), jobs=len(clones)+1,
                   epoch=10, step=STEP, ema=True, training_gate=TRAIN,
                   checkpoint_state_sha256=hashlib.sha256(state.read_bytes()).hexdigest())
    return result, copies, receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    plan, output = args.plan_dir.resolve(), args.output.resolve()
    store = SQLiteJobStore(plan_database(plan/'plan.tsv'))
    if args.apply:
        assert not store.get_admin_lock(), 'Existing admin lock'
        store.set_admin_lock(True)
    try:
        jobs, copies, receipt = prepare(store.load_jobs(), plan, output)
        output.mkdir(parents=True, exist_ok=True)
        write_plan(output/'preview.tsv', jobs)
        if args.apply:
            store.backup(output/'before.sqlite')
            for dest, doc, _ in copies:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(doc, indent=2)+'\n')
            store.import_jobs(jobs, preserve_runtime=True, require_admin_lock=True)
            store.backup(plan/'state.backup.sqlite')
        receipt['applied'] = args.apply
        (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps({**receipt, 'reused':len(receipt['reused']),
                          'missing':len(receipt['missing'])}, indent=2))
    finally:
        if args.apply:
            store.set_admin_lock(False)


if __name__ == '__main__':
    main()
