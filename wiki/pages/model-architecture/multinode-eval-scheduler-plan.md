---
type: Plan
title: Multi-Node Evaluation Scheduler Plan
description: Coordinator-worker design for safe multi-node evaluation, persistent vLLM reuse, cluster training handoff, and aggregate monitoring.
tags: [evaluation, scheduler, multi-node, vllm, monitoring, operations]
status: draft
last_updated: 2026-08-28
confidence: high
---
# Multi-Node Evaluation Scheduler Plan

## Objective

Extend `eval_scheduler` from one local eight-GPU runner into a fixed-membership
cluster scheduler for two, four, or eight mutually reachable eight-GPU nodes.
It must use every eligible GPU for independent evaluation work, preserve the
existing dependency/merge/sync/average semantics, and hand the whole cluster
to multi-node training without resource collisions.

The target is one scheduler plan and one authoritative control plane. Do not
run unrestricted copies of the current `Runner` against the same plan on every
node. Although `plan.tsv` claims are locked, GPU identities are local integers,
resource admission is process-local, and any runner can currently claim a
`train_until_step` row.

## Architecture Decision

Use a coordinator-worker architecture:

- A single coordinator on the control node is the only process allowed to
  mutate `plan.tsv`, finalize attempts, satisfy dependencies, launch
  multi-node training, and perform merge/sync/average/report actions.
- One worker daemon per node owns that node's subprocesses and persistent vLLM
  pool. It advertises node-qualified GPU resources and executes only jobs whose
  capability the coordinator assigns to it.
- Workers communicate with the coordinator over a low-rate authenticated JSON
  control protocol on the private allocation network. A standard-library HTTP
  server is sufficient for eight workers; avoid adding a database or external
  service for the first implementation.
- The existing shared filesystem remains the artifact and log plane, not the
  distributed lock or scheduling authority. Only the coordinator uses
  `PlanLock` for plan edits.
- Resource identities are `(node_id, gpu_id)`, never bare GPU integers. Every
  lease has a unique lease/fencing token and worker boot ID.

The existing single-node `eval_scheduler run --gpus ...` path remains
supported through a local-worker adapter and must retain current behavior.

## Execution Profiles

Every action maps to a non-overridable capability and resource profile:

| Profile | Actions | Placement |
|---|---|---|
| `control_cpu` | waits, barriers, merges, averages, reports | Coordinator only |
| `node_gpu` | HF export and all evaluation actions | One GPU on one eligible worker |
| `node_teardown` | persistent-server teardown | Broadcast to selected workers |
| `cluster_train` | `train_until_step` | Coordinator launches one fixed-membership SSH TorchRun job after a cluster drain |

Plan constraints may narrow placement by node, GPU count, environment, free
memory, model-server compatibility, or labels. They must never broaden an
action's capability. In particular, an eval worker cannot claim a training or
W&B-finalization action.

Add a backward-compatible plan schema revision with explicit
`execution_scope`, `required_capability`, `gpu_count`, and `node_selector`
fields. Old plans derive these values from `action` and `gpu_policy`. Keep
runtime scheduling state out of `plan.tsv`; assignments belong in coordinator
state and append-only events.

## Coordinator State And Protocol

The coordinator owns:

- the current plan and dependency graph;
- registered workers, boot IDs, capabilities, software identity, and last
  heartbeat;
- node-qualified GPU snapshots and persistent-server leases;
- active job leases with attempt number, worker, GPU, issue time, heartbeat,
  and fencing token;
- cluster mode: `evaluating`, `draining`, `training`, or `stopped`;
- append-only status/attempt telemetry and an atomically replaced cluster
  snapshot for the monitor.

Workers register with hostname, stable node ID, boot UUID, repository commit,
Python environment, Torch/CUDA/FA4 identity, GPU inventory, and supported
actions. Heartbeats report GPU memory/utilization, active exact process-group
PIDs, job progress, vLLM lease keys, and worker errors. Use a random bearer
token stored mode `0600` in the plan directory. Bind to the allocation's
private interface; launch workers over SSH so the token need not be typed on
remote shells.

