---
type: Software Reference
title: '`scripts/rebalance_export_audits.py`'
description: 'Part of Script Entities: `scripts/rebalance_export_audits.py`.'
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
# `scripts/rebalance_export_audits.py`

Part of [Script Entities](/entities/scripts.md).

Operational update on 2026-06-12. Confidence: high.

The export audit/generation run is currently guarded by an automatic watcher
that scans every 10 minutes and rebalances only after a currently open dataset
first reaches its token target. The current generation uses non-eager vLLM on
GPUs 0-3 only.

Active run root:

```text
logs/export_dataset_audits_rebalance_20260612T093058
```

Active allocation:

```text
GPU0: danish-dynaword-paragraph-reordering
GPU1: common-pile-denoising
GPU2: common-pile-span-filling
GPU3: common-pile-prefix-continuation
```

Watcher command:

```bash
cd /work/dfm/HRM-Text
setsid bash -lc 'exec python scripts/rebalance_export_audits.py watch \
  --target-tokens 100000000 \
  --gpus 0,1,2,3 \
  --port-base 8900 \
  --interval-seconds 600 \
  --no-enforce-eager \
  >> logs/export_dataset_audits_watch_20260612T102445_gpus0123.log 2>&1' \
  </dev/null >/dev/null 2>&1 &
echo $! > logs/export_dataset_audits_watch_20260612T102445_gpus0123.pid
```

Superseded: an attempted 8-GPU rebalance was started when GPUs 4-7 appeared
free. The user clarified that export audit generation must use only GPUs 0-3.
The 8-GPU attempt was stopped before any persistent 9000-series audit workers
remained, GPU 4-7 HRM EuroEval servers were terminated, and the watcher was
restarted with `--gpus 0,1,2,3` only.

Initial watcher status:

```text
complete: common-pile-paragraph-reordering, danish-dynaword-denoising,
          danish-dynaword-prefix-continuation, danish-dynaword-span-filling
open:     common-pile-denoising, common-pile-prefix-continuation,
          common-pile-span-filling, danish-dynaword-paragraph-reordering
```

Most recent full status before watcher launch:

```text
common-pile-denoising                          72.1M/100.0M open
common-pile-prefix-continuation                63.4M/100.0M open
common-pile-span-filling                       71.9M/100.0M open
danish-dynaword-paragraph-reordering           41.8M/50.0M  open
```

The full `status` command is filesystem-heavy because it rereads all historical
audit JSONL files. Use it sparingly while the WEKA filesystem is under load.

Manual denoising speed-up on 2026-06-12. Confidence: high.

The user explicitly authorized using GPUs 6 and 7 to speed up only
`common-pile-denoising`. The previous single denoising client on GPU1 was
stopped, the 0-3 watcher was paused to avoid conflicting process control, and
`common-pile-denoising` was relaunched as three hash shards:

```text
GPU1: shard 0/3, existing vLLM server on port 8900
GPU6: shard 1/3, new vLLM server on port 8916
GPU7: shard 2/3, new vLLM server on port 8917
```

Run root:

```text
logs/export_denoising_gpus167_20260612T131403
```

The GPU6/GPU7 servers were started without `--enforce-eager` and became
healthy. Initial verification showed GPU1/GPU6/GPU7 at 100% utilization and
GPU6/GPU7 generation throughput around 275-290 tokens/s.

Operational note on 2026-06-12. Confidence: high.

`danish-dynaword-paragraph-reordering` can appear stuck near `49.8M/50M`
accepted estimated tokens even while the worker is healthy. At 13:39 local
time the audit log was still advancing (`judged 38400`), the audit file mtime
was current, and the GPU0 vLLM server was serving at roughly 430-455 generation
tokens/s. The accepted-token total was flat because recent rows were rejected,
with the latest inspected rows marked `wrong_language`.

Manual span-filling speed-up on 2026-06-12. Confidence: high.

After `danish-dynaword-paragraph-reordering` exceeded its 50M target, the user
asked to stop that audit and reuse GPU0 for `common-pile-span-filling`. The
Danish paragraph audit client was stopped, its vLLM server on GPU0/port 8903
was kept alive, the previous single span-filling client on GPU2 was stopped,
and `common-pile-span-filling` was relaunched as two hash shards:

```text
GPU2: shard 0/2, existing vLLM server on port 8902
GPU0: shard 1/2, existing vLLM server on port 8903
```

Run root:

```text
logs/export_span_gpus02_20260612T140630
```

Initial verification showed GPU0 and GPU2 at 100% utilization, both span
shards reaching `judged 100`, and server throughput around 200-305 generation
tokens/s.

Gemma 4 E2B external-baseline metric caveat, 2026-06-17. Confidence: high for
local merged metrics and source inspection; medium for exact model-behavior
interpretation because the standard eval logs do not persist generated text.

The completed Gemma 4 E2B baseline under:

```text
logs/eval/gemma4_e2b_full_20260617
logs/dfm_evals/gemma4_e2b_full_20260617
logs/euroeval/gemma4_e2b_full_20260617
```

shows a split pattern: several EuroEval tasks produce plausible nonzero scores
(`bfcl-v2` tool accuracy `37.4`, `cnn-dailymail` chrF++ `36.0`,
`conll-en` micro-F1 `55.7`, `sst5` macro-F1 `49.4`), while many standard
HRM-Text evals are dominated by invalid parsing. Examples:

```text
eval/BoolQ/acc=0.5,     eval/BoolQ/invalid=1.0
eval/MATH/acc=0.0034,   eval/MATH/invalid=1.0
eval/GSM8k/acc=0.0076,  eval/GSM8k/invalid=0.7650
eval/HellaSwag/acc=0.2566, eval/HellaSwag/invalid=0.8813
eval/Winogrande/acc=0.5036, eval/Winogrande/invalid=0.6504
```

