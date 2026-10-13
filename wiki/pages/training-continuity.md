---
type: Policy
title: Training Continuity Across Evaluations
description: Evaluation and administrative failures must not strand the next training segment.
status: stable
confidence: high
last_updated: 2026-10-12
tags: [training, scheduler, operations, recovery]
---
# Training Continuity Across Evaluations

## Mandatory Rule

2026-10-12 resume: after the isolated full-size suspension experiment,
restarted the existing SQLite scheduler plan
`logs/scheduler/dfm10_XL_epoch9_20260831` (database
`/tmp/dfm14-xxl-wide-production/jobs.sqlite`). Row
`xxlw-dfm14-train-1000000` resumes `ephemeral_step_991000` from
`checkpoints/dfm14/XXL-wide-from-dfm13-step870000`, stopping at 1M.
The original production environment, BP8, LR settings and W&B
`DFM5/dfm10-xxl-wide` are retained; experimental NCCL preload/library overrides
are absent. New log, preserving the previous attempt:
`logs/training/dfm14_XXL_wide/to_1000000_from_991000/train_until_step_1000000.log`.
Checkpoint loading and progress beyond 991000 were verified. The experimental
suspend path is not enabled in production.

User instruction, 2026-10-11: training must remain able to resume regardless
of evaluation failures or unfinished merges, averages, reports and W&B syncs.
Those CPU/publication operations must not be success dependencies of training.
Retain their work for later completion; never fabricate successful results.

Explicit user pauses still take precedence. Resume only from a valid completed
checkpoint, with the required GPUs safely available. Do not overlap training
with incompatible inference processes or terminate unrelated GPU workloads.

## Handoff Requirements

Operational pause 2026-10-12: user stopped DFM14 XXL-wide at 991K. The complete
`ephemeral_step_991000` in
`checkpoints/dfm14/XXL-wide-from-dfm13-step870000` was verified and hard-link
preserved under `/work/dfm/tmp/dfm14-xxl-wide-stop-991000-20261012` before the
training process group was interrupted. A few steps beyond 991K had already
run; those unsaved steps are not part of the resume checkpoint. Scheduler
`logs/scheduler/dfm10_XL_epoch9_20260831` has `stop.request`; no automatic
resume is authorized. On the next requested resume, update the interrupted
1000K segment's source from step_950000 to ephemeral_step_991000 before reset.

- Gate training on safe completion/termination of GPU evaluation activity and
  release of owned servers, not successful benchmark scores or publication.
- Failed, cancelled or retry-exhausted inference must have a recovery path
  that releases resources and permits training; blocked descendants must not
  make the training dependency graph permanently unsatisfiable.
- Merges, averages, synchronization and reports may finish later on CPU.
- Administrative locks are short-lived editing tools, not unattended pauses.
  Release them in failure cleanup as well as on success. Never end a turn or
  leave monitoring with a lock held unless the user explicitly requested it.
- After editing a live plan, verify lock/stop state, the next training row's
  dependencies, teardown, and actual training progress. A pending row or a
  live scheduler process is not proof that the handoff works.
- Future scheduler safeguards should include owned, expiring edit leases and
  an independent stale-handoff alarm/recovery path. These are requirements,
  not claims that the current implementation already provides them. Never
  blindly override an explicit user pause or an active edit transaction.

## Incident and Supersession

On 2026-10-10 the final scheduled 950K inference finished at 22:31:40 CEST.
An administrative lock left enabled during cross-machine reconciliation
prevented pending publication, teardown and the next training segment from
being claimed. At 05:41 CEST on 2026-10-11, eight GPUs had been idle for about
7 hours 10 minutes, approximately 57 GPU-hours. This was an operational error,
not a requirement to wait for more evaluation results.

This policy supersedes any interpretation of earlier campaign-wide barriers
that requires merges, averages or syncs to complete before training can resume.
Documentation alone does not repair existing dependencies or implement leases;
live plans and scheduler behavior must be verified separately.

