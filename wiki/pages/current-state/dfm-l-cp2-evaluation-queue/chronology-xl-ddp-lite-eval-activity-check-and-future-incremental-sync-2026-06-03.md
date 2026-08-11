---
type: Operational Record
title: XL DDP lite eval activity check and future incremental sync (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: XL DDP lite eval
  activity check and future incremental sync (2026-06-03).'
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
# XL DDP lite eval activity check and future incremental sync (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

XL DDP lite eval activity check and future incremental sync, 2026-06-03.
Confidence: high.

At `07:30 CEST`, the active tmux run `hrm-1:xl-lite-eval` showed all eight
GPUs at `100%` utilization, with the monitor reporting `started=16`,
`finished=8`, `active=8`, and `queued=22`. Completed step-50000 lite jobs at
that snapshot included `ARC`, `BoolQ`, `HellaSwag`, `MMLU`, `Winogrande`,
`govreport`, `generative_talemaader`, and `nordjyllandnews`. Active jobs were
`dfm_ifeval` shard 0, `MATH`, `GSM8k`, `DROP`, `gec_dala`, `humaneval`,
`wmt24pp_en_da`, and `multi_wiki_qa`. Process inspection confirmed matching
`evaluation.main`, `dfm-evals`, and `hrm_openai_server.py` processes. The
current running scheduler was launched before the incremental merge/sync patch
below, so it will not automatically sync each completed task unless manually
merged during the run. Confidence: high.

Future `scripts/schedule_multiple_checkpoint_evals.sh` launches now perform
incremental merge and W&B sync per task. After every successful shard job,
`maybe_merge_task()` checks whether all expected shards for that task and
checkpoint are ready; if yes, it immediately runs the relevant merge script with
the configured prefix and W&B project/run:

- standard evals: `scripts/merge_standard_eval_shards.py`
- IFEval-DA: `scripts/merge_ifeval_da_shards.py`
- other DFM evals: `scripts/merge_dfm_eval_shards.py`

The implementation uses per-task lock and marker files under the checkpoint log
root to avoid duplicate merges when several workers finish near the same time.
In `LITE_EVAL=1`, readiness means the configured lite shard is done; in full
mode, readiness means all configured shards for that task are done. Final merge
at scheduler end remains in place as a second pass. Confidence: high.

Monitor update on 2026-06-03. Confidence: high.
`scripts/watch_multi_checkpoint_eval_progress.py` now parses standard eval tqdm
lines from each shard log and appends per-shard sample progress such as
`progress 58/79` for MATH, `progress 60/165` for GSM8k, and `progress
109/2384` for DROP. DFM tasks report HTTP completion counts from the local
OpenAI server logs. The monitor now also infers DFM shard totals from Inspect
`inspect/logs.json` when available and from known static totals for
`dfm_evals/ifeval-da` (`541` total) and `dfm_evals/piqa` (`108` total). After
the update, active lines showed `dfm_ifeval` as `completion 6/17`,
`humaneval` as `completion 15/41`, and `piqa` as `completion 16/108`.
The current eval batch-size defaults in `scripts/schedule_checkpoint_evals.sh`
are `STANDARD_BATCH_SIZE=8`, `DFM_BATCH_SIZE=8`, and `IFEVAL_BATCH_SIZE=1`.
