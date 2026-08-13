---
type: Operational Record
title: 2026-06-16 Eval Scheduler EuroEval Monitor Progress Fix
description: 'Part of Current State: 2026-06-16 Eval Scheduler EuroEval Monitor Progress
  Fix.'
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
# 2026-06-16 Eval Scheduler EuroEval Monitor Progress Fix

Part of [Current State](/pages/current-state.md).

Confidence: high for local code inspection and one-shot monitor verification.

`eval_scheduler/eval_scheduler/monitor.py` now reports EuroEval progress more
robustly. The monitor still prefers EuroEval's own tqdm sample bars
(`samples done/total`) and ETA calculation, but no longer falls back to the
unhelpful `progress unknown` during normal startup states. It now reports
`loading model`, `benchmark setup`, `starting`, or `requests N failed M` when
sample bars are not yet available. Server request counts are only an activity
signal because one EuroEval sample can issue multiple API calls; they are not
used as sample-count fractions.

Verified command:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_350k_400k_full_20260616 \
  --gpus 0,1 \
  --once
```

The check showed active EuroEval jobs with `samples done/total` and ETA, e.g.
`samples 57/157 ETA 4m36s` and `samples 141/157 ETA 17s`.
