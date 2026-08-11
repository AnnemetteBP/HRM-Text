---
type: Technical Reference
title: Superseded on (2026-05-29)
description: 'Chronological record from Residual Risk: Superseded on (2026-05-29).'
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
# Superseded on (2026-05-29)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Superseded on 2026-05-29: this environment-variable cap mechanism was removed. Current MPS dispatch is tensor-driven as described in the 2026-05-29 MPS dispatch update above. Confidence: high.

```bash
/Users/petersk/Nobackup/miniconda3/bin/conda run -n hrm python scripts/debug_mps_prefixlm_kernel.py --seqs 2 --prefix-len 4 --causal-len 4 --heads 2 --head-dim 32
```

Verified outside the sandbox on MPS:

```text
shape: tokens=4 seqs=1 heads=1 head_dim=16 causal=False
forward max abs diff: 2.38419e-07
dq max abs diff: 8.84756e-09
dk max abs diff: 6.51926e-09
dv max abs diff: 1.49012e-08

shape: tokens=16 seqs=2 heads=2 head_dim=32 causal=False
forward max abs diff: 4.76837e-07
dq max abs diff: 1.39698e-09
dk max abs diff: 1.39698e-09
dv max abs diff: 1.39698e-09
```

The tiny parity harness now also reports best-of-N forward+backward timings and one-pass memory deltas, using MPS synchronization around each timed/measured iteration. Default timing is best of 10 after 2 warmup iterations. This PyTorch MPS build exposes `current_allocated_memory()` and `driver_allocated_memory()`, but not CUDA-style peak memory stats, so memory output is a synchronized before/after delta rather than a true peak. The 16-token run above measured:

```text
dense forward+backward best of 10: 4.081 ms
kernel forward+backward best of 10: 0.944 ms
kernel/dense ratio: 0.231x
dense forward+backward memory: current_delta=0.027 MiB driver_delta=8.016 MiB current_after=0.096 MiB driver_after=18.656 MiB
kernel forward+backward memory: current_delta=0.027 MiB driver_delta=0.000 MiB current_after=0.096 MiB driver_after=10.641 MiB
kernel/dense current-memory ratio: 1.000x
kernel/dense driver-memory ratio: 0.000x
```

At this tiny shape, current-memory deltas are dominated by the retained tensors returned by the harness. Driver deltas are useful as an early signal of extra backend workspace, but larger isolated shapes are needed before drawing performance or memory conclusions. Confidence: high for the new tiny-kernel guard, parity harness, and tiny-shape timing/memory output.
