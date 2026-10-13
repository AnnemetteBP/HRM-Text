"""XXS scheduler handoff and injected restore-failure integration test. No W&B."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .protocol import atomic_write
from .smoke import make_data, assert_state_equal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--gpus', default='1,2')
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(exist_ok=False)
    make_data(root / 'data')
    os.environ.update(CUDA_VISIBLE_DEVICES=args.gpus, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                      WANDB_MODE='disabled', WANDB_DISABLED='true')
    base = [sys.executable, '-m', 'torch.distributed.run', '--standalone', '--nproc_per_node=2',
            'pretrain.py', 'arch/size@arch=XXS', f'data.path={root / "data"}', 'epochs=1',
            'global_batch_size=256', 'gradient_accumulation_steps=2', 'distributed_strategy=fsdp',
            'fsdp_reshard_after_forward=false', 'fsdp_accumulation_sync_mode=no_sync',
            'max_steps=6', 'training_total_steps=6', 'checkpoint_step_interval=2',
            'checkpoint_format=sharded', 'log_interval=1', 'lr=1e-4', 'lr_warmup_steps=0',
            'arch.bp_warmup_ratio=0', 'arch.bp_max_steps=5', 'compile_train_batch=true',
            'run_name=suspend-boundary-smoke', 'dataloader_prefetch_factor=1']
    ckpt = root / 'baseline'
    with (root / 'baseline.log').open('w') as log:
        subprocess.run(base + [f'checkpoint_path={ckpt}'], check=True,
                       stdout=log, stderr=subprocess.STDOUT, timeout=300)
    from eval_scheduler.model import Job, Action
    from eval_scheduler.cooperative_training import run_boundary
    from training_suspend.protocol import read_json
    settings = read_json(args.settings)
    os.environ['CUDA_CHECKPOINT_REAL'] = settings['cuda_checkpoint']
    reports = {}
    for mode in ('normal', 'failed_restore'):
        target = root / mode
        target.mkdir()
        checkpoint = target / 'checkpoints'
        shutil.copytree(ckpt, checkpoint, ignore=shutil.ignore_patterns('*step_4*', '*step_6*'))
        control = target / 'control'
        local = dict(settings, min_free_mib=8192, allow_existing_peers=True)
        if mode == 'failed_restore':
            local['cuda_checkpoint'] = str(Path('tests/fixtures/cuda_checkpoint_fail_restore.sh').resolve())
        config = target / 'settings.json'
        atomic_write(config, local)
        co = dict(control_root=str(control), python=sys.executable,
                  cuda_checkpoint=local['cuda_checkpoint'], launcher_settings=str(config),
                  side_smoke=True, command=base + [f'checkpoint_path={checkpoint}', 'suspend_after_steps=[4]'])
        metadata = dict(ckpt_path=str(checkpoint), ckpt_tag='step_4', stop_after_step=4,
                        resume_from_tag='step_2', workdir=str(Path.cwd()), cooperative_training=co)
        job = Job('smoke-4', Action.TRAIN_UNTIL_STEP, 'training', 'boundary',
                  metadata=metadata, log_dir=str(target))
        assert run_boundary(job, tuple(map(int, args.gpus.split(',')))) == 0
        second = job.with_updates(job_id='smoke-6', metadata={**metadata, 'ckpt_tag':'step_6',
             'stop_after_step':6, 'resume_from_tag':'step_4',
             'cooperative_training':{**co, 'final_boundary':True}})
        assert run_boundary(second, tuple(map(int, args.gpus.split(',')))) == 0
        fallbacks = list(control.glob('attempt-*/*/generation_*/disk_fallback.json'))
        assert bool(fallbacks) == (mode == 'failed_restore')
        import torch
        from torch.distributed.checkpoint.format_utils import dcp_to_torch_save
        expected = root / 'baseline_step6.pt'
        if not expected.exists():
            dcp_to_torch_save(ckpt / 'fsdp2_step_6', expected)
        actual = target / 'step6.pt'
        dcp_to_torch_save(checkpoint / 'fsdp2_step_6', actual)
        assert_state_equal(torch.load(expected, weights_only=False), torch.load(actual, weights_only=False))
        reports[mode] = dict(complete=True, fallbacks=len(fallbacks),
                            parity='exact model and optimizer/EMA state',
                            checkpoint=str(checkpoint / 'checkpoint_state_step_6.json'))
        atomic_write(root / 'result.json', reports)
        print(json.dumps(reports[mode]), flush=True)


if __name__ == '__main__':
    main()
