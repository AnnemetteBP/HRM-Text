---
type: Operational Record
title: 'On 2026-06-15: W&B scanhistory verified exactly four avg/ rows'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: On 2026-06-15:
  W&B scanhistory verified exactly four avg/ rows.'
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
# On 2026-06-15: W&B scanhistory verified exactly four avg/ rows

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

On 2026-06-15, `avg/*` headline averages were logged to W&B run
`DFM5/oti1lisg` for the completed DFM5-L checkpoints 50K, 100K, 150K, and
200K. Confidence: high; W&B `scan_history` verified exactly four `avg/*` rows.

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 50000:0.27608846182186414:logs/eval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full:logs/dfm_evals/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full:logs/euroeval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full/step_50000 \
  --item 100000:0.5521769236437283:logs/eval/dfm5_L_step100000_full_20260614_eurofirst_guard:logs/dfm_evals/dfm5_L_step100000_full_20260614_eurofirst_guard:logs/euroeval/dfm5_L_step100000_full_20260614_eurofirst_guard/step_100000 \
  --item 150000:0.8282653854655924:logs/eval/dfm5_L_step150000_full_20260615_eurofirst_guard:logs/dfm_evals/dfm5_L_step150000_full_20260615_eurofirst_guard:logs/euroeval/dfm5_L_step150000_full_20260615_eurofirst_guard/step_150000 \
  --item 200000:1.1043538472874566:logs/eval/dfm5_L_step200000_full_20260615_eurofirst_guard:logs/dfm_evals/dfm5_L_step200000_full_20260615_eurofirst_guard:logs/euroeval/dfm5_L_step200000_full_20260615_eurofirst_guard/step_200000 \
  2>&1 | tee logs/dfm5_L_avg_50k_200k_20260615.log
```

Verified rows:

```text
50K:  avg/danish=0.3204938053  avg/english=0.3394398505  avg/math_code=0.0648775454  avg/overall=0.2416037337
100K: avg/danish=0.3856718136  avg/english=0.4337499937  avg/math_code=0.1409537807  avg/overall=0.3201251960
150K: avg/danish=0.4332904762  avg/english=0.5028531674  avg/math_code=0.1945934388  avg/overall=0.3769123608
200K: avg/danish=0.4480947019  avg/english=0.5191093860  avg/math_code=0.2233228181  avg/overall=0.3968423020
```

Superseded in the same session: the DFM5-L 250K eval later reached
`FINAL_MERGE_END`, and its post-eval watcher logged the 250K row under
`avg/*`. See the 250K full-eval completion note near the top of this page for
the exact values.
