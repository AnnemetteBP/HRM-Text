# Experimental cooperative CUDA suspension

`pretrain.py` contains the opt-in training hook; the temporary copied entry
point has been removed. Defaults leave suspension disabled. Runtime helpers
administer the queue/handshake; the launcher owns recovery and the eval
scheduler owns GPU handoffs. This is a controlled single-node rollout with
disk fallback, not a guarantee of multi-hour full-size parity.

## Launch

Use the training Python environment, with the separately installed NVIDIA
binary (default: `cuda-checkpoint-test/bin/cuda-checkpoint`). No CRIU process
dump is needed: CPU workers remain alive.

```bash
python -m training_suspend.controller launch --control-root /path/to/control -- \
  torchrun --standalone --nproc_per_node=8 pretrain.py \
  <normal-training-arguments> \
  suspend_control_dir=/path/to/control \
  'suspend_after_steps=[1000000,1050000]' \
  suspend_poll_interval_steps=10 suspend_wait_poll_seconds=2
```

The launcher materializes a **fresh** NVIDIA checkpoint job handle in the
control directory before exec, avoiding descriptor loss through torchrun.
Every rank verifies it sees the same job file. Never reuse this handle in a
new launch. The hook prints the unique launch directory; use that directory
(not the parent) below. Shared storage is supported for the small control
files, with atomic rename and functioning POSIX locks required. Single node
only; shared files do not imply multi-node CUDA offload support.

## Control

```bash
python -m training_suspend.controller request CONTROL_DIR 1100000 1150000
python -m training_suspend.controller status CONTROL_DIR
python -m training_suspend.controller watch CONTROL_DIR
# In another terminal, once suspend_ready.json exists:
python -m training_suspend.controller offload CONTROL_DIR --lease-seconds 3600
# Release evaluation resources before restoring:
python -m training_suspend.controller restore CONTROL_DIR
```

`request` serializes writers and atomically publishes a whitespace-separated
step list. Rank 0 claims it by rename, broadcasts at fixed step boundaries,
persists the merged queue, and archives the request. Invalid files get an error
receipt. Late steps suspend at the next polling boundary; consumed steps do not
trigger again. All ranks check their queue minimum each step. Stop conditions
take precedence. CLI fields are now in the normal YAML; do not prefix them with `+`.

Suspension follows optimizer/EMA, metrics, validation and checkpoint activity.
A regular recovery checkpoint is saved. All ranks synchronize, empty only
unused allocator cache, acknowledge the exact step/generation and enter CPU
polling. `suspend_ready.json` means **quiescent**, not offloaded.

The controller validates PID/start-time/host/boot identities and all rank
acknowledgements. It checks host memory capacity, then locks all ranks and
checkpoints all ranks sequentially. `offloaded.json` is written only after
state and memory-release verification. Operation intent/outcome is fsynced
to a per-generation journal. Restore follows the original rank order; only
after all ranks are running are generation-bound `resume.PID` files published.
The workers consume these, synchronize, and publish `resumed.json`.

## Recovery and safety

### Managed scheduler launches

`python -m training_suspend.launcher --settings config/training_suspend_b200.json
--control-root /absolute/control -- torchrun ... pretrain.py ...` owns a private
loopback Redis and the checkpointable supervisor. Shim/NCCL preload is confined
to that child tree. Check machine-specific library paths before reuse.

The scheduler's `cooperative_training` metadata makes normal training rows
boundaries of one live process. A boundary is complete only after the regular
disk checkpoint and GPU-release checks. Before returning GPUs to eval, it
creates `CONTROL/hold`; the next training row removes that hold and requests
restoration after inference servers drain. Use SQLite/persistent servers only.

Recovery allows 900 seconds for CUDA restore and 120 seconds for rank
acknowledgement. On failure it verifies the regular sharded checkpoint, stops
only recorded launcher descendants, waits for safe GPU availability, and
relaunches with a fresh CUDA job handle and the remaining suspend queue.
At most three disk restarts per boundary are allowed. Process identities protect unrelated
workloads. Occupied GPUs and explicit holds defer restore; they do not trigger
termination. Automatic fallback currently supports no-carry sharded checkpoints.

`CONTROL/active.json` points to the UUID control directory. Do not run a second
`watch` for managed launches. `CONTROL/stop.request` terminates the owned
launcher without restarting. Scheduler soft-stop drains to the active training
boundary; parked training stays held until scheduling resumes. Training's
terminal gate depends only on GPU inference, not merges, averages or syncs.

