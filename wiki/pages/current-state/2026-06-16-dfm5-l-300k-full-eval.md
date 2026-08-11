---
type: Operational Record
title: 2026-06-16 DFM5 L 300K Full Eval
description: 'Part of Current State: 2026-06-16 DFM5 L 300K Full Eval.'
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
# 2026-06-16 DFM5 L 300K Full Eval

Part of [Current State](/pages/current-state.md).

Confidence: high for local checkpoint state, scheduler launch, and tmux
process inspection; medium for final metrics until all jobs finish and the
post-eval watcher logs averages/regenerates docs.

The DFM5 L `step_300000` checkpoint exists under `checkpoints/dfm5/L` with
`checkpoint_state_step_300000.json`, `fsdp2_step_300000/.metadata`, eight
FSDP shard files, and eight carry files. The checkpoint state says
`epoch=2`, `batch_in_epoch=118714`, `global_batch_size=196608`, and
`checkpoint_format=sharded`.

The eval x-axis value follows the same fractional-epoch convention used for
the earlier DFM5-L points:

```text
300000 / (35605979095 / 196608) = 1.6565307709311847
```

The full eval was launched on 2026-06-16 in tmux window `hrm-0:8` with
EuroEval-first ordering, W&B sync enabled, and incremental merge enabled by
the scheduler default:

```bash
cd /work/dfm/HRM-Text
CKPT_PATH=checkpoints/dfm5/L \
CKPT_TAG=step_300000 \
EVAL_EPOCH=1.6565307709311847 \
GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm5_L_step300000_full_20260616_eurofirst_guard \
DFM_LOG_ROOT=logs/dfm_evals/dfm5_L_step300000_full_20260616_eurofirst_guard \
EUROEVAL_LOG_ROOT=logs/euroeval/dfm5_L_step300000_full_20260616_eurofirst_guard \
WANDB_SYNC=1 \
WANDB_PROJECT=DFM5 \
WANDB_RUN_ID=oti1lisg \
WANDB_RUN_NAME=dfm5-L \
MODEL_PREFIX=hrm-dfm5-L \
RUN_EUROEVAL=1 \
QUEUE_ORDER=euroeval_first \
STANDARD_BATCH_SIZE=128 \
STANDARD_BATCH_SIZE_GSM8K=64 \
STANDARD_BATCH_SIZE_MATH=64 \
STANDARD_BATCH_SIZE_DROP=32 \
DFM_BATCH_SIZE=32 \
DFM_BATCH_SIZE_GOVREPORT=32 \
DFM_BATCH_SIZE_NORDJYLLANDNEWS=32 \
DFM_BATCH_SIZE_WMT24PP_EN_DA=32 \
DFM_BATCH_SIZE_HUMANEVAL=16 \
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16 \
IFEVAL_BATCH_SIZE=64 \
EUROEVAL_BATCH_SIZE=16 \
EUROEVAL_BATCH_SIZE_IFEVAL=32 \
EUROEVAL_BATCH_SIZE_IFEVAL_DA=32 \
MAX_RETRIES=5 \
EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py \
scripts/schedule_checkpoint_evals.sh \
  2>&1 | tee logs/dfm5_L_step300000_full_eval_20260616.log
```

The IFEval-specific batch sizes were intentionally set one step higher than
the previous full-eval command: DFM IFEval-DA uses `IFEVAL_BATCH_SIZE=64`,
while EuroEval `ifeval` and `ifeval-da` use task-specific overrides of `32`
instead of the base EuroEval batch size `16`.

Runtime finding, 2026-06-16. Confidence: high for local logs and process/GPU
inspection. The DFM IFEval-DA bump to `IFEVAL_BATCH_SIZE=64` was too high
while the DFM5-L training process was still resident on each GPU. Server logs
for shards 0-4 show CUDA OOMs after attempting an additional `640 MiB`
allocation with only about `92-602 MiB` free. Each DFM IFEval-DA job starts
`scripts/hrm_openai_server.py` with both `--batch-size 64` and the dfm-evals
client uses `--max-connections 64`, so the setting increases both server batch
capacity and request concurrency. With the training process using roughly
`104-107 GiB` and the eval server using roughly `71-76 GiB`, this leaves almost
no GPU memory headroom. The long shard runtime is therefore not normal IFEval
slowness; it is OOM/retry/stalled-client behavior from over-aggressive
concurrency. Future concurrent-with-training DFM IFEval-DA evals should use
`IFEVAL_BATCH_SIZE=32` unless telemetry proves a larger value is safe.

