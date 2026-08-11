---
type: Software Reference
title: '`scripts/run_dfm4_xl_ddp_lite_eval_700k.sh`'
description: 'Part of Script Entities: `scripts/run_dfm4_xl_ddp_lite_eval_700k.sh`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/run_dfm4_xl_ddp_lite_eval_700k.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-09. Confidence: high for local shell validation and launch.

Runs the DFM4 XL-DDP `step_700000` lite eval pair:

- no-EMA first, with `EVAL_PREFIX=lite_eval_noema` and
  `DFM_EVAL_PREFIX=lite_dfm_eval_noema`;
- EMA second, with `EVAL_PREFIX=lite_eval_ema` and
  `DFM_EVAL_PREFIX=lite_dfm_eval_ema`;
- syncs both to W&B run `dfm4xlddpclean` in project
  `Original Plus Mixed Danish Instruction Rich L`;
- uses all eight GPUs through `scripts/schedule_multiple_checkpoint_evals.sh`;
- uses the fractional epoch x-axis value `1.9112836727227056`.

Launched in tmux session `dfm4_lite_eval_700k`:

```bash
cd /work/dfm/HRM-Text
scripts/run_dfm4_xl_ddp_lite_eval_700k.sh \
  2>&1 | tee logs/dfm4_lite_eval_700k_20260609.log
```