This should be treated as an evaluation-harness compatibility problem before
being treated as a model-quality result. The standard external path uses
`evaluation.engines.OpenAIEngine`, which sends the benchmark prompt as one chat
`user` message, while `evaluation/benchmarks.py` applies strict HRM-oriented
extractors. Standard MCQ benchmarks require an exact single-letter response
after `max_tokens=1`; MATH requires a boxed answer for non-invalid scoring; and
GSM8K only became reliable for Qwen after the scorer was repaired to accept
explicit final-answer patterns and final standalone integers. The earlier Qwen
full run had `eval/GSM8k/invalid=1.0`; the corrected Qwen GSM8K rerun reached
`eval/GSM8k/acc=0.66566` and `eval/GSM8k/invalid=0.0235`, demonstrating that
prompt/extraction can dominate the external standard metrics.

Additional Gemma-specific caveat: the local snapshot advertises
`Gemma4ForConditionalGeneration`, but text-only vLLM serving had to force
`Gemma4ForCausalLM`; the tokenizer snapshot has no `chat_template`, so the plan
used the local fallback template
`evaluation/chat_templates/gemma4_e2b_plain_chat.jinja`. Do not cite the
current Gemma standard scores as official or fair until at least a small
diagnostic rerun saves generations and uses task-specific external-model
prompts/extractors.

Related external-eval code caveat: `OpenAIEngine.generate()` currently ignores
`max_context`, and `_generate_one()` returns an empty string for HTTP 400. This
can turn context-length/server request failures into normal-looking invalid
answers unless the vLLM logs are inspected. A quick search of the Gemma BoolQ
vLLM log showed ordinary `200 OK` responses, so BoolQ's all-invalid result is
more likely answer-format/template mismatch than context overflow; nevertheless
the silent-empty 400 behavior should be fixed before relying on external
baseline standard metrics.

Gemma clean external diagnostic preparation, 2026-06-17. Confidence: high for
local code inspection, `compileall`, and generated-plan inspection. The next
Gemma 4 E2B baseline should run through a separate diagnostic plan after the
current DFM5-L `step_500000` eval finishes:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler run \
  --plan-dir logs/scheduler/gemma4_e2b_clean_external_after_500k \
  --gpus 0,1,2,3,4,5,6,7
```

Monitor:

```bash
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/gemma4_e2b_clean_external_after_500k \
  --interval 30
```

The plan was created by:

```bash
PLAN_DIR=logs/scheduler/gemma4_e2b_clean_external_after_500k \
  bash scripts/create_gemma4_e2b_clean_external_eval_plan.sh
