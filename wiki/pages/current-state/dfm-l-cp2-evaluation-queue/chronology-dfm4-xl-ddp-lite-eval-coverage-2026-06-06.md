---
type: Operational Record
title: DFM4 XL-DDP lite eval coverage (2026-06-06)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP lite
  eval coverage (2026-06-06).'
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
# DFM4 XL-DDP lite eval coverage (2026-06-06)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP lite eval coverage, 2026-06-06. Confidence: high for local merged
artifacts and path naming; medium for older unlabelled `dfm4_XL_ddp_lite_probe`
being EMA because that follows scheduler defaults rather than an explicit path
marker.

Local merged eval artifacts show EMA lite evals for:

- `step_50000` and `step_100000` under `logs/eval/dfm4_XL_ddp_lite_probe` and
  `logs/dfm_evals/dfm4_XL_ddp_lite_probe`; these paths are unlabelled but the
  scheduler default is EMA unless `NO_EMA=1`.
- `step_200000` under
  `logs/eval/dfm4_XL_ddp_ema_lite_probe_20260604T064428_200k` and matching
  `logs/dfm_evals/...`.
- `step_250000` under
  `logs/eval/dfm4_XL_ddp_ema_lite_probe_20260604_250k` and matching
  `logs/dfm_evals/...`.

Explicit no-EMA lite eval artifacts exist for `step_50000`, `step_100000`,
`step_150000`, `step_200000`, `step_250000`, `step_300000`, `step_350000`,
`step_400000`, and `step_450000`.
