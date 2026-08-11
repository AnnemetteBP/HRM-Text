---
type: Software Reference
title: '`eval_scheduler/`'
description: 'Part of Script Entities: `eval_scheduler/`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `eval_scheduler/`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-16. Confidence: high for local package compilation, Typer CLI
startup, smoke plan creation, status display, and pending batch-size editing;
medium for full end-to-end eval execution until a real checkpoint eval is run
through this new scheduler.

`eval_scheduler/` is a new self-contained Python package for a plan-first HRM
evaluation scheduler. It deliberately does not import
`scripts/schedule_checkpoint_evals.sh`; it owns its own job model, plan writer,
state/event files, retry policy, and Typer CLI. It still calls the repository's
existing evaluation entrypoints as external commands (`evaluation.main`,
`scripts/hrm_openai_server.py`, dfm-evals via `uv run`, merge scripts,
headline-average logging, and report generation).

Main files:

```text
eval_scheduler/README.md
eval_scheduler/pyproject.toml
eval_scheduler/eval_scheduler/cli.py
eval_scheduler/eval_scheduler/model.py
eval_scheduler/eval_scheduler/catalog.py
eval_scheduler/eval_scheduler/plan.py
eval_scheduler/eval_scheduler/runtime.py
eval_scheduler/eval_scheduler/monitor.py
```

The editable plan format is `plan.tsv` with header:

```text
job_id	action	family	name	shard	shards	deps	deps_mode	initial_batch	max_retries	gpu_policy	status	attempt	log_dir	metadata_json
```

The plan is intentionally more expressive than the old `jobs.tsv`. It includes
evaluation jobs plus merge, average, and report jobs as dependency-gated rows.
Pending rows can be edited directly, and `initial_batch` controls future
attempts. This avoids the previous workaround where synthetic telemetry rows
had to be injected to force future shards to use a lower batch size.

Current supported actions:

```text
train_until_step
terminal_barrier
teardown_eval
wait_checkpoint
eval_standard
eval_dfm
eval_dfm_ifeval
eval_euroeval
merge_standard
merge_dfm
merge_ifeval
average
report
```

Checkpoint-wait update, 2026-06-16. Confidence: high for local plan smoke tests
and a missing-checkpoint runtime smoke test. Generated plans now include a
`wait_checkpoint` row by default. All eval rows for that checkpoint depend on
the wait row. The wait row completes only when either
`CKPT_PATH/fsdp2_<tag>/.metadata` or `CKPT_PATH/unsharded_<tag>.pt` exists and
all configured `carry_<tag>.<rank>.pt` files exist. Defaults are 8 carry ranks,
300 seconds between polls, and no maximum wait time. CLI controls:

```text
--include-checkpoint-wait / --no-include-checkpoint-wait
--checkpoint-carry-ranks 8
--checkpoint-wait-seconds 300
--checkpoint-wait-max-seconds 0
```

This makes it possible to queue evals before a checkpoint exists. When the wait
row becomes `done`, downstream eval shards become ready and can start on free
GPUs.

Multiple-checkpoint plan update, 2026-06-16. Confidence: high for local append
smoke test. `plan create --append` appends another checkpoint subgraph to an
existing `plan.tsv`. Job IDs and internal dependencies are rebased
automatically. A smoke plan with `step_300000` and appended `step_350000`
contained two independent `wait_checkpoint` rows:

```text
wait-00001  step_300000
wait-00191  step_350000
```

The first appended eval row for `step_350000` depended on `wait-00191`, not
the first checkpoint wait row.

The runner now has a small non-GPU worker pool for `wait_checkpoint`, merge,
average, and report jobs in addition to GPU worker slots. This prevents future
checkpoint wait rows from consuming GPU slots while still allowing multiple
upcoming checkpoints to be watched.

External-model evaluation update, 2026-06-16. Confidence: high for local source
inspection, `compileall`, generated plan inspection, and process/status
inspection. `eval_scheduler` supports external Hugging Face/vLLM models through
`plan create-external`. External standard evals, DFM evals, DFM IFEval-DA, and
EuroEval start one single-GPU vLLM OpenAI-compatible server per GPU worker/task,
run the client against that per-task server, then tear the server down. The
external standard path uses `evaluation.engines.OpenAIEngine`; dfm-evals and
EuroEval use OpenAI-compatible target URLs.

Operational notes for external vLLM jobs:

- Prefer a local snapshot path, e.g.
  `/home/ucloud/.cache/huggingface/hub/models--Qwen--Qwen3.5-2B/snapshots/<rev>`,
  instead of a remote model id when launching many concurrent per-task servers.
  The first Qwen3.5-2B attempt hit Hugging Face Hub `429 Too Many Requests`
  because every vLLM server queried the Hub.