```

It has `207` pending jobs and deliberately uses `log_wandb=false`, so local
artifacts can be inspected before any clean W&B run is created. Important
prepared changes:

- `evaluation/config/external_chat_benchmarking.yaml` defines explicit
  chat-model prompts for the standard evals: MCQ tasks return only an option
  letter, GSM8K ends with `Final answer: <integer>`, and MATH boxes the final
  answer.
- `evaluation/main.py` supports `save_generations_dir=...`; external standard
  scheduler jobs now write per-shard `*.generations.jsonl` files containing
  prompt, generation, and sanitized ground truth.
- `evaluation/benchmarks.py` now accepts conservative MCQ final-answer forms
  (`A`, `A.`, `(A)`, `Answer: A`, `The answer is A`) instead of only exact raw
  letters. This should not change exact-letter HRM outputs, but makes chat-model
  external baselines less brittle.
- `evaluation/engines.py` no longer converts HTTP 400 responses into empty
  strings; bad OpenAI-compatible requests now fail visibly.
- `eval_scheduler plan create-external` accepts `--standard-config`, and the
  scheduler supports `--no-log-wandb` for diagnostic runs.
- `scripts/backfill_external_eval_to_wandb.py` can later log a clean W&B run
  from local merged artifacts once the diagnostic values and saved generations
  look credible.

The generated plan uses the local model
`/work/dfm/brainsurgery/models/google/gemma-4-E2B-it`, served as
`gemma4-e2b-it-clean`, with the same text-only Gemma vLLM overrides:
`--enforce-eager`, `--hf-overrides '{"architectures":["Gemma4ForCausalLM"]}'`,
and `--chat-template evaluation/chat_templates/gemma4_e2b_plain_chat.jinja`.
It also keeps the previous GovReport caps (`dfm_context_length=3968`,
`dfm_max_gen_toks=128`, `max_report_chars=10000`) and
`euroeval_generative_type=instruction_tuned`.

Scoring smoke follow-up, 2026-06-17. Confidence: high for local smoke tests on
cached benchmark rows. The clean external scoring changes were smoke-tested
without using GPUs:

- Conservative MCQ extraction accepts `A`, `A.`, `(B)`, `Answer: C`,
  `Final answer is D`, and `The answer is A`, while rejecting prose such as
  `I think A`.
- Data-backed MCQ smoke on the first 12 rows of `BoolQ`, `Winogrande`, and
  `ARC` with generations of the form `Answer: <gold>` produced `acc=1.0` and
  `invalid=0.0`.
- Data-backed GSM8K smoke on the first 12 cached rows with generations ending
  `Final answer: <gold>` produced `acc=1.0` and `invalid=0.0`.
- Data-backed MATH smoke on the first 12 rows of shard `0/64` with boxed gold
  answers produced `acc=1.0` and `invalid=0.0`.

The smoke exposed and fixed two launch/scoring issues before the Gemma clean
run:

- `evaluation/config/external_chat_benchmarking.yaml` had to escape literal
  braces in the MATH prompt as `\boxed{{}}`; otherwise Python `.format()` treats
  `\boxed{}` as an empty replacement field.
- MATH scoring normalized `\dfrac` and `\tfrac` to `\frac` before calling
  `math_verify.parse()`. Without this, an exact boxed answer such as
  `\boxed{\dfrac{3}{2}}` could be marked wrong because both the ground truth and
  answer parsed to empty lists.

`python -m compileall -q evaluation eval_scheduler
scripts/backfill_external_eval_to_wandb.py` passed after these changes.

Tiny live Gemma standard-smoke preparation, 2026-06-17. Confidence: high for
local config/script syntax and GPU-state inspection; the live smoke itself was
not launched because all GPUs were at 100% utilization and active 500K eval
jobs were already retrying after OOMs.

Prepared files:

```text
evaluation/config/external_chat_smoke.yaml
scripts/run_gemma4_e2b_standard_smoke.sh
```

The smoke uses the clean external-chat standard prompts on only:

```text
BoolQ  20 rows
GSM8K  20 rows
MATH   20 rows from shard 0/64
```

It starts a single local Gemma 4 E2B vLLM server with the same text-only
overrides as the clean full plan, runs `evaluation.main`, and writes
`evaluation.log`, `vllm.log`, and generation JSONL files under
`logs/eval/gemma4_e2b_clean_standard_smoke_<timestamp>/`. Launch once a GPU is
really free:

```bash
cd /work/dfm/HRM-Text
GPU=0 bash scripts/run_gemma4_e2b_standard_smoke.sh
```

Use `VLLM_GPU_MEMORY_UTILIZATION=...` only when deliberately testing on a
partially occupied GPU; default is `0.9`, which is appropriate when the GPU is
free.

Impact note for HRM checkpoint evals. Confidence: high for source inspection.
The clean external prompt config affects only runs that explicitly use
`evaluation/config/external_chat_benchmarking.yaml` or
`evaluation/config/external_chat_smoke.yaml`. `save_generations_dir` and
`max_samples` are inert unless set. The conservative MCQ extraction change can
affect future standard MCQ metrics if an evaluated model emits `Answer: A`,
`(A)`, etc.; existing HRM checkpoint standard evals usually generated exactly
one token for MCQ tasks, so they should be unchanged in practice. The MATH
`\dfrac`/`\tfrac` normalization can affect all future MATH evals slightly by
fixing exact boxed answers that previously parsed to empty lists. The HTTP-400
change affects only `OpenAIEngine` external baselines, not `SimpleEngine` HRM
checkpoint evals. Existing W&B/local metrics are not retroactively changed.

Gemma 4 E2B live standard smoke with batch size 1, 2026-06-17. Confidence:
high for local command output and saved generation inspection. The first
attempt used:

```bash
GPU=3 SMOKE_BATCH_SIZE=1 VLLM_GPU_MEMORY_UTILIZATION=0.25 \
  LOG_ROOT=logs/eval/gemma4_e2b_clean_standard_smoke_bs1_$(date +%Y%m%d_%H%M%S) \
  bash scripts/run_gemma4_e2b_standard_smoke.sh
```

It failed during vLLM startup because GPU3 had only `16.16/178.34 GiB` free,
less than the requested 25% vLLM memory budget. A second attempt succeeded:

```bash
GPU=5 SMOKE_BATCH_SIZE=1 VLLM_GPU_MEMORY_UTILIZATION=0.08 PORT=18645 \
  LOG_ROOT=logs/eval/gemma4_e2b_clean_standard_smoke_bs1_$(date +%Y%m%d_%H%M%S) \
  bash scripts/run_gemma4_e2b_standard_smoke.sh
```

Output directory:

```text
logs/eval/gemma4_e2b_clean_standard_smoke_bs1_20260617_175531
```

Scores:

```text
BoolQ   n=20  acc=0.5000  invalid=1.0000
GSM8K   n=20  acc=0.0000  invalid=0.8000
MATH    n=20  acc=0.0000  invalid=1.0000
```

Saved generations indicate a model serving/prompt-template problem rather than
a scorer-only problem. BoolQ produced 20/20 empty generations. GSM8K had 6/20
empty generations, 7/20 literal placeholder generations such as
`Final answer: <integer>`, and one `Final answer:` loop. MATH had 1/20 empty
generations and 10/20 `Assistant:` label loops. Do not run or backfill the full
Gemma 4 E2B clean external evaluation until the Gemma serving/template path is
fixed and a fresh smoke produces structurally valid outputs.

Gemma 4 native chat-template fix, 2026-06-17. Confidence: high for local
tokenizer rendering and batch-size-1 live smoke. The local E2B snapshot has no
`chat_template` in `tokenizer_config.json`; the previous fallback
`User:`/`Assistant:` template was wrong for Gemma 4. A native Gemma 4 template
from the installed E4B snapshot was copied into:

```text
evaluation/chat_templates/gemma4_native_chat.jinja
```

The template renders prompts as Gemma 4 turns, e.g.:

```text
<bos><|turn>user
...
<turn|>
<|turn>model
```

`scripts/run_gemma4_e2b_standard_smoke.sh`,
`scripts/create_gemma4_e2b_clean_external_eval_plan.sh`, and the two existing
Gemma scheduler plans were updated to reference this native template instead of
`gemma4_e2b_plain_chat.jinja`. The already-completed
`logs/scheduler/gemma4_e2b_then_dfm5_L_500k_20260617` artifacts were produced
before this fix and should be considered stale unless reset and rerun.

Live smoke command:

```bash
cd /work/dfm/HRM-Text
GPU=6 SMOKE_BATCH_SIZE=1 VLLM_GPU_MEMORY_UTILIZATION=0.08 PORT=18646 \
  LOG_ROOT=logs/eval/gemma4_e2b_native_standard_smoke_bs1_$(date +%Y%m%d_%H%M%S) \
  bash scripts/run_gemma4_e2b_standard_smoke.sh
