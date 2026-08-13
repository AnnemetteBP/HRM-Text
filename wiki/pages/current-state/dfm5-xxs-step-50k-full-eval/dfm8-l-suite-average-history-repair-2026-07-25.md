---
type: Operational Record
title: DFM8 L Suite-Average History Repair, 2026-07-25
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 L Suite-Average History Repair,
  2026-07-25.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 L Suite-Average History Repair, 2026-07-25

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high from scheduler logs, the live W&B workspace specification,
and remote sampled-history inspection.

The DFM5 workspace `760qd0evtsa` correctly contains all three suite panels and
uses `suite_avg_v3/epoch` as their x-axis. For run `g2oaotmc`, the 50K
`suite_avg_v3/dfm` job originally reported a successful W&B sync, but that
history point was absent remotely while the standard and EuroEval points were
present. Relogging the 50K DFM-only average restored it. Remote history now
contains:

```text
50K:  epoch 0.1859719823565767, suite_avg_v3/dfm 0.49810676177982177
100K: epoch 0.3719439647131534, suite_avg_v3/dfm 0.5822767417590341
```

Operational lesson: a successful W&B CLI sync message is not sufficient
verification for average rows written into an active resumed run. When one
suite panel is missing a point, inspect remote sampled history for the metric
and x-axis pair and relog only the missing suite/epoch point.

Update, 2026-07-25. Confidence: high from local merged artifacts and remote
W&B summary/history inspection.

A full 50K/100K sync audit for DFM8 L run `g2oaotmc` checked 878 prefixed
numeric metrics. Besides the repaired DFM average and 100K Angry Tweets point,
it found and selectively restored Winogrande at both checkpoints, 50K
EuroEval NordjyllandNews, and 100K DFM PIQA/Danish Citizen Tests plus EuroEval
Danske Talemaader. A second audit reported zero missing and zero mismatched
values across standard, DFM, and EuroEval.

The first persistent-vLLM comparison attempt exposed two implementation
issues. Pool acquisition originally held one global lock while waiting for
server startup, serializing independent GPU starts. This is superseded by
per-GPU lifecycle locks, covered by a concurrent-start unit test. The original
persistent port formula could also exceed port 65535 on higher GPU IDs (for
example 65574-65774). It now allocates a compact, process-specific eight-port
block in the safe range 20000-51999. GNU `/usr/bin/time` is not installed on
this host, so the comparison wrapper now records elapsed wall seconds directly.

The clean no-W&B comparison plan is:

```text
logs/scheduler/dfm8_L_step100k_persistent_vllm_compare_v2_20260725
```

This v2 claim is superseded. EuroEval's native proxy was still assigned by the
legacy additive port formula. It advertised ports above 65535 (for example
68144); Linux bound the wrapped port, but LiteLLM rejected the advertised URL.
Only EuroEval's initial model probe reached vLLM, after which clients repeatedly
reported connection errors and GPUs appeared inactive. Relative EuroEval
run/cache paths could also be resolved below the run directory a second time
because the client changes its working directory.

Update, 2026-07-25. Confidence: high from process arguments, listening sockets,
proxy request logs, scheduler events, and live GPU utilization.

`start_native_proxy` now maps legacy offsets into the valid unprivileged range
30000-59999, and both EuroEval runners resolve their run roots before launching
clients. The focused server-pool suite now has seven passing tests, including
valid-port and concurrent-start checks. The clean replacement plan is:

```text
logs/scheduler/dfm8_L_step100k_persistent_vllm_compare_v3_20260725
```

It runs in `hrm-0:6`; the Rich monitor in `hrm-0:7` targets the same plan. The
first wave completed six evaluation jobs without failures and immediately
reused resident servers for later tasks. Proxy logs grew to hundreds or
thousands of requests per completed task, and active inference produced
55-95% GPU utilization.

Persistent comparison result, 2026-07-25. Confidence: high from the completed
scheduler state, lifecycle events, and local metric artifacts.

- The v3 run finished 210 workflow rows, skipped the intentionally disabled
  W&B row, and completed 186 of 187 GPU evaluation jobs.
