---
type: Operational Record
title: XL DDP lite eval launch correction (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: XL DDP lite eval
  launch correction (2026-06-03).'
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
# XL DDP lite eval launch correction (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

XL DDP lite eval launch correction, 2026-06-03. Confidence: high.

The intended intra-epoch lite eval target is not `checkpoints/dfm/L`; it is
`checkpoints/dfm4/XL-ddp`. That checkpoint directory contains unsharded DDP
checkpoints:

- `unsharded_step_50000.pt` plus `carry_step_50000.{0..7}.pt`
- `unsharded_step_100000.pt` plus `carry_step_100000.{0..7}.pt`

`step_150000` was not present at inspection time. The active W&B training run
for this XL DDP run is `Original Plus Mixed Danish Instruction Rich L/4chqwd3w`
with run name `dfm4-XL-ddp`; the earlier `dbap7xai` run was crashed.

The shared-queue lite eval was launched in tmux window `hrm-1:xl-lite-eval`
with two panes: one scheduler pane and one per-GPU monitor pane. The monitor is
`scripts/watch_multi_checkpoint_eval_progress.py`, which parses the
multi-checkpoint status file and displays one line per GPU. Launch target:

```bash
CKPT_TAGS=step_50000,step_100000 \
EVAL_EPOCHS=0.11945518877503482,0.23891037755006964 \
LITE_EVAL=1 QUEUE_ORDER=heavy_first \
CKPT_PATH=checkpoints/dfm4/XL-ddp \
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_lite_probe \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_lite_probe \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=4chqwd3w \
WANDB_RUN_NAME=dfm4-XL-ddp \
GPUS=0,1,2,3,4,5,6,7 \
MAX_RETRIES=3 \
CHECKPOINT_POLL_SECONDS=60 \
scripts/schedule_multiple_checkpoint_evals.sh
```

At launch, the scheduler queued `38` jobs for two checkpoints and started the
first eight `step_50000` jobs across GPUs `0..7`. Confidence: high.

Superseded: the first tmux launch of the XL DDP lite eval used the tmux base
environment, so standard evals failed immediately with
`ModuleNotFoundError: No module named 'pydantic'` and DFM server logs failed
with `ModuleNotFoundError: No module named 'uvicorn'`. Because the scheduler
ran job bodies under `set +e`, failed `wait_for_server` calls did not stop DFM
jobs before launching `dfm-evals`, leaving eval processes waiting on dead local
OpenAI endpoints. Confidence: high.