- Each vLLM job now gets isolated cache directories under the job log directory
  via `VLLM_CACHE_ROOT`, `TORCHINDUCTOR_CACHE_DIR`, `TRITON_CACHE_DIR`, and
  `CUDA_CACHE_PATH`.
- vLLM startup now fails fast if the server process exits or logs an OOM while
  the scheduler waits for `/health`.
- For Qwen3.5-2B on this machine, `--vllm-extra-args "--enforce-eager"` avoids
  torch.compile/CUDAGraph startup fragility, with a speed tradeoff.
- Follow-up on 2026-06-16: after CUDA was installed in `/usr/local/cuda`, the
  scheduler-managed vLLM environment was changed to expose `CUDA_HOME`,
  `CUDA_PATH`, `PATH`, and `LD_LIBRARY_PATH` to each vLLM server when
  `/usr/local/cuda` exists. This allows vLLM's DeepGEMM warmup to import
  `deep_gemm` successfully. A single-GPU Qwen3.5-2B smoke on GPU0 reached
  `/health` with DeepGEMM enabled; the ordered Qwen/DFM5 scheduler was then
  relaunched and the first Qwen EuroEval jobs completed and synced.
- Follow-up on 2026-06-16: Qwen external standard evals initially failed on
  MATH because `evaluation.main` passed checkpoint-oriented Hydra keys such as
  `ckpt_path` into `OpenAIEngine`. `evaluation.engines.OpenAIEngine` now accepts
  and ignores extra keyword arguments, matching the external-model use case
  where checkpoint keys are scheduler metadata rather than engine arguments.
  The failed/running Qwen MATH rows in
  `logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616/plan.tsv` were reset to
  pending and the scheduler was relaunched.
- Separate `eval_scheduler run` instances do not coordinate GPU leases. The
  Qwen plan `logs/scheduler/qwen35_2b_full_20260616` was stopped on 2026-06-16
  after the DFM5 checkpoint scheduler began running `step_400000` EuroEval jobs
  on GPUs 0 and 1. Its running rows were reset to pending so it can be resumed
  later on an explicitly non-conflicting GPU set.

Stop/resume update, 2026-06-16. Confidence: high for local smoke tests with a
missing-checkpoint wait row and a manual stale-`running` repair. The scheduler
now supports graceful stop and later resume:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler stop \
  --plan-dir logs/scheduler/dfm5_L_step300000

python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step300000 \
  --gpus 0,1,2,3,4,5,6,7
```

`stop` writes `PLAN_DIR/stop.request`. The runner observes this file between
job launches and stops claiming new jobs. Already running eval jobs are allowed
to finish normally. A running `wait_checkpoint` row exits with scheduler stop
status and is returned to `pending`, not failed. Starting `run` removes stale
`stop.request` at the beginning, so a later run continues the remaining
pending jobs.

For hard-killed schedulers, rows may be left as `running`. Repair them before
resuming:

```bash
python -m eval_scheduler plan reset-running \
  --plan-dir logs/scheduler/dfm5_L_step300000
```

`plan reset-running --increment-attempt` is also available if an interrupted
attempt should count against the retry budget.

Smoke commands verified locally:

```bash
cd /work/dfm/HRM-Text
python -m compileall -q eval_scheduler
python -m eval_scheduler --help

rm -rf /tmp/hrm-eval-scheduler-smoke
python -m eval_scheduler plan create \
  --plan-dir /tmp/hrm-eval-scheduler-smoke \
  --ckpt-path checkpoints/dfm5/L \
  --ckpt-tag step_300000 \
  --eval-epoch 1.6565307709311847 \
  --log-root logs/eval/smoke_new_scheduler \
  --dfm-log-root logs/dfm_evals/smoke_new_scheduler \
  --euroeval-log-root logs/euroeval/smoke_new_scheduler \
  --wandb-run-id oti1lisg \
  --wandb-run-name dfm5-L \
  --model-prefix hrm-dfm5-L \
  --run-euroeval \
  --queue-order euroeval-first \
  --standard-batch 64 \
  --dfm-batch 32 \
  --ifeval-batch 32 \
  --euroeval-batch 16

python -m eval_scheduler status --plan-dir /tmp/hrm-eval-scheduler-smoke
python -m eval_scheduler plan set-batch \
  --plan-dir /tmp/hrm-eval-scheduler-smoke \
  --family dfm_ifeval \
  --batch 16
python -m eval_scheduler plan list \
  --plan-dir /tmp/hrm-eval-scheduler-smoke \
  --family dfm_ifeval \
  --limit 5
