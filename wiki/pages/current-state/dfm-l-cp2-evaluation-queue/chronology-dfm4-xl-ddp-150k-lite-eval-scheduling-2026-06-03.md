---
type: Operational Record
title: DFM4 XL-DDP 150K lite eval scheduling (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP 150K
  lite eval scheduling (2026-06-03).'
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
# DFM4 XL-DDP 150K lite eval scheduling (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP 150K lite eval scheduling, 2026-06-03. Confidence: high.

`step_150000` exists under `checkpoints/dfm4/XL-ddp` as an unsharded checkpoint
with all eight carry files. Its checkpoint metadata reports `step=150000`,
`epoch=1`, `batch_in_epoch=150000`, and `global_batch_size=196608`. Given
`data/sampled_dfm4` `total_length=72007089569`, the run has `366246` full
optimizer steps per epoch, so the lite eval x-axis value for this checkpoint is
`0.4095607870120083`.

A no-EMA lite eval for `step_150000` was queued in tmux window
`hrm-1:dfm4-150k-lite`. It is intentionally waiting for the active DFM4 XL-DDP
training process using all eight GPUs to exit before starting eval workers. The
queued scheduler uses:

```bash
CKPT_TAGS=step_150000 \
EVAL_EPOCHS=0.4095607870120083 \
CKPT_PATH=checkpoints/dfm4/XL-ddp \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
LITE_SHARD_INDEX=0 \
QUEUE_ORDER=heavy_first \
NO_EMA=1 \
STANDARD_CONFIG=evaluation/config/hrm_benchmarking_lite.yaml \
STANDARD_BATCH_SIZE=16 \
DFM_BATCH_SIZE=16 \
IFEVAL_BATCH_SIZE=16 \
EVAL_PREFIX=lite_eval_noema \
DFM_EVAL_PREFIX=lite_dfm_eval_noema \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=4chqwd3w \
WANDB_RUN_NAME=dfm4-XL-ddp \
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_probe_20260603_150k \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260603_150k \
bash scripts/schedule_multiple_checkpoint_evals.sh
```
