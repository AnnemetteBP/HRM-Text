---
type: Technical Reference
title: XS target-batch dense diagnostic on (2026-05-26)
description: 'Chronological record from Residual Risk: XS target-batch dense diagnostic
  on (2026-05-26).'
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
# XS target-batch dense diagnostic on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XS target-batch dense diagnostic on 2026-05-26:

Ran `arch/size@arch=XS` with the target effective batch and dense MPS fallback:

```text
global_batch_size=32768
gradient_accumulation_steps=8
local_microbatch_size=4096
```

Ten optimizer-step timing:

```text
dense MPS fallback train_step_wall_ms:
  step 1: 10154.409
  step 2: 8064.698
  step 3: 10417.585
  step 4: 8831.811
  step 5: 10437.219
  step 6: 9719.472
  step 7: 9236.608
  step 8: 9654.086
  step 9: 8904.924
  step 10: 9089.388
```

Summary:

```text
mean: 9451.020 ms/optimizer-step
median: 9445.347 ms/optimizer-step
min: 8064.698 ms
max: 10437.219 ms
steps 4-10 mean: 9410.501 ms/optimizer-step
mean per physical microbatch: 1181.378 ms
steps 4-10 per physical microbatch: 1176.313 ms
```

Memory:

```text
after_init current=1028.016 MiB driver=1152.438 MiB
highest after_train current=2165.414 MiB driver=13767.875 MiB
after_zero_grad current≈1029 MiB
```

Result: all ten optimizer steps completed with finite loss, metrics, gradients, parameters, and post-optimizer parameters. Confidence: high.