- Aggregate completed evaluation-job time fell from `32231` seconds in the
  fresh-server 100K baseline to `15393` seconds with persistence: a `2.09x`
  reduction in occupied GPU-job time.
- The measured evaluation wall span fell from `7677` to `2106` seconds. This
  `3.65x` figure is not a clean standalone speedup because the baseline plan
  interleaved 50K and 100K work on the same eight GPUs; GPU-job time is the
  more defensible comparison.
- Lifecycle events recorded 27 server starts and 166 successful reuses. Seven
  servers were invalidated during retries/configuration transitions, and all
  remaining servers were torn down at scheduler exit.
- Local comparison found 437 shared metrics. The only missing candidate keys
  were `eval/MATH/{acc,invalid,n}` because MATH shard 42/64 repeatedly exited
  with signal `-11`, ultimately leaving its merge plus three dependent average
  rows blocked.
- Other metric differences include expected nondeterminism from generated
  answers and EuroEval confidence/bootstrap calculations. There was no broad
  systematic shift attributable to server reuse.

The partial comparison is saved at:

```text
logs/scheduler/dfm8_L_step100k_persistent_vllm_compare_v3_20260725/comparison.partial.json
```

MATH shard-42 investigation, 2026-07-25. Confidence: high from the failed
client log, the successful fresh-server log, local Gemma-template tokenization,
and focused tests.

- The persistent server itself did not segfault. One MATH shard-42 prompt
  exceeded the OpenAI request budget: vLLM received at least 1025 input tokens
  plus the requested 3072 output tokens for a 4096-token model and returned
  HTTP 400.
- Python subsequently segfaulted during exception-driven interpreter teardown,
  making scheduler status `-11` obscure the preceding actionable HTTP error.
  Reducing batch size from 64 through 4 could not help because this was a
  per-request context-length error.
- The fresh baseline used in-process `VLLMEngine`, which accepted the same
  request and dynamically limited output to the remaining model context.
- Local inspection found exactly one shard-42 outlier above 1024 tokens. Under
  the Gemma template it is about 1456 tokens; the next-longest prompt is only
  476. Its correct maximum output allowance is therefore about
  `4096 - 1456 = 2640`, while shorter prompts can retain the configured 3072.
- Internal OpenAI standard evaluations now receive the exported tokenizer,
  exact chat template, and model context window. `OpenAIEngine` counts each
  rendered prompt locally and clamps only that request's output budget to the
  remaining context. External-model behavior remains unchanged. The HTTP-400
  parser remains as a generic fallback.
- Nine focused scheduler/engine tests pass and both changed Python modules
  compile. The shard has not yet been rerun because the DFM8 XXL training
  started on all eight GPUs immediately after the comparison.

DFM8 XXL 50K/100K persistent-evaluation campaign, 2026-07-25. Confidence:
high from the W&B run config, live GPU telemetry, generated plan inspection,
and running scheduler state.

- Training run: W&B project `DFM5`, run ID `ak41pnma`, run name `dfm8-XXL`.
  The architecture has `3,978,297,344` parameters.
- Plan:
  `logs/scheduler/dfm8_XXL_steps50k_100k_persistent_vllm_20260725`.
  It contains guarded EMA exports and all standard, DFM, DFM IFEval-DA, and
  EuroEval jobs for `step_50000` and `step_100000`, followed by task-local
  merges, W&B sync, headline/suite averages, and reports.
- Epoch coordinates are `0.1859719823565767` and `0.3719439647131534`,
  derived from the DFM8 epoch size and the `262144` global batch.
- The scheduler is running in `hrm-0:6` and its 30-second Rich monitor is in
  `hrm-0:7`. Both were launched from the `hrm` conda environment.
- Superseded launch setting: the first version restricted execution to GPUs
  `1,3,6,7` and set every target server to utilization `0.08`. This was safe
  but would provide unnecessarily little KV cache and ignore the established
  successful task-specific settings.
- Ordinary batches are standard `64`, DFM `32`, DFM IFEval-DA `32`, and
  EuroEval `32`. Judged rows use batch/max-connections `16`. Every job allows
  five retries after its initial attempt.