```

Output directory:

```text
logs/eval/gemma4_e2b_native_standard_smoke_bs1_20260617_202216
```

Scores:

```text
BoolQ   n=20  acc=0.6500  invalid=0.0000
GSM8K   n=20  acc=0.7000  invalid=0.0000
MATH    n=20  acc=0.7000  invalid=0.9500
```

Saved generations are now structurally sane: BoolQ generations are single
letters, GSM8K generations are step-by-step answers, and MATH generations are
real derivations rather than empty strings or role-label loops. The remaining
high MATH invalid rate is a scorer/answer-extraction issue to inspect
separately, not the previous Gemma serving-template failure.

Scoring-diff minimization for Gemma external evals, 2026-06-17. Confidence:
high for local `git diff --exit-code -- evaluation/benchmarks.py`, compile
check, and smoke output. Temporary edits to shared benchmark scoring were
removed to avoid changing DFM5-L comparability. `evaluation/benchmarks.py` is
clean relative to HEAD again. Removed temporary changes were:

- lenient GSM8K extraction from final-answer prose or last number
- `\dfrac`/`\tfrac` normalization in MATH
- lenient MCQ parsing of `Answer: A`, `(A)`, etc.

The retained changes are non-scoring support for external diagnostics:
`OpenAIEngine`, `max_samples`, and optional generation JSONL saving. For Gemma
external standard evals, strict scorer compatibility is handled by prompt
templates in `evaluation/config/external_chat_smoke.yaml` and
`evaluation/config/external_chat_benchmarking.yaml`, not by changing the shared
scorers.

Strict-scoring Gemma smoke command:

```bash
cd /work/dfm/HRM-Text
GPU=1 SMOKE_BATCH_SIZE=1 VLLM_GPU_MEMORY_UTILIZATION=0.08 PORT=18647 \
  LOG_ROOT=logs/eval/gemma4_e2b_native_strict_prompt_smoke_bs1_$(date +%Y%m%d_%H%M%S) \
  bash scripts/run_gemma4_e2b_standard_smoke.sh
```

Output directory:

```text
logs/eval/gemma4_e2b_native_strict_prompt_smoke_bs1_20260617_205021
```

Scores under the original strict shared scorers:

```text
BoolQ   n=20  acc=0.6500  invalid=0.0000
GSM8K   n=20  acc=0.1000  invalid=0.0000
MATH    n=20  acc=0.7000  invalid=0.2000
```

The prompt-only fix made GSM8K structurally valid but low on the 20-row smoke
sample; MATH still often emits derivations despite instructions to return only
`\boxed{...}`, but strict invalid rate fell from 95% to 20%.

Step-by-step external scoring without shared scorer changes, 2026-06-17.
Confidence: high for local implementation, compile check, saved generation
inspection, and smoke output. To let instruction-tuned external baselines solve
GSM8K step by step without changing DFM5-L comparability, `evaluation.main`
now supports an opt-in per-benchmark field:

```yaml
score_extractor: final_integer
```

This is not a benchmark scorer change. `evaluation/benchmarks.py` remains clean
relative to HEAD. The extractor is applied only when a config requests it. Raw
generations are still saved; when `save_generations_dir` is enabled, JSONL rows
also include `scoring_generation` and `score_extractor` so the exact scored
text is auditable.

External Gemma GSM8K prompts were changed back to step-by-step reasoning with a
required final marker:

```text
Solve the problem step by step.
End your response with a separate line exactly like:
Final answer: <integer>
```

Fresh smoke command:

```bash
cd /work/dfm/HRM-Text
GPU=2 SMOKE_BATCH_SIZE=1 VLLM_GPU_MEMORY_UTILIZATION=0.08 PORT=18648 \
  LOG_ROOT=logs/eval/gemma4_e2b_native_stepwise_extract_smoke_bs1_$(date +%Y%m%d_%H%M%S) \
  bash scripts/run_gemma4_e2b_standard_smoke.sh
```

Output directory:

```text
logs/eval/gemma4_e2b_native_stepwise_extract_smoke_bs1_20260617_215137
```

Scores:

```text
BoolQ   n=20  acc=0.6500  invalid=0.0000
GSM8K   n=20  acc=0.6500  invalid=0.2500
MATH    n=20  acc=0.7000  invalid=0.2000
```

The remaining GSM8K invalids are not shared-scorer failures; they are rows
where Gemma omitted the requested final-answer marker, so the extractor
deliberately left the raw generation untouched and the strict original GSM8K
scorer marked it invalid.

Gemma 4 E2B native rerun plus DFM5-L 550K scheduler, 2026-06-17.
Confidence: high for local plan inspection, pane/process inspection, patched
runtime behavior, and completed first EuroEval shards.

Combined scheduler plan:

```text
logs/scheduler/gemma4_e2b_native_then_dfm5_L_550k_20260617_222323
```

This plan first runs the corrected Gemma 4 E2B instruct external eval with the
native Gemma 4 chat template, then waits for the fully written DFM5-L
`step_550000` checkpoint before launching the DFM5-L full eval. W&B targets:

```text
Gemma 4 E2B: project=DFM5 run_id=gemma4-e2b-it-native-full
DFM5-L:      project=DFM5 run_id=oti1lisg run_name=dfm5-L
```

The DFM5-L wait row is deliberately gated on Gemma completion:

```text
average-00208  tag=gemma4_e2b_it_native
wait-00209     tag=step_550000  deps=average-00208
```

Pane 9 in tmux session `hrm-0` was repointed to this plan:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/gemma4_e2b_native_then_dfm5_L_550k_20260617_222323 \
  --gpus 0,1,2,3,4,5,6,7

/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/gemma4_e2b_native_then_dfm5_L_550k_20260617_222323 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30
```

