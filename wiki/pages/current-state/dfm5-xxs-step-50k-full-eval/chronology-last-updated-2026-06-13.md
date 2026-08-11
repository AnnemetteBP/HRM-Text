---
type: Operational Record
title: Last updated (2026-06-13)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Last updated
  (2026-06-13).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Last updated (2026-06-13)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Last updated: 2026-06-13
Confidence: high
Scope: Active full evaluation of `checkpoints/dfm5/XXS` checkpoint
`step_50000`.

The full standard + dfm-evals + EuroEval campaign for the DFM5 XXS 50K
checkpoint was launched in tmux session `dfm5_xxs_step50000_full_eval`.
It intentionally runs on the remaining GPU headroom while the 8-GPU XXS
training run continues.

W&B target:

```text
project: DFM5
run_id:  2tv9u438
run:     dfm5-XXS
```

The epoch x-axis value is the fractional epoch implied by the DFM5 sample size
and batch size:

```text
EVAL_EPOCH = 50000 / (35,605,979,095 / 196,608) = 0.276088
```

Launch command:

```bash
cd /work/dfm/HRM-Text
RUN_EUROEVAL=1 \
CKPT_PATH=checkpoints/dfm5/XXS \
CKPT_TAG=step_50000 \
EVAL_EPOCH=0.276088 \
GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm5_XXS_step50000_full_20260613 \
DFM_LOG_ROOT=logs/dfm_evals/dfm5_XXS_step50000_full_20260613 \
EUROEVAL_LOG_ROOT=logs/euroeval/dfm5_XXS_step50000_full_20260613 \
WANDB_PROJECT=DFM5 \
WANDB_RUN_ID=2tv9u438 \
WANDB_RUN_NAME=dfm5-XXS \
WANDB_SYNC=1 \
MODEL_PREFIX=hrm-dfm5-XXS \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=3 \
STANDARD_BATCH_SIZE=16 \
DFM_BATCH_SIZE=16 \
IFEVAL_BATCH_SIZE=16 \
EUROEVAL_BATCH_SIZE=8 \
EUROEVAL_BIN=./scripts/euroeval_api_no_flash_attn_guard.py \
EUROEVAL_MAX_CONCURRENT_CALLS=20 \
STARTUP_STAGGER_SECONDS=5 \
scripts/schedule_checkpoint_evals.sh
```

Initial status at launch: `169` queued jobs. After about four minutes,
`12` IFEval-DA shards had completed successfully, `8` were active, and
telemetry showed no OOMs. The eval servers used only a few GiB of additional
GPU memory on top of the training process.