- At launch, both checkpoint-wait jobs were active and no evaluation server
  had started. This preserves training memory until a complete checkpoint is
  available.

Superseding headroom-gated launch, 2026-07-25. Confidence: high from focused
tests, locked plan inspection, scheduler process arguments, and live status.

- `eval_scheduler` now supports `min_gpu_free_mib` per job and exposes
  `--min-gpu-free-mib` plus `--judged-min-gpu-free-mib` during plan creation.
  A ready job waits instead of exiting when no GPU meets the gate, and the
  eligible GPU with the most effective free memory is selected.
- Effective free memory credits an incompatible persistent server's allocation
  because it will be terminated before replacement. A compatible resident
  server bypasses the gate, avoiding a deadlock after the first shard. HF
  exports explicitly release any persistent server on their assigned GPU.
- Thirteen focused headroom, persistent-server, and OpenAI-engine tests pass.
- The live plan uses the previously verified production values rather than a
  new estimate: ordinary eval rows use utilization `0.25` and require
  `52,000 MiB` effective free memory; `generative_talemaader` rows use
  utilization `0.18`, the local `unsloth/gemma-4-E4B-it` judge, and require
  `55,000 MiB`. HF exports require `34,000 MiB`.
- The scheduler was restarted in `hrm-0:6` across GPUs `0-7`; the Rich monitor
  remains in `hrm-0:7`. Both checkpoint waits are active. Current XXL training
  headroom is below the evaluation thresholds, so evaluation will remain
  queued unless training releases sufficient memory.

Superseding DFM8 XXL utilization policy, 2026-07-25. Confidence: high from
locked plan inspection and live W&B workspace/API verification.

- At user direction, the current 50K/100K XXL campaign now prioritizes
  throughput on effectively free GPUs rather than coexistence with training.
  Its `358` pending non-judged eval rows use
  `vllm_gpu_memory_utilization=0.95` and require `178,000 MiB` effective free
  memory. Its `16` pending `generative_talemaader` rows use utilization `0.85`
  plus the local Gemma E4B judge and require `180,000 MiB`. The export gate
  remains `34,000 MiB`.
- These gates mean eval inference will not start while XXL training occupies
  the GPUs. Once a GPU is effectively free, the persistent server receives the
  requested large KV-cache allocation.
- W&B run `peter-sk-sdu/DFM5/ak41pnma` exists online as `dfm8-XXL`, is in
  `running` state, and had remote history through training step `5955` when
  checked. The manual DFM5 workspace `760qd0evtsa` had an explicit six-run
  selection tree that excluded this new run. The workspace was updated in
  place to append `ak41pnma`; server-side re-read confirms it is selected.

DFM8 XXL BP-memory risk, 2026-07-25. Confidence: high for the inspected
schedule/current telemetry; medium for the future-memory estimate because the
run has not executed an XXL step at BP 3-5.

- Run `ak41pnma` currently reports `bp_steps=2` and uses approximately
  `144,484-155,256 MiB` per B200, leaving only `27,370-38,142 MiB`.
- With `total_steps=1,881,999`, `bp_warmup_ratio=0.2`, `bp_min_steps=2`, and
  `bp_max_steps=5`, the integer schedule changes to BP 3 at about step
  `125,467`, BP 4 at about `250,934`, and BP 5 at about `376,400`.
- The active HRM has no activation checkpointing. BP 2 retains autograd state
  for one H and one L recurrent application; BP 5 retains two H and three L
  applications. The current most-used rank has only about `28 GiB` spare, so
  each of the three added recurrent applications would need to cost less than
  roughly `9 GiB` to fit. That is unlikely for the XXL 36-layer recurrent
  block at this sequence length and microbatch.
- Operational conclusion: do not assume this `gradient_accumulation_steps=2`
  run will survive BP 3-5. A restart/resume with greater accumulation, most
  plausibly `gradient_accumulation_steps=4` while retaining the same global
  batch, is the conservative path unless a BP-5 memory smoke test proves GAS 2
  viable.

