---
type: Operational Record
title: DFM4 XL-DDP step 200K lite eval queue (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP step
  200K lite eval queue (2026-06-04).'
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
# DFM4 XL-DDP step 200K lite eval queue (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP step 200K lite eval queue, 2026-06-04. Confidence: high.

`checkpoints/dfm4/XL-ddp/step_200000` is complete as an unsharded DDP checkpoint:
`unsharded_step_200000.pt`, `checkpoint_state_step_200000.json`, and
`carry_step_200000.{0..7}.pt` exist. The checkpoint metadata reports
`epoch=1`, `batch_in_epoch=200000`, `global_batch_size=196608`, and
`data_path=data/sampled_dfm4`. With `data/sampled_dfm4/metadata.json`
`total_length=72,007,089,569`, there are `366246` full optimizer steps per
epoch, so the W&B x-axis value is `0.546081049349`.

The no-EMA lite eval was launched in tmux window `hrm-1:dfm4-200k-lite` with
status/progress in the second pane. It targets W&B project
`Original Plus Mixed Danish Instruction Rich L`, run id `4chqwd3w`, run name
`dfm4-XL-ddp`, and logs under `lite_eval_noema/*` and
`lite_dfm_eval_noema/*`.

```bash
CKPT_TAGS=step_200000 \
EVAL_EPOCHS=0.546081049349 \
CKPT_PATH=checkpoints/dfm4/XL-ddp \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=3 \
NO_EMA=1 \
EVAL_PREFIX=lite_eval_noema \
DFM_EVAL_PREFIX=lite_dfm_eval_noema \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=4chqwd3w \
WANDB_RUN_NAME=dfm4-XL-ddp \
MODEL_PREFIX=hrm-dfm4-XL-ddp \
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_probe_20260604T035517_200k \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260604T035517_200k \
bash scripts/schedule_multiple_checkpoint_evals.sh
```

Initial status queued `19` jobs for `step_200000` and started the first eight
jobs across GPUs 0-7.
