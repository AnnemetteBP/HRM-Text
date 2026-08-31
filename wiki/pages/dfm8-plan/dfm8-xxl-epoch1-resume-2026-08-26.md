---
type: Plan Record
title: DFM8 XXL Epoch 1 Resume
description: Verified scheduler continuation from the latest complete ephemeral through the first DFM8 epoch.
tags: [dfm8, xxl, training, evaluation, scheduler]
status: stable
last_updated: 2026-08-27
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

## Checkpointed continuation from step 152500

The pause description above was superseded later on 2026-08-26. The scheduler
was resumed from the verified `ephemeral_step_152500` checkpoint with:

```text
activation_checkpointing=full
compile_train_batch=false
memory_log_interval=1
```

The first functional-checkpoint implementations failed before advancing the
optimizer because FSDP2 recomputation produced FP32 tensors where the original
forward saved BF16 tensors. Those failed starts did not alter checkpoint state.
The working implementation applies PyTorch composable checkpoint wrappers to
Transformer blocks before FSDP2 wrapping. It passed step 152500 and continued
normally in the existing W&B run and scheduler campaign.

The matched no-checkpoint control peaked at 143027 MiB allocated and 165168 MiB
reserved per GPU. Full checkpointing peaked at 41984 MiB allocated and 49970
MiB reserved, reductions of 70.6% and 69.7%, respectively. The current
checkpointed path runs at approximately 6.4 seconds per optimizer step after
warmup, versus 3.53 seconds for the compiled control. The throughput comparison
includes the current requirement to disable whole-batch compile.

## Selective checkpoint smoke and normal continuation

Training was soft-stopped again after the fully written
`ephemeral_step_153500` checkpoint. A W&B-disabled eight-step smoke from that
exact state tested `activation_checkpointing=l_only` with compile disabled and
no checkpoint writes. It measured 90228 MiB peak allocated, 105344 MiB peak
reserved, and a 5.59-second median optimizer step. The production campaign is
then resumed from step 153500 with `activation_checkpointing=none`,
`compile_train_batch=true`, and normal W&B logging, as requested.

On 2026-08-27 the scheduler was soft-stopped again and the exact production
TorchRun was terminated at approximately step 161115. The newest authoritative
resume point is the fully written `ephemeral_step_161000`, with DCP metadata,
state JSON, and all eight carry files. The 115-step unsaved tail is intentionally
discarded. All carries contain `None`, confirming that this HRM variant has no
cross-batch recurrent state to redistribute when changing world size.

## Production resume from step 161000

On 2026-08-27 the existing scheduler plan was repaired under its advisory lock
and resumed from `ephemeral_step_161000`. The plan repair utility now accepts an
explicit `--resume-tag`; this avoids embedding an obsolete ephemeral in future
recoveries. The failed 200K training row was reset to pending, its log directory
was changed to `logs/training/dfm8_XXL_1epoch/step_161000_to_200000`, and the
same evaluation and continuation graph was retained.

The resumed command explicitly selects the measured fastest compatible
single-node path:

```text
activation_checkpointing=none
compile_train_batch=true
fsdp_shard_degree=null
fsdp_reshard_after_forward=false
fsdp_accumulation_sync_mode=no_sync
```

It retains eight GPUs, GBS 262144, GAS 4, FP32 FSDP parameters, BF16 compute,
FA4, and W&B run `DFM5/40j5y877`. All eight ranks restored `step=161000`,
`start_epoch=1`, and `skip_batches=644000`. The run advanced past step 161015;
post-compilation five-step intervals were approximately 18 seconds. W&B warns
about non-monotonic points until the resumed process passes the previously
logged unsaved tail at step 161111; those warnings are expected and do not
alter checkpoint correctness.

## Capacity crossover interpretation

The configured XXL model has `3,978,299,136` parameters, versus
`1,786,773,504` for XL. At GBS 262144, the 50K, 100K, and 150K checkpoints
represent 13.11B, 26.21B, and 39.32B tokens, or only 3.3, 6.6, and 9.9 tokens
per XXL parameter. The estimated end of epoch one at step 268857 is 70.48B
tokens, or 17.7 tokens per parameter. A mature XL checkpoint from the long
DFM6/DFM7/DFM8 lineage has seen hundreds of billions of tokens, so comparing
it directly with the current sub-epoch XXL checkpoint conflates capacity with
training maturity.

The first three XXL headline/suite points are:

| Metric | 50K | 100K | 150K |
|---|---:|---:|---:|
| Danish headline | 0.442 | 0.517 | 0.539 |
| English headline | 0.460 | 0.543 | 0.542 |
| Math/code headline | 0.434 | 0.488 | 0.438 |
| Standard suite | 0.415 | 0.530 | 0.559 |
| DFM suite | 0.492 | 0.587 | 0.614 |
| EuroEval suite | 0.436 | 0.484 | 0.464 |

This is not a broad plateau: standard and DFM continue to improve from 100K
to 150K, while English is flat and math/code and EuroEval are volatile. Expect
the first credible capacity separation on difficult benchmarks near the end
of epoch one or during epoch two. A defensible ceiling comparison needs at
least roughly 80--160B tokens (20--40 tokens per XXL parameter), corresponding
to about 305K--610K optimizer steps at the current GBS. This range is an
engineering forecast, not a scaling-law guarantee; the custom recurrent depth,
data changes, and aggressive constant LR can move the crossover.

## Intentional pause at step 175000

Update 2026-08-27: the step-161000 resume point above is superseded for future
continuations. Scheduler dispatch was soft-stopped, and the exact production
TorchRun process group was terminated only after
`fsdp2_ephemeral_step_175000/.metadata` and
`checkpoint_state_ephemeral_step_175000.json` were fully published. The
sidecar records step 175000, epoch 1, exact global row cursor 141196506,
world size 8, local batch size 8192, GAS 4, and `carry_policy=none`. All eight
GPUs were free after termination.

The existing scheduler plan remains stop-requested. Its
`campaign-train-200000` row has been reset to pending with attempt zero,
`resume_from_tag=ephemeral_step_175000`, and log directory
`logs/training/dfm8_XXL_1epoch/step_175000_to_200000`. No scheduler process is
running. To continue the established one-node path, clear the stop request and
restart the existing plan; do not create a replacement campaign.

The training row requests all eight GPUs and requires 178000 MiB effective free
memory on every GPU, so it will not collide with active DFM10 audit vLLM
servers. This is a headroom gate, not an audit-completion dependency: an audit
worker deliberately releases its GPU between retry attempts. Do not rely on
the gate to order audit finalization before training. For strict ordering,
start the scheduler only after the audit launcher exits successfully and
`logs/dfm10_folketing_audit_8gpu_vllm/final_summary.json` exists, or add an
explicit external-completion guard.

Update 2026-08-28: after the DFM10 audit released the GPUs, the scheduler
started the prepared continuation. It was intentionally stopped again during
startup/compilation before producing a newer checkpoint. The scheduler is
stop-requested with no running process, and `campaign-train-200000` is pending
at attempt zero, still resuming from authoritative
`ephemeral_step_175000`.
