---
type: Operational Record
title: DFM4 XL-DDP step400000 EMA vs no-EMA partial comparison (2026-06-07)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP step400000
  EMA vs no-EMA partial comparison (2026-06-07).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# DFM4 XL-DDP step400000 EMA vs no-EMA partial comparison (2026-06-07)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP `step_400000` EMA vs no-EMA partial comparison, 2026-06-07.
Confidence: high for standard eval log parsing and local no-EMA merged files;
medium for overall conclusion because EMA dfm-evals were still running/not
merged. On standard lite evals, EMA was better on `DROP`, `MMLU`, and
`HellaSwag`, and worse on `GSM8k`, `ARC`, `Winogrande`, `BoolQ`, and `MATH`.
The largest regression was `BoolQ` (`0.4498` EMA vs `0.6930` no-EMA). Standard
metric table:

```text
task        EMA       no-EMA    delta
GSM8k       0.1273    0.1515   -0.0242
DROP        0.2708    0.2667   +0.0041
MMLU        0.3845    0.3692   +0.0153
ARC         0.3148    0.3524   -0.0376
HellaSwag   0.3071    0.3037   +0.0034
Winogrande  0.4980    0.5233   -0.0253
BoolQ       0.4498    0.6930   -0.2432
MATH        0.1519    0.1772   -0.0253
```