Assignment and completion are idempotent. A worker accepts a job only when the
assignment includes its current boot ID and a new lease token. The coordinator
accepts progress or completion only for the current token. This prevents a
late result from an expired worker attempt from overwriting a retry.

## Evaluation Scheduling

For each ready GPU job, choose among fresh worker heartbeats using:

1. required capability and node selectors;
2. compatible resident vLLM server, when available;
3. effective free-memory gate, including reclaimable incompatible-server
   memory using the existing policy;
4. highest effective headroom, then least recently assigned GPU.

Each worker keeps its own `VLLMServerPool`, keyed by node, GPU, checkpoint,
EMA mode, backend, model length, memory utilization, attention backend, chat
template, and judge configuration. A compatible server is reused only on the
same physical GPU. Incompatible leases are terminated by exact PID/process
group before replacement.

Independent shards from later checkpoints may fill GPUs while the tail of an
earlier checkpoint is still running, subject to plan dependencies. Merge a
sharded task as soon as all of its shards complete. Sync a single-shard task or
merged task immediately. Evaluation failures may block their own merge and
averages, but a `terminal_barrier` must still be able to release the cluster
for the next training segment.

## Training Handoff

`train_until_step` remains a coordinator action and calls
`scripts/launch_multinode_torchrun.py`. Before launch, the coordinator:

1. enters `draining` and stops issuing eval assignments;
2. lets running eval attempts finish unless the plan explicitly requests
   cancellation;
3. broadcasts persistent-server teardown and waits for acknowledgements;
4. verifies every selected node heartbeat is current and every selected GPU is
   free enough for training;
5. runs launcher preflight/NCCL smoke as configured, then starts TorchRun;
6. marks all selected nodes and GPUs leased to the training job;
7. follows the launch manifest and rank-zero training log for progress;
8. verifies the regular completion checkpoint before releasing the lease.

An eval merge, average, report, or W&B failure must not leave GPUs idle when a
terminal campaign barrier permits training to continue. Conversely, training
must never start while a worker still owns an eval or vLLM process on a
selected GPU.

## Failure And Stop Semantics

- **Soft stop:** stop new assignments; active evals or training finish. Workers
  keep heartbeating and close persistent servers before exit.
- **Abort:** coordinator requests exact process-group termination on workers;
  the SSH training launcher applies its existing coordinated TERM/KILL path.
- **Worker loss:** after a bounded heartbeat TTL, mark its leases lost, fence
  the old boot ID, and retry only affected jobs. On reconnect, the worker must
  terminate or report any orphan it owns before becoming eligible.
- **Coordinator restart:** rebuild dependency state from `plan.tsv`, events,
  attempt manifests, and worker reconciliation. Do not blindly reset every
  running row. Adopt a live matching lease or retry it after fencing.
- **Server/client coupling:** a failed vLLM server fails its client attempt and
  invalidates the lease; a failed client tears down task-specific servers when
  they are not reusable.
- **Shared-storage outage:** stop dispatch, retain current leases, and avoid
  finalization until logs/checkpoints are durable.

## Aggregate Monitor

The monitor reads the coordinator's atomic cluster snapshot rather than
running SSH or remote `nvidia-smi` on every refresh. Keep the current Rich and
plain modes, with a default 30-second refresh for interactive use.

Display:

- coordinator mode, plan counts, worker count, stale/unreachable workers, and
  cluster-wide ETA;
- one compact row per node/GPU, ordered by node then GPU, including memory,
  utilization, model/checkpoint, task/shard, batch, attempt, progress, and ETA;
- controller CPU jobs and the multi-node training job with node/rank health,
  current step, rate, ETA, and launcher phase;
- ready and blocked queues with clipping based on current terminal dimensions;
- persistent vLLM identity/reuse state and explicit stale-progress warnings.

