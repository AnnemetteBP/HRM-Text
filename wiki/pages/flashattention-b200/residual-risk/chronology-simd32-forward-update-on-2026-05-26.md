---
type: Technical Reference
title: SIMD32 forward update on (2026-05-26)
description: 'Chronological record from Residual Risk: SIMD32 forward update on (2026-05-26).'
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
# SIMD32 forward update on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

SIMD32 forward update on 2026-05-26:

Added `prefixlm_forward_online_hdim128_simd32`, following the shape of PyTorch's MPS decode kernels:

- 32 lanes per query/head.
- For `head_dim=128`, each lane owns 4 Q/K/V elements.
- Dot products use `simd_sum` instead of 128-lane threadgroup reductions.
- Threadgroup memory is effectively avoided for the main online softmax state.
- The experimental autograd path now uses SIMD32 forward for `head_dim=128`; backward remains the specialized scalar MPS backward.

Sequential 4096-token XXS-geometry result:

```text
shape: tokens=4096 seqs=16 heads=2 head_dim=128 causal=False
dense forward-only best of 3: 16.741 ms
kernel forward-only best of 3: 1.377 ms
simd32_hdim128 forward-only best of 3: 1.417 ms
dense backward-only best of 3: 4.924 ms
kernel backward-only best of 3: 10.018 ms
dense forward+backward best of 3: 22.944 ms
kernel forward+backward best of 3: 11.828 ms
kernel/dense ratio: 0.516x
```

Sequential 4096-token XL-geometry result:

```text
shape: tokens=4096 seqs=16 heads=12 head_dim=128 causal=False
dense forward-only best of 3: 18.270 ms
kernel forward-only best of 3: 5.475 ms
simd32_hdim128 forward-only best of 3: 5.520 ms
dense backward-only best of 3: 20.497 ms
kernel backward-only best of 3: 68.820 ms
dense forward+backward best of 3: 41.135 ms
kernel forward+backward best of 3: 67.990 ms
kernel/dense ratio: 1.653x
```

Interpretation: SIMD32 fixes the forward path. It is about 12x faster than dense forward for the XXS geometry and about 3.3x faster for the XL geometry. End-to-end XXS is now about 1.9x faster than dense. XL remains slower end-to-end because the scalar custom backward scales poorly with head count. Confidence: high for the sequential isolated benchmark results.
