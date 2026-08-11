---
type: Operational Record
title: DFM L all-checkpoint lite eval queue (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L all-checkpoint
  lite eval queue (2026-06-03).'
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
# DFM L all-checkpoint lite eval queue (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L all-checkpoint lite eval queue, 2026-06-03. Confidence: high.

A shared multi-checkpoint lite eval queue was launched for all local DFM L
checkpoints in `checkpoints/dfm/L`: `epoch_1`, `epoch_2`, `epoch_3`,
`epoch_4`, `step_500000`, `step_550000`, `step_600000`, and `step_650000`.
The epoch x-axis values are `1,2,3,4`; the step checkpoints use fractional
epoch values derived from checkpoint metadata as `3.03594610513`,
`3.339544966027`, `3.643143826924`, and `3.946742687821`. Results are targeted
at W&B project `Original Plus Mixed Danish Instruction Rich L`, run id
`dfm-l-resume-epoch3` / run name `dfm-L-resume-epoch3`.

```bash
CKPT_TAGS=epoch_1,epoch_2,epoch_3,epoch_4,step_500000,step_550000,step_600000,step_650000 \
EVAL_EPOCHS=1,2,3,4,3.03594610513,3.339544966027,3.643143826924,3.946742687821 \
CKPT_PATH=checkpoints/dfm/L \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=3 \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=dfm-l-resume-epoch3 \
WANDB_RUN_NAME=dfm-L-resume-epoch3 \
MODEL_PREFIX=hrm-dfm-L \
LOG_ROOT_BASE=logs/eval/dfm_L_lite_all_checkpoints_20260603T181543 \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm_L_lite_all_checkpoints_20260603T181543 \
bash scripts/schedule_multiple_checkpoint_evals.sh
```

The scheduler started in tmux window `hrm-1:dfmL-lite`, queued `152` jobs for
the eight checkpoints, and initially started one job per GPU.
