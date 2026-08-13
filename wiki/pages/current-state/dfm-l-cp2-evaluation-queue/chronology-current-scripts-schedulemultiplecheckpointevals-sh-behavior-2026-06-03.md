---
type: Operational Record
title: Current scripts/schedulemultiplecheckpointevals.sh behavior (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Current scripts/schedulemultiplecheckpointevals.sh
  behavior (2026-06-03).'
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
# Current scripts/schedulemultiplecheckpointevals.sh behavior (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Current `scripts/schedule_multiple_checkpoint_evals.sh` behavior, 2026-06-03.
Confidence: high.

The wrapper now builds one shared queue across all requested checkpoints, with
one worker per configured GPU. Each queued job carries its checkpoint tag,
fractional x-axis value, task, shard, and output roots. Workers only pop jobs
whose checkpoint files are complete; unavailable future checkpoint jobs stay in
the queue rather than occupying a GPU while waiting. After all jobs finish, the
wrapper runs final merge/W&B sync once per checkpoint.

For lite checkpoint probes, the command form remains:

```bash
CKPT_TAGS=step_50000,step_150000 \
EVAL_EPOCHS=0.11945518877503482,0.35836556632510447 \
LITE_EVAL=1 QUEUE_ORDER=heavy_first \
CKPT_PATH=checkpoints/dfm/L \
LOG_ROOT_BASE=logs/eval/dfm_L_lite_probe \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm_L_lite_probe \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=dfm-l-resume-epoch3 \
WANDB_RUN_NAME=dfm-L-resume-epoch3 \
scripts/schedule_multiple_checkpoint_evals.sh
```
