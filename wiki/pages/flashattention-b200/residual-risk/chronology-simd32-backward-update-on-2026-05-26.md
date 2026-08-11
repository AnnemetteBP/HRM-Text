---
type: Technical Reference
title: SIMD32 backward update on (2026-05-26)
description: 'Chronological record from Residual Risk: SIMD32 backward update on (2026-05-26).'
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
# SIMD32 backward update on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

SIMD32 backward update on 2026-05-26:

Added SIMD32 versions of the `head_dim=128` backward kernels:

- `prefixlm_backward_query_dot_hdim128_simd32`
- `prefixlm_backward_dq_hdim128_predot_simd32`
- `prefixlm_backward_dk_dv_hdim128_predot_simd32`

The experimental autograd path now uses SIMD32 forward plus SIMD32 backward for `head_dim=128`. The kernels keep the same exact PrefixLM mask semantics as the dense reference. Each 32-lane group handles one `(token, head)` item, and each lane owns four head-dimension elements for 128-dimensional heads.

Sequential 4096-token XXS-geometry result:

```text
shape: tokens=4096 seqs=16 heads=2 head_dim=128 causal=False
forward max abs diff: 1.72853e-06
dq max abs diff: 1.31877e-11
dk max abs diff: 1.86446e-11
dv max abs diff: 2.10321e-12
dense forward-only best of 5: 15.633 ms
kernel forward-only best of 5: 1.297 ms
dense backward-only best of 5: 4.190 ms
kernel backward-only best of 5: 2.889 ms
dense forward+backward best of 5: 21.274 ms
kernel forward+backward best of 5: 4.213 ms
kernel/dense ratio: 0.198x
```

Sequential 4096-token XL-geometry result:

```text
shape: tokens=4096 seqs=16 heads=12 head_dim=128 causal=False
forward max abs diff: 2.20537e-06
dq max abs diff: 3.35376e-12
dk max abs diff: 3.97904e-12
dv max abs diff: 5.11591e-13
dense forward-only best of 3: 17.862 ms
kernel forward-only best of 3: 5.598 ms
dense backward-only best of 3: 19.346 ms
kernel backward-only best of 3: 16.519 ms
dense forward+backward best of 3: 40.504 ms
kernel forward+backward best of 3: 22.758 ms
kernel/dense ratio: 0.562x
```

Interpretation: SIMD32 backward changed the custom path from forward-only useful to end-to-end useful for the tested XXS and XL geometries. XXS is about 5.0x faster than dense end-to-end; XL is about 1.8x faster. These are isolated kernel benchmarks, not full-model training throughput measurements. Confidence: high.