```

The smoke plan produced 209 explicit jobs:

```text
eval_euroeval: 20
eval_dfm_ifeval: 32
eval_standard: 85
merge_standard: 8
eval_dfm: 51
merge_dfm: 10
merge_ifeval: 1
average: 1
report: 1
```

The batch edit command changed all 32 pending `dfm_ifeval` rows from batch
`32` to batch `16`.

Qwen GovReport retry update, 2026-06-16. Confidence: high for local source
inspection, shard logs, merge logs, and W&B API checks. The Qwen3.5-2B
GovReport failures in
`logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616` were not OOM failures.
They were vLLM HTTP 400 context-length failures: long GovReport prompts plus
the requested generation length exceeded the model's 4096-token context. Batch
size retries could not fix this.

Fixes applied:

- `dfm-evals/dfm_evals/tasks/summarization.py` now lets `govreport()` accept
  `max_report_chars`; the default is `None`, so normal GovReport behavior is
  unchanged unless a caller opts in.
- `eval_scheduler/eval_scheduler/runtime.py` now passes DFM template overrides
  from job metadata, including `dfm_max_gen_toks` and arbitrary
  `dfm_task_args`.
- The Qwen GovReport plan rows were reset with `dfm_max_gen_toks=128` and
  `dfm_task_args=["max_report_chars=10000"]`.
- Client fatal logs such as OpenAI bad requests now terminate the paired vLLM
  server and fail the joint task attempt, instead of leaving an orphan server or
  treating the worker and server independently.

All 16 Qwen GovReport shards then completed, merged, and synced to W&B run
`peter-sk-sdu/DFM5/qwen35-2b-full`. Verified summary keys include:

```text
dfm_eval/govreport/chrf3pp/mean = 9.986128459008524
dfm_eval/govreport/bertscore_f1/mean = 0.8529781600554213
dfm_eval/govreport/rouge2/mean = 0.061699390782425347
```

Gemma 4 E2B external baseline update, 2026-06-17. Confidence: high for local
process inspection, vLLM logs, EuroEval logs, and scheduler status.

The Gemma baseline is queued in:

```text
logs/scheduler/gemma4_e2b_then_dfm5_L_500k_20260617
```

The first block evaluates local model:

```text
/work/dfm/brainsurgery/models/google/gemma-4-E2B-it
```

against the full standard, dfm, and EuroEval suite, then the same plan waits
for `checkpoints/dfm5/L` `step_500000` and evaluates it. The `step_500000`
wait row depends on the Gemma average row, so the 500K HRM eval block starts
after the Gemma baseline is averaged.

Gemma-specific vLLM notes:

- Loading the snapshot as its advertised `Gemma4ForConditionalGeneration`
  failed because the local snapshot has no `preprocessor_config.json`.
- For text-only evaluation, vLLM must be forced to
  `Gemma4ForCausalLM` with:

```text
--hf-overrides '{"architectures":["Gemma4ForCausalLM"]}'
```

- The local tokenizer has no `chat_template`, and vLLM chat completions fail
  without one. The scheduler plan therefore passes:

```text
--chat-template /work/dfm/HRM-Text/evaluation/chat_templates/gemma4_e2b_plain_chat.jinja
```

This is a conservative plain role-label template using `System:`, `User:`, and
`Assistant:` rather than Gemma-specific turn tokens, because the local
tokenizer did not expose `<start_of_turn>`/`<end_of_turn>` as normal tokens.

EuroEval-specific notes:

- Use the explicit HRM Python wrapper:

```text
/home/ucloud/miniforge3/envs/hrm/bin/python /work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py
```

- Set `euroeval_generative_type=instruction_tuned`.
- Set `fixed_retry_batch=true` for the Gemma jobs so non-OOM retries do not
  halve the deliberately chosen baseline batches.

With these settings, the first Gemma EuroEval jobs reached real benchmarking
logs such as `Loading the model ...` and per-sample progress, and scheduler
status showed completed rows rather than the earlier `Model ... not found`
failures.

Gemma baseline repair, 2026-06-17. Confidence: high for local scheduler status,
plan edits, and successful rerun logs.

The initial Gemma baseline run later blocked before the `step_500000` wait row
because two DFM merge rows depended on failed shards:

```text
merge-00162 dfm:govreport
merge-00180 dfm:generative_talemaader
```

The failed `euroeval:valeu-en` row was not an average dependency and failed
because the model produced too many invalid labels; it was marked `skipped`
rather than retried indefinitely.

GovReport failed with vLLM context overflow: prompts near 3585 input tokens
plus 512 requested output tokens exceeded the 4096 context limit. The failed
Gemma GovReport rows were reset with:

```json
{
  "dfm_context_length": 3968,
  "dfm_max_gen_toks": 128,
  "dfm_task_args": ["max_report_chars=10000"]
}
```

All 16 repaired GovReport shards completed successfully and `merge-00162`
succeeded.

`generative_talemaader` failed because the DFM suite requires a judge model.
The failed Gemma rows were reset with:

```json
{
  "judge_model": "openai/gemma-4-e4b-judge",
  "judge_base_url": "http://127.0.0.1:8099/v1",
  "max_connections": 4
}
```

The judge server was already running as:

```text
/home/ucloud/miniforge3/envs/hrm/bin/python scripts/transformers_openai_server.py unsloth/gemma-4-E4B-it --served-model-name gemma-4-e4b-judge --host 127.0.0.1 --port 8099 --dtype bfloat16 --attn-implementation sdpa --max-new-tokens 64
```

The same GovReport and judge metadata were also applied to the future
`step_500000` rows in the same plan so that the HRM 500K block does not repeat
the same failures.

Qwen EuroEval MultiWikiQA sync update, 2026-06-16. Confidence: high for local
metrics and W&B API checks. The local MultiWikiQA metric existed but initially
did not appear in the remote W&B summary/history. Re-running
`scripts/log_euroeval_to_wandb.py` against
`logs/euroeval/qwen35_2b_full_ordered_20260616/qwen35_2b/multi-wiki-qa-da/euroeval_benchmark_results.jsonl`
logged the metric to the same run. Verified key:

```text
euroeval/da/reading-comprehension/multi-wiki-qa-da/f1 = 73.03916213314417
```

Qwen GSM8K note, 2026-06-16. Confidence: high for local metric/log/source
inspection, medium for exact generation-format inference because standard evals
do not persist generated text. The Qwen3.5-2B full run logged
`eval/GSM8k/acc=0.0`, `eval/GSM8k/invalid=1.0`, and `eval/GSM8k/n=1319`.
All eight GSM8K shards under
`logs/eval/qwen35_2b_full_ordered_20260616/standard_shards/GSM8k/` had
`invalid=1.0`. The local GSM8K scorer in `evaluation/benchmarks.py` parses only
the whole generated string as a number unless `last_boxed_only_string` finds a
boxed answer. The standard config gives Qwen the raw GSM8K question with
`max_tokens=512` and no explicit final-answer-only or boxed-answer instruction.
Treat this as an extraction/prompt mismatch, not as evidence that Qwen solves
zero GSM8K. Any fixed rerun should save generations and use a new metric key or
clear suffix rather than silently replacing the old all-invalid metric.

Follow-up on 2026-06-16. Confidence: high for source inspection and local
synthetic extraction tests. `evaluation/benchmarks.py` now makes GSM8K answer
extraction more robust: boxed answers still win, bare numeric strings still
work, `####`, `final answer`, and `answer is` patterns are accepted, and the
fallback is the last standalone integer-valued number in the generation.
Non-integer floats remain invalid. This changes future GSM8K scoring and should
not be silently mixed with the earlier all-invalid Qwen GSM8K result.

