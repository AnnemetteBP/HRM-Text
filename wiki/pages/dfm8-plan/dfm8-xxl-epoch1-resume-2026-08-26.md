---
type: Plan Record
title: DFM8 XXL Epoch 1 Resume
description: Verified scheduler continuation from step 151K through the first DFM8 epoch.
tags: [dfm8, xxl, training, evaluation, scheduler]
status: stable
last_updated: 2026-08-26
confidence: high
part_of: /pages/dfm8-plan.md
---
# DFM8 XXL Epoch 1 Resume

The stopped DFM8 XXL campaign is resumed in its existing plan:

```text
logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725
```

The source is the fully written eight-rank checkpoint
`checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_151000`, with all eight carry
files and an exact state sidecar. Training continues in the existing W&B run
`peter-sk-sdu/DFM5/40j5y877`, named `dfm8-XXL-1epoch`; the remote history was
at step 151175 before resume, so repeated points through 151175 may be rejected
as non-monotonic before normal logging resumes.

The remaining chain is:

```text
151K -> train to 200K -> short-context 200K eval -> train to 250K
     -> short-context 250K eval -> train until epoch_1
```

Each evaluation graph has 188 GPU rows across standard, DFM, DFM IFEval-DA,
and EuroEval. Every row uses a 4096-token server ceiling; no RULER, LongAlign,
LongBench, Marathon, or other long-context task is present. EMA checkpoints are
exported before evaluation. Non-judged servers retain utilization `0.95`;
generative Talemaader retains batch 16, utilization `0.85`, and the separate
`unsloth/gemma-4-E4B-it` SDPA judge.

Training uses the same environment and precision path as the successful 151K
lineage: explicit `hrm` TorchRun, DFM8 data, XXL architecture, LR `4e-4`, global
batch `262144`, GAS 4, FP32 FSDP parameters, BF16 forward/backward, EMA
`0.9999`, BP 2-to-5 with warmup ratio `0.2`, and sharded checkpoints. The
command also mirrors the latest successful 8K training envelope by explicitly
setting GCC, G++, assembler, compiler path, and `hrm/bin` on `PATH`.

The final numeric target `268857` remains a conservative metadata-derived
upper bound. The scheduler now accepts the fully verified `epoch_1` checkpoint
when the data loader exhausts before that estimate, preventing the historical
false failure caused by demanding a nonexistent estimated step checkpoint.

The runner uses the verified `hrm` environment, `CUDA_HOME=/usr/local/cuda`,
persistent vLLM, FA4 attention, and `VLLM_USE_FLASHINFER_SAMPLER=0`. A detached
watcher records to `start-watch.log`; it waits until every GPU has at least
178000 MiB free, waits another two minutes, then checks scheduler state, the
training process, and forward/backward progress. While the independent DFM10
audit owns the GPUs, only the plan's CPU-side checkpoint waits run.

## Intentional pause at step 152500

On 2026-08-26 the scheduler received a soft stop request. A detached watcher
then waited for `ephemeral_step_152500` to become complete before terminating
the active TorchRun process. The checkpoint has a readable state sidecar,
FSDP/DCP metadata, and all eight rank carry files. No training or scheduler
runner process remains active, and the plan's `stop.request` remains present.

The scheduler consequently records `campaign-train-200000` as failed with
status `-15`; this is the expected result of the intentional SIGTERM, not a
training failure. Before continuing, update that row to resume from
`ephemeral_step_152500`, reset it to pending, and clear the stop request only
when training should actually restart.
