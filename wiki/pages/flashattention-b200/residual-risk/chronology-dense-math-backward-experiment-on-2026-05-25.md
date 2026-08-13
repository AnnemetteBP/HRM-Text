---
type: Technical Reference
title: Dense-math backward experiment on (2026-05-25)
description: 'Chronological record from Residual Risk: Dense-math backward experiment
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
# Dense-math backward experiment on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Dense-math backward experiment on 2026-05-25:

Added a benchmark-only explicit backward helper:

```python
flash_attn_varlen_prefixlm_mps_backward_dense_math
```

It keeps the packed PrefixLM sequence loop but computes per-sequence dense attention matrices with MPS tensor ops:

```text
P = softmax(QK^T * scale + mask)
dV = P^T @ dO
dP = dO @ V^T
dS = P * (dP - sum(dO * O))
dQ = dS @ K
dK = dS^T @ Q
```

4096-token XXS-geometry result:

```text
dense-math dq max abs diff: 1.96695e-06
dense-math dk max abs diff: 1.90735e-06
dense-math dv max abs diff: 1.43051e-06
dense backward-only best of 3: 4.530 ms
kernel backward-only best of 3: 9.966 ms
dense-math backward explicit best of 3: 18.008 ms
estimated online-forward+dense-math-backward: 22.540 ms
dense forward+backward best of 3: 20.962 ms
kernel forward+backward best of 3: 14.892 ms
```

Conclusion: explicit Python-level per-sequence dense-math backward is correct but too slow. PyTorch's native dense SDPA autograd remains much faster for dense backward than reproducing the formulas manually in Python tensor ops. Keep this helper benchmark-only. Confidence: high.
