---
type: Operational Record
title: Original-plus-mixed lite eval queue, verified on (2026-06-04)
description: 'Chronological record from dfm-evals: Original-plus-mixed lite eval queue,
  verified on (2026-06-04).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Original-plus-mixed lite eval queue, verified on (2026-06-04)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Original-plus-mixed lite eval queue, verified on 2026-06-04. Confidence: high.

The original-plus-mixed Danish instruction rich L checkpoints `epoch_1`,
`epoch_2`, `epoch_3`, and `epoch_4` under
`checkpoints/original_plus_mixed_danish_instruction_rich/L` were queued for the
generic lite multi-checkpoint evaluator. All four `fsdp2_epoch_*` directories
had `.metadata`, and all `carry_epoch_*.{0..7}.pt` files were present. The W&B
target is project `Original Plus Mixed Danish Instruction Rich L`, run id
`es1od1in`, run name `original-plus-mixed-danish-instruction-rich-L`.

The launch is staged in tmux window `hrm-1:opm-lite`. It first waits for
`logs/eval/dfm4_XL_ddp_noema_lite_probe_20260604T035517_200k/status.tsv` to
contain `DONE status_0`, then starts the original-plus-mixed lite queue. This
avoids stacking a second 8-GPU lite eval wave on top of the active DFM4 200K
lite queue.

```bash
CKPT_TAGS=epoch_1,epoch_2,epoch_3,epoch_4 \
EVAL_EPOCHS=1,2,3,4 \
CKPT_PATH=checkpoints/original_plus_mixed_danish_instruction_rich/L \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=3 \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=es1od1in \
WANDB_RUN_NAME=original-plus-mixed-danish-instruction-rich-L \
MODEL_PREFIX=hrm-original-plus-mixed-L \
LOG_ROOT_BASE=logs/eval/original_plus_mixed_danish_instruction_rich_L_lite_all_checkpoints_20260604T035922 \
DFM_LOG_ROOT_BASE=logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_lite_all_checkpoints_20260604T035922 \
bash scripts/schedule_multiple_checkpoint_evals.sh
```
