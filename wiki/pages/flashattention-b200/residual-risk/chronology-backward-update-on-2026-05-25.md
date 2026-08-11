---
type: Technical Reference
title: Backward update on (2026-05-25)
description: 'Chronological record from Residual Risk: Backward update on (2026-05-25).'
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
# Backward update on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Backward update on 2026-05-25:

- Added `head_dim=128` specialized backward kernels for the experimental MPS path.
- The specialized kernels reduce the QK dot product and softmax-gradient dot product in one reduction loop, reducing threadgroup barrier overhead.
- Added a precomputed per-query `sum(dO * O)` scalar, then use `sum(dO * V_j) - sum(dO * O)` inside `dq` and `dk/dv`.
- For PrefixLM, the pre-dot kernels also compute exact query/key loop bounds instead of scanning the full sequence and checking the mask for every pair.

512-token result:

```text
dense forward-only best of 5: 3.840 ms
kernel forward-only best of 5: 0.886 ms
online_hdim128 forward-only best of 5: 0.857 ms
dense backward-only best of 5: 1.216 ms
kernel backward-only best of 5: 1.132 ms
dense forward+backward best of 5: 5.535 ms
kernel forward+backward best of 5: 1.951 ms
kernel/dense ratio: 0.353x
```

4096-token XXS-geometry result:

```text
dense forward-only best of 3: 15.485 ms
kernel forward-only best of 3: 4.406 ms
online_hdim128 forward-only best of 3: 4.423 ms
dense backward-only best of 3: 4.327 ms
kernel backward-only best of 3: 10.206 ms
dense forward+backward best of 3: 22.020 ms
kernel forward+backward best of 3: 14.641 ms
kernel/dense ratio: 0.665x
```

Interpretation: the specialized backward improved the realistic 4096-token full path from roughly parity/slight win (`0.937x`) to `0.665x`, or about 1.5x faster than dense. Backward is still the bottleneck and remains about 2.4x slower than dense backward at this shape. Confidence: high for the measured isolated benchmark.
