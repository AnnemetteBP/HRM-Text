---
type: Technical Reference
title: Memory readout for the same diagnostic, rerun on (2026-05-26)
description: 'Chronological record from Residual Risk: Memory readout for the same
  diagnostic, rerun on (2026-05-26).'
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
# Memory readout for the same diagnostic, rerun on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Memory readout for the same diagnostic, rerun on 2026-05-26 after adding MPS memory logging:

```text
mps_memory startup: current=0.000 MiB driver=0.375 MiB
mps_memory after_init: current=456.016 MiB driver=1104.438 MiB
mps_memory step_1_before_train: current=456.109 MiB driver=1104.422 MiB
mps_memory step_1_after_train: current=552.192 MiB driver=6376.703 MiB
mps_memory step_1_after_zero_grad: current=456.192 MiB driver=6378.859 MiB
```

Interpretation: live tensor allocation for the one-step XXS diagnostic is about `552 MiB` immediately after train/optimizer work, and returns to about `456 MiB` after gradients are zeroed. The Metal/MPS driver allocator retained about `6.38 GiB`; this is retained driver memory, not live tensor memory. Confidence: high.