CPU tests cover safety gates and process-tree cleanup. The two-GPU
`training_suspend.boundary_smoke` tests normal restoration and an injected
CUDA restore error followed by disk recovery. Both produced exact final model
and optimizer/EMA equality on 2026-10-12, without W&B logging. Evidence:
`/work/dfm/tmp/suspend-boundary-main-v2-20261012/`.

### Manually managed experiments

- Run `watch` under an external supervisor/tmux before suspending. This tool
  does not silently install a service. When the offload lease expires it
  attempts recovery; an abandoned ready-only handshake is cancelled after
  `--ready-timeout` seconds (default 600).
- `recover` reconciles actual CUDA states after a partial operation or
  controller restart, then follows the restore path. Never use blind toggle.
- A `hold` file in the launch directory explicitly prevents controller
  restoration/cancellation. Remove it only when that pause should end.
- Recovery waits for sufficient GPU memory and for new GPU processes (not
  present before offload) to disappear. It never kills evaluation, training
  or unrelated processes. An external scheduler must still reserve the GPUs:
  a memory observation is not an exclusive resource lease.
- A failed CUDA operation can leave a process unrecoverable. Preserve the
  regular disk checkpoint and use an ordinary restart if recovery fails.
- Generation receipts are historical; do not interpret an old offloaded
  receipt as current state after a restored/resumed receipt exists.
- CPU threads, NCCL watchdogs and data-loader workers remain alive. Long
  pauses, IPC types and multi-node use require separate validation.

## Tests

CPU-only:

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. \
  python -m pytest -q tests/test_training_suspend.py tests/test_training_suspend_distributed.py
```

Bounded GPU smoke (only explicitly chosen GPU IDs):

```bash
python -m training_suspend.smoke --gpus 1 --output /new/path/single
python -m training_suspend.smoke --gpus 1,2 --output /new/path/two
python -m training_suspend.smoke --gpus 0,1,2,3,4,5,6,7 --output /new/path/eight --compile
```

For a full-size synthetic smoke, add `--full-size` and select all eight GPUs.
This uses XXL_wide, BP8, context 4096, vocabulary 262144, GBS 262144 and GAS4;
it requires otherwise empty GPUs. It does not load production weights or log
to W&B. The 2026-10-12 compiled test completed two offload/restore cycles but
failed exact parity (differences already occurred before suspension). See
`wiki/pages/cooperative-cuda-suspension.md` for evidence and limitations.

By default the harness uses the real training entry point, XXS backbone,
64-token context, reduced 256-token vocabulary, synthetic deterministic data,
FSDP2, GAS 2, BP5, and six optimizer steps. It compares uninterrupted training
against suspension after steps 2 and 4. It disables W&B, requires at least
8 GiB free per selected GPU. The old test-only allocator cap was removed with
the copied entry point; the tiny workload is intrinsically small. It only terminates
its own subprocess group on a test failure/deadline.

`--legacy-nccl` is an explicit experimental alternative that sets
`NCCL_CUMEM_ENABLE=0`, `NCCL_CUMEM_HOST_ENABLE=0`, and `NCCL_NVLS_ENABLE=0`
only for smoke child processes. A pass with these flags is **not** a pass
with production/default NCCL allocations. Both modes must retain their own
receipts; never silently enable this workaround in production.

Receipts include step metrics, model/optimizer/EMA exact comparison, transfer
timing, CUDA-operation journals and memory logs. This is not a large-model
capacity benchmark or a validation of carry-enabled architectures. Use
dedicated capacity for prolonged pauses and production-size validation.

Use `--pause-seconds 900 --timeout 2400` for two 15-minute offloaded pauses.
The harness checks worker liveness, CUDA state, and owned GPU allocations
throughout the pause, recording `pause_health` journal entries. CUDA failures
retain stdout/stderr diagnostics. Launch receipts record NCCL overrides.

The narrower tested two-rank workaround is `NCCL_CUMEM_ENABLE=0` together with
`NCCL_NVLS_ENABLE=0`, without `--legacy-nccl`; host cuMem can stay at default.
Do not interpret this as default-NCCL support or a production rollout.
These overrides belong on a fresh worker launch before NCCL initialization;
changing controller environment variables cannot retrofit live communicators.

### Verified on 2026-10-12

Sixteen CPU tests pass. Single GPU, two GPUs with `--legacy-nccl`, and eight
GPUs with `--legacy-nccl --compile` passed two cycles with exact model,
optimizer/EMA and per-step metric parity. Default two-GPU NCCL checkpointing
stalled and timed out: this is not production-ready with default settings.
See [the wiki evidence](../wiki/pages/cooperative-cuda-suspension.md) for
receipt paths and remaining validation gates. Production training was untouched.

Follow-up: with only `NCCL_CUMEM_ENABLE=0 NCCL_NVLS_ENABLE=0`, two-rank
short pauses and compiled eight-rank **two 15-minute pauses** passed exact
model/optimizer/EMA/per-step-metric parity against the same-settings baseline.
All 50 long-pause health checks reported 0 MiB owned GPU allocation. Offload
took 49-52s and restore/release 71-76s; this is not a large-model bandwidth
benchmark. Multi-hour pauses, full-size training and real eval handoff remain
unvalidated; default NCCL is still incompatible in the tested setup.

## Experimental NCCL checkpoint shim

The separate NCCL 2.32.3 experiment uses `--nccl-shim`. The hook calls
`ncclCheckpointPrepare` after draining GPU work, before publishing readiness,
and `ncclCheckpointRestore` after CUDA restoration, before the resume barrier.
The shim is off by default (`SUSPEND_TEST_NCCL_SHIM=1` is set by the harness).
It requires a fresh launch; this cannot be attached to existing training.

Local isolated artifacts (2026-10-12):

- `/work/dfm/tmp/nccl-shim-env`: system-site-packages venv over `hrm`, with only
  `nvidia-nccl-cu13==2.32.3` installed locally using `uv pip --no-deps`.
- `/work/dfm/tmp/nccl-checkpoint-2.32.3`: NVIDIA source tag `v2.32.3-1`,
  commit `12df1a11afad322be5a204a2db890161cbf8131d`; shim built with `make -j8`,
  CUDA headers/libraries from the existing `audit` environment, no edits there.
- `/work/dfm/tmp/nccl-shim-tools`: isolated Redis server and hiredis C library.
  Conda package `hiredis` is the Python binding, not the required C development
  library; the latter was built from hiredis v1.3.0 into this prefix.

Start a dedicated loopback-only Redis server before tests, stop it afterwards:

```bash
/work/dfm/tmp/nccl-shim-tools/bin/redis-server \
  --bind 127.0.0.1 --port 16389 --save '' --appendonly no --protected-mode yes