Qwen clean-run backfill and GSM8K rerun, 2026-06-17. Confidence: high for local
scheduler status, local merged artifact, and W&B API checks. The old Qwen
metrics were backfilled to a new clean W&B run, excluding old GSM8K and all
headline averages:

```text
project: DFM5
run_id: qwen35-2b-full-clean
run_name: Qwen3.5 2B full clean
script: scripts/backfill_qwen35_clean_wandb.py
```

The backfill logged 444 keys from existing local standard, DFM, and EuroEval
artifacts. Verified remote summary had no `eval/GSM8k/*` keys and no `avg/*`
keys before the rerun. The corrected GSM8K rerun was inserted at the front of
`logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616/plan.tsv` as eight
external standard-eval shards plus one merge row:

```text
eval-qwengsm-00000 .. eval-qwengsm-00007
merge-qwengsm-00008
log root: logs/eval/qwen35_2b_gsm8k_fixed_20260616
```

Final merged fixed GSM8K metrics, synced to `qwen35-2b-full-clean`:

```text
eval/GSM8k/acc = 0.6656600454890069
eval/GSM8k/invalid = 0.023508567096285068
eval/GSM8k/n = 1319
```

The clean run intentionally still has no headline averages; recompute them only
if the desired average definition should include the corrected Qwen GSM8K.

Follow-up on 2026-06-17. Confidence: high for local dry-run output, W&B sync
logs, and W&B API verification. Headline averages were added to the clean Qwen
run after creating a clean standard-eval root that symlinks all standard
artifacts from the original Qwen run except GSM8K, which points to the fixed
GSM8K rerun:

