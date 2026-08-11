---
type: Technical Reference
title: First cautious XXS-geometry ramp test, also run outside the sandbox on (2026-05-25)
description: 'Chronological record from Residual Risk: First cautious XXS-geometry
  ramp test, also run outside the sandbox on (2026-05-25).'
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
# First cautious XXS-geometry ramp test, also run outside the sandbox on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

First cautious XXS-geometry ramp test, also run outside the sandbox on 2026-05-25:

```bash
HRM_EXPERIMENTAL_MPS_MAX_TOKENS=512 \
HRM_EXPERIMENTAL_MPS_MAX_SEQS=4 \
HRM_EXPERIMENTAL_MPS_MAX_HEADS=2 \
HRM_EXPERIMENTAL_MPS_MAX_HEAD_DIM=128 \
/Users/petersk/Nobackup/miniconda3/bin/conda run -n hrm python scripts/debug_mps_prefixlm_kernel.py \
  --seqs 4 \
  --prefix-len 32 \
  --causal-len 96 \
  --heads 2 \
  --head-dim 128 \
  --timing-iterations 3 \
  --warmup-iterations 1
```

Result:

```text
shape: tokens=512 seqs=4 heads=2 head_dim=128 causal=False
forward max abs diff: 1.2219e-06
dq max abs diff: 5.00222e-11
dk max abs diff: 7.27596e-11
dv max abs diff: 1.09139e-11
dense forward+backward best of 3: 5.482 ms
kernel forward+backward best of 3: 3.144 ms
kernel/dense ratio: 0.573x
dense forward+backward memory: current_delta=3.500 MiB driver_delta=8.016 MiB current_after=12.002 MiB driver_after=26.406 MiB
kernel forward+backward memory: current_delta=3.500 MiB driver_delta=0.000 MiB current_after=12.002 MiB driver_after=18.391 MiB
```

Confidence: high for the 512-token isolated benchmark result.