Task progress parsers remain centralized and consume shared logs. Worker
heartbeats provide GPU/process liveness and the active log/attempt identity.
This preserves existing task-specific progress extraction while adding remote
resource truth.

## Implementation Sequence

### Phase 1: Resource And State Refactor

1. Introduce `NodeId`, `GpuId`, `ResourceId`, `WorkerInfo`, `Lease`, and action
   execution profiles in separate modules.
2. Separate plan/dependency coordination from local subprocess execution.
3. Add the backward-compatible plan schema fields and node-qualified columns
   to status/attempt telemetry.
4. Adapt the current runner through an in-process local worker; require all
   existing tests and a live single-node smoke to remain unchanged.

### Phase 2: Coordinator And Worker MVP

1. Implement registration, heartbeat, long-poll assignment, progress,
   completion, teardown, and fencing-token endpoints.
2. Add `eval_scheduler coordinator` and `eval_scheduler worker` Typer commands.
3. Add atomic coordinator snapshots and restart reconciliation.
4. Test multiple fake workers, duplicate completions, stale leases, worker
   restarts, and concurrent plan edits.

### Phase 3: Multi-Node Evaluation

1. Add an SSH worker launcher using the host-file/environment conventions of
   the TorchRun launcher and exact remote PID manifests.
2. Move persistent vLLM ownership into each worker and make lease keys
   node-qualified.
3. Run a two-node campaign with standard, DFM, EuroEval, judged, sharded,
   merge, sync, and average rows.
4. Expand to four and eight nodes and measure dispatch overhead, server reuse,
   shared-filesystem pressure, tail utilization, and end-to-end wall time.

### Phase 4: Cluster Training Handoff

1. Implement cluster drain, acknowledged vLLM teardown, headroom verification,
   and coordinator-owned SSH TorchRun launch.
2. Surface launcher manifest/rank state in coordinator snapshots.
3. Exercise eval-to-train-to-eval with a short two-node job, including a failed
   eval, failed worker, failed training rank, soft stop, and coordinator restart.
4. Validate the same flow on the intended four- or eight-node production
   topology before using it for DFM10.

### Phase 5: Operations And Hardening

1. Add `cluster status`, `cluster stop`, `cluster abort`, `worker list`, and
   `worker drain` commands.
2. Add Rich cluster monitor tests for narrow/wide and short/tall terminals.
3. Document firewall/interface/token setup, startup, recovery, and teardown.
4. Add retention/rotation for heartbeat snapshots and event logs without
   removing attempt evidence.

## Acceptance Gates

- Existing single-node plans run without migration and produce identical
  merged metrics and W&B keys.
- No job can be active under two valid leases, and a stale completion cannot
  finalize a retried row.
- Two nodes sustain 16 concurrent one-GPU eval jobs; four and eight nodes
  sustain 32 and 64 when the queue and storage permit.
- On a large homogeneous shard queue, evaluation throughput reaches at least
  75% parallel efficiency relative to the measured one-node baseline after
  excluding one-time model export and server startup.
- Compatible persistent servers are reused locally; no server is reused across
  incompatible checkpoint/EMA/config keys.
- Loss of one eval worker retries only its jobs and does not corrupt completed
  merges or W&B history.
- Cluster training cannot start until all selected eval leases are released;
  eval finalization failures do not unnecessarily block an allowed training
  barrier.
- The monitor reports every node/GPU and flags stale worker data within two
  heartbeat intervals.
- A two-node end-to-end train/eval/train campaign survives coordinator restart
  and one deliberately failed worker before production rollout.

## Expected Result

The first useful milestone is multi-node evaluation only: one coordinator plus
workers should turn 16, 32, or 64 GPUs into a shared opportunistic shard pool
while preserving immediate merges and syncs. Training handoff follows after
lease fencing and worker recovery pass. This ordering provides evaluation
speed early without putting production checkpointing or W&B history at risk.

