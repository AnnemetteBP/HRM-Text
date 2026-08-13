---
type: Technical Reference
title: Ten-step XS dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Ten-step XS dense-vs-custom
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
# Ten-step XS dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Ten-step XS dense-vs-custom timing on 2026-05-26:

Same diagnostic setup as the S/B/L/XL comparisons, but with `arch/size@arch=XS`. The custom run used the experimental MPS kernel with caps `tokens=4096`, `heads=4`, `head_dim=128`.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 183.148
  step 2: 136.713
  step 3: 791.673
  step 4: 136.787
  step 5: 131.993
  step 6: 128.659
  step 7: 122.648
  step 8: 124.118
  step 9: 128.996
  step 10: 124.114

dense MPS fallback train_step_wall_ms:
  step 1: 358.637
  step 2: 185.095
  step 3: 448.623
  step 4: 253.336
  step 5: 288.552
  step 6: 289.228
  step 7: 289.653
  step 8: 256.429
  step 9: 204.237
  step 10: 236.410
```

Summary:

```text
all-step mean:
  custom: 200.885 ms
  dense:  281.020 ms
  dense/custom speedup: 1.399x

median:
  custom: 130.495 ms
  dense:  272.490 ms
  dense/custom speedup: 2.088x

excluding step 3 outlier:
  custom: 135.242 ms
  dense:  262.397 ms
  dense/custom speedup: 1.940x

steps 4-10:
  custom: 128.188 ms
  dense:  259.692 ms
  dense/custom speedup: 2.026x
```

Memory:

```text
custom after_init current=1028.016 MiB driver=1152.438 MiB
custom highest after_train current=1530.060 MiB driver=5994.891 MiB
dense after_init current=1028.016 MiB driver=1152.438 MiB
dense highest after_train current=1403.718 MiB driver=5940.297 MiB
```

Interpretation: XS shows the largest steady-state full-model speedup so far: about `2.0x` on median/steady-step comparisons, and still about `1.4x` faster in the all-step mean with the step-3 spike included. Live memory after model init is about `1.03 GiB`; peak live after-train memory was about `1.53 GiB` for custom and about `1.40 GiB` for dense. Confidence: high for the recorded run; medium for longer-run throughput because only 10 steps were measured.
