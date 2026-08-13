---
type: Technical Reference
title: XS target-batch custom-kernel diagnostic on (2026-05-26)
description: 'Chronological record from Residual Risk: XS target-batch custom-kernel
  diagnostic on (2026-05-26).'
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
# XS target-batch custom-kernel diagnostic on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XS target-batch custom-kernel diagnostic on 2026-05-26:

Same target effective batch as the dense diagnostic:

```text
global_batch_size=32768
gradient_accumulation_steps=8
local_microbatch_size=4096
HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1
HRM_EXPERIMENTAL_MPS_MAX_TOKENS=4096
HRM_EXPERIMENTAL_MPS_MAX_HEADS=4
```

Ten optimizer-step timing:

```text
custom experimental MPS kernel train_step_wall_ms:
  step 1: 4182.757
  step 2: 5032.271
  step 3: 3788.423
  step 4: 4666.824
  step 5: 3445.798
  step 6: 3577.579
  step 7: 4407.849
  step 8: 3931.713
  step 9: 4276.995
  step 10: 4725.162
```

Paired dense-vs-custom summary:

```text
all-step mean:
  custom: 4203.537 ms/optimizer-step
  dense:  9451.020 ms/optimizer-step
  dense/custom speedup: 2.248x

median:
  custom: 4229.876 ms/optimizer-step
  dense:  9445.347 ms/optimizer-step
  dense/custom speedup: 2.233x

steps 4-10 mean:
  custom: 4147.417 ms/optimizer-step
  dense:  9410.501 ms/optimizer-step
  dense/custom speedup: 2.269x

per physical microbatch:
  custom mean: 525.442 ms
  dense mean:  1181.378 ms
```

Memory:

```text
custom after_init current=1028.016 MiB driver=1152.438 MiB
custom highest after_train current=1298.934 MiB driver=7482.859 MiB
dense after_init current=1028.016 MiB driver=1152.438 MiB
dense highest after_train current=2165.414 MiB driver=13767.875 MiB
```

Result: all ten custom optimizer steps completed with finite loss, metrics, gradients, parameters, and post-optimizer parameters. Interpretation: at the target XS effective batch (`32768` with `gas=8`), the custom kernel is about `2.25x` faster than dense and uses substantially less live and retained MPS memory during the step. Confidence: high.
