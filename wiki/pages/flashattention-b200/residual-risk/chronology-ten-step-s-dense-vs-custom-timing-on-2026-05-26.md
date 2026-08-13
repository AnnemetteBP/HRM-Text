---
type: Technical Reference
title: Ten-step S dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Ten-step S dense-vs-custom
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
# Ten-step S dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Ten-step S dense-vs-custom timing on 2026-05-26:

Same diagnostic setup as the B/L/XL comparisons, but with `arch/size@arch=S`. The custom run used the experimental MPS kernel with caps `tokens=4096`, `heads=6`, `head_dim=128`.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 300.132
  step 2: 207.104
  step 3: 1492.006
  step 4: 264.668
  step 5: 261.283
  step 6: 234.830
  step 7: 217.919
  step 8: 221.069
  step 9: 226.032
  step 10: 217.958

dense MPS fallback train_step_wall_ms:
  step 1: 618.271
  step 2: 291.430
  step 3: 798.322
  step 4: 388.066
  step 5: 381.017
  step 6: 447.687
  step 7: 414.812
  step 8: 380.657
  step 9: 332.358
  step 10: 374.163
```

Summary:

```text
all-step mean:
  custom: 364.300 ms
  dense:  442.678 ms
  dense/custom speedup: 1.215x

median:
  custom: 230.431 ms
  dense:  384.541 ms
  dense/custom speedup: 1.669x

excluding step 3 outlier:
  custom: 238.999 ms
  dense:  403.162 ms
  dense/custom speedup: 1.687x

steps 4-10:
  custom: 234.823 ms
  dense:  388.394 ms
  dense/custom speedup: 1.654x
```

Memory:

```text
custom after_init current=1862.016 MiB driver=2352.438 MiB
custom highest after_train current=2429.056 MiB driver=7090.891 MiB
dense after_init current=1862.016 MiB driver=2352.438 MiB
dense highest after_train current=2428.710 MiB driver=8276.281 MiB
```

Interpretation: S shows the strongest steady-state gain so far: about `1.65x-1.69x` faster for custom on median/steady-step comparisons, and still `1.21x` faster even in the all-step mean with the step-3 spike included. Live memory after model init is about `1.86 GiB`; peak live after-train memory is about `2.43 GiB` for both custom and dense. Confidence: high for the recorded run; medium for longer-run throughput because only 10 steps were measured.
