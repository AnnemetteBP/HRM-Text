---
type: Operational Record
title: DFM L lite no-EMA prefix relog (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L lite no-EMA
  prefix relog (2026-06-03).'
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
# DFM L lite no-EMA prefix relog (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L lite no-EMA prefix relog, 2026-06-03. Confidence: high.

The completed DFM L lite metrics from
`logs/eval/dfm_L_lite_all_checkpoints_20260603T181930` and
`logs/dfm_evals/dfm_L_lite_all_checkpoints_20260603T181930` were resynced to
W&B project `Original Plus Mixed Danish Instruction Rich L`, run id
`dfm-l-resume-epoch3`, under `lite_eval_noema/*` and
`lite_dfm_eval_noema/*`. This relog did not rerun inference; it read the stored
`merged_metrics.json` and `merged_ifeval_da_metrics.json` files. W&B reported
syncing history steps `132079-132094`. For each of the eight checkpoints
(`epoch_1`, `epoch_2`, `epoch_3`, `epoch_4`, `step_500000`, `step_550000`,
`step_600000`, `step_650000`), the relog wrote `195` `lite_eval_noema` metrics
and `74` `lite_dfm_eval_noema` metrics, preserving the stored fractional epoch
values for step checkpoints.
