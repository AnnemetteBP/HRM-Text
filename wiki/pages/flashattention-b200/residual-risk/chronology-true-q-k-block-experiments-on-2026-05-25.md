---
type: Technical Reference
title: True Q/K block experiments on (2026-05-25)
description: 'Chronological record from Residual Risk: True Q/K block experiments
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
# True Q/K block experiments on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

True Q/K block experiments on 2026-05-25:

Two forward-only benchmark kernels were tried:

- `prefixlm_forward_matmulblock_hdim128_q4_k8`: 4 query rows x 8 key columns, 16 lanes per dot product.
- `prefixlm_forward_matmulblock_hdim128_q2_k8_l32`: 2 query rows x 8 key columns, 32 lanes per dot product.

Both compute a real Q/K score tile in threadgroup memory and perform a tile-level online softmax update. Both were numerically correct but slower than the simpler one-query online kernel and slower than dense SDPA at XL geometry.

Small smoke:

```text
512 tokens, 4 heads:
dense forward-only best of 3: 3.953 ms
online_hdim128 forward-only best of 3: 1.070 ms
headblock4_hdim128 forward-only best of 3: 1.217 ms
matmulblock_q2_k8_l32_hdim128 forward-only best of 3: 1.873 ms
```

XL geometry:

```text
4096 tokens, 12 heads:
dense forward-only best of 3: 18.028 ms
online_hdim128 forward-only best of 3: 23.176 ms
headblock4_hdim128 forward-only best of 3: 26.471 ms
matmulblock_q2_k8_l32_hdim128 forward-only best of 3: 52.895 ms
```

An earlier q4/k8/l16 XL run measured:

```text
matmulblock_q4_k8_hdim128 forward-only best of 3: 31.741 ms
```

Conclusion: hand-rolled threadgroup Q/K tiling without Apple matrix/SIMDgroup matrix instructions is not competitive for XL-width MPS attention. The barrier/reduction overhead dominates. The dense PyTorch MPS SDPA path remains the practical XL path. A future custom XL kernel would need to target Apple GPU matrix instructions or another lower-level acceleration path, not scalar threadgroup reductions. Confidence: high for the benchmark result; medium for the hardware-specific next-step assessment.
