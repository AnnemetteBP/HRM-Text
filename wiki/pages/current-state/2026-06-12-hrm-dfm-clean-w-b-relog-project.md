---
type: Operational Record
title: 2026-06-12 HRM DFM Clean W&B Relog Project
description: 'Part of Current State: 2026-06-12 HRM DFM Clean W&B Relog Project.'
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
# 2026-06-12 HRM DFM Clean W&B Relog Project

Part of [Current State](/pages/current-state.md).

Confidence: high for local script execution, W&B sync output, local run
summaries, and live manifest; medium for remote UI state until manually
inspected in the browser.

Created `scripts/relog_hrm_dfm_project.py` to relog local merged eval artifacts
into a new W&B project named `HRM DFM`. The script normalizes all source eval
prefixes (`eval`, `dfm_eval`, `lite_eval`, `lite_dfm_eval`, and EMA/no-EMA
variants) to `eval/*`, logs rows at the exact checkpoint training step via
W&B `_step`, and also logs `eval/train_step`, `eval/epoch`, and
`eval/checkpoint`.

Executed:

```bash
cd /work/dfm/HRM-Text
python scripts/relog_hrm_dfm_project.py \
  --manifest logs/wandb_relog_hrm_dfm_manifest_live_20260612.json \
  2>&1 | tee logs/wandb_relog_hrm_dfm_live_20260612.log
```

The project URL reported by W&B is:

```text
https://wandb.ai/peter-sk-sdu/HRM%20DFM
```

Created/synced run IDs:

```text
original-sapient-L-full-ema
original-sapient-L-lite-ema
original-sapient-L-lite-noema
original-plus-mixed-L-full-ema
original-plus-mixed-L-lite-ema
dfm-L-full-ema
dfm-L-lite-ema
dfm4-XL-ddp-full-ema
dfm4-XL-ddp-full-noema
dfm4-XL-ddp-lite-ema
dfm4-XL-ddp-lite-noema
```

Local W&B summaries confirm the last logged train steps:

```text
original-sapient-L-*:       325928
original-plus-mixed-L-*:    645263
dfm-L-*:                    658771
dfm4-XL-ddp-full-*:         734484
dfm4-XL-ddp-lite-*:         750000
```

Known caveats from the live manifest:

- `original-plus-mixed-L-full-ema` epoch 1 has only `3` recovered metrics
  from the local full-eval artifacts; epoch 2 has `202`, epoch 3 has `205`,
  and epoch 4 has `221`. The separate
  `original-plus-mixed-L-lite-ema` run has complete `269`-metric rows for all
  four epochs.
- `dfm4-XL-ddp-lite-noema` step `600000` has `221` metrics; the other logged
  DFM4 lite rows have `269`.

The live manifest is the audit source for exactly which checkpoints and metric
counts were relogged:

```text
logs/wandb_relog_hrm_dfm_manifest_live_20260612.json
```
