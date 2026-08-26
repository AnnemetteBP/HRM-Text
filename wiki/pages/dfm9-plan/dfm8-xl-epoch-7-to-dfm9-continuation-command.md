---
type: Plan Record
title: DFM8 XL Epoch-7 To DFM9 Continuation Command
description: 'Part of DFM9 Plan: DFM8 XL Epoch-7 To DFM9 Continuation Command.'
tags:
- dfm9
- data
- training
- factual-knowledge
- code
status: stable
last_updated: 2026-08-18
confidence: high
part_of: /pages/dfm9-plan.md
---
# DFM8 XL Epoch-7 To DFM9 Continuation Command

Part of [DFM9 Plan](/pages/dfm9-plan.md).

Update, 2026-08-10. Confidence: high from checkpoint shard/sidecar inspection,
sampled-data inspection, trainer resume-code inspection, and successful Hydra
configuration composition. The command has not yet been launched.

The newest complete DFM8 XL epoch checkpoint is
`checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5/fsdp2_epoch_7`. Its sidecar records
global step `1768071`, completed epoch `7`, global batch size `262144`, gradient
accumulation `2`, and exact epoch-boundary state. All eight FSDP shards and all
eight carry files are present.

Resuming `epoch_7` gives `start_epoch=8`; the trainer then loads sampled dataset
directory `data/sampled_dfm9/epoch_7`. Therefore `epochs=8` trains exactly one
DFM9 continuation epoch and writes `epoch_8`. Use a separate checkpoint tree so
DFM8 checkpoint artifacts remain intact.

Superseded, 2026-08-10: the initial command used a new W&B run named
`DFM9-XL from DFM8 epoch7`. The subsequent operational decision is to continue
the existing `DFM8-XL clean full from DFM6-DFM7 epoch5` history instead, using
run ID `dfm8-xl-from-dfm6-dfm7-epoch5-clean-full` in project `DFM5`.

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm9 \
  arch/size@arch=XL \
  lr=3e-4 \
  lr_min_ratio=1 \
  lr_warmup_steps=2000 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=0.9999 \
  global_batch_size=262144 \
  gradient_accumulation_steps=2 \
  epochs=8 \
  training_total_steps=2127489 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  checkpoint_format=sharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=true \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=500 \
  checkpoint_path=checkpoints/dfm9/XL-from-dfm8-epoch7 \
  resume_checkpoint_path=checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5 \
  resume_checkpoint_tag=epoch_7 \
  resume_step=1768071 \
  resume_epoch=7 \
  reset_ema_on_resume=false \
  upcast_optimizer_state_on_resume=false \
  project_name=DFM5 \
  run_name="DFM8-XL clean full from DFM6-DFM7 epoch5" \
  wandb_run_id=dfm8-xl-from-dfm6-dfm7-epoch5-clean-full \
  wandb_resume=allow
