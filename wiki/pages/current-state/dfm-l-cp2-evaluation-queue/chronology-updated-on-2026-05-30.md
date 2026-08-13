---
type: Operational Record
title: Updated on (2026-05-30)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Updated on (2026-05-30).'
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
# Updated on (2026-05-30)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Updated on 2026-05-30. Confidence: high.

CP2 exists locally under `checkpoints/dfm/L`: `fsdp2_epoch_2/.metadata` and all
eight `carry_epoch_2.{0..7}.pt` files were present before scheduling.

The CP2 all-evals scheduler was launched on all eight GPUs with:

```bash
EPOCH=2 CKPT_PATH=checkpoints/dfm/L GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm_L_epoch2_queued_all \
DFM_LOG_ROOT=logs/dfm_evals/dfm_L_epoch2_queued_all \
WANDB_PROJECT="DFM L" WANDB_RUN_ID=kgnbdmwf WANDB_RUN_NAME=dfm-L \
MODEL_PREFIX=hrm-dfm-L MAX_RETRIES=3 scripts/schedule_checkpoint_evals.sh
```

Launcher PID:

```text
3530318
```

Files:

- Scheduler PID file: `logs/eval/dfm_L_epoch2_queued_all/scheduler.pid`
- Launcher log: `logs/eval/dfm_L_epoch2_queued_all.launcher.log`
- Status log: `logs/eval/dfm_L_epoch2_queued_all/status.tsv`
- Queue file: `logs/eval/dfm_L_epoch2_queued_all/jobs.tsv`

Dry run and launch both reported `168` jobs. Current future-run sharding is in
effect, including `MATH=64` shards and `IFEval-DA=32` shards. The scheduler
started with all eight `GSM8k` shards across GPUs `0..7`.

`scripts/report_eval_progress.py` was patched on 2026-05-30 so CP2 progress
reports infer the epoch from `--log-root` and scale the MATH ETA from the old
8-shard measurement to the current 64-shard schedule. Use:

```bash
python scripts/report_eval_progress.py \
  --log-root logs/eval/dfm_L_epoch2_queued_all \
  --dfm-log-root logs/dfm_evals/dfm_L_epoch2_queued_all
```

Initial progress report at `2026-05-30T15:04:23+02:00` showed
`completed=0`, `active=8`, `queued=160`, `total_visible=168`, with an early
full ETA of about `3h03m`.
