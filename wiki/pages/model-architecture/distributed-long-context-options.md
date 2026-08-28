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
| Full per-block activation checkpointing | implemented | benchmarked on B200 | Uses composable checkpoint wrappers before FSDP2 wrapping. |
| Selective/per-block checkpointing | 2--5 days | 1--2 weeks | Choose a useful memory policy and verify memory/throughput tradeoffs. |
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
and is therefore the conservative first implementation. The `checkpointing`
branch has an opt-in `activation_checkpointing=full` mode. It applies
`torch.distributed._composable.checkpoint` to every `TransformerBlock` before
FSDP2 wraps those blocks. At BP=5, checkpoint recomputation is triggered only
for the differentiable `H0`, `L3`, `L4`, `L5`, and `H1` recurrent calls. The
detached `L0--L2` calls do not retain backward activations or recompute.

The default is `activation_checkpointing=none`, which preserves the prior
path. Full mode also sets FSDP2 `reshard_after_forward=true`; ordinary mode
retains the established `false` setting. It is compatible with existing
checkpoint and EMA formats because it adds no parameters or buffers. CPU tests
verify output and gradient parity, expected BP=5 recomputation, inactivity
during evaluation, and a compiled single-process smoke path.

The initially implemented functional `torch.utils.checkpoint` wrappers were
superseded on 2026-08-26. With FSDP2 mixed precision, recomputation entered the
FSDP pre-backward state without repeating the forward BF16 parameter cast,
causing saved-BF16/recomputed-FP32 metadata mismatches. Explicit autocast,
moving functional checkpoints to blocks, disabling compile, and enabling
resharding did not resolve that FSDP2 state-machine issue. The composable API,
applied before `fully_shard`, is the working ordering.

A matched DFM8 XXL continuation from step 152500 established the memory result:

| Mode | Compile | Peak allocated / GPU | Peak reserved / GPU | Steady optimizer step |
|---|---:|---:|---:|---:|
| No checkpointing | yes | 143027 MiB | 165168 MiB | 3.53 s |
| Full block checkpointing | no | 41984 MiB | 49970 MiB | about 6.4 s |
| L-only block checkpointing | no | 90228 MiB | 105344 MiB | 5.59 s |

Full mode therefore reduced peak allocated memory by 70.6% and peak reserved
memory by 69.7%. Its observed optimizer-step time was about 1.8x the compiled
baseline. This is not a perfectly isolated throughput comparison because the
working composable FSDP2 path currently runs with `compile_train_batch=false`;
it is nevertheless representative of the resumed production configuration.

The `l_only` selective mode checkpoints the 36 blocks under `L_level` while H
remains uncheckpointed. At BP=5 this recomputes three L calls and no H calls.
In a W&B-disabled smoke resumed from DFM8 XXL step 153500, it was 13.0% faster
than full checkpointing while using 48244 MiB more peak allocated memory. Only
selected L blocks use FSDP2 `reshard_after_forward=true`; uncheckpointed H
blocks retain the established no-reshard path.

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

1. Use the validated full block checkpointing path where memory is the limiting
   resource; add a selective policy if its measured throughput cost is too high.
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

## Positional-extension decision, 2026-08-26

Use vanilla RoPE for the next longer-context training experiment. The earlier
YaRN comparison included an incorrectly exported checkpoint and therefore does
not establish that YaRN caused the observed regression. YaRN remains a possible
later controlled comparison, but it must use correctly exported checkpoints
and otherwise matched training and evaluation settings.

## Multi-node readiness, 2026-08-26

The core trainer is structurally multi-node aware: TorchRun initializes NCCL,
CUDA placement uses `LOCAL_RANK`, sampling uses global `RANK` and `WORLD_SIZE`,
rank zero owns W&B, and distributed checkpoints use PyTorch DCP. This has not
yet been validated as an end-to-end production multi-node path.

Known gaps and constraints:

- The evaluation scheduler launches and accounts for one local GPU host; it
  does not launch or monitor multi-node TorchRun jobs.
- Checkpoint guards default to eight carry files. Multi-node plans must require
  `WORLD_SIZE` carry files.
- Carries are rank-local tensors. DCP can reshard model and optimizer state,
  but resuming with a different world size is not currently supported safely
  because carry files and shapes do not get redistributed.
- Gradient accumulation does not suppress DDP/FSDP synchronization on
  non-final microbatches, so multi-node communication is repeated for every
  accumulation microbatch.
- FSDP2 currently shards over the entire world process group. There is no
  hybrid-shard device mesh that shards within a node and replicates across
  nodes.
- Checkpoint paths must be on a shared filesystem visible under the same path
  from every node.
- `global_batch_size / (WORLD_SIZE * GAS)` must remain large enough to hold at
  least one complete packed training sequence on every rank.

Clarifications from the 2026-08-27 audit:

- TorchRun normally relies on a cluster scheduler such as Slurm to launch one
  agent per node, then uses a c10d rendezvous to assign global and local ranks.
  TorchRun does not allocate remote nodes or redistribute application state
  when elastic membership changes.
- Carry-rank requirements should come from checkpoint/run metadata, not a
  default of eight. For the current no-carry HRM, every saved carry is literally
  `None`, so changing world size does not require tensor redistribution. A
  stateful architecture would need carry state keyed by global sample identity.
- FSDP2 supports HSDP directly through a two-dimensional `DeviceMesh` whose
  first dimension replicates and second dimension shards. The repository does
  not yet construct or pass that mesh.
- FSDP2 exposes `set_requires_gradient_sync` and
  `set_requires_all_reduce` for accumulation-aware communication; DDP exposes
  `no_sync`. The current accumulation loop uses none of these and synchronizes
  each microbatch.

The copied LUMI DFM9 XXL-32 configuration is internally valid at 256 GPUs:
GBS 1,048,576, GAS 1, and 4096 tokens per rank for a 4096-token context. At
step 10K its actual packed length was 1,042,679 tokens (99.44% utilization)
across 2675 logical sequences. This geometry does not by itself explain the
reported divergence. Material differences from the current XXL run include LR
`1e-3`, only 89,665 optimizer updates per epoch, no gradient clipping, and
`bp_max_steps=3` instead of 5. Relative to the current 262,144-token, `4e-4`
run, square-root batch scaling suggests about `8e-4`; `1e-3` is 25% above that
reference. Treat LR and optimization trajectory as stronger suspects than the
one-packed-block-per-rank layout.

For the current XXL model, choose FSDP rather than replicated DDP if using only
the implemented paths. A production 2/4/8-node design should add hybrid
sharding within each fast local GPU island and DDP-style replication across
nodes, plus accumulation-aware synchronization. DDP is preferable for smaller
models only when the complete parameters, gradients, optimizer, EMA, and
activations fit comfortably on every GPU.