Two scheduler/runtime issues were fixed while launching this plan:

- External Gemma vLLM extra args must quote the JSON override for shlex:
  `--hf-overrides '{"architectures":["Gemma4ForCausalLM"]}'`.
- `eval_scheduler/eval_scheduler/runtime.py` now normalizes `euroeval_bin`
  only when it is a single script path. Multi-token commands such as
  `/home/ucloud/miniforge3/envs/hrm/bin/uv run --no-project --with euroeval
  /work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py` must not be
  treated as one relative `.py` path.

The first corrected launch reached real EuroEval execution. At the first
verified status snapshot, 8 Gemma EuroEval jobs were done, 8 were running, and
0 were failed.

DFM5-L 550K failed-row repair, 2026-06-18. Confidence: high for local plan
inspection, failed logs, process arguments, and scheduler status. The combined
plan later stopped blocked with 28 failed `step_550000` rows:

- 20 EuroEval rows failed because the appended DFM5-L block still used
  `scripts/euroeval_api_no_flash_attn_guard.py` directly, producing
  `ModuleNotFoundError: No module named 'euroeval'`.
- 8 `dfm/generative_talemaader` rows failed because the appended DFM5-L block
  lacked `judge_model` and `judge_base_url`; dfm-evals raised
  `Placeholder {{judge_model}} ... requires --judge-model`.

The repair reset only those failed rows to `pending` with `attempt=0`. EuroEval
rows now use:

```text
/home/ucloud/miniforge3/envs/hrm/bin/uv run --no-project --with euroeval /work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py
```

`generative_talemaader` rows now use:

```text
judge_model=openai/gemma-4-e4b-judge
judge_base_url=http://127.0.0.1:8099/v1
judged_max_connections=4
```

The judge server was already running on port 8099. After restarting pane 9,
the scheduler immediately picked up `eval-00210` through `eval-00217`; live
process arguments confirmed the repaired EuroEval jobs were running through
`uv run --no-project --with euroeval`.

Monitor progress fixes, 2026-06-18. Confidence: high for local monitor output
and log inspection. `eval_scheduler/eval_scheduler/monitor.py` now has two
additional progress fallbacks:

- DFM tasks can infer an active shard's denominator from completed sibling
  shard logs for the same task/checkpoint. This fixes
  `completion X/?` on `dfm/generative_talemaader`; the step-550000 shards show
  `101/101` once sibling shard headers are available.
- EuroEval progress groups repeated sample tqdm loops and reports them as
  `pass X/10 samples Y/Z`. This avoids misleading resets such as
  `cnn-dailymail` dropping from `118/165` to `1/157` when EuroEval starts the
  next pass.

At the time of the fix, `euroeval:valeu-da` for DFM5-L `step_550000` had
failed because EuroEval aborted on invalid labels in 3/53 samples. VaLEU is
excluded from the headline averages, so no synthetic value was created for
that failed task.

Qwen final-extract GSM8K repair, 2026-06-18. Confidence: high for local vLLM
logs, package reinstall output, and a one-GPU health smoke test. The appended
`qwen-finalextract-gsm-*` standard-eval rows initially failed with status 71
before extraction/scoring could run. The root cause was vLLM server startup
failure for Qwen3.5-2B on Blackwell:

```text
FlashInfer Blackwell GDN requires an intact nvidia-cutlass-dsl-libs-cu13 install ...
terminate called after throwing an instance of 'nanobind::builtin_exception'
what(): Expected an MLIR object ...
RuntimeError: Engine core initialization failed.
```

The package repair command was:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/uv pip install \
  --force-reinstall --no-deps nvidia-cutlass-dsl-libs-cu13
```

A one-GPU smoke server then reached `/health`, with vLLM using
`Using FlashInfer GDN prefill kernel`. The eight Qwen GSM rows were reset to
`pending`, the scheduler stop request was cleared, and pane 9 was restarted.
After restart, all eight Qwen GSM shards launched at batch 64 and began
processing samples.

DFM5-L `step_600000` full eval launch, 2026-06-18. Confidence: high for local
checkpoint inspection, scheduler status, and process inspection. The
`checkpoints/dfm5/L` `step_600000` checkpoint exists as
`fsdp2_step_600000/.metadata` plus `carry_step_600000.{0..7}.pt`. Its W&B
epoch x-value is `3.3130615418623695`, using the established DFM5-L mapping
`181101.374791` steps per epoch.

The full standard + DFM + EuroEval campaign was scheduled with the default
HRM simple-server path, not external/vLLM standard evals. Process inspection
confirmed launched jobs run `scripts/hrm_openai_server.py --ckpt-path
checkpoints/dfm5/L --ckpt-tag step_600000`.

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler plan create \
  --plan-dir logs/scheduler/dfm5_L_step600000_full_simple_20260618_600k_simple \
  --ckpt-path checkpoints/dfm5/L \
  --ckpt-tag step_600000 \
  --eval-epoch 3.3130615418623695 \
  --log-root logs/eval/dfm5_L_step600000_full_simple_20260618_600k_simple \
  --dfm-log-root logs/dfm_evals/dfm5_L_step600000_full_simple_20260618_600k_simple \
  --euroeval-log-root logs/euroeval/dfm5_L_step600000_full_simple_20260618_600k_simple \
  --wandb-project DFM5 \
  --wandb-run-id oti1lisg \
  --wandb-run-name dfm5-L \
  --model-prefix hrm-dfm5-L \
  --run-euroeval \
  --queue-order euroeval-first \
  --standard-batch 64 \
  --dfm-batch 32 \
  --ifeval-batch 32 \
  --euroeval-batch 16 \
  --max-retries 5 \
  --port-base 22000 \
  --judge-model openai/gemma-4-e4b-judge \
  --judge-base-url http://127.0.0.1:8099/v1 \
  --judged-max-connections 4 \
  --force
```

