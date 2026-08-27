---
type: Plan
title: DFM8 XXL to DFM10 Multi-Node Transition
description: Planned epoch-boundary transition from the one-node DFM8 XXL run to a four- or eight-node DFM10 continuation.
tags: [dfm8, dfm10, xxl, multi-node, hsdp, training]
status: draft
last_updated: 2026-08-27
confidence: high
---
# DFM8 XXL to DFM10 Multi-Node Transition

The intended transition point is the fully written DFM8 XXL `epoch_1`
checkpoint. Changing both dataset and topology at this exact epoch boundary is
safer than an in-epoch change: there is no old-dataset row cursor to repartition,
and the DFM10 epoch index can begin from a clean boundary. Preserve model,
optimizer, and EMA state and continue the global optimizer-step counter.

## Batch Geometry

Keep global batch size 262144 and 4K context:

| Topology | World size | GAS | Tokens per GPU per microbatch | Comment |
|---|---:|---:|---:|---|
| Current one node | 8 | 4 | 8192 | Established production path |
| Four nodes | 32 | 1 | 8192 | Same local geometry; removes accumulation |
| Eight nodes | 64 | 1 | 4096 | One full context block per rank; more memory headroom |

Use native FSDP2 HSDP with `fsdp_shard_degree=8`: shard parameters within each
NVLink-connected node and replicate across nodes. Start with
`fsdp_reshard_after_forward=false` for speed, but measure memory before
production. Four nodes retain the current very tight 8192-token local memory
geometry, and HSDP replica communication may add buffers. Eight nodes halve
local tokens and should have more activation headroom, at the cost of a larger
cross-node replica group and lower per-GPU kernel occupancy.

Do not scale LR with node count because GBS is unchanged. The dataset boundary
is a reasonable point to reduce the aggressive constant LR from `4e-4` to
`3e-4`; `pretrain.py` reapplies the configured LR after loading optimizer
state. Do not restart warmup, optimizer moments, or EMA.

## Readiness Gates

DFM10 is not currently launchable: `data/sampled_dfm10` has not been built,
the accepted Folketing source has not been fully consolidated/tokenized, and
known high-impact `Filter`/`Repair` findings such as DBC prompt-language and
GovReport grounding defects remain unresolved. Finalize, rebuild, sample, and
audit DFM10 before constructing the production command.

The SSH launcher and HSDP implementation are locally tested but not yet
multi-node validated. Before the transition:

1. Pass SSH/software/path preflight and NCCL all-reduce on two nodes.
2. Load a copy of the DFM8 epoch checkpoint on 16 ranks and save a disposable
   HSDP checkpoint without W&B logging.
3. Verify optimizer, EMA, global step, no-carry policy, and DCP completeness.
4. Repeat on four nodes, including a forced agent failure and exact coordinated
   teardown.
5. Benchmark at least 200 steady steps on four and eight nodes, comparing
   tokens/second, peak memory, NCCL time, and input stalls.
6. Export and run one evaluation smoke from a multi-node-produced checkpoint.

Use the [fixed-membership SSH launcher](multinode-ssh-launcher.md). Prefer the
four-node topology as the closest numerical/per-rank control. Prefer eight
nodes for production only if its measured throughput is materially higher and
the shared filesystem and cross-node replica all-reduce remain healthy.

## Checkpoint Cadence

Step time should fall substantially, so retaining a 500-step ephemeral cadence
would produce large checkpoints too frequently. Target roughly 30--60 minutes
between ephemerals based on measured steady-state time. Keep regular semantic
checkpoints at evaluation boundaries. DCP writes from 32 or 64 ranks must be
tested against the shared filesystem before selecting exact intervals.

## Evaluation Attribution

Run and preserve a full DFM8 epoch-one evaluation before the switch. Evaluate
DFM10 every 50K global steps afterward. W&B and reports must label the dataset
transition explicitly so later gains are not attributed solely to XXL scale or
multi-node execution.
