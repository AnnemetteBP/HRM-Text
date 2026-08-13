---
type: Technical Reference
title: Ten-step XXS dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Ten-step XXS dense-vs-custom
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
# Ten-step XXS dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Ten-step XXS dense-vs-custom timing on 2026-05-26:

Same diagnostic setup as the XS/S/B/L/XL comparisons, but with `arch/size@arch=XXS`. The custom run used the experimental MPS kernel with caps `tokens=4096`, `heads=2`, `head_dim=128`.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 125.844
  step 2: 62.802
  step 3: 406.887
  step 4: 74.021
  step 5: 72.748
  step 6: 72.820
  step 7: 69.706
  step 8: 69.932
  step 9: 72.769
  step 10: 69.829

dense MPS fallback train_step_wall_ms:
  step 1: 322.335
  step 2: 108.761
  step 3: 297.280
  step 4: 183.558
  step 5: 205.398
  step 6: 211.766
  step 7: 198.437
  step 8: 216.849
  step 9: 175.935
  step 10: 204.939
```

Summary:

```text
all-step mean:
  custom: 109.736 ms
  dense:  212.526 ms
  dense/custom speedup: 1.937x

median:
  custom: 72.758 ms
  dense:  205.168 ms
  dense/custom speedup: 2.820x

excluding step 3 outlier:
  custom: 76.719 ms
  dense:  203.109 ms
  dense/custom speedup: 2.647x

steps 4-10:
  custom: 71.689 ms
  dense:  199.555 ms
  dense/custom speedup: 2.784x
```

Memory:

```text
custom after_init current=456.016 MiB driver=1104.438 MiB
custom highest after_train current=556.573 MiB driver=4874.891 MiB
dense after_init current=456.016 MiB driver=1104.438 MiB
dense highest after_train current=556.143 MiB driver=4908.312 MiB
```

Interpretation: XXS is the strongest result so far. Custom is about `1.94x` faster even in the all-step mean with the spike included, and about `2.65x-2.82x` faster on non-outlier/steady-step comparisons. Live memory after model init is about `456 MiB`; peak live after-train memory is about `557 MiB` for both custom and dense. Confidence: high for the recorded run; medium for longer-run throughput because only 10 steps were measured.