DFM8 XXL one-epoch GAS4/BP5 run command, 2026-07-25. Confidence: high from a
successful Hydra `--cfg job` composition check.

- To start at BP 5, set the absent/defaulted field with
  `+arch.bp_min_steps=5` and retain `arch.bp_max_steps=5`. Do not set
  `bp_warmup_ratio=0`; the current HRM scheduling expression divides by the
  warmup ratio.
- The isolated checkpoint path is
  `checkpoints/dfm8/XXL-gas4-bp5-1epoch`, avoiding the active XXL run.

DFM8 XXL one-epoch 50K/100K eval campaign, 2026-07-25. Confidence: high from
the live process, W&B API, locked plan inspection, and running scheduler state.

- Training target: W&B `DFM5/40j5y877`, run `dfm8-XXL-1epoch`, checkpoint path
  `checkpoints/dfm8/XXL-1epoch`. The run uses GAS4 and BP2-to-BP5 warmup.
- Plan:
  `logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725`.
  It guards `step_50000` and `step_100000`, exports EMA weights, and runs all
  standard, DFM, DFM IFEval-DA, and EuroEval jobs with merges, W&B sync,
  averages, and reports.
- Pending non-judged rows use persistent vLLM utilization `0.95` and a
  `178,000 MiB` effective-free-memory gate. Judged Talemaader rows use
  utilization `0.85`, the local Gemma E4B judge, and a `180,000 MiB` gate.
  Superseded 2026-07-28: exports initially used a separate `34,000 MiB` gate,
  but that was insufficient for XXL HF conversion.
- Scheduler: `hrm-0:6`; 30-second Rich monitor: `hrm-0:7`. Both checkpoint
  guards are active. The obsolete scheduler for crashed run `ak41pnma` was
  stopped and its stale wait rows reset.
- The manual DFM5 workspace `760qd0evtsa` explicitly selects runs. Run
  `40j5y877` was appended and verified server-side.

DFM8 XXL one-epoch resume point, 2026-07-28. Confidence: high from DCP
metadata, all rank/carry files, and the checkpoint-state sidecar.

- Newest complete checkpoint:
  `checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_60500`.
- `checkpoint_state_ephemeral_step_60500.json` records step `60500`, epoch
  `1`, exact `batch_in_epoch=242000`, GAS `4`, local batch `8192`, and global
  row cursor `48,806,932`. All eight DCP rank files, `.metadata`, and all eight
  carry files exist.
- Resume the same W&B run as ID `40j5y877` with
  `wandb_resume=allow`. The remote run was marked crashed and its summary
  lagged the local checkpoint, but beginning new history at step `60500` is
  monotonic relative to the remote summary.

DFM8 XXL 50K export failure and corrected gate, 2026-07-28. Confidence: high
from scheduler events, attempt telemetry, and the conversion traceback.

- The `step_50000` checkpoint completed at `2026-07-27 09:06:15 +02:00`.
  Its checkpoint guard completed at `09:06:43`, and the scheduler immediately
  launched HF export while training still occupied the GPUs.
- The old `34,000 MiB` export gate admitted GPUs with only about
  `38,926-39,780 MiB` free. HF conversion instantiated the model and
  `AdamATan2` state; the traceback showed a training process retaining about
  `131.12 GiB`, and conversion OOMed while allocating optimizer state.
- All six export attempts were consumed between `09:06:46` and `09:08:38`.
  The row then remained terminally failed, so stopping training later did not
  make it retry and no 50K eval or W&B metric was produced.
- The incomplete export directory was removed, `export-00002` was reset to
  pending with attempt zero, and both 50K and 100K export rows now require
  `178,000 MiB` effective free GPU memory. This prevents export from competing
  with active XXL training; it will run when a GPU is effectively free.

Segmented training/evaluation campaign support, 2026-07-28. Confidence: high
from Hydra composition, 20 focused tests, and an end-to-end dry scheduler plan.

- `pretrain.py` and `config/cfg_pretrain.yaml` expose `stop_after_step`. At the
  exact global optimizer step, training forces a regular step checkpoint and
  then follows the normal distributed/W&B shutdown path. Null preserves the
  previous behavior.