```text
logs/eval/qwen35_2b_clean_standard_20260617/standard_shards/GSM8k
  -> logs/eval/qwen35_2b_gsm8k_fixed_20260616/standard_shards/GSM8k
```

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id qwen35-2b-full-clean \
  --run-name 'Qwen3.5 2B full clean' \
  --metric-prefix avg \
  --item '0:0.0:logs/eval/qwen35_2b_clean_standard_20260617:logs/dfm_evals/qwen35_2b_full_ordered_20260616:logs/euroeval/qwen35_2b_full_ordered_20260616/qwen35_2b'
```

Verified summary values:

```text
avg/danish = 0.4471885859937283   (count 18)
avg/english = 0.5782765269227623  (count 15)
avg/math_code = 0.542416855396642 (count 4)
avg/overall = 0.5226273227710442
```

Scheduler average dependency fix, 2026-06-17. Confidence: high for local plan
inspection, log inspection, active-plan edit, and `compileall`. The
`step_450000` wait guard in
`logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616` was present but blocked
behind the previous checkpoint's `average-00417` row. That average row depended
on `eval-00219` (`euroeval:valeu-da`), which had failed because EuroEval found
no candidate label for 1/53 samples and aborts ValEU-da when invalid outputs
are present. Since `valeu-*` metrics are excluded from headline averages, this
dependency was wrong.

Fixes applied:

- Removed all existing `valeu-*` EuroEval dependencies from active-plan average
  rows (`average-00208`, `average-00417`, `average-00626`).
- Updated `eval_scheduler/eval_scheduler/plan.py` so future generated average
  jobs include EuroEval dependencies except groups whose names start with
  `valeu-`.
- Restarted the scheduler. `average-00417` completed, `wait-00418` immediately
  saw `step_450000` as ready, and `step_450000` eval jobs started at
  `2026-06-17T06:24:17+02:00`.

DFM5 report update, 2026-06-17. Confidence: high for local artifact inspection
and regenerated Markdown. `scripts/generate_dfm5_l_eval_comparison_report.py`
now includes the DFM5-L `step_400000` full-eval artifacts and populates the
Qwen3.5 2B comparison column from the local clean Qwen artifacts where
available:

```text
DFM5 400K standard: logs/eval/dfm5_L_step400000_full_ordered_20260616
DFM5 400K DFM:      logs/dfm_evals/dfm5_L_step400000_full_ordered_20260616
DFM5 400K EuroEval: logs/euroeval/dfm5_L_step400000_full_ordered_20260616/step_400000
Qwen clean standard: logs/eval/qwen35_2b_clean_standard_20260617
Qwen DFM:            logs/dfm_evals/qwen35_2b_full_ordered_20260616
Qwen EuroEval:       logs/euroeval/qwen35_2b_full_ordered_20260616/qwen35_2b
```

The canonical report is `docs/dfm5.md`. Superseded, 2026-06-20: the former
compatibility symlink `docs/df5m.md -> dfm5.md` was deleted so the repo has only
one canonical DFM5 report path.
At 400K, DFM5-L beats local-clean Qwen3.5 2B on the Danish average
(`51.0` vs `44.7`) and slightly on the English average (`59.1` vs `57.8`), but
loses badly on Math & Code (`27.0` vs `54.2`).

DFM5 docs cleanup, 2026-06-20. Confidence: high for local filesystem
inspection and regenerated Markdown. The Slack paste-table files
`docs/dfm5_slack_tables.md` and `docs/dfm5_slack_tables/` were deleted, as was
the misnamed compatibility symlink `docs/df5m.md`. `docs/dfm5.md` is now the
only file under `docs/`, and it was regenerated with:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm5_l_eval_comparison_report.py
```

DFM5 450K report update, 2026-06-17. Confidence: high for local artifact
inspection and regenerated Markdown. `scripts/generate_dfm5_l_eval_comparison_report.py`
now also includes:

```text
DFM5 450K standard: logs/eval/dfm5_L_step450000_full_ordered_20260616
DFM5 450K DFM:      logs/dfm_evals/dfm5_L_step450000_full_ordered_20260616
DFM5 450K EuroEval: logs/euroeval/dfm5_L_step450000_full_ordered_20260616/step_450000
```

The regenerated `docs/dfm5.md` has DFM5-L 450K headline averages:
Danish `48.1`, English `60.1`, Math & Code `27.9`. Key Math & Code rows are
GSM8K `33.4`, MATH `47.1`, HumanEval `31.1`, and BFCL-v2 `0.0`.

Gemma 4 E2B external-baseline eval note, 2026-06-17. Confidence: high for
local path/config inspection and scheduler CLI inspection; medium for exact
batch sizes until run. A Qwen3.5-2B-style external eval can be scheduled for
the local Gemma 4 E2B instruct checkpoint without new scheduler code. The local
model path is:

