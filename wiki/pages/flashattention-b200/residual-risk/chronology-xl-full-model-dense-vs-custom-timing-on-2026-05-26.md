---
type: Technical Reference
title: XL full-model dense-vs-custom timing on (2026-05-26)
description: 'Chronological record from Residual Risk: XL full-model dense-vs-custom
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
# XL full-model dense-vs-custom timing on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XL full-model dense-vs-custom timing on 2026-05-26:

Same one-step diagnostic configuration as above, run once with `HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1` and once without it:

```text
custom experimental MPS kernel:
  train_step_wall_ms=2133.971
  after_train current=18533.056 MiB driver=24064.703 MiB

dense MPS fallback:
  train_step_wall_ms=3073.054
  after_train current=18117.512 MiB driver=24016.750 MiB
```

Interpretation: for full XL model training at `global_batch_size=1024`, the experimental MPS kernel is about `1.44x` faster for the measured train step (`3073.054 / 2133.971`). Live MPS memory after the step is similar: custom is about `18.53 GiB`, dense is about `18.12 GiB`. Confidence: high for this single-step diagnostic comparison.