Scheduler fix and active-run intervention, 2026-06-16. Confidence: high for
code inspection, `bash -n`, process list, and scheduler status. The scheduler
scripts were patched so future DFM and EuroEval jobs monitor their local
OpenAI shim server while the eval client is running. If the server exits or
logs an OOM, the client is killed and the job returns nonzero, allowing the
existing retry path to halve the batch size. Patched files:

```text
scripts/schedule_checkpoint_evals.sh
scripts/run_euroeval_on_checkpoint.sh
```

The currently running `step_300000` scheduler had already loaded the old shell
functions, so the stuck DFM IFEval-DA batch-64 clients/servers were manually
terminated for shards 0-5. The scheduler observed nonzero exits and retried
those shards at batch `32`:

```text
2026-06-16T07:33:35+02:00 RETRY dfm_ifeval ... next_attempt_2
2026-06-16T07:33:45+02:00 START dfm_ifeval ... attempt_2_of_6 batch_32
```

The training processes were not targeted by the intervention.

Follow-up in the same active run: shards 0-5 completed successfully at batch
`32`, but the old in-memory scheduler then launched shards 6-11 at batch `64`
because batch selection is keyed by task/shard id. Synthetic OOM telemetry rows
were appended for DFM IFEval-DA shard ids 6-31 at batch `64`, and the stuck
batch-64 processes for shards 6-11 were terminated. The scheduler then retried
shards 6-11 at batch `32`. This telemetry seeding is an active-run workaround
only; future scheduler launches should rely on the patched server-monitor
behavior and a conservative `IFEVAL_BATCH_SIZE=32`.

Initial scheduler status:

```text
2026-06-16T06:23:48+02:00 QUEUED 188 jobs
2026-06-16T06:23:48+02:00 CHECKPOINT_READY step_300000 path_checkpoints/dfm5/L
2026-06-16T06:23:48+02:00 WORKERS 1985476 1985477 1985478 1985479 1985480 1985481 1985482 1985483
2026-06-16T06:23:49+02:00 START euroeval angry-tweets shard_0_of_20 gpu_0 attempt_1_of_6 batch_16 mem_free_before_72785
2026-06-16T06:23:58+02:00 START euroeval scala-da shard_1_of_20 gpu_1 attempt_1_of_6 batch_16 mem_free_before_75699
```

The post-eval watcher is running in tmux window `hrm-0:9`. It waits for
`FINAL_MERGE_END`, then logs the 300K headline averages under `avg/*` and
regenerates `docs/dfm5.md`:

```bash
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 300000:1.6565307709311847:logs/eval/dfm5_L_step300000_full_20260616_eurofirst_guard:logs/dfm_evals/dfm5_L_step300000_full_20260616_eurofirst_guard:logs/euroeval/dfm5_L_step300000_full_20260616_eurofirst_guard/step_300000 \
  2>&1 | tee logs/dfm5_L_step300000_headline_averages_20260616.log

python scripts/generate_dfm5_l_eval_comparison_report.py \
  2>&1 | tee logs/dfm5_L_step300000_generate_docs_20260616.log
```

The progress monitor is running in tmux window `hrm-0:10`:

```bash
python scripts/watch_eval_progress.py \
  --log-root logs/eval/dfm5_L_step300000_full_20260616_eurofirst_guard \
  --dfm-log-root logs/dfm_evals/dfm5_L_step300000_full_20260616_eurofirst_guard \
  --euroeval-log-root logs/euroeval/dfm5_L_step300000_full_20260616_eurofirst_guard \
  --ckpt-tag step_300000 \
  --interval 10
```

`scripts/generate_dfm5_l_eval_comparison_report.py` now includes a
`DFM5-L 300K` column sourced from the 2026-06-16 eval roots above. Until the
300K eval finishes, the generated docs table may show missing 300K values.