Related: [evaluation baseline](dfm14-evaluation-baseline.md) and
[SQLite scheduler runbook](model-architecture/request-shared-eval-scheduler.md).

## GPU State Offload Candidate (2026-10-11)

Update 2026-10-12: an isolated [cooperative suspension prototype](cooperative-cuda-suspension.md)
now exists. Short-context XXS tests passed on one GPU and on two/eight GPUs
with test-only NCCL compatibility flags, including compiled eight-rank exact
parity. Default two-rank NCCL offload stalled. This does not establish safety
for the production workload or authorize migration. Further 2026-10-12 tests
narrowed the workaround to disabling device cuMem and NVLS only; compiled
eight-rank XXS passed two 15-minute offloaded pauses with exact parity and
zero owned GPU memory throughout. Default NCCL, full-size and multi-hour
production suspension are not validated by this result.

Local B200 driver verified as 610.57.04. NVIDIA's
[cuda-checkpoint documentation](https://github.com/NVIDIA/cuda-checkpoint)
describes device-memory offload to driver-managed host RAM, release of CUDA
GPU resources, and restoration into the same running process. Driver 610
adds cuIpcGetMemHandle IPC support with job-aware launch setup; this does not
prove our eight-rank NCCL/FSDP workload can be suspended safely.
Neither cuda-checkpoint nor criu was found on the inspected shell PATH.
At the original 2026-10-11 inspection no suspend/restore experiment had been
performed; the isolated 2026-10-12 results above supersede that observation.
Production was not altered.
Before adopting it, test collective quiescence, rank coordination, watchdog
timeouts, memory capacity, numerical continuity and recovery on a disposable
multi-GPU workload. CPU threads are not suspended by cuda-checkpoint itself.

### Isolated test installation (2026-10-12)

The earlier PATH observation is superseded for the newly created test env:
`/home/ucloud/miniforge3/envs/cuda-checkpoint-test`.
Activate with `conda activate cuda-checkpoint-test`.

- NVIDIA cuda-checkpoint 610.57.04, official x86_64 binary pinned to upstream
  commit `00d5cce84c628088d6caa203fc4af40c1538b6f7`.
- CRIU 4.2.1, source tag v4.2.1, commit
  `9539417f3e3cfa4eb84c319cd71f4d52f1f08645`, built with eight CPU jobs.
- CRIU CUDA plugin installed at `$CONDA_PREFIX/lib/criu/cuda_plugin.so`.
- Neither CRIU nor libnet was available from conda-forge. Conda supplies
  Python 3.12, make, pkg-config, c-compiler, protobuf-c, libnl and libcap.
  libnet 1.3 was built from its official release into the same prefix.
- CRIU build source: `/work/dfm/tmp/criu-checkpoint-test-src`; libnet source:
  `/work/dfm/tmp/libnet-1.3`. The CRIU protobuf descriptor generation rule
  was patched to use `pkg-config protobuf --variable=includedir` instead of
  `/usr/include`. A prefix-local `include/google/protobuf-c -> ../protobuf-c`
  compatibility symlink supplies the old header path CRIU expects.
- Build/install targets: `make -j8 criu cuda_plugin`, then
  `make install-criu install-cuda_plugin`, both with
  `PREFIX=/home/ucloud/miniforge3/envs/cuda-checkpoint-test` and
  `SBINDIR=/home/ucloud/miniforge3/envs/cuda-checkpoint-test/bin` inside the env.
- Optional setproctitle, AMD plugin, GnuTLS and nftables support were not built.
  No system package, driver, training environment or scheduler change was made.

Verified `cuda-checkpoint --help`, `criu --version`, and dynamic dependencies
for CRIU and its CUDA plugin (no missing libraries). This verifies installation,
not kernel/container permissions or actual process restore. No CRIU kernel
probe, process dump, GPU suspension or NCCL round-trip was attempted.
