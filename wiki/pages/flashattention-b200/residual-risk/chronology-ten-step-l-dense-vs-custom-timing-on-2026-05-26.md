---
type: Technical Reference
title: Ten-step L dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Ten-step L dense-vs-custom
  timing on (2026-05-26).'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200/residual-risk.md
---
# Ten-step L dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Ten-step L dense-vs-custom timing on 2026-05-26:

Same diagnostic setup as the XL comparison, but with `arch/size@arch=L`. The custom run used the experimental MPS kernel with caps `tokens=4096`, `heads=10`, `head_dim=128`.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 1373.142
  step 2: 1139.257
  step 3: 7711.535
  step 4: 1277.349
  step 5: 1336.466
  step 6: 1278.594
  step 7: 1309.203
  step 8: 1328.550
  step 9: 1322.252
  step 10: 1165.187

dense MPS fallback train_step_wall_ms:
  step 1: 1854.250
  step 2: 1250.963
  step 3: 3961.176
  step 4: 1772.268
  step 5: 1637.370
  step 6: 1671.016
  step 7: 1744.570
  step 8: 1755.720
  step 9: 1700.678
  step 10: 1497.062
```

Summary:

```text
all-step mean:
  custom: 1924.154 ms
  dense:  1884.507 ms
  dense/custom speedup: 0.979x

median:
  custom: 1315.727 ms
  dense:  1722.624 ms
  dense/custom speedup: 1.309x

excluding step 3 outlier:
  custom: 1281.111 ms
  dense:  1653.766 ms
  dense/custom speedup: 1.291x

steps 4-10:
  custom: 1288.229 ms
  dense:  1682.669 ms
  dense/custom speedup: 1.306x
```

Memory:

```text
custom after_init current=7958.016 MiB driver=8272.438 MiB
custom highest after_train current=11267.556 MiB driver=19938.891 MiB
dense after_init current=7958.016 MiB driver=8272.438 MiB
dense highest after_train current=10997.335 MiB driver=26652.312 MiB
```

Interpretation: L shows the same shape as XL. The custom kernel is about `1.29x-1.31x` faster on median/steady steps, but the custom step-3 outlier makes the 10-step all-step mean slightly worse than dense. Live memory after model init is about `8.0 GiB`; peak live after-train memory was about `11.3 GiB` for custom and about `11.0 GiB` for dense. Confidence: high for the recorded run; medium for longer-run throughput because only 10 steps were measured.
