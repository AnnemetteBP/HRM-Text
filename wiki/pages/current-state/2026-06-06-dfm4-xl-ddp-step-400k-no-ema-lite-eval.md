---
type: Operational Record
title: 2026-06-06 DFM4 XL-DDP Step 400K No-EMA Lite Eval
description: 'Part of Current State: 2026-06-06 DFM4 XL-DDP Step 400K No-EMA Lite
  Eval.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-06 DFM4 XL-DDP Step 400K No-EMA Lite Eval

Part of [Current State](/pages/current-state.md).

Confidence: high for checkpoint presence, checkpoint metadata, and launch
command; completion pending.

The `checkpoints/dfm4/XL-ddp` `step_400000` unsharded checkpoint is present:

```text
unsharded_step_400000.pt
checkpoint_state_step_400000.json
carry_step_400000.{0..7}.pt
```

`checkpoint_state_step_400000.json` reports `step=400000`,
`batch_in_epoch=32753`, `epoch=2`, `global_batch_size=196608`, and
`data_path=data/sampled_dfm4`. The `epoch_1` checkpoint was saved at
`step=367247`, so the fractional eval x-value for W&B is:

```text
1 + (400000 - 367247) / 367247 = 1.0891852077756932
```

A no-EMA lite eval was launched in tmux session/window
`dfm4_lite_eval:noema_400k`, syncing to W&B project
`Original Plus Mixed Danish Instruction Rich L`, run id `dfm4xlddpclean`, under
the usual clean-history Lite prefixes:

```text
lite_eval_noema/*
lite_dfm_eval_noema/*
```

Command:

```bash
cd /work/dfm/HRM-Text
env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_400k_20260606_tmux \
  DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_400k_20260606_tmux \
  CKPT_TAGS=step_400000 \
  EVAL_EPOCHS=1.0891852077756932 \
  CKPT_PATH=checkpoints/dfm4/XL-ddp \
  GPUS=2,3,7 \
  JUDGE_GPU=0 \
  LITE_EVAL=1 \
  LITE_SHARD_INDEX=0 \
  QUEUE_ORDER=heavy_first \
  MAX_RETRIES=3 \
  NO_EMA=1 \
  WANDB_SYNC=1 \
  WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
  WANDB_RUN_ID=dfm4xlddpclean \
  WANDB_RUN_NAME="dfm4-XL-ddp clean lite history" \
  EVAL_PREFIX=lite_eval_noema \
  DFM_EVAL_PREFIX=lite_dfm_eval_noema \
  MODEL_PREFIX=hrm-dfm4-XL-ddp-noema \
  STANDARD_BATCH_SIZE=1 \
  DFM_BATCH_SIZE=1 \
  IFEVAL_BATCH_SIZE=1 \
  bash scripts/schedule_multiple_checkpoint_evals.sh
```

Initial monitor output at `2026-06-06T08:29:07`:

```text
started=3 finished=0 active=3 queued=16
GPU2: step_400000 dfm_ifeval:0 shard 0/32
GPU3: step_400000 standard:MATH shard 0/64
GPU7: step_400000 standard:GSM8k shard 0/8
```

Completion update, 2026-06-06. Confidence: high. The `step_400000` no-EMA lite
eval completed with `DONE status_0`. The final scheduler status was
`started=19 finished=19 active=0 queued=0`, with final merge ending at
`2026-06-06T11:25:53+02:00`.
