---
type: Plan
title: Multi-Node and 32K Training Plan
description: Implementation and validation plan for direct-SSH TorchRun, run-aware checkpoints, efficient accumulation, HSDP, elastic resume, and staged 4K-to-32K B200 training.
tags: [training, multi-node, torchrun, fsdp, hsdp, long-context, checkpointing]
status: draft
last_updated: 2026-08-27
confidence: high
---
# Multi-Node and 32K Training Plan

## Goals

1. Run fixed-size jobs on 2, 4, or 8 mutually reachable 8xB200 nodes without
   Slurm.
2. Make checkpoint completeness depend on the actual run topology and carry
   policy.
3. Resume model, optimizer, EMA, data position, and carry safely at a different
   world size.
4. Make GAS communication-correct and efficient even though planned large
   runs normally use GAS 1.
5. Expose native FSDP2 hybrid sharding as an opt-in argument while preserving
   current full-world FSDP as the default.
6. Keep global batch near 262,144 tokens while extending XXL training from 4K
   to 32K without paying full-checkpointing cost throughout training.

## Fixed-Membership TorchRun Over SSH

TorchRun works without Slurm when every node has the same repository,
environment, data/checkpoint paths, and a reachable master address and port.
Launch one command concurrently on each node with a unique fixed node rank:

```bash
torchrun \
  --nnodes="$NUM_NODES" \
  --nproc-per-node=8 \
  --node-rank="$NODE_RANK" \
  --master-addr="$MASTER_ADDR" \
  --master-port="$MASTER_PORT" \
  pretrain.py ...
```

Add a repository launcher that reads an ordered host file, checks SSH and the
shared paths, chooses node zero as rendezvous host, starts all commands with
per-node logs, records remote PIDs and exit statuses, and terminates the whole
job if any TorchRun agent fails. Use fixed membership first; elastic membership
does not remove the need to restore application checkpoint and data state.

Preflight checks must cover Python/Torch/CUDA/FA4 commit identity, eight visible
GPUs per node, hostname/IP resolution, master-port reachability, NCCL interface,
shared dataset and checkpoint paths, clock sanity, and an NCCL all-reduce smoke.

## Run-Aware Checkpoint Contract

Extend checkpoint sidecars with:

```text
world_size
local_world_size
carry_policy: none | per_rank
carry_schema_version
fsdp_shard_degree
```

Checkpoint guards must read the sidecar atomically and derive expected carry
files from it. Preserve fallback behavior for old sidecars. For `carry_policy:
none`, do not require or write redundant per-rank `None` files. For
`per_rank`, require exactly `world_size` completed carry files.

The current no-carry HRM returns `None`; its world-size transition needs no
carry redistribution. A stateful model is harder because rank-local carries
are aligned with examples assigned to that rank. Safe redistribution requires
saving each carry together with a stable global example/sequence identity,
then repartitioning carries to the examples assigned after resume. Tensor-only
resharding by rank is incorrect when packing, rank count, or local batch size
changes. Mutable caches add sequence-length and ownership concerns. A generic
stateful implementation therefore needs a versioned carry schema and explicit
sample-keyed gather/scatter or DCP-sharded representation.

## Efficient Gradient Accumulation

Refactor the microbatch loop so only the final microbatch performs the required
global synchronization:

- DDP: use `DistributedDataParallel.no_sync()` before the final microbatch.
- FSDP2: call `set_requires_gradient_sync(False)` before non-final
  microbatches and restore it for the final microbatch.
- HSDP: benchmark full no-sync against `set_requires_all_reduce(False)`, which
  retains intra-shard reduce-scatter while postponing replica all-reduce.

Keep the supervised-token divisor and metric reductions mathematically
unchanged. Add deterministic one-step tests comparing GAS 1 and GAS 2/4 from
the same initial state and effective token batch for model gradients, optimizer
state, EMA, and updated parameters. Run DDP, 1D FSDP2, and 2D HSDP variants;
then benchmark communication and memory. Existing GAS behavior remains the
compatibility reference until parity passes.

## Native FSDP2 Hybrid Sharding

Add the conservative argument:

```text
fsdp_shard_degree: null  # current full-world 1D FSDP
fsdp_shard_degree: 8     # shard within each 8-GPU node, replicate across nodes
```

When set below `WORLD_SIZE`, validate divisibility and construct a 2D CUDA
`DeviceMesh` shaped `(WORLD_SIZE / fsdp_shard_degree, fsdp_shard_degree)` with
dimensions `("replicate", "shard")`. Initially require shard degree to equal
`LOCAL_WORLD_SIZE`, ensuring all parameter all-gathers stay within a node. Pass
the same mesh to every bottom-up `fully_shard` call. Record the topology in
checkpoint metadata and W&B configuration. `null` must preserve today's path.

