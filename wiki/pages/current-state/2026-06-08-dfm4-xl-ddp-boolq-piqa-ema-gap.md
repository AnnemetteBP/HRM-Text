---
type: Operational Record
title: 2026-06-08 DFM4 XL-DDP BoolQ/PIQA EMA Gap
description: 'Part of Current State: 2026-06-08 DFM4 XL-DDP BoolQ/PIQA EMA Gap.'
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
# 2026-06-08 DFM4 XL-DDP BoolQ/PIQA EMA Gap

Part of [Current State](/pages/current-state.md).

Confidence: high for local merged eval artifacts.

Comparing lite no-EMA and EMA metrics from local `merged_metrics.json` files
shows that the recent BoolQ and Danish PIQA gaps are not closing. BoolQ no-EMA
continues improving while EMA stays around `0.44-0.45` after `step_300000`;
the absolute gap grows from `0.1110` at `step_450000` to `0.1459` at
`step_500000`, `0.1618` at `step_550000`, `0.2226` at `step_600000`, and
`0.2764` at `step_650000`.

Danish PIQA is noisier, but EMA is almost flat around `0.1481` while no-EMA
varies widely; the gap is `0.2593` at `step_450000`, `0.2963` at
`step_500000`, `0.0185` at `step_550000`, `0.1481` at `step_600000`, and
`0.3889` at `step_650000`. Interpretation: for BoolQ and PIQA specifically,
EMA is not catching up yet; the recent apparent trend favors no-EMA.