The plan contains 210 jobs: 1 checkpoint wait, 20 EuroEval jobs, 85 standard
eval shards, 51 DFM task shards, 32 DFM IFEval-DA shards, merge rows, an
average row, and a report row. Pane 9 in tmux session `hrm-0` now runs:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step600000_full_simple_20260618_600k_simple \
  --gpus 0,1,2,3,4,5,6,7

/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step600000_full_simple_20260618_600k_simple \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30
```

Initial status after launch: wait row completed, 8 EuroEval jobs running, 180
jobs ready, 21 blocked on dependencies, and no failures.

DFM5-L clean W&B backfill, 2026-06-19. Confidence: high for local audit files,
W&B sync logs, and W&B API summary readback. A new run was backfilled in
project `peter-sk-sdu/DFM5` with display name `dfm5-L clean`. It uses the
main DFM5-L run `oti1lisg` as source for training and non-650K history, but
uses the clean W&B run
`dfm5-l-vllm-clean-650k-700k-20260618` as the source for 650K eval metrics.

Correct synced run:

```text
https://wandb.ai/peter-sk-sdu/DFM5/runs/dfm5-l-clean-20260619-v2
```

Important pitfall: the main DFM5-L source history did not only contain 650K
eval-like values at W&B `_step=650000`. It also had a later row at internal
step `673992` with `avg/train_step=650000`, which overwrote the clean 650K
average after the first attempted backfill. The corrected sanitizer removes
eval-like keys from any source row whose own `eval/train_step`,
`dfm_eval/train_step`, `euroeval/train_step`, or `avg/train_step` equals the
replacement step, regardless of the W&B internal `_step`.

Verified sanitized audit:

```text
logs/backfill_dfm5_l_clean_rows_wandb_summary650_sanitized.jsonl
```

The sanitized audit contains no non-650000 row with `*/train_step=650000`; the
650K row has the replacement values from the clean vLLM W&B run, including:

```text
eval/MMLU/acc = 0.536375
eval/GSM8k/acc = 0.3760511751326763
avg/overall = 0.4565571277762064
dfm_eval/generative-talemaader/model_graded_fact/accuracy = 0
euroeval/da/sentiment-classification/angry-tweets/macro_f1 = 65.04088348514136
```

Online `wandb.init` timed out repeatedly for this large backfill, so the
working path was to create an offline run and then `wandb sync` it:

```bash
cd /work/dfm/HRM-Text
python scripts/backfill_dfm5_l_clean_wandb.py \
  --use-existing-audit \
  --wandb-mode offline \
  --dest-run-name 'dfm5-L clean' \
  --dest-run-id dfm5-l-clean-20260619-v2 \
  --audit-jsonl logs/backfill_dfm5_l_clean_rows_wandb_summary650_sanitized.jsonl

wandb sync --entity peter-sk-sdu --project DFM5 \
  wandb/offline-run-20260619_090701-dfm5-l-clean-20260619-v2
```

The sync log is:

```text
logs/backfill_dfm5_l_clean_v2_offline_sync_20260619.log
```

DFM5-L clean append, 2026-06-19. Confidence: high for local audit files,
offline W&B sync output, and W&B API summary readback. After the clean run was
created, the live source run `oti1lisg` advanced beyond the clean run. The
append-only backfill script:

```text
scripts/append_dfm5_l_clean_from_source_wandb.py
```

was used to append source rows with W&B `_step > 735320` into the existing
clean run `dfm5-l-clean-20260619-v2`. This added missing training rows and the
750K eval/average rows from the main DFM5-L source run.

Audit and logs:

```text
logs/append_dfm5_l_clean_from_oti1lisg_after735320_20260619.jsonl
logs/append_dfm5_l_clean_from_oti1lisg_after735320_offline_create_20260619.log
logs/append_dfm5_l_clean_from_oti1lisg_after735320_sync_20260619.log
```

The dry-run found `4083` rows to append, including `38` eval-like rows, covering
internal W&B steps `735325..755545`. The append was done offline and synced:

```bash
cd /work/dfm/HRM-Text
python scripts/append_dfm5_l_clean_from_source_wandb.py \
  --use-existing-audit \
  --audit-jsonl logs/append_dfm5_l_clean_from_oti1lisg_after735320_20260619.jsonl \
  --wandb-mode offline

wandb sync --entity peter-sk-sdu --project DFM5 \
  wandb/offline-run-20260619_115118-dfm5-l-clean-20260619-v2
