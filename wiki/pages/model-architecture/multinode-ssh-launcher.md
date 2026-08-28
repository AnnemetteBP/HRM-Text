---
type: Runbook
title: Fixed-Membership SSH TorchRun Launcher
description: Operational contract and commands for launching fixed-size multi-node TorchRun jobs without Slurm.
tags: [training, multi-node, torchrun, ssh, nccl, operations]
status: draft
last_updated: 2026-08-27
confidence: high
---
# Fixed-Membership SSH TorchRun Launcher

Use [`scripts/launch_multinode_torchrun.py`](../../../scripts/launch_multinode_torchrun.py)
when the allocated nodes can SSH to one another but have no cluster scheduler.
The launcher is implemented and locally unit-tested. Its SSH and NCCL paths
remain unverified until at least two allocated nodes are available.

## Host And Storage Contract

Create an ordered host file with one unique SSH target per line. Blank lines
and `#` comments are allowed; the first host is node rank zero and the default
rendezvous host.

```text
node-a  # rank 0
node-b  # rank 1
node-c  # rank 2
node-d  # rank 3
```

Every host must expose the same:

- repository commit and absolute working-directory path;
- Python environment, Torch/CUDA, FlashAttention 4 build, and eight B200 GPUs;
- sampled data and checkpoint paths;
- network interface selected for NCCL, if one is supplied explicitly.

Dataset and checkpoint storage must have identical absolute paths on every
node. The launcher does not copy code, data, environments, or checkpoints.

## Preflight

Run a non-training preflight before the first allocation test:

```bash
cd /work/dfm/HRM-Text
python scripts/launch_multinode_torchrun.py \
  --hostfile config/multinode/hosts.txt \
  --python-env /home/ucloud/miniforge3/envs/hrm \
  --required-path /work/dfm/HRM-Text/data/sampled_dfm8 \
  --required-path /work/dfm/HRM-Text/checkpoints \
  --nccl-interface ib0 \
  --preflight-only
```

The preflight checks SSH, required paths, repository commit, Python, Torch,
Torch CUDA, FA4 package identity/import, GPU count and names, interface
presence, clock skew, hostname resolution, and rendezvous-port binding. A real
launch additionally runs a one-tensor NCCL all-reduce across every rank before
starting training. Do not use `--skip-preflight` or `--skip-nccl-smoke` for a
new allocation.

## Training Launch

Pass the ordinary single-node `pretrain.py` arguments after `--`; the launcher
adds fixed `--nnodes`, `--nproc-per-node`, `--node-rank`, rendezvous, and
environment-specific TorchRun arguments on each host.

```bash
cd /work/dfm/HRM-Text
python scripts/launch_multinode_torchrun.py \
  --hostfile config/multinode/hosts.txt \
  --python-env /home/ucloud/miniforge3/envs/hrm \
  --master-port 29500 \
  --nccl-interface ib0 \
  --required-path /work/dfm/HRM-Text/data/sampled_dfm8 \
  --required-path /work/dfm/HRM-Text/checkpoints \
  --env OMP_NUM_THREADS=1 \
  --env MKL_NUM_THREADS=1 \
  -- \
  pretrain.py data=dfm8 arch/size@arch=XXL \
  distributed_strategy=fsdp fsdp_shard_degree=8 \
  global_batch_size=262144 gradient_accumulation_steps=1
```

Use `fsdp_shard_degree=8` only when each node has eight GPUs and local HSDP is
the intended topology. Omit it for full-world FSDP2. The global batch, GAS,
checkpoint, resume, W&B, and context arguments remain properties of the
training run and must be specified normally.

## Logs And Failure Handling

Each invocation creates a unique directory under `logs/multinode/` containing:

- `manifest.json`, atomically replaced with phase and per-node return codes;
- one SSH/TorchRun log per node;
- separate NCCL smoke logs;
- one exact remote process-group PID per node.

The launcher owns the SSH clients in the foreground. If any node-level
TorchRun agent exits unsuccessfully, or the launcher receives an interrupt, it
sends `TERM` and then bounded `KILL` only to the exact remote process groups it
started. It does not use broad `pkill` patterns. Run it in a durable tmux pane
or under `setsid`; killing the launcher intentionally tears down its job.

## First Multi-Node Gate

Before production, test two nodes with a short deterministic run and verify:

1. preflight and NCCL smoke completion;
2. forward/backward and optimizer/EMA parity;
3. regular and ephemeral checkpoint completeness;
4. same-world and changed-world resume;
5. coordinated teardown when one test agent is deliberately failed;
6. HF export and one evaluation from the resulting checkpoint.

Only after this gate should 4-node or 8-node throughput and HSDP topology
benchmarks be trusted.
