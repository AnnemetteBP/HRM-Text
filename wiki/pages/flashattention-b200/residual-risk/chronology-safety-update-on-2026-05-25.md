---
type: Technical Reference
title: Safety update on (2026-05-25)
description: 'Chronological record from Residual Risk: Safety update on (2026-05-25).'
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
# Safety update on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Safety update on 2026-05-25: the experimental MPS kernel now refuses large shapes even when `HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1` is set. Default caps are:

```text
HRM_EXPERIMENTAL_MPS_MAX_TOKENS=256
HRM_EXPERIMENTAL_MPS_MAX_SEQS=8
HRM_EXPERIMENTAL_MPS_MAX_HEADS=4
HRM_EXPERIMENTAL_MPS_MAX_HEAD_DIM=64
```

Only raise these caps in isolated kernel tests, not full training runs. A tiny standalone parity harness was added:
