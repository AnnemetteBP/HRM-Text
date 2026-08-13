---
type: Technical Reference
title: Online-softmax forward update on (2026-05-25)
description: 'Chronological record from Residual Risk: Online-softmax forward update
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
# Online-softmax forward update on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Online-softmax forward update on 2026-05-25:

- Added `prefixlm_forward_online_hdim128`, a forward-only MPS kernel specialized for `head_dim=128`.
- The experimental autograd path now uses this online forward for `head_dim=128`; backward still uses the previous custom backward kernels.
- The harness also reports an estimated `online-forward + dense-backward` best case by adding separately timed online forward and dense backward. This is not an implemented autograd path; it is a performance ceiling for prioritization.

Forward-only results:

```text
512 tokens, 4 seqs x 128:
dense forward-only best of 3: 4.425 ms
old kernel forward-only best of 3: 1.570 ms
online_hdim128 forward-only best of 3: 0.842 ms

2048 tokens, 16 seqs x 128:
dense forward-only best of 3: 19.049 ms
old kernel forward-only best of 3: 4.732 ms
online_hdim128 forward-only best of 3: 1.570 ms

4096 tokens, 16 seqs x 256:
dense forward-only best of 3: 17.525 ms
old kernel forward-only best of 3: 17.122 ms
online_hdim128 forward-only best of 3: 4.591 ms

8192 tokens, 16 seqs x 512, online-only because the old streaming forward produced a bad outlier:
dense forward-only best of 3: 19.746 ms
online_hdim128 forward-only best of 3: 16.319 ms
```

Full 4096-token result after using online forward inside the experimental autograd path:

```text
shape: tokens=4096 seqs=16 heads=2 head_dim=128 causal=False
forward max abs diff: 1.07288e-06
dq max abs diff: 7.7307e-12
dk max abs diff: 1.18234e-11
dv max abs diff: 1.19371e-12
dense forward-only best of 3: 16.330 ms
kernel forward-only best of 3: 4.420 ms
online_hdim128 forward-only best of 3: 4.325 ms
dense backward-only best of 3: 4.595 ms
kernel backward-only best of 3: 16.600 ms
estimated online-forward+dense-backward best-case: 8.920 ms
dense forward+backward best of 3: 22.918 ms
kernel forward+backward best of 3: 21.482 ms
kernel/dense ratio: 0.937x
```

Interpretation: online forward is now the right forward design and is substantially faster at realistic 4096-token XXS geometry. The remaining blocker is backward; the existing custom backward is about 3.6x slower than dense backward at 4096. Confidence: high.