```

DFM9 contains `93,929,976,190` tokens per epoch. At global batch size `262144`,
the coarse token-ratio estimate is about `358,314` optimizer steps, placing the
next epoch boundary near global step `2,126,385`; the actual packed-batch count
and resulting checkpoint step are authoritative.

## Scheduled After DFM8 L Epoch 3
Update, 2026-08-10. Confidence: high from direct sampler iteration and atomic
inspection/mutation of the active scheduler plan.

The continuation is queued in
`logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv` as an eight-segment
train/evaluate campaign. Direct sampler iteration showed that the DFM8 L third
epoch starts at step `537300` and contains `268645` optimizer steps, so its
exact endpoint is `805945`. This supersedes the legacy plan's incorrect
`806365` estimate.

The first DFM9 row, `dfm9-xl-train-1800000`, therefore depends on terminal
completion of `campaign-train-806365`, rather than on the stale `step_806365`
checkpoint or its evaluation teardown. The L process naturally exhausts the
dataset and fully writes `epoch_3` at step `805945`; only the scheduler's
subsequent check for the nonexistent `step_806365` is expected to mark that
legacy row failed. Using terminal dependency semantics lets DFM9 start after
the completed epoch despite that stale verification target. The old DFM8 L
continuation remains behind `campaign-teardown-806365` and cannot race DFM9
for the GPUs.

Cleanup, 2026-08-16. After DFM9 had advanced through the 2.05M evaluation and
resumed training toward 2.10M, the obsolete `step_806365` branch was removed
from the live plan under its advisory lock. The removed transitive closure had
214 rows: the stale checkpoint wait, export, eval/merge/finalization graph,
teardown, and obsolete `campaign-train-850000` continuation. It had no external
dependents. The historical failed `campaign-train-806365` row and completed
`dfm9-xl-train-1800000` transition row were retained. A pre-edit backup is
`plan.tsv.before_prune_806365_20260816_075219` in the plan directory; validation
afterward found no dangling dependencies.

The same locked cleanup then removed the six impossible DFM8 L checkpoint
branches at `850000`, `900000`, `950000`, `1000000`, `1050000`, and `1075016`.
Their union contained 1,283 rows: six stale waits, 1,271 blocked pending rows,
six intentionally skipped eval rows, and all dependent exports, evals, merges,
finalization, teardowns, and obsolete training continuations. The DFM8 L
checkpoint tree stops at 800K because the epoch ended at step `805945`; none of
these later checkpoint waits could succeed. The removed graph had no external
dependents. Its backup is
`plan.tsv.before_prune_850k_to_1075016_20260816_075643` in the plan directory.
Afterward the live plan had 577 pending rows, all belonging to the valid DFM9
2.10M and exact-endpoint 2,127,489 campaigns, with zero dangling dependencies.

Direct iteration of the DFM9 `epoch_7` multipack sampler with eight ranks,
`16384` tokens per rank/microbatch, and GAS 2 produced `718837` complete
microbatches. This is `359418` optimizer steps plus one trailing microbatch that
cannot form a GAS-2 update. Starting at DFM8 XL step `1768071` therefore gives
the exact optimizer endpoint `2127489`.

The scheduler campaign stops and evaluates at steps `1800000`, `1850000`,
`1900000`, `1950000`, `2000000`, `2050000`, `2100000`, and the exact epoch
endpoint `2127489`. Each block includes standard, DFM, and EuroEval tasks,
checkpoint export, merging, W&B sync/averaging, a terminal GPU-eval barrier,
and persistent-vLLM teardown. The next training segment starts after that
teardown; CPU-side merges and finalization do not unnecessarily hold the GPUs.

The final scheduler segment injects `stop_after_step=2127489` and verifies the
complete sharded `step_2127489` checkpoint under
`checkpoints/dfm9/XL-from-dfm8-epoch7`. This checkpoint has the same trained
weights as natural exhaustion of DFM9 sampled epoch `epoch_7`; because the
scheduler stops immediately after the final optimizer update, its tag is a
step tag rather than the standalone command's natural `epoch_8` tag.

Progress/LR endpoint correction, 2026-08-11. Confidence: high from code
inspection, Hydra composition, and atomic inspection of all queued training
rows. The default `pretrain.py` total was `epochs * current_dataset_steps`,
which is wrong when a run starts at a nonzero global step and switches to a new
dataset: it displayed approximately eight DFM9 epochs instead of the DFM8
global starting step plus one DFM9 epoch. `PretrainConfig` now has an optional
`training_total_steps` field. When supplied, it is the global `tqdm` denominator
and cosine-LR endpoint; when omitted, legacy behavior is unchanged. All eight
DFM9 scheduler training rows specify `training_total_steps=2127489`. The first
row was already running when this correction was installed, so its in-process
bar retains the old denominator until step `1800000`; every subsequent segment
will display the correct `.../2127489` total. This run uses
`lr_min_ratio=1`, so the old denominator did not alter its constant learning
rate.

Evaluation x-axis values are computed as
`7 + (checkpoint_step - 1768071) / 359418`, giving fractional epochs for the
50K checkpoints and exactly `8.0` at the final checkpoint. Non-judged vLLM
jobs use utilization `0.9`; `generative_talemaader` uses the established
`unsloth/gemma-4-E4B-it` judge with batch `32`, 32 connections, and vLLM
utilization `0.65`.

The queued command logs directly into the existing W&B run
`peter-sk-sdu/DFM5/dfm8-xl-from-dfm6-dfm7-epoch5-clean-full` with
`wandb_resume=allow`. The checkpoint's authoritative training step remains
`1768071`; do not raise `resume_step` merely to match W&B. Direct API inspection
on 2026-08-10 found that later eval/backfill records had advanced the run's
internal history step to `1768093`. With the default five-step logging interval,
W&B may reject continuation records at steps `1768075`, `1768080`, `1768085`,
and `1768090`, then accepts training metrics from `1768095` onward. This small
logging gap is preferable to skipping 22 training steps or misaligning model,
optimizer, and data-loader state.

## Scheduler Pause At Step 1,857,500
Update, 2026-08-12. Confidence: high from direct process, checkpoint-artifact,
and atomically locked scheduler-plan inspection.

The DFM9 XL continuation was intentionally paused after the next fully written
ephemeral checkpoint. Scheduler dispatch was stopped first with
`eval_scheduler stop`; training then continued until
`ephemeral_step_1857500` contained its state sidecar, DCP metadata and shards,
and all eight rank carry files. Only then was the training process group sent
`SIGTERM`. The interrupted `dfm9-xl-train-1900000` row was reset from `failed`
to `pending`, with attempt `0` and both resume-source fields changed to
`ephemeral_step_1857500`. Its original dependency, target `step_1900000`,
global endpoint `2127489`, and W&B continuation identity remain unchanged.

The plan is `logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv`. Its
`stop.request` intentionally remains present, and neither the runner nor a
training process is active. To continue, clear the stop request and relaunch
the scheduler with the standard `hrm`-environment and persistent-vLLM command;
the pending row will validate and resume from `ephemeral_step_1857500`.

## Scheduler Resume From Step 1,857,500
Update, 2026-08-13. Confidence: high from scheduler status, the emitted
training command, checkpoint-load output, live progress, and `nvidia-smi`.

The stop request was cleared and the same scheduler plan was relaunched from
the `hrm` environment with persistent vLLM enabled. The campaign directory
still has the historical name
`logs/scheduler/dfm8_L_campaign_epoch2_20260803`; the active training row and
checkpoint tree are nevertheless DFM9 XL.

`dfm9-xl-train-1900000` resumed from
`checkpoints/dfm9/XL-from-dfm8-epoch7/ephemeral_step_1857500`, restored global
step `1857500` and epoch `8`, and retained target `step_1900000`, global
endpoint `2127489`, GAS 2, and the existing W&B run identity. After data-loader
position restoration, progress advanced beyond step `1857590`; all eight GPUs
reported 100% utilization and approximately 128--132 GiB allocated per GPU.
The active detached runner log is
`runner_dfm9_resume_1857500_20260813_011917.log` in the plan directory.

## Scheduler Pause At Step 2,164,000
Update, 2026-08-26. Confidence: high from the scheduler stop state, process
inspection, and complete checkpoint artifacts.

The DFM9 XL 8K continuation was paused to free all eight GPUs for XXL
checkpoint evaluation. Scheduler dispatch was stopped first. Training then
continued through the next ephemeral boundary, where
`fsdp2_ephemeral_step_2164000` was verified to contain DCP metadata, all eight
multi-gigabyte DCP shards, all eight carry files, and the matching exact
data-loader state sidecar. Only after this verification was the torchrun
process group sent `SIGTERM`.

The plan remains
`logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv`, despite its
historical name. `stop.request` remains present, the scheduler runner and all
training ranks are stopped, and no GPU compute process remains. The interrupted
`dfm9-8k-train-2200000` row was atomically reset to pending with attempt zero
and `resume_from_tag=ephemeral_step_2164000`; the plan has no failed rows. Do
not clear the stop request until the intended XXL evaluations are complete.

## Recovery From Step 1,859,000 After External SIGKILL
Update, 2026-08-13. Confidence: high from the torchrun failure report,
checkpoint artifacts, locked plan mutation, emitted resume command, live
training progress, and `nvidia-smi`.

All eight training ranks were simultaneously terminated with `SIGKILL` at
approximately step `1859120`. No CUDA OOM was reported. The newest fully
written checkpoint was `ephemeral_step_1859000`; it contains the state
sidecar, DCP metadata, all eight approximately 3.57 GB DCP shards, and all
eight carry files.

The scheduler's terminal barriers had treated the failed training segment's
blocked eval graph as terminal and consequently walked through later teardown
rows. This caused training rows through `2127489` to fail immediately while
looking for predecessor checkpoints that had never been produced. The runner
was stopped before repair. Under the scheduler plan lock:

- `dfm9-xl-train-1900000` was reset to pending with resume source
  `ephemeral_step_1859000`;
- the later DFM9 training rows and their prematurely completed barriers and
  teardowns were reset to pending;
- every training row after `1900000` was changed to require both the preceding
  training row and its eval teardown to succeed, preventing another training
  failure from cascading forward.

The scheduler was relaunched from the `hrm` environment with persistent vLLM.
Checkpoint and data-loader restoration succeeded, and the new process advanced
beyond the checkpoint to step `1859020`, with all eight GPUs active and about
122--133 GiB allocated per GPU. The detached runner log is
`runner_dfm9_resume_1859000_20260813_053957.log` in the plan directory.

## XXL-32 Step 10K Evaluation Before DFM9 XL Recovery
Update, 2026-08-13. Confidence: high from checkpoint sidecars, DCP metadata,
carry-file counts, W&B API inspection, and atomically locked scheduler-plan
inspection.

The copied DFM9 XXL-32 checkpoint at `checkpoints/XXL-32/step_10000` is a
complete 256-rank FSDP checkpoint: it has DCP metadata, 256 distributed
checkpoint shards, 256 carry files, and a matching checkpoint-state sidecar.
Its copied `all_config.yaml` identifies the XXL architecture (72 layers,
hidden size 1792), DFM9 data, global batch size 1,048,576, and run name
`dfm9-XXL-lumi`. The checkpoint has no existing matching W&B run in the local
account. The initial evaluation plan mistakenly assigned its dedicated run to
the `DFM9` project. **Superseded, 2026-08-13:** the completed local artifacts
were atomically re-logged to the intended `DFM5` project run ID
`dfm9-xxl-32`, display name `DFM9 XXL-32`. Step 10K is logged at
`eval/epoch=0.11163379812627204`, derived from its 93,929,976,190-token epoch
and global batch size.

The full standard, DFM, and EuroEval graph was appended to
`logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv`. It contains 244 GPU
evaluation rows and uses the production persistent-vLLM path, FlashAttention,
the Gemma-4 native chat template, six total attempts per shard, non-judged
vLLM utilization 0.95, and judged-task utilization 0.18 with
`unsloth/gemma-4-E4B-it`. Checkpoint readiness explicitly requires all 256
carry ranks. A terminal evaluation barrier and persistent-server teardown
release DFM9 training after every XXL-32 GPU evaluation row reaches a terminal
state, so an exhausted eval retry does not strand the GPUs indefinitely.

Remote verification after the corrected relog found 56 of the 57 configured
headline metrics, all four `headline_avg_v3/*` values, and all three
`suite_avg_v3/*` values. The sole absent headline metric is
`dfm_eval/generative-talemaader/model_graded_fact/accuracy`, because all eight
judged shards exhausted their retries; EuroEval `valeu-en` also failed but is
not a headline metric. The run was explicitly added to the additive selection
tree in DFM5 workspace `760qd0evtsa`; workspace `3fvncok3gjh` already exposed
it through its subtractive selection mode. Workspace specifications were
backed up under `logs/wandb_workspace_specs/` before and after the update.

The previously failed `dfm9-xl-train-1900000` row now depends on that XXL-32
teardown and resumes from the newer verified
`checkpoints/dfm9/XL-from-dfm8-epoch7/ephemeral_step_1867500`. That checkpoint
contains DCP metadata, all eight model shards, all eight carry files, and a
sidecar recording exact global step 1,867,500 and epoch 8. Future DFM9 training
rows through step 2,127,489 remain gated by both the preceding training row and
its evaluation teardown; prematurely completed barriers and teardowns from the
interrupted attempt were reset to pending.

## XXL-32 Local Checkpoint Inventory
Update, 2026-08-26. Confidence: high from direct DCP metadata, shard, carry,
and checkpoint-state inspection.

The local tree is `checkpoints/XXL-32`. Complete regular 256-rank FSDP
checkpoints exist at every 10K step from 10K through 100K:
`fsdp2_step_{10000,20000,30000,40000,50000,60000,70000,80000,90000,100000}`.
The regular `fsdp2_epoch_1` checkpoint is also complete and records exact step
89,665. Each has DCP metadata, 256 DCP shards, 256 carry files, and a matching
regular checkpoint-state sidecar, and is therefore eligible for export and
evaluation.

Do not use the newest `fsdp2_ephemeral_step_106250` for evaluation or resume
from this local copy: it has metadata and 256 carry files but only 176 of 256
DCP shards. Older incomplete ephemeral copies at 57,500 and 70,750 are also
non-authoritative; complete neighboring regular checkpoints supersede them.
The earlier shorthand path `checkpoints/XXL-32/step_10000` is superseded by the
actual on-disk name `checkpoints/XXL-32/fsdp2_step_10000`.

## XXL-32 Steps 20K--100K Evaluation Campaign
Update, 2026-08-26. Confidence: high from checkpoint validation, generated
plan inspection, and live export status.

The complete regular checkpoints at steps 20K, 30K, 40K, 50K, 60K, 70K,
80K, 90K, and 100K are queued for full standard, DFM, and one-dataset
EuroEval evaluation in
`logs/scheduler/dfm9_XXL32_steps20k_100k_20260826/plan.tsv`. The campaign has
2,583 rows, 287 per checkpoint, and logs EMA results directly to W&B project
`DFM5`, run ID `dfm9-xxl-32`, display name `DFM9 XXL-32`. Fractional epochs
use the exact epoch-1 endpoint of 89,665 steps.

Checkpoint readiness requires all 256 carry ranks. HF exports are serialized
to avoid concurrent reads of multiple 256-shard checkpoints, while later
checkpoint GPU evaluations may begin as earlier checkpoints enter their long
tails. The plan uses persistent vLLM, the `hrm-cu132` vLLM runtime, the native
Gemma 4 chat proxy and BFCL adaptation, FlashAttention, six total attempts,
and the batch sizes proven by the 10K run: 32 for standard and ordinary DFM,
16 for DFM IFEval-DA, EuroEval, and judged DFM tasks. Non-judged vLLM uses
utilization 0.95; judged tasks use 0.18 and a colocated
`unsloth/gemma-4-E4B-it` judge with 16 connections. Long-context tasks are not
included because these are 4K checkpoints.

The detached runner is visible in tmux window `hrm-1:9`; the Rich monitor is
in `hrm-1:10`. The first live action is the step-20K EMA HF export. The paused
DFM9 XL 8K campaign remains separately stop-requested and cannot resume during
these evaluations.

W&B identity clarification, 2026-08-13. Confidence: high from direct remote
history and workspace API reads. DFM9 XL does not have a separately named W&B
run. By design, it continues in `peter-sk-sdu/DFM5` run ID
`dfm8-xl-from-dfm6-dfm7-epoch5-clean-full`, whose display name remains
`DFM8-XL clean full from DFM6-DFM7 epoch5`. The completed DFM9 evaluations are
present on that run at epoch `7.088835283708662` (step 1,800,000) and epoch
`7.227949073223934` (step 1,850,000). Both manual workspaces `760qd0evtsa` and
`3fvncok3gjh` include the run; it must be identified by the legacy display name.
Remote verification found the standard task points and all atomic v3 averages
at both checkpoints.

## Recovery From Machine Restart At Step 1,931,000
Update, 2026-08-14. Confidence: high from checkpoint-artifact inspection,
locked scheduler-plan mutation, emitted command inspection, W&B connection
output, live step progress, and GPU telemetry.

The machine restart interrupted `dfm9-xl-train-1950000` after step 1,931,155.
The newest fully written checkpoint is
`checkpoints/dfm9/XL-from-dfm8-epoch7/ephemeral_step_1931000`; it contains the
state sidecar, DCP metadata, all eight approximately 3.57 GB DCP shards, and all
eight carry files. The existing plan remains
`logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv`; no replacement plan
was created.

Under the plan lock, the stale running training row was reset to pending with
attempt zero and `resume_from_tag=ephemeral_step_1931000`. The first launch
restored the checkpoint correctly but failed before training because the
rebooted account had no W&B credentials. That failure again caused the
scheduler's terminal barriers to cascade through the future DFM9 teardown
rows. W&B authentication was restored in `/home/ucloud/.netrc`; the 1.95M
training row and only the prematurely completed DFM9 barriers/teardowns from
1.95M onward were reset under the plan lock.

The existing scheduler was relaunched from the `hrm` environment with
`--persistent-vllm`. It resumed the existing DFM5 W&B run from global step
1,931,000 and advanced beyond step 1,931,020. The scheduler runner log is
`runner_machine_restart_wandb_retry_20260814_104520.log` in the plan directory.
In tmux session `hrm-1`, window `2` tails the training log and window `3` runs
the Rich scheduler monitor at a 30-second interval. W&B may reject replayed
training records through its pre-restart history step 1,931,151; subsequent
training records are expected to append normally.

## Step 1,950,000 Evaluation Failure After Restart
Update, 2026-08-14. Confidence: high from failed-job enumeration and persistent
vLLM server logs.

The resumed training reached step 1,950,000, but 242 GPU evaluation rows in
that checkpoint wave exhausted their six attempts. This was one shared runtime
failure rather than 242 independent benchmark failures: after the machine
restart, neither `nvcc` nor `/usr/local/cuda` existed. vLLM selected
FlashAttention 4 for attention as intended, then its separate FlashInfer
top-k/top-p sampler attempted to JIT-build a sampling kernel. Every persistent
server exited during profiling with `RuntimeError: Could not find nvcc and
default cuda_home='/usr/local/cuda' doesn't exist`.

The scheduler's total failed count then consisted of 242 step-1.95M eval rows,
the nine already documented XXL-32 step-10K eval failures, and two historical
DFM8 L training failures. Its terminal dependency policy correctly released
the GPUs, so DFM9 XL continued toward step 2,000,000; however, step 1.95M has no
valid evaluation results or averages. Restore a CUDA toolkit visible to the
`hrm` environment before the 2.00M evaluation, then reset the 242 failed 1.95M
evaluation rows and their downstream merge/sync/average rows for a later rerun.

Reschedule update, 2026-08-14. Confidence: high from locked plan inspection and
direct environment probes. **Supersedes the instruction above to restore CUDA
to the `hrm` environment for this campaign:** use the existing `hrm-cu132`
environment for DFM9 evaluations. It provides CUDA 13.2 `nvcc`, Ninja, the
same vLLM build, FlashAttention 4, and FlashInfer. With
`PATH=/home/ucloud/miniforge3/envs/hrm-cu132/bin:$PATH` and
`CUDA_HOME=/home/ucloud/miniforge3/envs/hrm-cu132`, FlashInfer resolves its CUDA
root to that conda environment.

All 1,430 evaluation-related plan rows from step 1.95M through the final DFM9
checkpoint now point `python_bin`, `vllm_python`, and `euroeval_bin` at
`hrm-cu132`. The 242 failed step-1.95M GPU rows were reset to pending at attempt
zero, and their terminal barrier and teardown were reopened. The scheduler was
soft-stopped so the active 1.95M-to-2.00M training segment remains undisturbed.
A detached handoff waits specifically for that training process to finish,
then terminates only the old scheduler process; this avoids being held open by
seven unrelated historical checkpoint wait workers. It then clears the stop
request and relaunches the same plan under `hrm-cu132` with
`--persistent-vllm`. Its log is
`hrm_cu132_handoff_after_training_20260814_233602.log` in the plan directory.

## Step 2.10M Versus DFM8 Step 1.65M
Update, 2026-08-17. Confidence: high from finalized local merged artifacts.

Across the eight standard headline benchmarks plus HumanEval, GovReport,
AngryTweets, DaLA, GEC-DaLA, PIQA-DA, MultiWikiQA, WMT24++ EN-DA,
NordjyllandNews, IFEval-DA, and HellaSwag-DA, an equal-weight normalized mean
fell slightly from `0.715935` at 1.65M to `0.711438` at 2.10M (`-0.45` points;
8 gains and 11 regressions). The standard-only mean improved from `0.728064`
to `0.732154` (`+0.41` points), while the 11 supplementary metrics fell from
`0.707114` to `0.696372` (`-1.07` points). Largest gains were MultiWikiQA
`+3.71`, DROP `+3.21`, and AngryTweets `+1.19` points; largest regressions were
PIQA-DA `-7.41`, WMT `-3.44`, HumanEval `-2.44`, and GEC-DaLA `-1.66` points.
PIQA-DA has only 108 samples, so its large swing is noisy; excluding it leaves
the aggregate nearly tied (`-0.06` points). SDU-Daisy was not present in either
finalized full-eval artifact set and was excluded from this comparison.

## DFM9-Mini Sample Size And Incomplete Backing Store
Update, 2026-08-18. Confidence: high from direct NumPy index and file-header
inspection.

`data/sampled_dfm9_mini` has three complete epoch index sets containing
`17,066,309,932` sampled tokens in total:

- epoch 0: `5,690,532,273`
- epoch 1: `5,687,297,092`
- epoch 2: `5,688,480,567`

The average is `5,688,769,977.3` tokens per epoch, matching the rounded
`metadata.json` value of `5,688,769,977`.

The artifact is not currently safe to train from. Its shared `tokens.npy`
source backing store declares `101,818,079,842` int32 tokens but physically
contains only `11,077,812,192` complete token elements (`10.88%`). The file was
last modified seconds after the epoch indices on 2026-08-12, consistent with an
interrupted source-token concatenation. Rebuild or complete `tokens.npy` before
using `data=dfm9_mini`; the complete epoch indices alone are insufficient.

Rebuild update, 2026-08-18. Confidence: high from complete source validation,
atomic replacement, and post-install content checks. **Supersedes the unusable
artifact warning above:** `data/sampled_dfm9_mini/tokens.npy` is now complete
and usable. `scripts/rebuild_sampled_token_store.py` selected the same `5,653`
tasks from `data/tokenized_dfm9` using
`data_io/prefix_config_dfm9_mini.yaml`, copied all `101,818,079,842` int32
source tokens into a temporary file, fsynced and reopened it, and only then
atomically replaced the incomplete backing store. The installed file is
`407,272,319,496` bytes.

The first repair implementation used a writable NumPy mmap and was stopped at
20% because its RSS had reached about 99 GB. It never replaced the original.
The final implementation uses one sequential 64 MiB byte stream under
`nice -n 15` and `ionice -c2 -n7`; observed RSS was about 158 MB. Post-install
validation checked the exact shape and dtype, all epoch index bounds, and 96
source/destination content positions spanning 32 selected tasks. The rebuild
log is
`logs/data/rebuild_sampled_dfm9_mini_tokens_bounded_20260818.log`.

Ten-epoch extension update, 2026-08-18. Confidence: high from deterministic
regeneration, byte comparison, and full index-bound validation. The sample now
contains epochs 0 through 9 in the same `data/sampled_dfm9_mini` directory,
with `56,885,982,109` sampled tokens in total and a rounded metadata mean of
`5,688,598,211` tokens per epoch. The seven added epochs contribute
`39,819,672,177` tokens. They were generated in a temporary sibling directory
with `reuse_tokens=true`, `skip_unmatched=true`, seed 0, and the existing
`prefix_config_dfm9_mini.yaml`. Regenerated epochs 0 through 2 were byte-for-byte
identical to the installed originals before epochs 3 through 9 and the updated
metadata were moved into place. The generation used one low-priority process;
the log is `logs/data/extend_sampled_dfm9_mini_to_10_epochs_20260818.log`.