Validate one-step parameter, gradient, optimizer, and EMA parity between 1D
FSDP and HSDP. Test sharded save/resume both at the same topology and after a
world-size change. Measure per-node and inter-node collective time, step time,
and peak GPU memory.

## World-Size-Changing Resume

PyTorch DCP should reshard model and optimizer DTensors. The repository must
add the application-level guarantees around it:

1. Save on 8 ranks and load on 4 and 16 ranks; reverse those directions.
2. Compare model, optimizer moments, EMA, step, and LR scheduler state.
3. Verify the global row cursor produces no skipped or duplicated examples.
4. Compare the next effective global batch by stable example IDs.
5. Compare one optimizer update with a fixed-topology reference, allowing only
   documented floating-point reduction-order tolerance.
6. Reject incompatible stateful carry schemas rather than silently resetting.
7. Verify incomplete DCP or carry writes are never accepted as resumable.

For the current `None` carry model this is expected to be a small, low-risk
extension. Generic stateful-carry redistribution is a separate feature.

## Staged 4K-to-32K B200 Strategy

Without TP/CP/PP, every GPU is a data-parallel worker even under HSDP. At GAS 1
the minimum global batch is therefore `WORLD_SIZE * context_length`. To retain
GBS 262,144, scale the node count down as context grows:

| Stage | Nodes x GPUs | Context | Tokens/GPU | GBS | Initial checkpoint policy |
|---|---:|---:|---:|---:|---|
| Majority training | 8 x 8 = 64 | 4K | 4K | 262,144 | none |
| Context adaptation I | 4 x 8 = 32 | 8K | 8K | 262,144 | none, then L-only if needed |
| Context adaptation II | 2 x 8 = 16 | 16K | 16K | 262,144 | L-only benchmark, full fallback |
| Final long-context stage | 1 x 8 = 8 | 32K | 32K | 262,144 | full |

This uses all available nodes where they improve throughput without forcing a
larger batch. The measured 4K XXL baseline used 8K tokens per GPU and consumed
about 160--170 GiB physically without checkpointing, so 4K on 64 GPUs should
be easier and 8K on 32 GPUs should resemble that baseline. Full checkpointing
reduced the 8K-token microbatch peak allocation to about 42 GiB; approximately
linear activation scaling suggests that 16K and 32K are plausible with full
checkpointing on 180-GiB B200s, but both require measured smokes.

Do not jump directly from 4K to 32K. Build correctly sampled 8K, 16K, and 32K
epochs containing substantial examples that actually cross the preceding
boundary. Keep vanilla RoPE for the first controlled path, evaluate short- and
long-context metrics before and after each transition, and gate advancement on
both memory stability and quality. A provisional token allocation is 70--80%
at 4K, 10--15% at 8K, 5--10% at 16K, and 5--10% at 32K; revise from adaptation
curves rather than treating these percentages as fixed.

If using all 32 or 64 GPUs at 32K while preserving GBS 262,144 becomes a hard
requirement, add model parallelism. Four-node training needs model-parallel
degree 4; eight-node training needs degree 8. Context parallelism is the most
direct fit but remains difficult because packed PrefixLM and the custom FA4
two-pass path must be distributed correctly. HSDP alone does not solve this.

## LUMI XXL-32 Lesson

The 256-GPU LUMI configuration had valid geometry: GBS 1,048,576, GAS 1,
4096 tokens per rank, and 99.44% packing utilization at step 10K. It should not
be used as evidence that one-block-per-rank is invalid. It did, however, force
a 1M-token batch and only 89,665 updates per epoch. LR `1e-3`, no clipping, and
BP max 3 further confound comparison with the current 262K-token, `4e-4`, BP-5
XXL run. Do not automatically scale LR with node count or batch size; benchmark
conservatively and compare by processed tokens as well as optimizer steps.

## Delivery Order and Gates

1. Implement run-aware checkpoint metadata and no-carry policy.
2. Implement and test accumulation-aware DDP/FSDP2 synchronization.
3. Add `fsdp_shard_degree` and HSDP parity tests.
4. Add world-size-changing DCP resume tests for the no-carry HRM.
5. Add the fixed-membership SSH launcher and two-node preflight/smoke.
6. Benchmark 2, 4, and 8 nodes at 4K with GBS 262,144 and GAS 1.
7. Benchmark 8K none/L-only/full on four nodes, 16K L-only/full on two nodes,
   and 32K full on one node.