```

The test's `/work/dfm/tmp/nccl-shim-kvs.txt` contains `127.0.0.1:16389`.
Use a separate rendezvous service/file for concurrent campaigns.

```bash
SHIM=/work/dfm/tmp/nccl-checkpoint-2.32.3/contrib/nccl_checkpoint/build/lib/libnccl-checkpoint-shim.so
NCCL=/work/dfm/tmp/nccl-shim-env/lib/python3.13/site-packages/nvidia/nccl/lib
LD_LIBRARY_PATH="$NCCL:/home/ucloud/miniforge3/envs/audit/targets/x86_64-linux/lib" \
LD_PRELOAD="$SHIM:$NCCL/libnccl.so.2" \
NCCL_CHECKPOINT_KVS_PATH=/work/dfm/tmp/nccl-shim-kvs.txt NCCL_DEBUG=INFO \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/work/dfm/tmp/nccl-shim-env/bin/python -m training_suspend.smoke \
  --gpus 1,2 --nccl-shim --timeout 600 --output /new/path/shim-two
```

Both libraries must be preloaded in this order: shim alone failed to resolve
`ncclCommInitRankConfig` through `RTLD_NEXT` with this PyTorch build. Verify the
actual runtime with `ncclGetVersion` or NCCL logs: `torch.cuda.nccl.version()`
still reports its build-time 2.28.9 in this environment, not loaded 2.32.3.
Leave the NCCL disabling overrides unset. CUDA graph capture is unsupported;
compilation alone is not graph capture. This is not a production rollout.

Validated: two-rank uncompiled and eight-rank compiled XXS both passed two
offload/restore cycles with exact model, optimizer/EMA and per-step metric
parity, with P2P/CUMEM and NVLS enabled. Eight-rank pauses requested 30 seconds;
all health checks reported zero owned GPU memory. Receipts:
`/work/dfm/tmp/suspend-shim-two-preload-20261012/result.json` and
`/work/dfm/tmp/suspend-shim-eight-compiled-20261012/result.json`.
Production dependencies, training and scheduler were unchanged; test services
were stopped after completion. Longer pauses on this shim and production-size
performance still require validation.

To shorten an active smoke's pauses, create `finish_early.request` in its
`--output` directory. The harness will restore through its own controller and
skip the wait on subsequent cycles, retaining final parity comparison. Do not
restore externally while the harness's health monitor is active: it interprets
changed CUDA state as a failure and terminates its test workers. Suspending the
monitor with signals is not a supported handoff mechanism.
