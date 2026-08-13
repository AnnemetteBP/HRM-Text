---
type: Operational Record
title: 'Update 2026-06-07: The remaining no-EMA step450000 standard tasks that had
  finished after'
description: 'Chronological record from DFM L CP2 Evaluation Queue: Update 2026-06-07:
  The remaining no-EMA step450000 standard tasks that had finished after.'
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
# Update 2026-06-07: The remaining no-EMA step450000 standard tasks that had finished after

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Update, 2026-06-07. Confidence: high. The remaining no-EMA `step_450000`
standard tasks that had finished after the first final merge were manually
merged and synced to W&B run `dfm4xlddpclean` under `lite_eval_noema/*`:
`MMLU`, `ARC`, `HellaSwag`, `Winogrande`, and `MATH`. The local merged files
are under:

```text
logs/eval/dfm4_XL_ddp_noema_lite_450k_20260606_tmux/step_450000/standard_shards/*/merged_metrics.json
```

As of 2026-06-07 09:15 CEST, there are no local `step_450000` EMA lite-eval
artifacts and no active `step_450000` EMA eval processes. The active EMA eval
work at that time is for `step_400000`, not `step_450000`.
