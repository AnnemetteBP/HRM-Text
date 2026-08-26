---
type: Runbook
title: hrm-cu132 FA4 and Triton Recovery
description: Verified environment repair for FlashAttention 4 and Triton compiler discovery.
tags: [environment, flash-attention, triton, training]
status: stable
last_updated: 2026-08-24
confidence: high
---
# `hrm-cu132` FA4 and Triton Recovery

The `hrm-cu132` environment had two independent problems. CUTLASS DSL `4.6.0`
did not expose `cutlass.cute.core.ThrMma`, which the installed FlashAttention 4
stack expects. Triton also failed to discover a C compiler when launched by the
evaluation scheduler, even though `/usr/bin/gcc` was available on an interactive
shell `PATH`.

The environment now uses CUTLASS DSL and CUDA 13 libraries `4.5.2`, installed
with `uv pip`:

```bash
uv pip install --python /home/ucloud/miniforge3/envs/hrm-cu132/bin/python \
  --reinstall nvidia-cutlass-dsl==4.5.2 \
  nvidia-cutlass-dsl-libs-base==4.5.2 \
  nvidia-cutlass-dsl-libs-cu13==4.5.2 --no-deps
```

The Conda environment has persistent `CC=/usr/bin/gcc` and
`CXX=/usr/bin/g++` variables. Scheduler-launched training commands must still
export these explicitly because the scheduler starts subprocesses directly and
does not necessarily source Conda activation hooks:

```bash
CC=/usr/bin/gcc CXX=/usr/bin/g++ \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /home/ucloud/miniforge3/envs/hrm/bin/torchrun ...
```

Validation succeeded for both `cutlass.cute.core.ThrMma` and Triton's NVIDIA
driver/compiler probe. The 8K global/global DFM9 run resumed from the 4K epoch-8
checkpoint after this repair.

For the active 8K campaign, ephemeral checkpoints remain every 500 steps and
regular checkpoints are scheduled every 10,000 steps for all segments after
the currently running `2,150,000` target. The already-running process retains
the command with its original 50,000-step regular interval; changing the plan
does not mutate an already-launched process.

The scheduler also contains an epoch-8 long-context baseline subgraph. After
the `2150000` evaluation teardown, it exports the original 4K `epoch_8`
checkpoint, runs the long-context suite, merges and averages it, and only then
allows training to resume toward `2200000`. This provides a direct pre-8K
extension baseline without competing with the 2150K vLLM evaluation servers.
