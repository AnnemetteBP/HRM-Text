---
type: Technical Reference
title: MPS kernel benchmark harness update on (2026-05-25)
description: 'Chronological record from Residual Risk: MPS kernel benchmark harness
  update on (2026-05-25).'
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
# MPS kernel benchmark harness update on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

MPS kernel benchmark harness update on 2026-05-25:

- `scripts/debug_mps_prefixlm_kernel.py` now reports granular timings:
  - dense forward-only
  - kernel forward-only
  - tiled `head_dim=128` forward-only
  - dense backward-only
  - kernel backward-only
  - dense forward+backward
  - kernel forward+backward
- `models/flash_attention_prefixlm_mps.py` has a benchmark-only tiled forward kernel specialized for `head_dim=128`, processing 4 queries per threadgroup. This is not used in the autograd/training path.
- A q8 variant was briefly tested and was slower on the 512-token shape, so the retained tiled benchmark path is q4.

Best-of-10 XXS-geometry result:

```text
shape: tokens=512 seqs=4 heads=2 head_dim=128 causal=False
forward max abs diff: 1.2219e-06
dq max abs diff: 5.00222e-11
dk max abs diff: 7.27596e-11
dv max abs diff: 1.09139e-11
forward-only kernel max abs diff: 1.43051e-06
forward-only tiled_q4_hdim128 max abs diff: 1.43051e-06
dense forward-only best of 10: 4.427 ms
kernel forward-only best of 10: 2.456 ms
tiled_q4_hdim128 forward-only best of 10: 2.195 ms
tiled/dense forward-only ratio: 0.496x
tiled/kernel forward-only ratio: 0.894x
kernel/dense forward-only ratio: 0.555x
dense backward-only best of 10: 1.668 ms
kernel backward-only best of 10: 1.698 ms
kernel/dense backward-only ratio: 1.018x
dense forward+backward best of 10: 6.927 ms
kernel forward+backward best of 10: 3.424 ms
kernel/dense ratio: 0.494x
dense forward+backward memory: current_delta=3.500 MiB driver_delta=16.016 MiB current_after=13.502 MiB driver_after=34.656 MiB
kernel forward+backward memory: current_delta=3.500 MiB driver_delta=0.000 MiB current_after=13.502 MiB driver_after=18.641 MiB
```

Interpretation: q4 tiling improves forward-only time by roughly 11% versus the existing one-query custom forward on this shape, but the full training-path gap is currently constrained by backward. The custom backward is about equal to dense backward at 512 tokens but does not yet use tiled work sharing. Confidence: high for this isolated benchmark.
