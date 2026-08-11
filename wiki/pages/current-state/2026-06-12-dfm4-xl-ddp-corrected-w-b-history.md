---
type: Operational Record
title: 2026-06-12 DFM4 XL-DDP Corrected W&B History
description: 'Part of Current State: 2026-06-12 DFM4 XL-DDP Corrected W&B History.'
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
# 2026-06-12 DFM4 XL-DDP Corrected W&B History

Part of [Current State](/pages/current-state.md).

Confidence: high for local W&B datastore inspection, script output, and W&B API
summary readback.

The original `dfm4xlddpclean` W&B run was made unsafe for continued logging
when full epoch-2 EMA aliases were backfilled at `_step=900000`. The training
resume from `ephemeral_step_865000` then produced valid training locally, but
W&B core ignored rows below its internal current step:

```text
handler: ignoring partial history record, step=865530, current=900001
```

The checkpoint itself was valid and should be resumed with the ephemeral tag,
not the regular-step tag:

```text
resume_checkpoint_tag=ephemeral_step_865000
```

`scripts/clone_dfm4_xl_ddp_clean_wandb.py` now supports a corrected-history
replay. It reads local `.wandb` datastores for `dfm4xlddpclean`, drops the
artificial `_step=900000` row, drops old full-eval alias rows, and re-adds full
EMA `eval/*` and `dfm_eval/*` aliases at the real checkpoint steps:

```text
epoch_1 -> step 367247
epoch_2 -> step 734484
```

The script also supports `--repair-lite-history`. In that mode it drops old
`lite_eval_noema/*`, `lite_dfm_eval_noema/*`, `lite_eval_ema/*`, and
`lite_dfm_eval_ema/*` rows from the source history and rebuilds them from local
merged lite eval artifacts at the actual checkpoint steps. This avoids plotting
lite evals at sync-time W&B steps.

Corrected run created on 2026-06-12:

```text
project: Original Plus Mixed Danish Instruction Rich L
run id:  dfm4xlddpcleanfixed2
name:    dfm4-XL-ddp clean corrected history v2
url:     https://wandb.ai/peter-sk-sdu/Original%20Plus%20Mixed%20Danish%20Instruction%20Rich%20L/runs/dfm4xlddpcleanfixed2
```

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/clone_dfm4_xl_ddp_clean_wandb.py \
  --repair-lite-history \
  --target-run-id dfm4xlddpcleanfixed2 \
  --target-run-name 'dfm4-XL-ddp clean corrected history v2' \
  2>&1 | tee logs/wandb_clone_dfm4_xl_ddp_clean_fixed2_20260612.log
```

Replay summary:

```text
rows replayed: 173158
max step: 865110
dropped old lite rows: 1066
repaired lite checkpoint rows: 34
contains step 900000: false
train rows after 865000: 23
```

Local readback confirmed `lite_eval_*` and `lite_dfm_eval_*` rows at checkpoint
steps such as `50000`, `100000`, `300000`, `367247`, `700000`, `734484`, and
`750000`, with no row at `900000`. W&B API summary readback showed:

```text
clean_history/max_step = 865110
clean_history/replayed_rows = 173158
clean_history/dropped_lite_eval_rows = 1066
clean_history/lite_repair_row_count = 34
train/loss = 0.985303521156311
eval/epoch = 2
dfm_eval/epoch = 2
lite_eval_noema/epoch = 2.0478039350600414
lite_eval_ema/epoch = 2.0478039350600414
```

Use `dfm4xlddpcleanfixed2` as the corrected comparison/backfill run. Do not
continue training into `dfm4xlddpclean`; its local/remote W&B history contains
the bad high-step alias state.

Additional coverage check on 2026-06-12: the corrected local W&B datastore has
EMA and no-EMA lite rows for every complete local 50K checkpoint from
`step_50000` through `step_750000`, plus `epoch_1` at step `367247` and
`epoch_2` at step `734484`. Each of those rows contains all four epoch keys:
`lite_eval_noema/epoch`, `lite_dfm_eval_noema/epoch`,
`lite_eval_ema/epoch`, and `lite_dfm_eval_ema/epoch`. Local merged lite eval
artifacts were not found for `step_800000`, `step_850000`, or
`ephemeral_step_865000`, so those points cannot be backfilled without running
and merging those lite evals first. Confidence: high for local artifact and
W&B-datastore inspection.
