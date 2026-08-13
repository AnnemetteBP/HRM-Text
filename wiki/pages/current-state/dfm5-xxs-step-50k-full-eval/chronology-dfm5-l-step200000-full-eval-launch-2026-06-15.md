---
type: Operational Record
title: DFM5 L step200000 full eval launch (2026-06-15)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L step200000
  full eval launch (2026-06-15).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM5 L step200000 full eval launch (2026-06-15)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L `step_200000` full eval launch, 2026-06-15. Confidence: high for local
checkpoint state, launch command, and scheduler logs; medium for final sync
until the post-eval watcher completes.

The `step_200000` checkpoint exists under `checkpoints/dfm5/L` with
`checkpoint_state_step_200000.json`, `fsdp2_step_200000/`, and eight
`carry_step_200000.*.pt` files. Its eval epoch x-value is:

```text
1.1043538472874566
```

The full eval was launched in tmux window `hrm-0:7` with EuroEval-first
ordering while DFM5 L training continued:

```bash
cd /work/dfm/HRM-Text
CKPT_PATH=checkpoints/dfm5/L \
CKPT_TAG=step_200000 \
EVAL_EPOCH=1.1043538472874566 \
GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm5_L_step200000_full_20260615_eurofirst_guard \
DFM_LOG_ROOT=logs/dfm_evals/dfm5_L_step200000_full_20260615_eurofirst_guard \
EUROEVAL_LOG_ROOT=logs/euroeval/dfm5_L_step200000_full_20260615_eurofirst_guard \
WANDB_SYNC=1 \
WANDB_PROJECT=DFM5 \
WANDB_RUN_ID=oti1lisg \
WANDB_RUN_NAME=dfm5-L \
MODEL_PREFIX=hrm-dfm5-L \
RUN_EUROEVAL=1 \
QUEUE_ORDER=euroeval_first \
STANDARD_BATCH_SIZE=128 \
STANDARD_BATCH_SIZE_GSM8K=64 \
STANDARD_BATCH_SIZE_MATH=64 \
STANDARD_BATCH_SIZE_DROP=32 \
DFM_BATCH_SIZE=32 \
DFM_BATCH_SIZE_GOVREPORT=32 \
DFM_BATCH_SIZE_NORDJYLLANDNEWS=32 \
DFM_BATCH_SIZE_WMT24PP_EN_DA=32 \
DFM_BATCH_SIZE_HUMANEVAL=16 \
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16 \
IFEVAL_BATCH_SIZE=32 \
EUROEVAL_BATCH_SIZE=16 \
MAX_RETRIES=5 \
EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py \
scripts/schedule_checkpoint_evals.sh \
  2>&1 | tee logs/dfm5_L_step200000_full_eval_20260615.log
```

Monitor window: `hrm-0:8`. A post-eval watcher runs in `hrm-0:10`; it waits
for `FINAL_MERGE_END`, then logs the 200K headline averages to W&B and
regenerates the comparison table:

```bash
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 200000:1.1043538472874566:logs/eval/dfm5_L_step200000_full_20260615_eurofirst_guard:logs/dfm_evals/dfm5_L_step200000_full_20260615_eurofirst_guard:logs/euroeval/dfm5_L_step200000_full_20260615_eurofirst_guard/step_200000

python scripts/generate_dfm5_l_eval_comparison_report.py
```

`scripts/generate_dfm5_l_eval_comparison_report.py` was added to regenerate
the Markdown comparison report from local artifacts. It includes DFM5-L
50K/100K/150K/200K, original Sapient L e1-e4 EMA/default, and README model-card
L/XL standard values. The script normalizes local fraction-style metrics to the
report's percent-style display and excludes VaLEU rows from section averages.