- `eval_scheduler` supports `train_until_step`, `terminal_barrier`, and
  `teardown_eval`, plus explicit `deps_mode` in `plan.tsv`. Existing plans
  remain success-only by default.
- `train_until_step` atomically reserves all scheduler GPUs, closes persistent
  vLLM leases, injects a verified resume checkpoint path/tag and exact stop
  target, and accepts success only after the target's regular checkpoint,
  carry files, and state sidecar verify.
- `plan add-eval-release` builds a terminal barrier over only the selected
  checkpoint's GPU eval rows, followed by evaluator teardown.
  `plan add-training` appends the next all-GPU training segment.
- The next training segment depends on evaluator teardown, not on
  merge/sync/average. Eval failures and their blocked post-processing no longer
  waste GPU time; active or runnable retries still delay teardown.
- This support has not been inserted into the currently live
  `dfm8-XXL-1epoch` plan. Its scheduler process loaded the previous code;
  campaign rows should run from a fresh scheduler process.

Superseded 2026-07-28: the segmented campaign support was subsequently added
to the live `dfm8-XXL-1epoch` plan. Confidence: high from locked plan
inspection, checkpoint sidecar inspection, and live scheduler telemetry.

- Plan:
  `logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725`.
- The source resume checkpoint is the complete
  `checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_62000`, with all eight
  carry files and sidecar row cursor `50,017,079`.
- `campaign-barrier-50000` has terminal dependencies on all `188` 50K GPU eval
  rows. `campaign-teardown-50000` follows it independently of merges and
  averages.
- `campaign-train-100000` then reserves all eight GPUs, resumes
  `ephemeral_step_62000`, keeps the same W&B run `DFM5/40j5y877`, and injects
  `stop_after_step=100000`.
- The old scheduler and monitor processes were stopped before adding the new
  action rows. Fresh code is running in separate tmux windows `hrm-0:6` and
  `hrm-0:7` with persistent vLLM enabled and the `hrm` environment.
- Training had stopped and released all GPUs; the corrected 50K HF export
  started on GPU 7 immediately after scheduler restart.

DFM8 XXL segmented 100K-to-150K continuation, 2026-07-28. Confidence: high
from locked plan inspection, Hydra composition, checkpoint-sidecar inspection,
the remote W&B run config, and live scheduler telemetry.

- The live plan now also contains the complete `step_150000` evaluation graph:
  all standard, DFM, 32-shard DFM IFEval-DA, and EuroEval tasks, followed by
  per-task merges, W&B synchronization, `suite_avg_v3` averages, and report
  generation. Its eval epoch is `0.5579159470697301`.
- The 150K graph exactly preserves the production 100K settings: EuroEval
  first; initial batches `64` standard, `32` DFM, `32` DFM IFEval-DA, and
  `32` EuroEval; five retries after the first attempt; EMA HF export; Gemma 4
  native chat template; persistent vLLM utilization `0.95`; and a
  `178,000 MiB` effective-free-memory gate.
- Judged Talemaader rows retain batch/concurrency `16`, vLLM utilization
  `0.85`, the `unsloth/gemma-4-E4B-it` local judge, and the `180,000 MiB`
  effective-free-memory gate.
- `campaign-barrier-100000` has terminal dependencies on exactly the 188
  `step_100000` GPU eval rows. `campaign-teardown-100000` then releases all
  evaluator servers even when a post-processing row is blocked by an eval
  failure.
- `campaign-train-150000` depends on that teardown, reserves all eight GPUs,
  resumes the forced regular `step_100000` checkpoint, and injects
  `stop_after_step=150000`. The 150K checkpoint wait is already active, which
  verifies that the running scheduler picked up the appended graph without a
  restart.
- Both scheduled training segments use the same base command and match the
  resolved local and remote `DFM5/40j5y877` config: DFM8 XXL, BP 2-to-5 with
  warmup ratio `0.2`, LR `4e-4`, LR ratio `1`, GAS `4`, global batch
  `262144`, FP32 FSDP parameters, BF16 forward/backward, sharded checkpoints,
  EMA `0.9999`, and the original optimizer/checkpoint settings.