```

W&B API readback after sync showed the clean run at `_step=755545` with:

```text
avg/train_step = 750000
avg/overall = 0.5236963639147983
avg/danish = 0.5194176019991262
avg/english = 0.6620535778037574
avg/math_code = 0.3896179119415115
eval/MMLU/acc = 0.5478999999999999
eval/GSM8k/acc = 0.36922160727824105
dfm_eval/generative-talemaader/model_graded_fact/accuracy = 0.0012376237623762376
euroeval/da/sentiment-classification/angry-tweets/macro_f1 = 66.17822158112952
```

DFM5-L clean append to 800K, 2026-06-19. Confidence: high for local audit
files, offline W&B sync output, and W&B API summary readback. The same
append-only script was used again after the clean run had reached
`_step=755545`:

```bash
cd /work/dfm/HRM-Text
python scripts/append_dfm5_l_clean_from_source_wandb.py \
  --dry-run \
  --audit-jsonl logs/append_dfm5_l_clean_from_oti1lisg_after755545_20260619.jsonl

python scripts/append_dfm5_l_clean_from_source_wandb.py \
  --use-existing-audit \
  --audit-jsonl logs/append_dfm5_l_clean_from_oti1lisg_after755545_20260619.jsonl \
  --wandb-mode offline

wandb sync --entity peter-sk-sdu --project DFM5 \
  wandb/offline-run-20260619_192323-dfm5-l-clean-20260619-v2
```

Audit and logs:

```text
logs/append_dfm5_l_clean_from_oti1lisg_after755545_20260619.jsonl
logs/append_dfm5_l_clean_from_oti1lisg_after755545_dryrun_20260619.log
logs/append_dfm5_l_clean_from_oti1lisg_after755545_offline_create_20260619.log
logs/append_dfm5_l_clean_from_oti1lisg_after755545_sync_20260619.log
```

The dry-run found `11232` rows to append, including `36` eval-like rows,
covering internal W&B steps `755550..811530`. W&B API readback after sync
showed the clean run at `_step=811530` with:

```text
avg/train_step = 800000
avg/overall = 0.4941255723568704
avg/danish = 0.5140386857991142
avg/english = 0.6653983714808205
avg/math_code = 0.3029396597906766
avg/epoch = 4.417415389149824
eval/MMLU/acc = 0.54305
eval/GSM8k/acc = 0.3767944655041698
eval/BoolQ/acc = 0.8471
dfm_eval/generative-talemaader/model_graded_fact/accuracy = 0
dfm_eval/nordjyllandnews/chrf3pp/mean = 36.063069175646135
euroeval/da/sentiment-classification/angry-tweets/macro_f1 = 72.50525327604699
```

Superseded, 2026-06-19: the `dfm5-l-clean-20260619-v2` clean run was deleted.
It still allowed stale source eval rows at the 650K epoch to survive for some
standard eval metrics such as ARC, because the sanitizer only stripped rows by
`*/train_step=650000` or W&B `_step=650000`. Some source eval rows only carried
`*/epoch=3.5891500036842338`, so they could overwrite the clean rerun values.

DFM5-L clean v3 backfill, 2026-06-19. Confidence: high for local audit diff,
offline W&B sync output, W&B summary readback, and remote ARC row readback. The
corrected script:

```text
scripts/backfill_dfm5_l_clean_wandb.py
```

now defaults to `--replacement-source history`, which streams all non-null
eval-like rows from the rerun W&B history rather than copying only the rerun
summary. It also strips source eval-like rows when they target either
`650000` via `*/train_step` or the replacement epoch
`3.5891500036842338` via `*/epoch`. The script no longer writes replacement
metric values directly to `run.summary` after logging the full history; this
keeps the final summary at the latest logged checkpoint.

The corrected clean run is:

```text
https://wandb.ai/peter-sk-sdu/DFM5/runs/dfm5-l-clean-20260619-v3
```

Commands used:

```bash
cd /work/dfm/HRM-Text
python scripts/backfill_dfm5_l_clean_wandb.py \
  --dry-run \
  --wandb-mode offline \
  --dest-run-id dfm5-l-clean-20260619-v3 \
  --dest-run-name 'dfm5-L clean' \
  --audit-jsonl logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl

python scripts/backfill_dfm5_l_clean_wandb.py \
  --sanitize-existing-audit \
  --dry-run \
  --wandb-mode offline \
  --dest-run-id dfm5-l-clean-20260619-v3 \
  --dest-run-name 'dfm5-L clean' \
  --audit-jsonl logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl

python scripts/backfill_dfm5_l_clean_wandb.py \
  --use-existing-audit \
  --wandb-mode offline \
  --dest-run-id dfm5-l-clean-20260619-v3 \
  --dest-run-name 'dfm5-L clean' \
  --audit-jsonl logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl

wandb sync --entity peter-sk-sdu --project DFM5 \
  wandb/offline-run-20260619_203345-dfm5-l-clean-20260619-v3
