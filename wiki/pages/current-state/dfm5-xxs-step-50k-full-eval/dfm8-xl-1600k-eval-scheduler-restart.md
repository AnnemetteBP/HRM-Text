---
type: Operational Record
title: DFM8 XL 1600K+ Eval Scheduler Restart
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 XL 1600K+ Eval Scheduler Restart.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 XL 1600K+ Eval Scheduler Restart

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-20. Confidence: high from local scheduler/tmux status.

The existing DFM8 XL scheduler plan already contained the next checkpoint
subgraphs for `step_1600000`, `step_1650000`, `step_1700000`, and
`step_1750000`, with the judged-task best-practice exception preserved:
`generative_talemaader` uses batch `16`, `max_connections=16`,
`unsloth/gemma-4-E4B-it`, and HRM checkpoint
`vllm_gpu_memory_utilization=0.18`.

The run had no live scheduler process and four stale `running` wait rows. It
was restarted from the `hrm` conda env after:

```bash
python -m eval_scheduler clear-stop \
  --plan-dir logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255

python -m eval_scheduler plan reset-running \
  --plan-dir logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255
```

The active tmux windows in session `hrm-0` are:

```text
5: dfm8eval  # scheduler runner
6: dfm8mon   # rich monitor, 30s refresh
```

After restart, status was:

```text
pending=860 running=4 done=1512 failed=0 skipped=11
```

The four active jobs are checkpoint waits for `1600K`, `1650K`, `1700K`, and
`1750K`. At restart time, training had only reached
`ephemeral_step_1579500`, so the regular `step_1600000` checkpoint did not yet
exist.