```text
/work/dfm/brainsurgery/models/google/gemma-4-E2B-it
```

Its local `._param_count.json` reports `5,123,178,979` total parameters and
`config.json` advertises `Gemma4ForConditionalGeneration` with
`model_type="gemma4"`. Project decision after review: do not reduce batch sizes
below the Qwen3.5-2B external-eval defaults just because the total parameter
count is larger. Much of the total is non-text/image-side capacity, while the
effective text model is E2B-scale, and prior vLLM jobs had substantial GPU
headroom. The scheduler's `plan create-external` command already supports the
needed vLLM fields (`--model`, `--served-model-name`, `--vllm-extra-args`,
`--vllm-gpu-memory-utilization`, and batch defaults). Start with Qwen-style
batch sizes (`standard=64`, `dfm=32`, `ifeval=32`, `euroeval=16`) and rely on
the scheduler's OOM retry/halving path only if a specific task proves too large.
If vLLM text-only loading has issues, try the known Gemma text-only override:

```text
--vllm-extra-args '--enforce-eager --hf-overrides {"architectures":["Gemma4ForCausalLM"]}'
```

DFM6 data-mix note, 2026-06-17. Confidence: medium; this is a forward-looking
project decision informed by the 400K vs Qwen3.5 2B comparison. DFM6 should:

- include all new DFM post-training datasets;
- scale up Danish math and code datasets;
- scale up English math and code datasets.
- include Danish tool-calling data;
- include English tool-calling data.

Reason: DFM5-L at 400K is already competitive or better than local-clean
Qwen3.5 2B on the HRM-Text model-card standard eval average (`58.4` vs `49.3`)
and on Danish/English language-oriented averages, but remains substantially
behind on math/code (`27.0` vs `54.2` Math & Code average; GSM8K `31.5` vs
`66.6`, HumanEval `30.5` vs `47.6`, BFCL-v2 `0.0` vs `52.1`). The next data
mix should therefore not only add post-training breadth, but explicitly
increase math/code and tool-calling coverage in both Danish and English.

DFM6 tokenizer/instruction-format note, 2026-06-17. Confidence: medium; this is
a forward-looking architecture/data-format decision. For DFM6, replace the
current tokenizer with the Gemma 4 tokenizer and use the Gemma 4 chat template
for instruction-format data instead of the instruction format used for the
original Sapient and DFM5 corpora. This should be treated as a dataset
conversion and training-compatibility change, not a cosmetic tokenizer swap:
all instruction/post-training sources need to be rendered through the new chat
template, and evaluation/export paths should be checked for tokenizer/chat
template assumptions.

Expanded DFM6 checklist, 2026-06-17. Confidence: medium. The DFM6 direction is
solid, but the plan should explicitly cover these items before sampling or
training:

- Verify the exact Gemma 4 tokenizer artifact, license, vocabulary size,
  special tokens, and chat-template rendering; update model config and embedding
  sizes accordingly.
- Treat DFM6 as a fresh-tokenizer training run unless a deliberate
  retokenization/upcycling strategy is implemented; old DFM5 checkpoints are not
  directly resume-compatible after a tokenizer swap.
- Define canonical schemas for tool-calling data in both Danish and English,
  including tool/function JSON, multi-turn tool traces, invalid/tool-error
  cases, and final natural-language responses.
- Add dedicated eval coverage for tool calling in both languages, not only
  BFCL-v2 English; otherwise the data addition cannot be validated.
- Balance post-training data against pretraining/instruction data so Gemma
  chat-template formatting does not overfit short assistant-style replies.
- Rebuild all tokenized/sampled artifacts from source after the tokenizer
  change; do not mix old tokenizer outputs with Gemma-tokenized outputs.
- Check conversion/export/inference/eval paths for hard-coded tokenizer path,
  chat tokens, BOS/EOS handling, and generation stop tokens.
- Add explicit data-mix targets for math/code/tool calling rather than only
  "include more"; DFM5 showed that general language gains do not automatically
  close GSM8K/HumanEval/BFCL gaps.
- Add contamination and dedup checks for the expanded math/code/tool-calling
  sources, especially against held-out eval prompts and common benchmark
  training/test splits.
- Run at least one small end-to-end migration rehearsal before committing a
  large DFM6 run: convert a tiny Gemma-template sample, tokenize it, sample it,
  train for a short smoke run, export, serve, and run standard/DFM/EuroEval
  smoke evals.
