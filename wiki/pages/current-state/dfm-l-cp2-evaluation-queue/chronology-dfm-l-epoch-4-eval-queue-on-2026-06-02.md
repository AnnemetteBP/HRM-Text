---
type: Operational Record
title: DFM L epoch 4 eval queue on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L epoch 4
  eval queue on (2026-06-02).'
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
# DFM L epoch 4 eval queue on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L epoch 4 eval queue on 2026-06-02. Confidence: high.

The completed DFM L checkpoint `checkpoints/dfm/L/fsdp2_epoch_4` plus
`carry_epoch_4.{0..7}.pt` is present locally. A full eval queue for epoch 4 was
prepared with `scripts/schedule_checkpoint_evals.sh` using all 8 GPUs,
`QUEUE_ORDER=heavy_first`, `MAX_RETRIES=3`, project `DFM L`, and run id
`kgnbdmwf`. The dry-run queue contained `168` jobs:

- `32` DFM IFEval-DA shards
- `64` MATH shards
- sharded GSM8k, DROP, MMLU, HellaSwag, GovReport, WMT24++ EN-DA,
  generative-talemaader, NordjyllandNews, HumanEval, GEC-DALA, Multi Wiki QA
- single ARC, Winogrande, BoolQ, Danish citizen tests, DALA, and PIQA jobs

Superseded: Because all GPUs were occupied by the DDP XL run at launch time, a
tmux watcher was started in `hrm-1:7` (`dfmL-cp4-evals`) to wait until all GPUs
dropped below `20GB` used.

The user then requested immediate launch despite GPU occupancy. A fresh tmux
window `hrm-1:7` (`dfmL-cp4-evals-now`) launched the scheduler immediately at
`2026-06-02T13:27:03+02:00`. It queued `168` jobs, confirmed checkpoint
readiness for `epoch_4`, and started 8 worker processes:
`3767743 3767744 3767745 3767746 3767747 3767748 3767749 3767750`.
The command was:

```bash
EPOCH=4 CKPT_TAG=epoch_4 CKPT_PATH=checkpoints/dfm/L \
GPUS=0,1,2,3,4,5,6,7 \
WANDB_PROJECT="DFM L" WANDB_RUN_ID=kgnbdmwf WANDB_RUN_NAME=dfm-L \
LOG_ROOT=logs/eval/dfm_L_epoch4_queued_all \
DFM_LOG_ROOT=logs/dfm_evals/dfm_L_epoch4_queued_all \
QUEUE_ORDER=heavy_first MAX_RETRIES=3 \
scripts/schedule_checkpoint_evals.sh
```

A live progress monitor was added at `scripts/watch_eval_progress.py`.
Confidence: high. It periodically scans scheduler status plus standard/DFM eval
logs, normalizes tqdm carriage-return output, prints aggregate scheduler counts,
GPU memory/utilization, recent scheduler events, and the latest progress-like
lines from active logs. It intentionally ignores binary Inspect `.eval` archives.

The monitor was launched as a split pane in the scheduler window:

```text
hrm-1:7.1  scheduler
hrm-1:7.2  python scripts/watch_eval_progress.py ...
```

Command:

```bash
python scripts/watch_eval_progress.py \
  --log-root logs/eval/dfm_L_epoch4_queued_all \
  --dfm-log-root logs/dfm_evals/dfm_L_epoch4_queued_all \
  --interval 10 \
  --max-logs 24
```
