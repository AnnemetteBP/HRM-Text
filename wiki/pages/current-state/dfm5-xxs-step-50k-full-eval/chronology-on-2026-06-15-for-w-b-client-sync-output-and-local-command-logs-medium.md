---
type: Operational Record
title: 'On 2026-06-15: for W&B client sync output and local command logs; medium'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: On 2026-06-15:
  for W&B client sync output and local command logs; medium.'
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
# On 2026-06-15: for W&B client sync output and local command logs; medium

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

On 2026-06-15, `avg/*` headline averages were also logged for DFM5-XXS and the
original Sapient L backfilled run. Confidence: high for W&B client sync output
and local command logs; medium for remote history verification because a later
W&B `scan_history` verification call hung and was terminated without touching
active eval jobs.

DFM5-XXS run:

```text
project: DFM5
run id:  2tv9u438
name:    dfm5-XXS
log:     logs/dfm5_XXS_avg_50k_300k_20260615.log
```

Synced rows:

```text
50K:  avg/danish=0.1973913085  avg/english=0.2084723215  avg/math_code=0.0122617477  avg/overall=0.1393751259
100K: avg/danish=0.1992734184  avg/english=0.2355164296  avg/math_code=0.0170418092  avg/overall=0.1506105524
150K: avg/danish=0.2221133424  avg/english=0.2255464438  avg/math_code=0.0122899433  avg/overall=0.1533165765
200K: avg/danish=0.1915085591  avg/english=0.2427157514  avg/math_code=0.0108271777  avg/overall=0.1483504961
250K: avg/danish=0.2311608317  avg/english=0.2312142869  avg/math_code=0.0137397351  avg/overall=0.1587049512
300K: avg/danish=0.2014285955  avg/english=0.2378867045  avg/math_code=0.0145517530  avg/overall=0.1512890176
```

Original Sapient L backfilled run:

```text
project: DFM5
run id:  original-sapient-L-dfm5-backfill-20260615
name:    original Sapient L backfilled
log:     logs/original_sapient_L_backfill_avg_20260615.log
```

Synced rows:

```text
epoch 1: avg/danish=0.1802960225  avg/english=0.4288698321  avg/math_code=0.2313500000  avg/overall=0.2801719515
epoch 2: avg/danish=0.2225090016  avg/english=0.4979667276  avg/math_code=0.2937250000  avg/overall=0.3380669097
epoch 3: avg/danish=0.2250292546  avg/english=0.5219291269  avg/math_code=0.3142750000  avg/overall=0.3537444605
epoch 4: avg/danish=0.2211987137  avg/english=0.5481151233  avg/math_code=0.3203250000  avg/overall=0.3632129457
```