- Keep an ablation trail for the main DFM6 additions. At minimum, record which
  source families are new relative to DFM5 and keep enough sampling metadata to
  compare base DFM6, math/code-scaled DFM6, and tool/post-training-enriched
  DFM6 rather than treating all changes as one opaque bundle.

Monitor update, 2026-06-16. Confidence: high for local log inspection and a
live monitor snapshot. External-model DFM jobs write the OpenAI-compatible
server log as `vllm.log`, while the monitor originally looked only for
`server.log`. This made active tasks such as Qwen `generative_talemaader`
display `progress unknown` even though the vLLM log contained successful
`POST /v1/chat/completions` lines. The monitor now falls back to `vllm.log`
when `server.log` is absent. It can therefore show request counts such as
`completion 63/? failed 0`.

Superseded caveat, 2026-06-18: ETA previously remained unknown for some DFM
tasks whose active shard had not yet written a sample total. The monitor now
also infers DFM shard totals from completed sibling shard logs for the same
task/checkpoint. This fixed `generative_talemaader` lines that looked like
`completion 51/? ... ETA unknown` once at least one sibling shard had emitted a
stable `(N samples)` task header. Confidence: high for local monitor snapshots
on the `dfm5_L_step550000_full_native_followup_20260617` campaign.

Follow-up, 2026-06-18. Confidence: high for local log inspection, code
compilation, and a live monitor snapshot on
`logs/scheduler/dfm5_L_step600000_full_simple_20260618_600k_simple`. Some
active DFM shards can keep `dfm-evals.log` empty until late in the run, so no
current sibling shard has a visible `(N samples)` header yet. The monitor now
falls back to older completed campaigns for the same DFM task and shard count,
preferring the exact same shard and using the most common historical total.
For `generative_talemaader` with `8` shards, local prior logs showed `101`
samples per shard, and the live monitor changed from
`completion 56/? ... ETA unknown` to `completion 59/101 ... ETA 5m20s` without
touching the running eval jobs.

Monitor checkpoint/model-label update, 2026-06-16. Confidence: high for local
compilation and a one-shot monitor snapshot. `eval_scheduler/eval_scheduler/monitor.py`
now includes the evaluated model/checkpoint label on active GPU lines and in the
`next ready` queue, using `external_served_model_name`, `model_prefix`,
`ckpt_tag`, and `no_ema` metadata. Example labels:
`qwen35-2b@qwen35_2b:ema`, `hrm-dfm5-L@step_400000:ema`, and
`hrm-dfm5-L@step_400000:noema`.

Locking update, 2026-06-16. Confidence: high for local smoke test. The
scheduler now uses an advisory `fcntl.flock` lock at `PLAN_DIR/plan.lock` for
plan reads and writes. Package commands that mutate or read `plan.tsv` acquire
this lock. The runner claims a job under the same interprocess lock and
re-checks that dependencies are still complete and the row is still pending.

Manual edit workflow:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler plan edit \
  --plan-dir logs/scheduler/dfm5_L_step300000 \
  --editor "vim"
```

Explicit lock/unlock workflow for manual editing in another terminal:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler plan lock \
  --plan-dir logs/scheduler/dfm5_L_step300000

vim logs/scheduler/dfm5_L_step300000/plan.tsv

python -m eval_scheduler plan unlock \
  --plan-dir logs/scheduler/dfm5_L_step300000
```

`plan lock` starts a background lock-holder process and writes
`PLAN_DIR/plan.lock.holder.json` with the holder PID. `plan unlock` terminates
that holder. A smoke test on `/tmp/hrm-eval-scheduler-smoke` verified that
`python -m eval_scheduler status` blocks while the holder owns the lock and
works again after `plan unlock`.

The root `pyproject.toml` now includes `typer` as a dependency so the scheduler
CLI is part of the normal repo environment.

Monitor update, 2026-06-16. Confidence: high for local compilation, CLI smoke
test, and parsing real EuroEval IFEval logs. The scheduler now has two status
views:

```bash
python -m eval_scheduler status --plan-dir logs/scheduler/dfm5_L_step300000
python -m eval_scheduler monitor --plan-dir logs/scheduler/dfm5_L_step300000 --gpus 0,1,2,3,4,5,6,7
```

`status` remains a terse plan/event summary. `monitor` is the operational view:
it reports total `done/running/ready/blocked_pending/failed/skipped`, one line
per GPU with memory/utilization, the active job on that GPU, shard, batch,
attempt, elapsed time, parsed progress, and ETA when the progress fraction is
known. It also lists the next ready jobs.

Progress parsers:

- standard evals: latest generation tqdm `done/total` from the shard log.
- dfm-evals: local server completion counts and server-batch tqdm when present;
  Inspect `logs.json` and dfm-evals task headers are used to infer sample
  totals when available. During model/metric setup before any task header or
  server request exists, progress may still be reported as unknown.