8. Freeze a context curriculum only after memory, throughput, resume, and
   short/long evaluation gates pass.

Do not start a costly multi-node production run until a two-node job has passed
forward/backward parity, optimizer/EMA parity, regular and ephemeral save,
same-world resume, changed-world resume, HF export, and one evaluation smoke.

## Single-Node Implementation and XXL Validation

On 2026-08-27 the first implementation landed on the `checkpointing` branch:

- `fsdp_shard_degree=null` preserves the established full-world FSDP2 path.
  Explicit degrees must divide `WORLD_SIZE` and may not exceed
  `LOCAL_WORLD_SIZE`. A smaller degree constructs the native 2D
  `("replicate", "shard")` mesh. Degrees 4 and 2 were exercised on the local
  eight-GPU node as simulated HSDP.
- `fsdp_reshard_after_forward=null` preserves the preceding behavior: false
  without activation checkpointing and true for checkpointed blocks/root.
  Explicit true or false overrides all FSDP-wrapped modules.
- Accumulation now defers DDP and FSDP synchronization until the final
  microbatch. `fsdp_accumulation_sync_mode=reduce_scatter` is available for
  HSDP: it retains intra-shard reduce-scatter on each microbatch and postpones
  only the replica all-reduce. The conservative default remains `no_sync`.
- New checkpoints atomically publish topology and carry policy in the sidecar.
  This no-carry HRM no longer writes redundant rank-local `None` files.
  Scheduler readiness derives carry requirements from the sidecar, with the
  old eight-rank behavior retained for legacy checkpoints.
- A world-size change forces row-cursor resume even when the local microbatch
  size happens to remain unchanged. Legacy sidecars infer their old world size
  from carry ranks when possible.

Deterministic fixed-example tests using the production accumulation function
passed GAS 1 versus GAS 4 for DDP, 1D FSDP, degree-4 HSDP, and degree-2 HSDP.
The maximum absolute model/optimizer difference was `8.94e-8`; parameters and
EMA were exactly equal. Both HSDP synchronization modes passed.

The full XXL timing matrix resumed the same DFM8 `ephemeral_step_161000`
checkpoint. It used six optimizer steps, discarded two timing warmups, disabled
W&B, and used full activation checkpointing except for the production control:

| World | Shard degree | Accumulation | Reshard | Median s/step | Peak allocated MiB |
|---:|---:|---|---|---:|---:|
| 8 | 8 | no-sync GAS 4 | current/true | 6.22 | 55,326 |
| 8 | 8 | no-sync GAS 4 | false | 5.99 | 61,028 |
| 8 | 4 | no-sync GAS 4 | current/true | 6.41 | 62,897 |
| 8 | 4 | no-sync GAS 4 | false | 6.06 | 68,610 |
| 8 | 4 | reduce-scatter GAS 4 | current/true | 6.35 | 51,468 |
| 8 | 2 | no-sync GAS 4 | current/true | 6.46 | 78,075 |
| 8 | 2 | no-sync GAS 4 | false | 6.28 | 83,789 |
| 8 | 2 | reduce-scatter GAS 4 | current/true | 6.40 | 70,443 |
| 8 | 8 | GAS 1 | current/true | 4.58 | 131,599 |
| 4 | 4 | GAS 8 | current/true | 12.63 | 62,897 |
| 2 | 2 | GAS 16 | current/true | 24.42 | 78,078 |
| 8 | 8 | production GAS 4, compiled, no AC | current/false | 3.80 | 156,692 |

The 8-to-4 and 8-to-2 DCP loads and subsequent full XXL optimizer steps
succeeded. Their near-2x/4x timing is consistent with the reduced GPU count.
The full-data runs are not strict cross-GAS numerical tests: changing local
microbatch geometry changes packed sequence grouping, and repeated nominally
identical degree-8 replays also showed optimizer-fingerprint variation. Use
the deterministic fixed-example test as the communication parity gate. The
full XXL runs establish operational load, memory, and throughput behavior.

`reduce_scatter` is the preferred HSDP GAS mode based on this one-node test: it
reduced degree-4 peak allocation by about 11.4 GiB and degree-2 by about 7.6
GiB relative to full no-sync, without a meaningful time penalty. Revalidate
on multiple nodes because inter-node all-reduce changes that tradeoff.

Artifacts and reproducible commands live under
`logs/benchmarks/fsdp_hsdp_xxl/` and in
`scripts/benchmark_fsdp_topology_xxl.sh`. The multi-node SSH launcher,
multi-node NCCL measurements, HF export, and evaluation smoke remain open
delivery gates.
