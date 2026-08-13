---
type: Technical Reference
title: Direct internal MPS SDPA test on (2026-05-25)
description: 'Chronological record from Residual Risk: Direct internal MPS SDPA test
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
# Direct internal MPS SDPA test on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Direct internal MPS SDPA test on 2026-05-25:

```python
torch.ops.aten._scaled_dot_product_attention_math_for_mps(
    q, k, v, mask, 0.0, False, None, scale=None, enable_gqa=False
)
```

Forward-only worked and matched `F.scaled_dot_product_attention` exactly on a small masked MPS test:

```text
out diff: 0.0
F.sdpa forward:        0.909 ms
mps_internal forward:  0.435 ms
```

However, training backward is not implemented:

```text
RuntimeError: derivative for aten::_scaled_dot_product_attention_math_for_mps is not implemented
```

Conclusion: do not use `_scaled_dot_product_attention_math_for_mps` in the training path. It may be useful for forward-only inference/eval experiments, but it is a private/internal aten op with no autograd support in this build. Confidence: high.
