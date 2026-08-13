---
type: Technical Reference
title: Multi-node Scaling, 2026-06-18
description: 'Part of FlashAttention on B200: Multi-node Scaling, 2026-06-18.'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200.md
---
# Multi-node Scaling, 2026-06-18

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Confidence: high for live dev-g runs across 2/4/8/16 nodes.

Strong-scaling benchmark of the L model with a fixed `global_batch_size=172032`
tokens, `gradient_accumulation_steps=1`, bf16, FSDP2/RCCL, run via
`scripts/lumi_bench_scaling.sh` (adds an optional `max_steps` config that records
per-step times to `BENCH_OUTPUT`). A small synthetic dataset (1024-token rows)
was used to isolate compute + communication from Lustre I/O.

| Nodes | GCDs | tokens/GCD/step | median s/step | speedup vs 2-node | parallel eff |
|---|---|---|---|---|---|
| 2  | 16  | 10752 | 1.499 | 1.00x | 100% |
| 4  | 32  | 5376  | 0.887 | 1.69x | 85%  |
| 8  | 64  | 2688  | 0.660 | 2.27x | 57%  |
| 16 | 128 | 1344  | 0.645 | 2.32x | 29%  |

Findings:

- Scaling saturates by 8 nodes; 8->16 nodes gives almost no speedup because the
  fixed global batch leaves only ~1344 tokens/GCD at 16 nodes, so FSDP
  all-gather/reduce-scatter and fixed per-step overhead dominate. 16 nodes wastes
  roughly half the GCDs for this batch size.
- For real multi-node training, scale the GLOBAL batch with node count (weak
  scaling) and/or raise `gradient_accumulation_steps` so each GCD keeps a useful
  microbatch.
- Two benchmark gotchas learned: (1) synthetic benchmark rows must be SHORTER
  than the per-GCD token budget `global_batch_size / world_size`, or the sampler
  produces no batches at high node counts (1344 at 16 nodes); (2) keep all
  benchmark/checkpoint writes on `/scratch`, never `/projappl` (54 GB quota -
  a stray relative `checkpoints/` dir filled it and crashed an 8-node run).
- Results saved on LUMI:
  `/scratch/project_465002606/bench/rocm_l_scaling/SCALING_RESULTS.md` and
  `scaling_summary.json`.
