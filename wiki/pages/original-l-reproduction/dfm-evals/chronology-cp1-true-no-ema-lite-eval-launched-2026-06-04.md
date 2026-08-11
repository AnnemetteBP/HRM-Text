---
type: Operational Record
title: CP1 true no-EMA lite eval, launched (2026-06-04)
description: 'Chronological record from dfm-evals: CP1 true no-EMA lite eval, launched
  (2026-06-04).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# CP1 true no-EMA lite eval, launched (2026-06-04)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

CP1 true no-EMA lite eval, launched 2026-06-04. Confidence: high.

A real original Sapient L CP1 no-EMA lite eval was launched local-only in tmux
window `hrm:8` (`origL-cp1-noema`), with monitor in `hrm:9`
(`origL-cp1-mon`). It uses `NO_EMA=1`, `WANDB_SYNC=0`, and the distinct
prefixes `lite_eval_noema_real/*` and `lite_dfm_eval_noema_real/*`. Logs:

- `logs/eval/original_sapient_L_cp1_noema_lite_real_20260604T184821`
- `logs/dfm_evals/original_sapient_L_cp1_noema_lite_real_20260604T184821`

The CP1 no-EMA lite eval completed with `DONE status_0`. Comparing CP1 default
EMA vs true no-EMA across 19 inspected metrics: no-EMA was better on 4, EMA was
better on 12, and 3 were ties. The mean `noEMA - EMA` delta was `-0.0175`, so
EMA was already beneficial at CP1, but much less decisively than at CP4.
Representative values:

- Standard evals: ARC `0.4582` vs `0.4394`, BoolQ `0.7260` vs `0.7419` (no-EMA
  better), DROP F1 `0.5810` vs `0.4886`, GSM8k `0.1697` vs `0.1576`,
  HellaSwag `0.3318` vs `0.3145`, MATH `0.2658` vs `0.2025`, MMLU `0.4351` vs
  `0.3905`, Winogrande `0.5422` vs `0.5099`.
- DFM evals: DALA macro-F1 `0.0382` vs `0.0000`, WMT chrf++ `0.2030` vs
  `0.1715`, MultiWiki F1 `0.0087` vs `0.0186` (no-EMA better), NordjyllandNews
  ROUGE-2 `0.0487` vs `0.0581` (no-EMA better), IFEval-DA final acc `0.2279`
  vs `0.2049`, Talemaader `0.0000` vs `0.0099` (no-EMA better).

```bash
cd /work/dfm/HRM-Text
CKPT_TAGS=epoch_4 \
EVAL_EPOCHS=4 \
CKPT_PATH=checkpoints/original_sapient/L \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
QUEUE_ORDER=heavy_first \
MAX_RETRIES=3 \
NO_EMA=1 \
WANDB_SYNC=0 \
EVAL_PREFIX=lite_eval_noema_real \
DFM_EVAL_PREFIX=lite_dfm_eval_noema_real \
MODEL_PREFIX=hrm-original-sapient-L-noema \
LOG_ROOT_BASE=logs/eval/original_sapient_L_cp4_noema_lite_real_20260604T181038 \
DFM_LOG_ROOT_BASE=logs/dfm_evals/original_sapient_L_cp4_noema_lite_real_20260604T181038 \
bash scripts/schedule_multiple_checkpoint_evals.sh
```