- The 62K source is complete: DCP `.metadata`, all eight carry files, and an
  exact state sidecar with step `62000`, epoch `1`,
  `batch_in_epoch=248000`, global row cursor `50,017,079`, GAS `4`, local
  batch `8192`, and global batch `262144`.
- Neither resume command supplies manual step, epoch, or batch offsets.
  Resume position comes from the verified checkpoint sidecar. The 100K source
  does not exist yet; `stop_after_step=100000` will force it to be written as
  a regular checkpoint before the first training segment exits, and the
  scheduler verifies it before accepting the segment.
- A fresh Hydra composition omits `data.validation_path`, whereas the saved
  runtime config serializes it as `null`; these are equivalent and both mean
  that no validation dataset is configured.
- The 50K EuroEval results are remotely synchronized to the same W&B run at
  `euroeval/epoch=0.1859719823565767` and
  `euroeval/train_step=50000`. Nineteen task rows completed; `valeu-da` was
  intentionally skipped.
- At `20:32` on 2026-07-28, the 50K GPU eval rows became terminal, persistent
  servers were torn down, and `campaign-train-100000` started successfully on
  all eight GPUs. Its direct stdout/stderr log is followed in tmux window
  `hrm-0:8` (`training-output`); scheduler and Rich monitor remain in windows
  `6` and `7`.
- The remote W&B history had reached step `62056`, while the newest fully
  resumable checkpoint was step `62000`. W&B therefore ignores the first 56
  repeated log points as non-monotonic; logging resumes normally above
  `62056`. This does not prevent the training segment from continuing to
  `100000`.

DFM8 XXL segmented campaign through epoch 1, 2026-07-30. Confidence: high from
locked plan inspection, live scheduler telemetry, and dependency assertions.

- The same live plan now covers the complete remainder of epoch 1:
  `logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725`.
- The chain is:
  `100K eval -> train 100K-150K -> 150K eval -> train 150K-200K -> 200K
  eval -> train 200K-250K -> 250K eval -> train 250K-268857`.
- `268857` is the exact optimizer-step count for one DFM8 epoch under this
  run: `floor(70,479,433,697 / 262,144)`.
- Each of the 100K, 150K, 200K, and 250K checkpoints has 188 GPU evaluation
  rows: 85 standard shards, 51 DFM shards, 32 DFM IFEval-DA shards, and 20
  EuroEval jobs. Each also has one atomic `checkpoint-averages` finalizer.
- Every checkpoint release barrier uses terminal dependencies over exactly its
  188 GPU rows. Evaluator teardown and the next training segment therefore
  proceed after all eval attempts become terminal even if a merge, W&B sync,
  average, or report row fails.
- Training segments reserve all eight scheduler GPUs and resume from the
  preceding forced regular step checkpoint. Their targets are `step_150000`,
  `step_200000`, `step_250000`, and `step_268857`.
- The appended 200K and 250K evals preserve the production settings used at
  150K: EMA HF export, EuroEval-first ordering, batches 64/32/32/32 for
  standard/DFM/DFM-IFEval/EuroEval, six total attempts, Gemma 4 native chat
  template, persistent vLLM utilization `0.95`, and the `178000 MiB`
  effective-free-memory gate. Judged Talemaader uses batch/concurrency `16`,
  vLLM utilization `0.85`, a local `unsloth/gemma-4-E4B-it` judge, and the
  `180000 MiB` gate.
- The running scheduler noticed the newly appended rows without restart. The
  200K and 250K checkpoint waits are active while the 100K evaluation
  continues.
- At `12:55` on 2026-07-30, the 100K GPU eval graph became terminal,
  evaluator teardown completed, and `campaign-train-150000` resumed from
  `step_100000` on all eight GPUs. Tmux window `hrm-0:8` had remained
  hard-coded to the prior 62K-to-100K log. It now runs
  `scripts/follow_latest_training_log.sh`, which polls the campaign log root
  every 10 seconds and follows the newest segment automatically. A live check
  showed it following `step_100000_to_150000/train_until_step_150000.log` at
  step `100350`.

