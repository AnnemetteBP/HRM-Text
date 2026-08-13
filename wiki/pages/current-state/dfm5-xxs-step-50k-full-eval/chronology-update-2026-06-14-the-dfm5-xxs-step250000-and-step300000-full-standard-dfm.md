---
type: Operational Record
title: 'Update 2026-06-14: The DFM5 XXS step250000 and step300000 full standard +
  DFM'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-14:
  The DFM5 XXS step250000 and step300000 full standard + DFM.'
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
# Update 2026-06-14: The DFM5 XXS step250000 and step300000 full standard + DFM

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-14. Confidence: high. The DFM5 XXS `step_250000` and
`step_300000` full standard + DFM + EuroEval campaign completed and synced
headline averages to W&B project `DFM5`, run id `2tv9u438`.

Checkpoint epoch-axis values:

```text
step_250000 -> 1.3804423091093208
step_300000 -> 1.6565307709311847
```

Launch wrapper:

```bash
cd /work/dfm/HRM-Text
ROOT_TS=20260613_step250_300_highbs
cat > /tmp/dfm5_step250_300_highbs_run_and_avg.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /work/dfm/HRM-Text
ROOT_TS=20260613_step250_300_highbs
CKPT_TAGS=step_250000,step_300000 \
EVAL_EPOCHS=1.3804423091093208,1.6565307709311847 \
CKPT_PATH=checkpoints/dfm5/XXS \
GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT_BASE=logs/eval/dfm5_XXS_step250_300_full_highbs_${ROOT_TS} \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm5_XXS_step250_300_full_highbs_${ROOT_TS} \
EUROEVAL_LOG_ROOT_BASE=logs/euroeval/dfm5_XXS_step250_300_full_highbs_${ROOT_TS} \
RUN_EUROEVAL=1 \
LITE_EVAL=0 \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=5 \
WANDB_SYNC=1 \
WANDB_PROJECT=DFM5 \
WANDB_RUN_ID=2tv9u438 \
WANDB_RUN_NAME=dfm5-XXS \
MODEL_PREFIX=hrm-dfm5-XXS \
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
EUROEVAL_BATCH_TIMEOUT_MS=25 \
EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py \
scripts/schedule_multiple_checkpoint_evals.sh 2>&1 | tee logs/dfm5_xxs_eval_step250_300_highbs_${ROOT_TS}.log
python scripts/log_dfm5_headline_averages.py \
  --item '250000:1.3804423091093208:logs/eval/dfm5_XXS_step250_300_full_highbs_20260613_step250_300_highbs/step_250000:logs/dfm_evals/dfm5_XXS_step250_300_full_highbs_20260613_step250_300_highbs/step_250000:logs/euroeval/dfm5_XXS_step250_300_full_highbs_20260613_step250_300_highbs/step_250000' \
  --item '300000:1.6565307709311847:logs/eval/dfm5_XXS_step250_300_full_highbs_20260613_step250_300_highbs/step_300000:logs/dfm_evals/dfm5_XXS_step250_300_full_highbs_20260613_step250_300_highbs/step_300000:logs/euroeval/dfm5_XXS_step250_300_full_highbs_20260613_step250_300_highbs/step_300000' \
  2>&1 | tee logs/wandb_log_dfm5_headline_averages_no_valeu_250k_300k_20260613.log
SH
chmod +x /tmp/dfm5_step250_300_highbs_run_and_avg.sh
tmux new-session -d -s dfm5_xxs_eval_250k_300k_highbs /tmp/dfm5_step250_300_highbs_run_and_avg.sh
```

Completion evidence:

```text
2026-06-14T00:45:20+02:00 FINAL_MERGE_START step_250000
2026-06-14T00:46:36+02:00 FINAL_MERGE_END step_250000 status_0
2026-06-14T00:46:36+02:00 FINAL_MERGE_START step_300000
2026-06-14T00:47:51+02:00 FINAL_MERGE_END step_300000 status_0
2026-06-14T00:47:51+02:00 DONE status_0
```

No nonzero `END` statuses were found in the scheduler status file. The W&B
client confirmed sync to `https://wandb.ai/peter-sk-sdu/DFM5/runs/2tv9u438`.

Current no-VaLEU headline-average series:

```text
step_50000  epoch=0.276088            danish=0.153509 english=0.203071 math_code=0.012262 overall=0.122947
step_100000 epoch=0.5521769236437283  danish=0.156194 english=0.230057 math_code=0.017042 overall=0.134431
step_150000 epoch=0.8282653854655924  danish=0.179091 english=0.220028 math_code=0.012290 overall=0.137136
step_200000 epoch=1.1043538472874566  danish=0.148592 english=0.237147 math_code=0.010827 overall=0.132189
step_250000 epoch=1.3804423091093208  danish=0.188638 english=0.225618 math_code=0.013740 overall=0.142665
step_300000 epoch=1.6565307709311847  danish=0.159041 english=0.232286 math_code=0.014552 overall=0.135293
```

Interpretation as of 300K: this is not yet strong evidence of a pure XXS
capacity ceiling. English and Math/Code are mostly flat/noisy and Math/Code is
near zero, which is consistent with an XXS-capacity and/or training-objective
limit. Danish has clear upward spikes at 150K and 250K but regresses at 200K
and 300K, so the trend still looks noisy rather than converged. More evidence
from later checkpoints is needed before calling a hard capacity wall, but the
current results suggest XXS is already too small for robust math/code and
general English benchmark gains.
