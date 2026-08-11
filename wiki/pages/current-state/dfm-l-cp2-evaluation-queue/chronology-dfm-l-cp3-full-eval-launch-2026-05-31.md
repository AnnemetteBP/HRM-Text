---
type: Operational Record
title: DFM L CP3 full eval launch (2026-05-31)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L CP3 full
  eval launch (2026-05-31).'
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
# DFM L CP3 full eval launch (2026-05-31)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L CP3 full eval launch, 2026-05-31. Confidence: high.

Before scheduling CP3, W&B history for run `kgnbdmwf` in project
`Original Plus Mixed Danish Instruction Rich L` was checked for
`eval/MATH/acc` and contained only DFM CP1/CP2 rows. The local DFM CP3
checkpoint was complete under `checkpoints/dfm/L` with `fsdp2_epoch_3` and all
eight `carry_epoch_3.{0..7}.pt` files.

CP3 full evals were launched with heavy-first ordering:

```bash
EPOCH=3 EVAL_EPOCH=3 CKPT_TAG=epoch_3 CKPT_PATH=checkpoints/dfm/L \
GPUS=0,1,2,3,4,5,6,7 QUEUE_ORDER=heavy_first \
LOG_ROOT=logs/eval/dfm_L_epoch3_heavy_first_20260531T2227 \
DFM_LOG_ROOT=logs/dfm_evals/dfm_L_epoch3_heavy_first_20260531T2227 \
WANDB_PROJECT="DFM L" WANDB_RUN_ID=kgnbdmwf WANDB_RUN_NAME=dfm-L \
MODEL_PREFIX=hrm-dfm-L MAX_RETRIES=3 scripts/schedule_checkpoint_evals.sh
```

Scheduler PID: `3527439`.

Files:

- Scheduler PID file:
  `logs/eval/dfm_L_epoch3_heavy_first_20260531T2227/scheduler.pid`
- Launcher log:
  `logs/eval/dfm_L_epoch3_heavy_first_20260531T2227.launcher.log`
- Status log:
  `logs/eval/dfm_L_epoch3_heavy_first_20260531T2227/status.tsv`
- DFM log root:
  `logs/dfm_evals/dfm_L_epoch3_heavy_first_20260531T2227`

Initial verification showed `168` jobs queued, checkpoint readiness for
`epoch_3`, workers started on IFEval-DA shards, and all eight GPUs active.