DFM8 XL clean-full metric export and checkpoint ranking, 2026-07-31.
Confidence: high from unsampled W&B history, CSV validation, and explicit
metric calculations.

- Source run: `peter-sk-sdu/DFM5/dfm8-xl-from-dfm6-dfm7-epoch5-clean-full`,
  displayed as `DFM8-XL clean full from DFM6-DFM7 epoch5`.
- Tidy CSV:
  `exports/metrics/dfm8-xl-clean-full-from-dfm6-dfm7-epoch5_metrics.csv`.
  It contains `2,031,140` numeric observations across all `468` selected
  training/evaluation metric keys, is `365,260,686` bytes, has no blank metric
  values, and is monotonic over W&B steps `5` through `1,768,065`.
- The broad normalized headline average is highest at `step_1450000`, epoch
  `5.820123020035972`, with `0.6041569566`. `step_1700000`, epoch
  `6.749984582191261`, ranks third at `0.6009481502`.
- Removing EuroEval and averaging the remaining 8 standard plus 11 DFM
  headline metrics individually still selects 1450K: `0.6914526360` versus
  `0.6897745957` at 1700K.
- For an international equal-weight score of ARC, BoolQ, DROP, HellaSwag,
  MMLU, Winogrande, GovReport BERTScore, MATH, GSM8K, and HumanEval, the best
  checkpoint is `step_1650000`, epoch `6.564012269760203`, at `0.725127399`.
  The next checkpoints are 1550K (`0.722743017`), 1750K (`0.722418191`), and
  1450K (`0.722382183`). 1700K ranks eighth at `0.719983877`.
- If every one of the 37 headline metrics receives weight 1 but GSM8K and
  HumanEval each receive 5x or 10x weight, 1450K remains best. At 25x,
  1650K becomes best. If selection is almost exclusively the mean of GSM8K
  and HumanEval, 1750K is best.

Atomic W&B average finalization, 2026-07-28. Confidence: high from local logs,
remote W&B history inspection, raw workspace-spec inspection, focused plan
generation, and scheduler unit tests.

- The 50K plan launched seven separate average writers. `dfm-average` and
  `danish-average` both resumed W&B run `40j5y877` in the same second and both
  wrote internal history step `10846`; one row replaced the other. The
  calculated Danish value was valid, but its history point was initially
  absent.
- The 50K averages were repaired in one atomic W&B row. Remote history now
  contains `headline_avg_v3/danish=0.4415358429103832` with count `18` at
  epoch `0.1859719823565767`, together with the other headline and suite
  averages.
- Further diagnosis showed why the Danish point alone remained invisible in
  line panels: its rows existed and paired correctly with
  `headline_avg_v3/epoch`, but W&B's `historyKeys` registry had no numeric
  schema entry for `headline_avg_v3/danish`; English, Math/Code, and overall
  did. The metric and count were explicitly registered and re-logged.
  Server-side verification now shows numeric history-key entries and a fresh
  Danish point at internal history step `62756`. The user subsequently
  confirmed that the point renders in both Danish-average panels in workspace
  `3fvncok3gjh`.
- The average logger now explicitly calls `wandb.define_metric` for every
  emitted average key in addition to the prefix wildcard. Atomic average rows
  therefore register each series even if an earlier concurrent W&B client
  lost the wildcard-derived history-key update.
- Superseded mistaken diagnosis: `760qd0evtsa` was not the workspace the user
  was viewing. Adding an explicit panel to its auto-generated Danish section
  suppressed its other auto panels. That edit was fully reverted to the
  previously observed state (`panels=[]`, `isPanelsAuto=true`).
- The actual workspace is `3fvncok3gjh`. It already had the correct Danish
  average panel and all 20 Danish panels.
- Superseded mistaken selection interpretation: this workspace uses
  `selections.root=1`, W&B's subtractive mode, where IDs in `tree` are hidden
  rather than selected. Appending `40j5y877` therefore hid the run. The run ID
  was removed from that exclusion tree. A server-side re-read confirms it is
  no longer hidden and the workspace still has Danish `20`, English `17`, and
  Math/Code `5` panels with unchanged definitions.