```

Audit and logs:

```text
logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl
logs/backfill_dfm5_l_clean_v3_history650_dryrun_20260619.log
logs/backfill_dfm5_l_clean_v3_history650_sanitize_20260619.log
logs/backfill_dfm5_l_clean_v3_history650_offline_create_20260619.log
logs/backfill_dfm5_l_clean_v3_history650_sync_20260619.log
```

The strict local audit diff against the rerun W&B run
`dfm5-l-vllm-clean-650k-700k-20260618` showed `447` expected replacement keys,
`447` actual 650K audit keys, and zero missing, extra, or differing values.
Spot-checked replacement values:

```text
eval/ARC/acc = 0.6954
eval/ARC/n = 1172
eval/ARC/invalid = 0
eval/MMLU/acc = 0.536375
eval/GSM8k/acc = 0.3760511751326763
eval/BoolQ/acc = 0.8416
avg/overall = 0.45655712777620644
avg/train_step = 650000
avg/epoch = 3.589150003684234
```

W&B summary readback after sync showed the v3 clean run at `_step=820565`, with
latest summary values from 800K:

```text
avg/train_step = 800000
avg/epoch = 4.417415389149824
avg/overall = 0.4941255723568704
avg/danish = 0.5140386857991142
avg/english = 0.6653983714808205
avg/math_code = 0.3029396597906766
eval/MMLU/acc = 0.54305
eval/GSM8k/acc = 0.3767944655041698
eval/ARC/acc = 0.7099
eval/BoolQ/acc = 0.8471
```

A remote sparse-history spot check found the 650K ARC row at W&B `_step=650023`
with `eval/ARC/acc=0.6954`, `eval/train_step=650000`, and
`eval/epoch=3.589150003684234`.

DFM5-L clean v3 append to 900K, 2026-06-20. Confidence: high for local append
audit, offline W&B sync output, W&B API summary readback, and regenerated
`docs/dfm5.md`. After the v3 clean run had reached `_step=820565`, the
append-only script was used to add missing training rows plus the 850K and 900K
eval/average rows from the source DFM5-L run `oti1lisg`:

```bash
cd /work/dfm/HRM-Text
python scripts/append_dfm5_l_clean_from_source_wandb.py \
  --dry-run \
  --dest-run-id dfm5-l-clean-20260619-v3 \
  --audit-jsonl logs/append_dfm5_l_clean_from_oti1lisg_after820565_20260620.jsonl

python scripts/append_dfm5_l_clean_from_source_wandb.py \
  --use-existing-audit \
  --dest-run-id dfm5-l-clean-20260619-v3 \
  --audit-jsonl logs/append_dfm5_l_clean_from_oti1lisg_after820565_20260620.jsonl \
  --wandb-mode offline

wandb sync --entity peter-sk-sdu --project DFM5 \
  wandb/offline-run-20260620_092234-dfm5-l-clean-20260619-v3
```

Audit and logs:

```text
logs/append_dfm5_l_clean_from_oti1lisg_after820565_20260620.jsonl
logs/append_dfm5_l_clean_from_oti1lisg_after820565_dryrun_20260620.log
logs/append_dfm5_l_clean_from_oti1lisg_after820565_offline_create_20260620.log
logs/append_dfm5_l_clean_from_oti1lisg_after820565_sync_20260620.log
```

The dry-run found `17243` rows to append, including `73` eval-like rows,
covering W&B steps `820570..906456`. It included 850K at
`avg/epoch=4.693503850971687` and 900K at `avg/epoch=4.96959231279355`.
W&B API readback after sync showed the v3 clean run at `_step=906456` with:

```text
avg/train_step = 900000
avg/epoch = 4.96959231279355
avg/overall = 0.49627485017703776
avg/danish = 0.5110413263920152
avg/english = 0.6661624442926698
avg/math_code = 0.3116207798464284
eval/ARC/acc = 0.7159
eval/MMLU/acc = 0.55125
eval/GSM8k/acc = 0.3874275208491281
eval/BoolQ/acc = 0.8599
dfm_eval/nordjyllandnews/chrf3pp/mean = 35.676897848564714
euroeval/da/sentiment-classification/angry-tweets/macro_f1 = 70.41063419555583
```

The DFM5 comparison report generator:

```text
scripts/generate_dfm5_l_eval_comparison_report.py
```

was updated to include local artifacts for `DFM5-L 800K`, `DFM5-L 850K`, and
`DFM5-L 900K`. Running it regenerated:

```text
docs/dfm5.md
```

DFM5-L clean v3 850K/900K visible-history repair, 2026-06-20. Confidence:
high for W&B API summary readback and sparse-history row readback. The first
append to 900K updated the run summary but the newly appended rows were not
visible through W&B's normal history scan/workspace panels. In addition, the
source eval rows had `*/epoch` but many rows lacked the matching
`*/train_step` field required by the metric definitions.

The repair script:

```text
scripts/relog_dfm5_l_clean_eval_rows.py
```

reads the append audit, selects the 850K/900K eval rows, injects explicit
`eval/train_step`, `dfm_eval/train_step`, `euroeval/train_step`, or
`avg/train_step` for each row's prefix, and logs the repaired rows at fresh
W&B internal steps. The offline repair sync again updated summary but did not
make rows visible through `scan_history`, so the successful repair was the
online run:

```bash
cd /work/dfm/HRM-Text
python scripts/relog_dfm5_l_clean_eval_rows.py \
  --audit-jsonl logs/append_dfm5_l_clean_from_oti1lisg_after820565_20260620.jsonl \
  --output-jsonl logs/relog_dfm5_l_clean_850k_900k_explicit_train_step_online_20260620.jsonl \
  --target 850000:4.693503850971687 \
  --target 900000:4.96959231279355 \
  --base-step 920000 \
  --wandb-mode online
```

Logs and repaired audit:

```text
logs/relog_dfm5_l_clean_850k_900k_explicit_train_step_online_20260620.jsonl
logs/relog_dfm5_l_clean_850k_900k_explicit_train_step_online_20260620.log
```

Remote W&B sparse-history readback showed the repaired average rows:

```text
_step=920036 avg/train_step=850000 avg/epoch=4.693503850971687 avg/overall=0.49205879573912314
_step=920072 avg/train_step=900000 avg/epoch=4.96959231279355 avg/overall=0.49627485017703776
```

It also showed repaired standard eval rows, for example:

```text
_step=920023 eval/train_step=850000 eval/epoch=4.693503850971687 eval/ARC/acc=0.721
_step=920024 eval/train_step=850000 eval/epoch=4.693503850971687 eval/MMLU/acc=0.5447500000000001
```
