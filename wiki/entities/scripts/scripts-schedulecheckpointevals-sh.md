---
type: Software Reference
title: '`scripts/schedule_checkpoint_evals.sh`'
description: 'Part of Script Entities: `scripts/schedule_checkpoint_evals.sh`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/schedule_checkpoint_evals.sh`

Part of [Script Entities](/entities/scripts.md).

Updated on 2026-06-06. Confidence: high.

Queues standard HRM evals and dfm-evals onto a GPU worker pool. It supports
lite mode, no-EMA mode, sharded standard/DFM tasks, final merge, and W&B
logging.

Retry behavior now adapts batch size. On the first attempt, the scheduler uses
the highest configured batch size unless telemetry has already shown an OOM for
that task at the current-or-better free-memory level. Successful telemetry at
the same task and lower-or-equal free memory is treated as evidence that the
recorded batch size is safe. If no telemetry exists, the configured batch size
is used rather than falling back to batch size `1`.

On retry attempt `n`, the effective batch size is halved `n` times with a floor
of `1`:

- standard evals: `STANDARD_BATCH_SIZE`
- dfm-evals OpenAI shim server and `--max-connections`: `DFM_BATCH_SIZE`
- IFEval-DA shim server and `--max-connections`: `IFEVAL_BATCH_SIZE`

This means an OOM at batch size `8` will retry at `4`, then `2`, then `1`
within the existing `MAX_RETRIES` limit.

The scheduler also records per-attempt telemetry for future placement decisions
in:

```text
${LOG_ROOT}/eval_attempts.tsv
```

Each row records checkpoint tag, task/shard, GPU, attempt, effective batch
size, status, OOM flag, GPU free/used/total MiB before and after the attempt,
and the primary task log path. This is intended to build a table of highest
non-OOM-proven batch sizes by task and memory headroom.

Operational note from 2026-06-06. Confidence: high. During DFM4 XL-DDP
`step_400000` EMA lite eval, `ARC` first failed on GPU4 at about `6.4 GiB`
free above training even with batch size `1`. Retrying on GPU0 at about
`16.6 GiB` free succeeded at batch size `1`. The subsequent `MMLU` retry was
started on GPU0 at batch size `8` because no telemetry yet showed batch-size
OOM at that free-memory level.

Operational note from 2026-06-07. Confidence: high. Manual one-job retry
commands can still override the scheduler's adaptive first-attempt choice by
setting `DFM_BATCH_SIZE` or `IFEVAL_BATCH_SIZE` directly. During DFM4 XL-DDP
`step_400000` EMA DFM-lite cleanup, WMT24++ en-da was deliberately forced to
`DFM_BATCH_SIZE=1` after batch 2 had OOMed on low-headroom GPUs. GovReport
succeeded at batch 2 on GPU0, where about `16.6 GiB` was free above training.
The adaptive telemetry logic should be treated as the default path for queued
future runs; forced single-job retries are manual finish-the-run decisions.

Updated on 2026-06-08. Confidence: high. `scripts/schedule_multiple_checkpoint_evals.sh`
now supports attaching additional workers to an already-running shared queue:

```text
RESUME_EXISTING_QUEUE=1
SKIP_FINAL_MERGE=1
```

`RESUME_EXISTING_QUEUE=1` preserves the existing `jobs.tsv` and `status.tsv`
instead of rebuilding/truncating them. `SKIP_FINAL_MERGE=1` lets the extra
workers consume queued jobs while leaving final merge to the original scheduler
process. This was added to attach GPU1/GPU4 to the active DFM4 XL-DDP
`step_600000` no-EMA lite eval after the conservative initial launch used only
GPU0/GPU2/GPU7.

Updated on 2026-06-10. Confidence: high. `scripts/schedule_eval_campaign.sh`
adds a TSV-defined campaign queue for mixed eval variants. It delegates each
queued shard to `scripts/schedule_checkpoint_evals.sh` with
`SKIP_FINAL_MERGE=1`, so existing task definitions, retry/OOM-halving,
batch-size overrides, server launch code, and telemetry remain the source of
truth. After all shard jobs finish, it runs `FINAL_MERGE_ONLY=1` once per TSV
variant so each checkpoint/mode uses the intended `NO_EMA`, `LITE_EVAL`,
`EVAL_PREFIX`, and `DFM_EVAL_PREFIX` settings.

The campaign TSV columns are:

```text
variant_id ckpt_tag eval_epoch lite_eval no_ema eval_prefix dfm_eval_prefix log_root dfm_log_root
```

This helper fills the gap left by `scripts/schedule_multiple_checkpoint_evals.sh`,
where EMA/no-EMA, lite/full, and metric prefixes are process-wide settings and
therefore cannot be mixed in one queue.

Updated on 2026-06-10. Confidence: high. `scripts/watch_eval_campaign_progress.py`
monitors a campaign root from `scripts/schedule_eval_campaign.sh`. It prints
queue counts, one active-job line per GPU ordered by GPU id, elapsed active-job
time, live GPU memory/utilization, and the latest scheduler status rows.
