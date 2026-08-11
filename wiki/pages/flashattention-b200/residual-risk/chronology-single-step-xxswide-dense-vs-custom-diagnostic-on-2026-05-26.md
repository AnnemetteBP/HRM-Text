---
type: Technical Reference
title: Single-step XXSwide dense-vs-custom diagnostic on (2026-05-26)
description: 'Chronological record from Residual Risk: Single-step XXSwide dense-vs-custom
  diagnostic on (2026-05-26).'
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
# Single-step XXSwide dense-vs-custom diagnostic on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Single-step `XXS_wide` dense-vs-custom diagnostic on 2026-05-26: `scripts/compare_dense_custom_mps_attention.py --optimizer-step 153` with `arch/size@arch=XXS_wide`, `global_batch_size=16384`, `gradient_accumulation_steps=4`, and custom caps `tokens=4096`, `heads=3`, `head_dim=128` showed no immediate per-batch kernel mismatch from initial weights:

```text
logits first 512 tokens max_abs diff: 5.48362732e-06
all four microbatch losses matched at printed precision
metric loss/accuracy/exact_accuracy matched
largest gradient max_abs diff: 1.49011612e-08
```

Interpretation: the visible `XXS_wide` training divergence is not explained by a simple single-batch forward/backward indexing failure at step `153` from initial weights. The next likely causes are cumulative trajectory sensitivity from small numerical differences, a stateful/runtime issue across repeated MPS kernel launches, or a bug that only appears after weights/optimizer state have evolved. Confidence: high for the diagnostic result; medium for interpretation.
