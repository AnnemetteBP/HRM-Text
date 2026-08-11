---
type: Technical Reference
title: Five-step XL dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: Five-step XL dense-vs-custom
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
# Five-step XL dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Five-step XL dense-vs-custom timing on 2026-05-26:

Same XL diagnostic configuration as above, `global_batch_size=1024`, `gradient_accumulation_steps=1`, `float32`, `epochs=1`.

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 2372.040
  step 2: 1950.961
  step 3: 12726.719
  step 4: 2261.985
  step 5: 2267.201

dense MPS fallback train_step_wall_ms:
  step 1: 2889.071
  step 2: 2383.261
  step 3: 6622.240
  step 4: 3043.306
  step 5: 2945.985
```

Summary:

```text
all-step mean:
  custom: 4315.781 ms
  dense:  3576.773 ms
  custom/dense: 1.207x

median:
  custom: 2267.201 ms
  dense:  2945.985 ms
  dense/custom speedup: 1.299x

excluding step 3 outlier:
  custom: 2213.047 ms
  dense:  2815.406 ms
  dense/custom speedup: 1.272x
```

Interpretation: the custom kernel is consistently faster on the non-outlier steps, by about `1.27x` to `1.30x` for this 5-step run. However, custom step 3 had a larger allocation/shape outlier than dense (`12.7 s` vs `6.6 s`), making the all-step mean worse. The step-3 batch was also the one that exceeded the original 1024-token experimental cap, so packed attention shape variability matters for full-model timing. Confidence: high for the recorded run; medium for extrapolating steady-state throughput from only five steps.
