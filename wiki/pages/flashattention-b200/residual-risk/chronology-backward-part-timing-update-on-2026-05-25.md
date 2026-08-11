---
type: Technical Reference
title: Backward-part timing update on (2026-05-25)
description: 'Chronological record from Residual Risk: Backward-part timing update
  on (2026-05-25).'
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
# Backward-part timing update on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Backward-part timing update on 2026-05-25:

Added benchmark-only helpers to time the custom MPS backward pieces separately:

- `flash_attn_varlen_prefixlm_mps_backward_context`
- `flash_attn_varlen_prefixlm_mps_backward_dq_part`
- `flash_attn_varlen_prefixlm_mps_backward_dk_dv_part`

4096-token XXS-geometry result:

```text
dense backward-only best of 3: 4.450 ms
kernel backward-only best of 3: 10.441 ms
kernel backward context (lse+query_dot) best of 3: 4.941 ms
kernel backward dq-part best of 3: 4.881 ms
kernel backward dk/dv-part best of 3: 5.782 ms
kernel backward parts sum: 15.604 ms
dense forward+backward best of 3: 21.651 ms
kernel forward+backward best of 3: 15.148 ms
kernel/dense ratio: 0.700x
```

The `context` timing includes an `lse` recomputation for the benchmark helper; real autograd saves `lse` from forward, so it is not part of the training backward in the same way. Among actual gradient kernels, `dk/dv` is the larger piece (`5.782 ms`) but `dq` is close (`4.881 ms`). Confidence: high.