## Implementation Status (2026-08-28)

Phases 1--5 are implemented on the `multinode` branch:

- backward-compatible plan placement/capability fields and node-qualified
  resource/lease records;
- authenticated coordinator HTTP service, worker registration/heartbeats,
  assignment polling, boot-ID fencing, idempotent completion, worker draining,
  and atomic restart snapshots;
- per-node workers with local persistent-vLLM pools and an SSH launcher that
  records and stops exact worker process groups;
- coordinator-managed explicit and implicit server teardown, cluster drain,
  and wrapping of ordinary TorchRun rows with the fixed-membership SSH
  launcher when `multinode_hostfile` is configured;
- training child-process manifests and coordinator restart adoption;
- node/GPU aggregate plain and Rich monitors with heartbeat age, memory,
  utilization, model/task/shard progress, control/training jobs, and a
  provisional cluster ETA;
- cluster status, monitor, stop, abort, worker list, worker drain, worker
  launch, and exact worker-stop commands.

The original single-node `run --gpus ...` command remains unchanged. The full
local scheduler suite passes (`47` tests on 2026-08-28), including cluster
schema, assignment, an end-to-end HTTP worker execution/completion round trip,
fencing, teardown, authentication, snapshot restore, monitor, and
training-command wrapping tests.

A one-node compatibility deployment was started against the existing DFM8 XXL
campaign on 2026-08-28. It uses one coordinator, one local eight-GPU worker,
and the unchanged plan. This migration exposed and fixed a compatibility rule:
future `wait_checkpoint` control jobs must remain active alongside cluster
training and must not be treated as drain blockers. Other active control jobs
still block the training handoff.

Cluster-scoped training is coordinator-owned rather than represented by worker
evaluation leases. The aggregate monitor therefore projects the active
training job, progress, and ETA onto every participating worker GPU while the
snapshot is in `training` mode; those GPUs must not be displayed as idle.

The one-node compatibility run was stopped after the fully written
`ephemeral_step_178000` checkpoint on 2026-08-28. To protect that state from
automatic ephemeral cleanup, its distributed checkpoint files were promoted
with same-filesystem hard links to `fsdp2_step_178000`, and a separate atomic
`checkpoint_state_step_178000.json` marks it as a regular checkpoint. Strict
regular-checkpoint validation passes. The pending training row resumes from
`step_178000`; the plan remains stop-requested until an explicit restart.

**Superseded on 2026-08-28:** the earlier claim that real multi-node behavior
was unverified no longer applies. A two-node launcher preflight, 16-rank NCCL
smoke, changed-world checkpoint resume, and ten-step full-FSDP/HSDP training
comparison passed. The worker-based multi-node evaluation campaign and the
complete train/eval/train failure-injection gate remain outstanding. The
training measurements also exposed an allocation blocker: NCCL used
`NET/Socket` because `/dev/infiniband` was absent despite active RDMA devices
in sysfs. See the [SSH launcher runbook](multinode-ssh-launcher.md) for exact
results. The control protocol uses
bearer-authenticated plain HTTP and must bind only to the private allocation
network. The shared filesystem must expose identical absolute paths and
ownership on every node.

### Return To One Node, 2026-08-28

After the two-node allocation ended, the protected `step_178000` checkpoint
resumed on a fresh single eight-B200 node through the same coordinator plan.
The pending `campaign-train-200000` row retained the established one-node
geometry: GBS 262144, GAS 4, full-node FSDP2, no activation checkpointing,
regular checkpoints every 10K steps, ephemeral checkpoints every 500 steps,
and W&B run `DFM5/40j5y877`. The first launch attempt loaded the checkpoint but
stopped before training because the fresh node lacked `/home/ucloud/.netrc`.
Restoring the existing W&B credential and resetting only that training row to
pending allowed a clean resume from `step_178000`; eight-rank training passed
step 178020 with all GPUs active. On a fresh allocation, verify W&B login before
clearing the campaign stop request.
