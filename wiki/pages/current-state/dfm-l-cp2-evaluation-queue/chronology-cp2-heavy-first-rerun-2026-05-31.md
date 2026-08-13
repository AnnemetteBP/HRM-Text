---
type: Operational Record
title: CP2 heavy-first rerun (2026-05-31)
description: 'Chronological record from DFM L CP2 Evaluation Queue: CP2 heavy-first
  rerun (2026-05-31).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# CP2 heavy-first rerun (2026-05-31)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

CP2 heavy-first rerun, 2026-05-31. Confidence: high.

`scripts/schedule_checkpoint_evals.sh` now supports `QUEUE_ORDER=heavy_first`.
That queue order starts with IFEval-DA shards, then MATH shards, then the other
longer shard groups before the short single-shard tasks. A dry run with
`QUEUE_ORDER=heavy_first` queued `168` jobs and showed the expected leading
tasks.

The first CP2 heavy-first background launch at
`logs/eval/dfm_L_epoch2_heavy_first_20260531T1059` exited before workers
started, leaving an empty status log and a partial queue. It was superseded by a
detached `setsid` launch.

Active launch:

```bash
EPOCH=2 EVAL_EPOCH=2 CKPT_TAG=epoch_2 CKPT_PATH=checkpoints/dfm/L \
GPUS=0,1,2,3,4,5,6,7 QUEUE_ORDER=heavy_first \
LOG_ROOT=logs/eval/dfm_L_epoch2_heavy_first_20260531T1102 \
DFM_LOG_ROOT=logs/dfm_evals/dfm_L_epoch2_heavy_first_20260531T1102 \
WANDB_PROJECT="DFM L" WANDB_RUN_ID=kgnbdmwf WANDB_RUN_NAME=dfm-L \
MODEL_PREFIX=hrm-dfm-L MAX_RETRIES=3 scripts/schedule_checkpoint_evals.sh
```

Scheduler PID: `2557293`.

Files:

- Scheduler PID file:
  `logs/eval/dfm_L_epoch2_heavy_first_20260531T1102/scheduler.pid`
- Launcher log:
  `logs/eval/dfm_L_epoch2_heavy_first_20260531T1102.launcher.log`
- Status log:
  `logs/eval/dfm_L_epoch2_heavy_first_20260531T1102/status.tsv`
- DFM log root:
  `logs/dfm_evals/dfm_L_epoch2_heavy_first_20260531T1102`

Initial verification showed checkpoint readiness for `epoch_2`, all eight
workers started on IFEval-DA shards `0..7`, and `nvidia-smi` reported all eight
GPUs at `100%` utilization with roughly `101-125 GB` memory in use. Confidence:
high.
