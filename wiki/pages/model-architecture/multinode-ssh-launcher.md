---
type: Runbook
title: Fixed-Membership SSH TorchRun Launcher
description: Operational contract and commands for launching fixed-size multi-node TorchRun jobs without Slurm.
tags: [training, multi-node, torchrun, ssh, nccl, operations]
status: draft
last_updated: 2026-08-28
confidence: high
---
# Fixed-Membership SSH TorchRun Launcher

Use [`scripts/launch_multinode_torchrun.py`](../../../scripts/launch_multinode_torchrun.py)
when the allocated nodes can SSH to one another but have no cluster scheduler.
The launcher is implemented, locally unit-tested, and verified on two
eight-B200 nodes. The first allocation exposed a platform RDMA-device issue;
see [Two-Node Validation](#two-node-validation-2026-08-28).

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

## Two-Node Validation, 2026-08-28

The launcher passed preflight and its 16-rank NCCL all-reduce gate on UCloud
allocation `12375256`. Both nodes exposed the same repository commit, shared
paths, `2.11.0+cu130` Torch build, CUDA 13.0 runtime, FA4 commit
`4178915`, and eight B200 GPUs. A protected eight-rank DFM8 XXL
`step_178000` checkpoint resumed successfully on 16 ranks with its exact
optimizer step and row cursor.

The allocation's user SSH needed a one-time bootstrap. The image initialized
root-to-root host SSH, while `/home/ucloud/.ssh` was node-local and lacked an
authorized user key. After installing an allocation-scoped public key for
`ucloud`, the unprivileged launcher worked normally. Never place or document
the private key in the repository.

Two controlled ten-step runs used GBS 262144, GAS 2, 4096 context, no W&B,
no activation checkpointing, no checkpoint tensor writes, and
`fsdp_reshard_after_forward=false`:

| Topology | Setting | Median step | Mean step | Peak allocated | Result |
|---|---|---:|---:|---:|---|
| Full-world FSDP2 | `fsdp_shard_degree=null` | 13.424 s | 13.431 s | about 152.3 GiB | Passed |
| Two-node HSDP | `fsdp_shard_degree=8` | 4.227 s | 4.324 s | about 156.4 GiB | Passed |

Logs and atomic manifests are under
`logs/multinode/20260828_103400_5c2871aa` and
`logs/multinode/20260828_104056_75f84bc4`. Each benchmark measured nine
steps and discarded two warmup observations for its summary. The established
one-node production rate was about 3.6 seconds per step, so HSDP restored most
of the lost performance but did not provide useful two-node scaling.

The limiting cause is verified: NCCL 2.28.9 reported `NET/IB: No device found`
and used `NET/Socket/0` over `eth0`. The containers expose eight active
ConnectX-7 links in `/sys/class/infiniband`, but `/dev/infiniband` is absent on
both nodes. Treat this allocation as Ethernet-only until the platform exposes
the RDMA character devices. Do not infer production multi-node throughput from
these timings. Prefer `fsdp_shard_degree=8` over full-world FSDP when forced to
use this topology, but require an RDMA-enabled allocation before scaling to
four or eight nodes.

## Scheduler And Evaluation Boundary

Verified from the implementation on 2026-08-28: the SSH launcher can be used
as the command executed by a `train_until_step` row. The scheduler will inject
the resume and stop-step Hydra overrides, wait for the launcher, and verify the
resulting checkpoint on shared storage. However, scheduler GPU admission is
currently based only on local `nvidia-smi` GPU IDs, and it does not check or
lease remote-node GPUs before launching the SSH job.

The Rich monitor likewise reports plan state and local GPUs only. It can show
training progress from the shared rank-zero/launcher log, but it does not
aggregate remote GPU utilization, memory, failures, or per-node NCCL state.

Evaluation jobs and persistent vLLM pools run on the node hosting each
scheduler runner. A single runner therefore evaluates on only its local eight
GPUs; additional training nodes remain idle. Starting unrestricted runners on
all nodes against a train/eval/train plan is not yet safe because any runner
may atomically claim the next `train_until_step` row, and GPU identities and
monitor output are not hostname-qualified. Before end-to-end multi-node
orchestration, add node-qualified workers/resources, remote headroom and
heartbeat checks, action capabilities that prevent eval workers from claiming
training rows, and a monitor that aggregates all worker snapshots. Preserve a
single control-plane owner for multi-node training launch and checkpoint/W&B
finalization.