- Future generated plans now create one `checkpoint-averages` action instead
  of seven concurrent average actions. It waits for all standard/DFM merges
  and EuroEval jobs, then writes all `headline_avg_v3/*` section averages and
  all `suite_avg_v3/*` suite averages in one W&B history event.
- A subsequent full audit of the 46 unique metrics used by workspace
  `3fvncok3gjh` found seven raw series whose values existed in W&B summaries
  but lacked queryable history schemas: Angry Tweets, ARC, MATH, DFM
  MultiWikiQA, GovReport BERTScore, EuroEval Danish Talemaader, and Valeu-en.
  These were explicitly registered and re-logged at the 50K epoch. Remote
  history verification now finds the expected 50K value for all 45 metrics
  that were actually evaluated: standard `8/8`, DFM `11/11`, EuroEval
  `19/19`, headline averages `4/4`, and suite averages `3/3`. The remaining
  workspace metric, Valeu-da, is intentionally absent because that task was
  skipped and produced no value.
- Superseded implementation: registering every one of the roughly 449 raw
  evaluation keys in one W&B update was too broad and did not reliably create
  every remote history schema. The production loggers now explicitly register
  only metrics used by the headline workspace. Individual standard, DFM, and
  EuroEval writers do this when their task completes.
- The atomic `checkpoint-averages` finalizer is now also the authoritative
  raw-headline finalizer. Even though it is invoked with `--averages-only`, it
  collects and re-logs the 37 configured headline metrics together with all
  headline and suite averages in one history event. It does not re-log the
  hundreds of diagnostic metrics. This avoids concurrent W&B-client row
  collisions while ensuring every visible panel receives a schema-backed
  checkpoint point.
- DFM8 XXL 100K timing clarification, 2026-07-30. Confidence: high from the
  locked plan, merged local EuroEval artifacts, and remote W&B history. All
  19 executable EuroEval jobs had completed while standard, DFM, and
  IFEval-DA were still running. The unified `checkpoint-averages` row therefore
  correctly remained pending: it waits for all suites, not merely EuroEval.
  To expose the already-final EuroEval result promptly, the 100K suite average
  was logged separately with exact metric registration:
  `suite_avg_v3/euroeval=0.4836866461293064`, count `18`, epoch
  `0.3719439647131534`. Remote history verification found the point. The
  eventual atomic checkpoint finalizer will safely re-log the same result
  together with the other suites.
- The pending 100K and 150K rows in the live XXL plan were migrated under the
  plan lock to this atomic layout. The logger recognizes the atomic contract
  even when invoked by the already-running pre-change scheduler process, so
  training and scheduler processes do not need to restart.
- GPU release remains independent of average success: campaign teardown and
  the next training segment depend on the terminal state of GPU eval jobs, not
  on the atomic average or report row.
- Repo structure: submodules and .gitignore cleanup, 2026-08-07. Confidence:
  high from direct `git` inspection and successful commits. `data_io/` and
  `dfm-evals/` are now git submodules pinned to commits `0483afe` and
  `80c121d` respectively. `.gitmodules` uses HTTPS URLs
  (`https://github.com/schneiderkamplab/{data_io,dfm-evals}`). The parent
  `.gitignore` was extended to cover `/exports/`, `/export*/`, `/external/`,
  `/logs/`, `/tmp/`, `/outputs/`, `/synth/`, `tmp_*`, and the DFM8 packages
  (`/dfm8_openhermes_da/`, `/dfm8_openhermes_repaired/`, `/dfm8_synthetic/`).
  `eval_scheduler/tests/` (4 test files) is now tracked. `codex_proxy.py` and
  `eval_scheduler/uv.lock` were removed. The statement that `evals/ferrum/`
  remains intentionally untracked but not gitignored was superseded on
  2026-08-10: local `/evals/`, `/eval_scheduler/plans/`, and
  `/hellaswag-da-mini/` runtime/data artifacts are now explicitly ignored.
  Both submodules were clean after their respective commits; later DFM9 and
  evaluation work introduced separately staged changes described by current
  Git status.
