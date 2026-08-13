---
type: Operational Record
title: DFM5 L step50000 full eval completion (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L step50000
  full eval completion (2026-06-14).'
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
# DFM5 L step50000 full eval completion (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L `step_50000` full eval completion, 2026-06-14. Confidence: high for
local scheduler logs, merged artifacts, and W&B sync output. The full
standard+DFM+EuroEval run for `checkpoints/dfm5/L` `step_50000` used log roots:

```text
logs/eval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full
logs/dfm_evals/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full
logs/euroeval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full
```

The scheduler recorded `188` eval attempts, all with `status=0` and `oom=0`.
Its final status lines were `FINAL_MERGE_START` at `16:54:09+02:00` and
`FINAL_MERGE_END` at `16:55:25+02:00`. Merged metrics were written for all
standard evals, all DFM evals including IFEval-DA, and all 20 one-dataset
EuroEval groups. The merged metrics were synced to W&B project `DFM5`, run
`oti1lisg` (`dfm5-L`). The derived headline averages were then logged with:

```bash
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 50000:0.27608846182186414:logs/eval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full:logs/dfm_evals/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full:logs/euroeval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full/step_50000
```

W&B sync output confirmed the following summary values:

```text
headline_avg/danish      0.28379788656320293  count=18
headline_avg/english     0.33401347487407673  count=15
headline_avg/math_code   0.06487754537306532  count=4
headline_avg/overall     0.22756296893678166
headline_avg/epoch       0.27608846182186414
headline_avg/train_step  50000
```
