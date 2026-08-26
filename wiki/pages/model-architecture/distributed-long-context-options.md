---
type: Design Document
title: Distributed Long-Context Implementation Options
description: Main-branch implementation difficulty and risk for activation, tensor, context, and HRM-specific pipeline parallelism.
tags: [training, distributed, long-context, fsdp, hrm]
status: draft
last_updated: 2026-08-26
confidence: medium
---
# Distributed Long-Context Implementation Options

This assessment applies to the main branch. Its relevant constraints are the
six tied L calls and two tied H calls, BP-dependent truncated autograd, packed
PrefixLM batches, the custom two-pass FA4 path, whole-batch `torch.compile`,
per-block FSDP2, AdamATan2 EMA state, and distributed checkpoints.

| Option | Prototype | Production-ready | Main difficulty |
|---|---:|---:|---|
| Whole-call activation checkpointing | 1--3 days | 3--7 days | Recompute only differentiable recurrent calls while preserving compile/FSDP behavior. |
| Selective/per-block checkpointing | 3--7 days | 1--2 weeks | Choose a useful memory policy and verify custom FA4 recomputation. |
| FSDP `reshard_after_forward=true` | hours | 1--3 days | Performance measurement and checkpoint/resume validation; limited activation savings. |
| TP=2 | 2--3 weeks | 4--6 weeks | Sharded QKV/output/MLP plus vocabulary-parallel logits, CE, and metrics. |
| CP=2 | 3--5 weeks | 6--10 weeks | Correct distributed packed PrefixLM attention and backward. |
| Generic depth pipeline | 2--4 weeks | 4--8 weeks | Recurrent L/H execution repeatedly crosses pipeline boundaries. |
| HRM recurrent `L/L/L/H` pipeline | 4--6 weeks | 8--12 weeks | Cyclic schedule, tied replicas/gradients, optimizer ownership, and canonical checkpoints. |
| HRM recurrent `LL/LH` pipeline | 3--5 weeks | 6--10 weeks | Two-stage cyclic schedule and L-weight synchronization; H-side activation imbalance. |

These are indicative full-time ranges for an engineer already familiar with
the code and distributed PyTorch. Kernel work, unstable dependencies, or
multi-node debugging can increase them.

Activation checkpointing does not change weight layout or checkpoint format
and is therefore the conservative first implementation. At BP=5, checkpoint
only calls for which autograd is enabled; checkpointing the already detached
first-cycle L calls cannot save backward state.

TP is not an especially natural first choice for hidden size 1792 and 14
attention heads. TP=2 is clean; larger degrees encounter head divisibility or
communication concerns. TP also requires a vocabulary-parallel implementation
for the 262,144-token untied input/output matrices and global argmax/metrics.

CP is the strongest general long-context runtime design, but the current
packed PrefixLM implementation is its hardest integration point. A correct CP
path must preserve global position IDs, prefix and causal segment boundaries,
variable-length packing, the two attention passes, and backward communication.
Keep CP groups within an eight-GPU NVLink node.

Generic pipeline partitioning avoids tied replicas but causes repeated traffic
as the recurrent execution alternates L and H. Unroll-position pipelines such
as `L/L/L/H` balance compute better, but duplicate tied L (and potentially H)
weights. Their gradients must be reduced across both data replicas and tied
stage replicas before identical optimizer/EMA updates. Checkpoints need one
canonical copy of each tied module.

Recommended order:

1. Add memory and throughput benchmarks plus optional selective activation
   checkpointing.
2. Test whether checkpointing alone makes 16K practical.
3. Implement CP=2 for production 16K/32K if long-context throughput warrants
   the engineering cost.
4. Consider the two-stage `LL/LH` or four-stage `L/L/L/H` recurrent pipeline
   only after profiling checkpointing and CP.
5. Combine CP with selective checkpointing for 32K; avoid TP unless model-state
   or GEMM width becomes the limiting factor.

Every distributed path needs one-step forward, loss, gradient, optimizer,
EMA, save/resume, and HF-export parity tests on packed prefix/causal examples
before throughput measurements are accepted.

