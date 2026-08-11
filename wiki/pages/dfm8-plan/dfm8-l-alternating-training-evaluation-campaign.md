---
type: Plan Record
title: DFM8 L Alternating Training/Evaluation Campaign
description: 'Part of DFM8 Plan: DFM8 L Alternating Training/Evaluation Campaign.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# DFM8 L Alternating Training/Evaluation Campaign

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-08-01. Confidence: high from the atomically generated plan,
dependency audit, live scheduler state, and GPU telemetry.

The active campaign is:

```text
logs/scheduler/dfm8_L_campaign_150k_epoch1_20260801
```

It resumes from `ephemeral_step_101000`, forces regular checkpoints and full
evaluations every 50K steps at 150K, 200K, and 250K, and then trains the final
short segment to the one-epoch endpoint at step 268857. Each evaluation graph
has 188 GPU rows spanning standard, DFM, 32-shard DFM IFEval-DA, and EuroEval
tasks. A terminal eval barrier and evaluator teardown precede each next training
segment, while merges, W&B synchronization, averages, and reports can finish
independently and therefore cannot unnecessarily hold the training GPUs.

Training segments and exact sources are:

| Segment | Resume source | Forced target |
| --- | --- | ---: |
| `101000 -> 150000` | `ephemeral_step_101000` | `step_150000` |
| `150000 -> 200000` | `step_150000` | `step_200000` |
| `200000 -> 250000` | `step_200000` | `step_250000` |
| `250000 -> 268857` | `step_250000` | `step_268857` |

The production eval configuration uses the previous successful DFM8 L vLLM
path: EuroEval-first ordering, standard/DFM/IFEval/EuroEval initial batches of
128/64/64/64, six total attempts, Gemma 4 native chat template, vLLM utilization
0.9, and 178000 MiB effective-free-memory gates. Judged tasks use
`unsloth/gemma-4-E4B-it`, batch/concurrency 32, and vLLM utilization 0.65.
Persistent vLLM leases are enabled.

The campaign can be recreated by
`scripts/setup_dfm8_l_campaign.sh`. Its live tmux layout is:

| Window | Name | Purpose |
| ---: | --- | --- |
| 4 | `training` | follows the current scheduler-managed training log |
| 5 | `scheduler` | campaign scheduler with persistent vLLM |
| 6 | `monitor` | Rich scheduler monitor at 30-second refresh |

The `training` window uses `scripts/follow_dfm8_l_training.sh`, which
automatically switches to the newest segment log. At campaign launch,
`campaign-train-150000` successfully claimed GPUs 0-7 and resumed the complete
101000 checkpoint.

Monitor update, 2026-08-01. Confidence: high from focused tests and the live
150K training segment. The scheduler monitor now parses `train_until_step`
tqdm output, displays `current_step/forced_target` and segment-relative percent,
and computes ETA from the latest reported `it/s` or `s/it` rate. This avoids the
previous `ETA unknown` and avoids incorrectly extrapolating from the full-epoch
tqdm denominator. The Rich monitor in `hrm-0:6` was restarted on the updated
code without interrupting scheduler or training processes.

Managed-judge stall and fix, 2026-08-02. Confidence: high from process/socket
inspection, server logs, and successful live retries. Two step-200000
`generative_talemaader` shards assigned to GPUs 6 and 7 stalled for about 3.6
hours because the old judge formula generated ports 65606 and 65700. Uvicorn
silently listened on wrapped ports 70 and 164, while the OpenAI client rejected
the advertised out-of-range URLs; both jobs therefore remained at zero samples
with idle GPUs. `eval_scheduler.runtime.managed_judge_port` now folds all
deterministic GPU/shard offsets into ports 20000-59999. A regression test checks
validity and uniqueness across eight GPUs and eight shards. The scheduler was
stopped cleanly, the two malformed attempts were terminated, all persistent
servers were released, and only those two rows retried at valid ports 45606 and
45700. The retries immediately produced judge requests and active GPU load.

Tmux recovery note, 2026-08-02. Confidence: high from live tmux/process
inspection. When the old scheduler window exited during the managed-judge
restart, tmux renumbered window 6 to 5; respawning target 5 then replaced the
monitor while leaving the scheduler alive under the stale `monitor` name. The
layout was restored without interrupting training: `hrm-0:5` is the active
`scheduler`, and a fresh Rich `monitor` runs in `hrm-0:6`.
