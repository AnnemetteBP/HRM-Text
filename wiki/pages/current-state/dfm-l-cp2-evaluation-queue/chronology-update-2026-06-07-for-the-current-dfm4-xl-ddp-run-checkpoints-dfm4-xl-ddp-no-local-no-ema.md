---
type: Operational Record
title: 'Update 2026-06-07: For the current DFM4 XL-DDP run (checkpoints/dfm4/XL-ddp),
  no local no-EMA'
description: 'Chronological record from DFM L CP2 Evaluation Queue: Update 2026-06-07:
  For the current DFM4 XL-DDP run (checkpoints/dfm4/XL-ddp), no local no-EMA.'
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
# Update 2026-06-07: For the current DFM4 XL-DDP run (checkpoints/dfm4/XL-ddp), no local no-EMA

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Update, 2026-06-07. Confidence: high. For the current DFM4 XL-DDP run
(`checkpoints/dfm4/XL-ddp`), no local no-EMA lite-eval roots exist for
`step_500000` or `step_550000` as of this check. Local `step_500000` and
`step_550000` lite-eval directories found under
`logs/eval/dfm_L_lite_all_checkpoints_20260603T181930` belong to the older
DFM L run, not to DFM4 XL-DDP. The DFM4 XL-DDP `step_450000` no-EMA lite eval
is complete locally and merged under:

```text
logs/eval/dfm4_XL_ddp_noema_lite_450k_20260606_tmux
logs/dfm_evals/dfm4_XL_ddp_noema_lite_450k_20260606_tmux
```
