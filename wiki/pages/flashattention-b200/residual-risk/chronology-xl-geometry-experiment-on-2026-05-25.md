---
type: Technical Reference
title: XL-geometry experiment on (2026-05-25)
description: 'Chronological record from Residual Risk: XL-geometry experiment on (2026-05-25).'
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
# XL-geometry experiment on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XL-geometry experiment on 2026-05-25:

XL uses `heads=12`, `head_dim=128`. A 4096-token isolated benchmark with `16` sequences of length `256` showed the current custom MPS kernel is not competitive for XL-width attention:

```text
shape: tokens=4096 seqs=16 heads=12 head_dim=128 causal=False
dense forward-only best of 3: 20.089 ms
kernel forward-only best of 3: 26.239 ms
online_hdim128 forward-only best of 3: 25.518 ms
dense backward-only best of 3: 19.987 ms
kernel backward-only best of 3: 58.600 ms
dense forward+backward best of 3: 43.072 ms
kernel forward+backward best of 3: 84.394 ms
kernel/dense ratio: 1.959x
```

A forward-only head-grouping experiment was then added: `prefixlm_forward_online_hdim128_headblock4`, which processes 4 heads for the same query in one threadgroup. It was correct but slower:

```text
512 tokens, 4 heads:
dense forward-only best of 3: 4.528 ms
online_hdim128 forward-only best of 3: 1.647 ms
headblock4_hdim128 forward-only best of 3: 1.918 ms

4096 tokens, 12 heads:
dense forward-only best of 3: 17.713 ms
online_hdim128 forward-only best of 3: 24.035 ms
headblock4_hdim128 forward-only best of 3: 26.564 ms
```

Conclusion: grouping heads inside one threadgroup adds synchronization overhead without meaningful reuse, because each head has independent Q/K/V. It should remain benchmark-only. For XL and wider models on MPS, use the dense PyTorch SDPA path unless a fundamentally different block kernel is developed. Confidence: high for this benchmark result.
