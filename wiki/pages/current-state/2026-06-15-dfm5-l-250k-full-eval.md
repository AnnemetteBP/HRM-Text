---
type: Operational Record
title: 2026-06-15 DFM5 L 250K Full Eval
description: 'Part of Current State: 2026-06-15 DFM5 L 250K Full Eval.'
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
# 2026-06-15 DFM5 L 250K Full Eval

Part of [Current State](/pages/current-state.md).

Confidence: high for local checkpoint state, scheduler completion, merged
artifacts, W&B average sync, and regenerated Markdown report.

The DFM5 L `step_250000` checkpoint exists under `checkpoints/dfm5/L` with
`checkpoint_state_step_250000.json`, `fsdp2_step_250000/`, and eight carry
files. Its eval epoch x-value is:

```text
1.3831660928989149
```

The full eval was launched in tmux window `hrm-0:8` with EuroEval-first
ordering while DFM5 L training continued:

```bash
cd /work/dfm/HRM-Text
CKPT_PATH=checkpoints/dfm5/L \
CKPT_TAG=step_250000 \
EVAL_EPOCH=1.3831660928989149 \
GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm5_L_step250000_full_20260615_eurofirst_guard \
DFM_LOG_ROOT=logs/dfm_evals/dfm5_L_step250000_full_20260615_eurofirst_guard \
EUROEVAL_LOG_ROOT=logs/euroeval/dfm5_L_step250000_full_20260615_eurofirst_guard \
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
IFEVAL_BATCH_SIZE=32 \
EUROEVAL_BATCH_SIZE=16 \
MAX_RETRIES=5 \
EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py \
scripts/schedule_checkpoint_evals.sh \
  2>&1 | tee logs/dfm5_L_step250000_full_eval_20260615.log
```

Initial scheduler status:

```text
2026-06-15T18:49:55+02:00 QUEUED 188 jobs
2026-06-15T18:49:55+02:00 CHECKPOINT_READY step_250000 path_checkpoints/dfm5/L
2026-06-15T18:49:55+02:00 WORKERS 344695 344696 344697 344698 344700 344701 344702 344703
2026-06-15T18:49:55+02:00 START euroeval angry-tweets shard_0_of_20 gpu_0 attempt_1_of_6 batch_16 mem_free_before_72785
2026-06-15T18:50:05+02:00 START euroeval scala-da shard_1_of_20 gpu_1 attempt_1_of_6 batch_16 mem_free_before_75699
```

A post-eval watcher runs in tmux window `hrm-0:9`; it waits for
`FINAL_MERGE_END`, then logs headline averages to W&B and regenerates the
comparison table:

```bash
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 250000:1.3831660928989149:logs/eval/dfm5_L_step250000_full_20260615_eurofirst_guard:logs/dfm_evals/dfm5_L_step250000_full_20260615_eurofirst_guard:logs/euroeval/dfm5_L_step250000_full_20260615_eurofirst_guard/step_250000

python scripts/generate_dfm5_l_eval_comparison_report.py
```

The eval-progress monitor was updated on 2026-06-15 to show per-GPU active
task status plus total completed/active/queued/visible shards and an overall
ETA from the observed completion rate. The running monitor for this eval is in
tmux window `hrm-0:10`:

```bash
cd /work/dfm/HRM-Text
python scripts/watch_eval_progress.py \
  --log-root logs/eval/dfm5_L_step250000_full_20260615_eurofirst_guard \
  --dfm-log-root logs/dfm_evals/dfm5_L_step250000_full_20260615_eurofirst_guard \
  --euroeval-log-root logs/euroeval/dfm5_L_step250000_full_20260615_eurofirst_guard \
  --ckpt-tag step_250000 \
  --interval 10
```

Example fields now shown:

```text
jobs: completed=<n> active=<n> queued=<n> total=<n> ETA <...>
GPU0: euroeval:<task> shard x/y a/b elapsed <...> ETA <...> | <gpu memory/util>
```

Scheduler incremental merge update, 2026-06-15. Confidence: high for local
code inspection and `bash -n`; applies to scheduler processes launched after
this edit. `scripts/schedule_checkpoint_evals.sh` now defaults
`INCREMENTAL_MERGE=1`. After each successful shard, the worker checks whether
the full shard set for that standard or DFM task has completed. If yes, it
merges and syncs that task immediately under a merge lock, then writes a marker
file. The final merge phase skips marker-present tasks and only merges any
remaining complete task sets. EuroEval already merged/synced each one-dataset
group as its job finished.

Important active-run caveat: the already-running `step_250000` eval was
launched before this edit, so its Bash process has the old final-merge-only
standard/DFM functions loaded. Starting a sidecar incremental sync for the
current run would duplicate W&B points when the old final merge runs. For this
250K run, EuroEval remains incremental, while standard/DFM will sync in the
final merge. Future eval launches will use incremental standard/DFM merge by
default.

Completion update, 2026-06-15. Confidence: high for local scheduler status,
post-eval watcher log, and regenerated report artifact. The 250K eval reached
`FINAL_MERGE_END` at `2026-06-15T22:02:01+02:00`. The post-eval watcher then
logged the 250K headline averages to W&B run `DFM5/oti1lisg` under the new
`avg/*` prefix and regenerated the DFM5-L comparison Markdown table.

250K averages synced by
`logs/dfm5_L_step250000_headline_averages_20260615.log`:

```text
avg/danish=0.47466145094826273      count=18
avg/english=0.5565590118947327      count=15
avg/math_code=0.2507825859769966    count=4
avg/overall=0.427334349606664
avg/epoch=1.383166092898915
avg/train_step=250000
```

`scripts/generate_dfm5_l_eval_comparison_report.py` now includes the
`DFM5-L 250K` column, sourced from:

```text
logs/eval/dfm5_L_step250000_full_20260615_eurofirst_guard
logs/dfm_evals/dfm5_L_step250000_full_20260615_eurofirst_guard
logs/euroeval/dfm5_L_step250000_full_20260615_eurofirst_guard/step_250000
```

The regenerated Markdown report is:

```text
docs/dfm5.md
logs/reports/dfm5_l_eval_comparison_50k_250k_vs_original_ema_and_card.md
logs/reports/dfm5_l_eval_comparison_50k_100k_150k_vs_original_ema_and_card.md
```

`docs/dfm5.md` is the canonical human-facing copy. The two files under
`logs/reports/` are compatibility/report artifacts written with identical
content by `scripts/generate_dfm5_l_eval_comparison_report.py`.

Its section averages for `DFM5-L 250K` are Danish `47.5`, English `55.7`,
and Math & Code `25.1` in percent-style display.