- dfm-evals failures: early configuration failures such as missing judge
  placeholders are surfaced directly in monitor output instead of showing only
  `progress unknown`.
- EuroEval: nested tqdm parsing. Single-benchmark setup bars like `1/1` are
  ignored when a sample loop is still running. Real multi-pass bars are reported
  as `pass x/y samples a/b`; e.g. a synthetic `3/10` pass bar plus `137/343`
  samples reports `pass 3/10 samples 137/343`.

Follow-up, 2026-06-18. Confidence: high for live monitor snapshots. Some
EuroEval tasks such as `cnn-dailymail` and `nordjylland-news` do not keep a
single monotonic tqdm counter; the per-sample bar resets for repeated scoring
passes. The monitor now groups those resets into pass loops and defaults to
10 passes when the plan row has no explicit `euroeval_passes` metadata. This
turns misleading ETA resets into lines such as
`pass 6/10 samples 118/157 ETA 25m42s`.

Follow-up, 2026-06-18. Confidence: high for live monitor snapshots. EuroEval
single-pass tasks such as `ifeval` and `ifeval-da` now also render with an
explicit pass denominator, e.g. `pass 1/1 samples 101/343`, instead of only
`samples 101/343`. Repeated-pass tasks still render as `pass X/10 samples Y/Z`.

Superseded in the same session for IFEval-like tasks: after the first IFEval
generation loop, EuroEval can emit smaller follow-up loops such as
`343 -> 131 -> 47 -> ...`. Those are variable-sized stages, not repeated
passes. The monitor now classifies loops with roughly stable denominators as
`pass X/10` and variable-denominator loops as `stage X/? samples Y/Z`; the
stage ETA is only for the current stage. Confidence: high for the live
`euroeval:ifeval` `step_550000` log.

Verified against the current real EuroEval logs:

```text
ifeval    samples 237/343
ifeval-da samples 282/343
```

EuroEval path fix, 2026-06-16. Confidence: high. `eval_scheduler` now resolves
relative `.py` `euroeval_bin` values to absolute paths in
`eval_scheduler/eval_scheduler/runtime.py` before calling
`scripts/run_euroeval_on_checkpoint.sh`. This is required because that wrapper
changes directory into the EuroEval log root before running `${EUROEVAL_BIN}`.
Without this, scheduler-created EuroEval jobs failed with status `127` and
`No such file or directory` for `scripts/euroeval_api_no_flash_attn_guard.py`.

EuroEval package wrapper fix, 2026-06-18. Confidence: high for failed-run log
inspection and resumed scheduler status. On the DFM5-L `step_600000` eval
campaign, EuroEval jobs failed after server health checks because the default
`euroeval_bin` invoked `scripts/euroeval_api_no_flash_attn_guard.py` directly
from the HRM environment, where `euroeval` was not importable. The scheduler
default now uses:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/uv run --no-project --with euroeval \
  /work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py
```

The active plan's failed EuroEval rows were reset to pending with this
metadata, and freed GPUs subsequently picked up EuroEval jobs before lower
priority shards.

DFM progress/failure monitor update, 2026-06-16. Confidence: high for local
monitor snapshots. `eval_scheduler/eval_scheduler/monitor.py` now reads
dfm-evals `inspect/logs.json` and task-header text such as `(120 samples)` to
show totals when possible. It also detects placeholder errors like missing
`--judge-model` for `{{judge_model}}`; this exposed that the 350K
`generative_talemaader` shards failed because no judge model/base URL was wired
into the new scheduler run.

DFM judge-task runtime update, 2026-06-16. Confidence: high for local direct
judge request, one-sample Inspect smoke test, and completed 350K
`generative_talemaader` shards. `eval_scheduler/eval_scheduler/runtime.py` now
passes optional per-row metadata fields `judge_model` and `judge_base_url` to
dfm-evals jobs, and `max_connections` can cap the Inspect client fanout
independently of the HRM server batch size. For judged Talemaader shards, the
working settings were:

```text
initial_batch: 16
metadata.max_connections: 4
metadata.judge_model: openai/gemma-4-e4b-judge
metadata.judge_base_url: http://127.0.0.1:8099/v1
```

The initial judge server became wedged: a direct OpenAI-compatible
`/v1/chat/completions` request asking for `GRADE: C` timed out. Restarting
`scripts/transformers_openai_server.py` with `--max-new-tokens 64` fixed the
endpoint; a direct request returned in `0.63s`, and a one-sample
`hrm_danish_generative_talemaader` Inspect run completed in `4s`. After that,
the 350K Talemaader shards completed and merged successfully.
