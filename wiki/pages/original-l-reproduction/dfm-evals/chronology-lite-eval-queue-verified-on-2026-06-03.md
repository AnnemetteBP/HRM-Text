---
type: Operational Record
title: Lite eval queue, verified on (2026-06-03)
description: 'Chronological record from dfm-evals: Lite eval queue, verified on (2026-06-03).'
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
# Lite eval queue, verified on (2026-06-03)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Lite eval queue, verified on 2026-06-03. Confidence: high.

The original Sapient L checkpoints `epoch_1`, `epoch_2`, `epoch_3`, and
`epoch_4` were scheduled with the generic lite multi-checkpoint evaluator. The
W&B target is the corresponding clean-history run in project
`Original Plus Mixed Danish Instruction Rich L`, run id `origLclean`, run name
`original-sapient-L-clean-history`. The queue launched in tmux window
`hrm-1:origL-lite`, queued `76` jobs, and started one job on each of the eight
GPUs.

```bash
CKPT_TAGS=epoch_1,epoch_2,epoch_3,epoch_4 \
EVAL_EPOCHS=1,2,3,4 \
CKPT_PATH=checkpoints/original_sapient/L \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=3 \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=origLclean \
WANDB_RUN_NAME=original-sapient-L-clean-history \
MODEL_PREFIX=hrm-original-sapient-L \
LOG_ROOT_BASE=logs/eval/original_sapient_L_lite_all_checkpoints_20260603T213010 \
DFM_LOG_ROOT_BASE=logs/dfm_evals/original_sapient_L_lite_all_checkpoints_20260603T213010 \
bash scripts/schedule_multiple_checkpoint_evals.sh
```

The same merged lite metrics were resynced to the same W&B run under
`lite_eval_noema/*` and `lite_dfm_eval_noema/*` without rerunning inference.
The relog read the stored `merged_metrics.json` and
`merged_ifeval_da_metrics.json` files from the log roots above and wrote four
history rows for each prefix. W&B reported syncing history steps `65395-65402`.
Per epoch, the relog wrote `195` `lite_eval_noema` metrics and `74`
`lite_dfm_eval_noema` metrics. Confidence: high.
