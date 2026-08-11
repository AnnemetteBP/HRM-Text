---
type: Technical Reference
title: Ten-step B dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Ten-step B dense-vs-custom
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
# Ten-step B dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Ten-step B dense-vs-custom timing on 2026-05-26:

Same diagnostic setup as the L/XL comparisons, but with `arch/size@arch=B`. The custom run used the experimental MPS kernel with caps `tokens=4096`, `heads=8`, `head_dim=128`.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 566.046
  step 2: 446.681
  step 3: 2830.671
  step 4: 464.581
  step 5: 461.750
  step 6: 461.621
  step 7: 446.265
  step 8: 447.065
  step 9: 463.905
  step 10: 442.330

dense MPS fallback train_step_wall_ms:
  step 1: 819.578
  step 2: 500.184
  step 3: 1606.054
  step 4: 698.965
  step 5: 674.202
  step 6: 682.212
  step 7: 696.910
  step 8: 805.104
  step 9: 617.073
  step 10: 665.653
```

Summary:

```text
all-step mean:
  custom: 703.091 ms
  dense:  776.594 ms
  dense/custom speedup: 1.105x

median:
  custom: 461.685 ms
  dense:  689.561 ms
  dense/custom speedup: 1.494x

excluding step 3 outlier:
  custom: 466.694 ms
  dense:  684.431 ms
  dense/custom speedup: 1.467x

steps 4-10:
  custom: 455.360 ms
  dense:  691.446 ms
  dense/custom speedup: 1.518x
```

Memory:

```text
custom after_init current=3452.016 MiB driver=4144.438 MiB
custom highest after_train current=4547.792 MiB driver=9922.891 MiB
dense after_init current=3452.016 MiB driver=4144.438 MiB
dense highest after_train current=4474.851 MiB driver=13068.297 MiB
```

Interpretation: B is the cleanest full-model comparison so far. The custom kernel wins even in the all-step mean despite the same step-3 packed-shape spike. Steady-state speedup is about `1.5x`. Live memory after model init is about `3.45 GiB`; peak live after-train memory was about `4.55 GiB` for custom and about `4.47 GiB` for dense. Confidence: high for the recorded run; medium for longer-run throughput because only 10 steps were measured.
