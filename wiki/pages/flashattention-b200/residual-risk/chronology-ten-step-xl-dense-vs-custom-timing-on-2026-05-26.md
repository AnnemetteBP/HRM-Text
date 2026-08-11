---
type: Technical Reference
title: Ten-step XL dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Ten-step XL dense-vs-custom
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
# Ten-step XL dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Ten-step XL dense-vs-custom timing on 2026-05-26:

Same XL diagnostic configuration as above, `global_batch_size=1024`, `gradient_accumulation_steps=1`, `float32`, `epochs=1`, with the experimental custom run capped at 4096 packed attention tokens.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1:  2404.737
  step 2:  1932.350
  step 3: 12825.552
  step 4:  2273.799
  step 5:  2035.316
  step 6:  2039.646
  step 7:  1971.645
  step 8:  1980.948
  step 9:  2038.020
  step 10: 1958.623

dense MPS fallback train_step_wall_ms:
  step 1: 2921.895
  step 2: 2391.747
  step 3: 6603.023
  step 4: 2910.397
  step 5: 2810.847
  step 6: 2949.683
  step 7: 2750.941
  step 8: 2995.389
  step 9: 2729.211
  step 10: 2890.358
```

Summary:

```text
all-step mean:
  custom: 3146.064 ms
  dense:  3195.349 ms
  dense/custom speedup: 1.016x

median:
  custom: 2036.668 ms
  dense:  2900.378 ms
  dense/custom speedup: 1.424x

excluding step 3 outlier:
  custom: 2070.565 ms
  dense:  2816.719 ms
  dense/custom speedup: 1.360x

steps 4-10:
  custom: 2042.571 ms
  dense:  2862.404 ms
  dense/custom speedup: 1.401x
```

Interpretation: the custom kernel still has a severe step-3 outlier on this sampled-data prefix shape, but after that allocation/shape event it stabilizes tightly around `2.0 s/step`. Dense stabilizes closer to `2.8-3.0 s/step`. The best current steady-state estimate from this diagnostic is about `1.4x` full-model speedup for XL at `global_batch_size=1024`, while all-step mean over only 10 steps is nearly tied because the one custom outlier dominates. Confidence: high for the recorded run; medium for longer-run throughput because only 10 steps were measured.
