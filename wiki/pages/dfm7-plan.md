# DFM7 Plan

Last updated: 2026-07-02
Confidence: medium
Scope: Forward-looking DFM7 planning notes that should not be mixed into the active DFM6 intervention plan.

## DFM6-to-DFM7 XL Eval Scheduler Extension

Update, 2026-07-02. Confidence: high from local scheduler plan inspection and
locked `eval_scheduler plan create --append` commands.

The active DFM6-to-DFM7 XL eval plan was extended in place:

```text
plan_dir: logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253
checkpoint path: checkpoints/dfm7/XL-gas2-from-dfm6-epoch3
W&B target: DFM5 / dfm6-dfm7-xl-gas2
```

Added checkpoint eval blocks:

```text
step_1050000 epoch 4.297464085872718 port_base 45000
step_1100000 epoch 4.494099606107069 port_base 46000
step_1150000 epoch 4.690735126341419 port_base 47000
step_1200000 epoch 4.88737064657577  port_base 48000
step_1250000 epoch 5.08400616681012  port_base 49000
```

Each appended block has 217 rows, skips only `valeu-da`, waits for a fully
written checkpoint, exports an EMA HF/vLLM checkpoint to
`exports/dfm6_dfm7_XL_gas2_step_<step>_ema_hf_hrmenv_202253`, and uses the
same DFM7 eval settings as the earlier blocks: Gemma4 chat template, FA4,
vLLM GPU memory utilization `0.25`, EuroEval-first order, standard batch `64`,
DFM batch `32`, DFM IFEval batch/shards `32`, EuroEval batch `32`, and managed
`unsloth/gemma-4-E4B-it` judge rows for judged DFM tasks.

Follow-up, 2026-07-03. Confidence: high from local vLLM/proxy logs, patched
proxy code, rerun status, and generated result artifact. The `step_900000`
EuroEval BFCL-v2 row initially failed all six attempts with vLLM/Gemma4 native
tool parser error:

```text
OverflowError: cannot convert float infinity to integer
```

The model had emitted an invalid native tool-call argument (`Infinity`) for an
integer-like schema field. That should count as an incorrect BFCL item, not as
an infrastructure failure that aborts the whole benchmark. The proxy
`scripts/native_compatible_openai_proxy.py` now catches this narrow BFCL native
tool parser/coercion 400 and returns a valid OpenAI response containing an
empty/invalid BFCL tool-call answer. EuroEval then scores the item as wrong and
continues.

After resetting only `eval-00238` to `pending`, the rerun completed:

```text
eval-00238 step_900000 euroeval:bfcl-v2 status_0
BFCL-v2 Tool Calling Accuracy: 2.32% +/- 0.51%
```

The blocked `step_900000` EuroEval average, math/code average, headline average,
and report rows then completed with status `0`.

## Headline Average Normalization Issue

Update, 2026-07-01. Confidence: high from local code changes, dry-run audit,
and completed W&B relog job.

- `scripts/log_dfm5_headline_averages.py` now uses metric-specific
  normalization for headline averages: all `euroeval/*` source metrics are
  divided by 100, while standard `eval/*` and the included `dfm_eval/*`
  headline metrics remain ratio-scale.
- GovReport is handled correctly in the headline average because the included
  key is `dfm_eval/govreport/bertscore_f1/mean`, which is ratio-scale. The
  local GovReport CHRF metrics are mixed/percent-like but are not members of
  the headline average key list.
- Future scheduler-generated average rows now write `headline_avg_v3/*` and
  `suite_avg_v3/*`. Existing v2 keys are intentionally left untouched.
- The active DFM6-to-DFM7 eval plan was edited under `PlanLock`: a
  project-wide `relog_project_averages` CPU row was prepended, and 28 pending
  average rows were changed from v2 prefixes to v3 prefixes.
- `scripts/relog_project_averages_v3.py` relogged corrected v3 averages from
  local W&B history for DFM5 project runs. Audit file:
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253/relog_project_averages_v3_audit.jsonl`
  with 80 rows.
- The DFM5 workspace builder defaults now point average panels at
  `headline_avg_v3` and `suite_avg_v3`. A v3 SDK-created workspace was saved at
  `https://wandb.ai/peter-sk-sdu/DFM5?nw=k06l5ll2wq5`. The manual workspace
  id `nw=760qd0evtsa` could not be safely resolved through the available
  W&B workspace API surface during this session.
- Follow-up correction, 2026-07-01. Confidence: high from local audit rows and
  successful W&B sync. The first project-wide v3 relog only found two
  `dfm5-l-clean-20260619-v3` average points because that clean run's complete
  history lived mainly in audit JSONL files, not local `.wandb` files for the
  clean run id. The missing v3 average rows were recomputed from
  `logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl`,
  `logs/append_dfm5_l_clean_from_oti1lisg_after820565_20260620.jsonl`, and
  `logs/relog_dfm5_l_clean_850k_900k_explicit_train_step_20260620.jsonl`, then
  logged to `dfm5-l-clean-20260619-v3` for 18 epochs from 0.276 through 4.970.
  The corrected workspace preserving the previous panel order, including Suite
  Averages, and placing per-section averages first is:
  `https://wandb.ai/peter-sk-sdu/DFM5?nw=3fvncok3gjh`.

DFM6-DFM7 math/code average anomaly, 2026-07-01. Confidence: high from local
inspection of `scripts/log_dfm5_headline_averages.py`,
`eval_scheduler/eval_scheduler/plan.py`, and local EuroEval BFCL merged metric
files.

Observed issue:

- The Math & Code headline average uses four metrics:
  `eval/GSM8k/acc`, `eval/MATH/acc`,
  `dfm_eval/humaneval/verify_sanitized/accuracy`, and
  `euroeval/en/tool-calling/bfcl-v2/tool_calling_accuracy`.
- The average normalizer in `scripts/log_dfm5_headline_averages.py` is generic:
  values in `[0, 1]` are used directly, values in `(1, 100]` are divided by
  100, and larger values are ignored.
- Local DFM6-DFM7 BFCL merged metrics show a scale break between checkpoints:
  step 750000 has `tool_calling_accuracy=0.48`, while step 800000 has
  `tool_calling_accuracy=2.44`. The current normalizer therefore treats these
  as `0.48` and `0.0244`, respectively.
- This can make the Math & Code average go down even when all visible raw
  component panels go up. It is an averaging/normalization artifact, not by
  itself evidence that the model got worse.

Recommended fix:

- Make average normalization metric-specific rather than relying on the generic
  `>1 means percent` heuristic.
- For BFCL/tool-calling, first determine the intended EuroEval scale and then
  either normalize at ingestion/merge time to a stable `[0, 1]` metric or use a
  corrected metric-specific average key. Do not silently mix `0.48` as a ratio
  with `2.44` as a percent in the same headline average.
- Until fixed and backfilled, interpret `avg/math_code` and
  `headline_avg_v2/math_code` cautiously for checkpoints whose BFCL metric
  crosses above 1.

## Canonical DFM7 Tool-Use Rebuild

DFM7 tool-use rebuild, 2026-07-01. Confidence: high from local conversion,
audit, tokenization, and sampling commands.

Supersedes earlier references on this page to `data/sampled_dfm7_next`. The
canonical DFM7 training dataset is now `data/sampled_dfm7`, and
`config/data/dfm7.yaml` points there. The stale `data/sampled_dfm7_next` sample
was removed after the rebuilt canonical sample was verified.

What changed:

- The malformed original DOLCI tool-use rows are still present as tokenized
  inputs but are capped to zero in `data_io/prefix_config_dfm7.yaml` via
  `dolci_instruct_sft_tool_use__` and `dolci_instruct_sft_tool_use_sa__`.
- Corrected DOLCI native tool-use rows are generated as
  `dolci_native_tool_use`. The converter moves embedded function definitions to
  top-level `tools`, removes the old XML `<functions>/<function_calls>` response
  contract, normalizes tool schemas and names, and converts assistant targets to
  structured `tool_calls`.
- Three additional BFCL-shaped/native tool-call sources were integrated:
  `glaive_native_tool_use`, `toolace_native_tool_use`, and
  `xlam_native_tool_use`.
- `dfm_dyna_instruct_when2call` was not converted to native tool-call SFT. It
  remains auxiliary decision/no-call data because it does not contain assistant
  tool-call targets.
- Nemotron Agentic tool-use/search/interactive-agent sources were kept
  unconverted because they already contain top-level tools and structured
  assistant `tool_calls`.

Pre-tokenization audit:

- `scripts/audit_dfm7_tool_sources.py --fail-on-issues --json-out
  logs/dfm7_tool_audit_20260701.json` passed with zero converted-source issues.
- Audited converted source counts:
  - `dolci_native_tool_use`: 228,865 rows, 1,158,664 rendered examples,
    612,343 tool-call examples.
  - `glaive_native_tool_use`: 78,362 rows, 234,279 rendered examples,
    76,248 tool-call examples.
  - `toolace_native_tool_use`: 10,618 rows, 13,132 rendered examples,
    9,713 tool-call examples.
  - `xlam_native_tool_use`: 60,000 rows, 60,000 rendered examples,
    60,000 tool-call examples.
- The audit also checked unconverted tool-adjacent sources. Nemotron Agentic
  retained structured assistant tool calls; `when2call` and `agentic_code` were
  correctly identified as not native tool-call-response supervision.

Tokenization and sampling:

- DFM7 uses the Gemma4 tokenizer and chat template throughout:
  `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json` and
  `data_io/chat_templates/gemma4_native_chat.jinja`.
- Re-tokenization with `scripts/tokenize_chat_template.py` used 16 workers and
  produced 130 DFM7-added tokenized files with 7,460,205 rows and 99,552 skipped
  rows in 884.1 seconds.
- The rebuilt canonical sample metadata:
  `total_length=66657336296`, `max_seq_len=4097`,
  `template_mode=jinja_chat_template`, `enable_thinking=false`.
- `data/show_analytics_dfm7.md` reports 66.657B tokens in the sampled 5-epoch
  training array and 83.964B unique sampled tokens across source repetitions.
- Sampled tool-use additions:
  - `dolci_native_tool_use`: 8.103B sampled tokens over 5 epochs
    (7.403B target tokens).
  - `glaive_native_tool_use`: 777.6M sampled tokens over 5 epochs
    (676.3M target tokens).
  - `toolace_native_tool_use`: 126.1M sampled tokens over 5 epochs
    (110.8M target tokens).
  - `xlam_native_tool_use`: 334.8M sampled tokens over 5 epochs
    (295.9M target tokens).

Operational notes:

- Run DFM7 commands from the `hrm` conda environment. Launching the eval
  scheduler from outside that environment previously caused path/dependency
  issues.
- `scripts/backfill_dfm6_dfm7_xl_splice_wandb.py` now writes the target data
  path as `data/sampled_dfm7` in config and W&B summary metadata.

## Math Answer Contracts

DFM7 math data/eval contract investigation, 2026-06-30.
Confidence: high from local inspection of `evaluation/benchmarks.py`,
`evaluation/config/dfm6_vllm_benchmarking.yaml`,
`scripts/tokenize_chat_template.py`, DFM6 tokenized arrays, and source Parquet
schemas. Math has related but less severe format issues than BFCL tool calling.

Verified facts:

- Standard eval uses three different math-ish contracts:
  - `GSM8k`: raw question, `condition=direct`, `max_tokens=512`; scorer accepts
    a bare final integer or a boxed final integer.
  - `MATH`: raw problem, default `condition=synth,cot`, `max_tokens=3072`;
    scorer requires a parseable last `\boxed{...}` via `last_boxed_only_string`.
  - MMLU math subjects: few-shot multiple choice, `condition=direct`,
    `max_tokens=1`; scorer expects exactly one option letter.
- DFM6 vLLM standard eval wraps these prompts with the Gemma chat template and
  `enable_thinking=False`. The older HRM/Sapient eval path used HRM condition
  marker tokens rather than Gemma chat rendering.
- DFM6 contains many math sources with inconsistent answer styles:
  `openmathinstruct2__cot` teaches long `<think>...</think>` plus final natural
  language/boxed answers; `openmathinstruct2__direct` teaches direct expected
  answers for non-original sources; `math_train.jsonl` has both full solutions
  and direct boxed answers; `gsm8k_train.jsonl` direct rows teach bare numeric
  answers; FLAN GSM8K/MathQA, DMMath, AMPS Mathematica, Tulu math, and other
  reasoning sources use still other answer conventions.
- Prior DFM6 step-500000 probes showed MATH invalids often come from long
  reasoning that fails to terminate with a boxed answer under the token cap, and
  MMLU math invalids often start with `<think>` or `\boxed{...}` instead of the
  required single letter.
- Two intended DFM6 AllenAI RLVR math sources currently contribute zero
  tokenized rows:
  `data/tokenized_dfm6/allenai_rlvr_gsm__data__train-00000-of-00001.parquet`
  and
  `data/tokenized_dfm6/allenai_rlvr_math__data__train-00000-of-00001.parquet`
  have `tokens.npy` shape `(0,)` and empty index arrays. Their source Parquet
  files contain one-message `messages=[{"role": "user", ...}]` rows with a
  separate `ground_truth` column, not assistant messages. The chat-template
  tokenizer only emits supervised examples when it sees an assistant message
  with content or tool calls, and it also rejects examples with no prompt
  history.

Interpretation:

- This is not as binary as the BFCL parser mismatch. The MATH scorer can handle
  many normal CoT solutions if the model eventually emits `\boxed{...}`, and
  GSM8K can handle bare numeric answers. But DFM6 teaches several competing
  math response styles while the evals demand task-specific output contracts.
- The zero-row RLVR GSM/MATH bug is more concrete than a format preference. It
  means two sources intended to strengthen GSM8K/MATH did not enter the sampled
  dataset at all, despite being present in `data_io/prefix_config_dfm6.yaml`.

Recommended data fix:

1. Convert one-message RLVR rows into supervised two-message chat examples by
   splitting the few-shot `Question:/Answer:` prompt so the final target
   question is the user message and `ground_truth` or the final answer trace is
   the assistant message.
2. For GSM-like data, include a strong direct-answer slice whose target ends in
   a parseable final integer, preferably with a consistent phrase such as
   `The answer is N.` or a boxed final answer if we choose to standardize on
   boxed output.
3. For MATH-like data, ensure the supervised CoT target ends with exactly one
   final `\boxed{...}` answer and avoid examples that leave the answer only in
   prose.
4. Keep MCQ math separate from freeform math. For one-letter MCQ evals, either
   train explicit one-letter direct-answer examples or evaluate with an
   extraction/prompt variant deliberately labeled as non-card-comparable.

Preferred math-format policy, 2026-06-30. Confidence: medium until validated
with a rebuilt sample and eval smoke test. To reduce ambiguity between GSM8K
and MATH during evaluation, make the supervised freeform math contract converge
on one universal format: reasoning if useful, then exactly one final
`\boxed{...}` answer. This should work for MATH directly and remains compatible
with the current GSM8K scorer, which first checks for `\boxed{...}` and then
parses the boxed content as an integer. Direct numeric GSM8K-only rows can still
be kept as a smaller auxiliary slice, but the dominant freeform math style
should be boxed-final-answer rather than split between bare integers, prose
answers, and boxed answers.

## Open-Model Precedent

Open-model precedent for math answer contracts, 2026-06-30. Confidence: medium
from inspected public OLMES configs and OLMo 3 public materials. Recent open
training/eval stacks do not rely on an implicit benchmark name hidden from the
model. They make the expected output contract visible through task-specific
few-shot examples, task-specific prompt templates, answer extractors, and/or
format rewards/verifiers.

Observed examples:

- OLMES has separate task configs for GSM8K, Minerva/MATH-style math, MMLU CoT,
  styled math, and reasoning suites. OLMo 3 GSM8K configs use `STD:GSM8k`
  few-shot examples, explicit stop sequences, repeated stochastic samples, and
  `answer_format_correct_cutoff` metadata for format compliance. The OLMo 3
  base-chat suite tracks `gsm8k::olmo3:midtrain`,
  `minerva_math::olmo3:midtrain`, `styled_math500::olmo3:midtrain`, and
  `mmlu:cot::olmo3:midtrain` separately.
- OLMES/Tulu thinker configs explicitly distinguish GSM8K CoT LaTeX variants
  such as `gsm8k::zs_cot_latex`, rather than assuming the model will infer the
  desired final-answer syntax from the dataset name.
- The OLMo 3 report describes math/code improvements from generated/verifiable
  data: programmatically generated problems, thinking traces distilled from
  stronger models, and correctness filtering with output verifiers. This is
  consistent with making the final-answer contract machine-checkable.

DFM7 implication: if we want comparable HRM standard scores, keep the official
eval path fixed and adapt training data toward that path. If we want a stronger
native DFM math eval, add explicit prompt templates and report it as a separate
variant. In either case, the data should not mix bare integers, prose-only
answers, `<think>` continuations, and boxed answers without an explicit
instruction telling the model which format is desired.

## Direct Vs CoT

Direct-vs-CoT prompt contract for DFM7 math, 2026-06-30.
Confidence: medium until implemented and smoke-tested. DFM7 should keep
`direct` and `cot` as useful data/eval modes, but they must be visible in the
Gemma-rendered prompt. Treat them as prompt contracts, not hidden metadata.

Policy:

- `direct` math means: answer without reasoning and return only the final answer
  in a strict machine-checkable format. For freeform math, prefer
  `\boxed{...}` even for GSM-style problems because GSM8K scoring accepts boxed
  integers and MATH requires boxed answers.
- `cot` math means: reasoning is allowed or requested, but the completion must
  still end with exactly one final `\boxed{...}` answer.
- `direct` must not mean "short but arbitrary"; `cot` must not mean "long
  unconstrained prose." Both modes need an explicit final-answer contract.
- One-letter MCQ math remains a separate direct-answer contract: return exactly
  one of the option letters. It should not share freeform boxed math prompts.

Implementation suggestion:

- In `scripts/tokenize_chat_template.py::hrm_row_to_messages()` or in a
  DFM-specific pre-conversion layer, turn math `condition` values into short
  system/user instructions before rendering with the Gemma chat template.
- For `direct` freeform math rows, prepend an instruction equivalent to:
  `Return only the final answer in \boxed{...}.`
- For `cot`/`synth,cot` freeform math rows, prepend an instruction equivalent
  to: `Solve step by step. End with exactly one final answer in \boxed{...}.`
- For MCQ rows, use a different instruction equivalent to:
  `Return exactly one option letter.`

Evaluation policy:

- Keep the current HRM/card-comparable standard eval path unchanged unless we
  intentionally create a new metric namespace.
- Add any explicit DFM-native math prompt variants under a separate eval prefix
  or task name, so improvements from clearer prompting are not confused with
  card-comparable HRM standard scores.

## DFM6 Epoch-3 To DFM7 Continuation

DFM6 XL-GAS2 to DFM7 splice plan, 2026-06-30. Confidence: high for checkpoint
metadata, resume semantics, and the prepared W&B backfill from local/API
inspection.

Verified checkpoint state:

- `checkpoints/dfm6/XL-gas2/checkpoint_state_epoch_3.json` records
  `step=720084`, `epoch=3`, `batch_in_epoch=0`, `batch_in_epoch_exact=true`,
  `global_batch_size=262144`, `gradient_accumulation_steps=2`, and
  `data_path=data/sampled_dfm6`.
- `checkpoints/dfm6/XL-gas2/train_metadata.yaml` uses the Gemma4 tokenizer
  and chat template: `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`
  and `data_io/chat_templates/gemma4_native_chat.jinja`.
- Superseded 2026-07-01: `data/sampled_dfm7_next/metadata.json` was an earlier
  DFM7 sample. The corrected canonical sample is now
  `data/sampled_dfm7/metadata.json` with `total_length=66657336296`.

Resume behavior:

- In `pretrain.py`, resuming from `resume_checkpoint_tag=epoch_3` sets
  `start_epoch=4`, `skip_batches=0`, and preserves the checkpoint step from the
  sidecar. The dataset epoch is then set to `start_epoch - 1`, so using
  `data=dfm7` will start at DFM7's fourth epoch stream while keeping the global
  training step at `720084`.
- Keeping `epochs=5` means the continuation will run epochs 4 and 5 only. To
  train five full DFM7 epochs after the three DFM6 epochs, use a different
  explicit plan; do not overload this splice command.

Recommended W&B policy:

- A new clean W&B run was prepared:
  `peter-sk-sdu/DFM5/dfm6-dfm7-xl-gas2`
  (`DFM6-DFM7-XL-gas2`). It should be used for the DFM6-to-DFM7 splice instead
  of mutating the original `dfm6-XL-gas2` run. The original training source was
  `peter-sk-sdu/DFM5/39ht9plp`.
- Backfill policy, verified 2026-06-30: use DFM6 training rows from
  `peter-sk-sdu/DFM5/39ht9plp`, but do not use eval rows from that run. Use
  eval rows up to and including step 700000 from
  `peter-sk-sdu/DFM5/dfm6-xl-gas2-300k-stopfix-clean-20260624`.
- The prepared backfill used 144,028 W&B history rows, reached last training
  row step 720080, and merged eval-like rows at steps
  50000, 100000, 150000, 200000, 250000, 300000, 350000, 400000, 450000,
  500000, 550000, 600000, 650000, and 700000 from the clean stopfix eval run.
  Superseded 2026-07-01: the first backfill config pointed at
  `data/sampled_dfm7_next`. The helper and training config now point at
  `data/sampled_dfm7`.
- Before resuming training, verify the W&B run still has no newer live rows.
  Then start the DFM7 continuation into that same run id. This keeps the
  dashboard continuous and avoids having to append old rows after newer live
  training rows.
- If backfilling after resume is unavoidable, log historical eval rows without
  an explicit W&B `_step` and use explicit `eval/train_step`, `dfm_eval/train_step`,
  `euroeval/train_step`, and `*/epoch` axes. This is workable, but previous
  runs showed that late backfills and summary updates are easier to get wrong.

Continuation command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm7 \
  arch/size@arch=XL \
  lr=3e-4 \
  global_batch_size=262144 \
  gradient_accumulation_steps=2 \
  epochs=5 \
  distributed_strategy=fsdp \
  checkpoint_format=sharded \
  fsdp_params_precision=fp32 \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=500 \
  checkpoint_path=checkpoints/dfm7/XL-gas2-from-dfm6-epoch3 \
  resume_checkpoint_path=checkpoints/dfm6/XL-gas2 \
  resume_checkpoint_tag=epoch_3 \
  upcast_optimizer_state_on_resume=false \
  reset_ema_on_resume=false \
  project_name=DFM5 \
  run_name=DFM6-DFM7-XL-gas2 \
  wandb_run_id=dfm6-dfm7-xl-gas2 \
  wandb_resume=allow
```

Use the old `wandb_run_id=39ht9plp` only if the deliberate choice is to
continue the original DFM6 W&B run despite the data mix changing mid-run.

Resume after interrupted DFM6-DFM7 training, 2026-07-01. Confidence: high from
local checkpoint sidecars and `pretrain.py` resume-code inspection.

- The latest available DFM7 splice checkpoint after the interrupted run is
  `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3/checkpoint_state_ephemeral_step_772000.json`.
  It records `step=772000`, `epoch=4`, `batch_in_epoch=103832`, and
  `gradient_accumulation_steps=2`.
- `pretrain.py::resolve_resume_state()` uses the sidecar for `step`, `epoch`,
  and batch/row-cursor position. It does not use the sidecar `data_path` as the
  runtime dataset path; the active Hydra `data=dfm7` config supplies
  `data/sampled_dfm7`.
- Because the canonical DFM7 sample was rebuilt after this checkpoint, resuming
  from `ephemeral_step_772000` continues the model weights and global step while
  using the rebuilt DFM7 stream from the saved batch position in epoch 4. To
  replay corrected DFM7 from the beginning of the splice instead, resume from
  `checkpoints/dfm6/XL-gas2` `epoch_3` instead of the DFM7 ephemeral checkpoint.
- An eval scheduler may still be waiting for future DFM7 checkpoints; stop or
  pause it before resuming if the next training checkpoint should not trigger
  full-GPU evaluations.
- Eval scheduler monitor update, 2026-07-01. Confidence: high from local
  one-shot monitor tests. `python -m eval_scheduler monitor` remains plain text
  by default. Add `--rich` for an optional Rich table/live display with summary
  counts, per-GPU memory/utilization, active task progress/ETA, next-ready jobs,
  and blocked pending jobs. Use `--once --rich` for a static snapshot.
- Rich monitor refinement, 2026-07-01. Confidence: high from local tests with
  different `COLUMNS`/`LINES` values and live monitor restart in tmux
  `hrm-0:5`. The Rich monitor now uses the terminal size on each refresh,
  renders the status block as one compact line, keeps each GPU on a single row,
  and truncates `Next ready` / `Blocked pending` tables to the available height
  with an explicit `... N more` final row when not all rows fit. Follow-up in
  the same session: the height allocator now reassigns unused rows from an
  empty/small queue section to the other queue section, so a waiting plan with
  no ready rows can show more blocked rows instead of leaving blank vertical
  space.
- Rich monitor non-GPU running rows, 2026-07-01. Confidence: high from local
  one-shot render and tmux monitor restart. The Rich monitor now uses one
  combined `Running jobs` table. GPU-bound rows are labeled `GPU0`, `GPU1`,
  etc.; running jobs without a GPU assignment, such as checkpoint waits,
  exports, merges, averages, and report jobs, are labeled `CPU`. This makes
  all-current-wait states visible without spending vertical space on a separate
  `Other running` box.

## DFM6-DFM7 Eval Scheduling

DFM6-DFM7 `step_750000` and `step_800000` eval plan, 2026-06-30.
Confidence: high from local scheduler status and tmux inspection.

- Plan directory:
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps750k_800k_vllm_main_20260630_202739`.
- W&B target: project `DFM5`, run id `dfm6-dfm7-xl-gas2`, run name
  `DFM6-DFM7-XL-gas2`. Evals are logged directly to this run.
- Checkpoint path:
  `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3`.
- The plan contains explicit `wait_checkpoint` rows for `step_750000` and
  `step_800000`. It was launched before either checkpoint existed; status
  showed both wait rows running and all eval/export jobs blocked behind them.
- Superseded 2026-07-01: the original queued eval x-values used the previous
  `data/sampled_dfm7_next` length. With the fixed canonical
  `data/sampled_dfm7` metadata, epoch x-values are derived from the DFM6
  epoch-3 splice point `step=720084`, `total_length=66,657,336,296`, and
  `global_batch_size=262144`: `step_750000 -> eval_epoch=3.1176509644666166`,
  `step_772000 -> eval_epoch=3.2041705933697306`, and
  `step_800000 -> eval_epoch=3.3142864847009665`.
- Runtime profile follows the DFM6 stopfix vLLM best-practice path:
  `evaluation/config/dfm6_vllm_benchmarking.yaml`, vLLM/FA4,
  Gemma native chat template, EuroEval first, BFCL native-tool conversion,
  standard batch `64`, DFM batch `32`, DFM IFEval-DA `32` shards at batch
  `32`, EuroEval batch/concurrency `32`, global
  `vllm_gpu_memory_utilization=0.28`, and managed
  `unsloth/gemma-4-E4B-it` judge as `openai/gemma-4-e4b-judge` for judged
  DFM tasks with judged utilization `0.18`.
- Tmux window `hrm-0:dfm6dfm7-scheduler` has one pane running:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps750k_800k_vllm_main_20260630_202739 \
  --gpus 0,1,2,3,4,5,6,7
```

- Tmux window `hrm-0:dfm6dfm7-monitor` has one pane running:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps750k_800k_vllm_main_20260630_202739 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30
```

Failure note, 2026-07-01. Confidence: high from scheduler status and vLLM
logs. The 750K eval campaign did not produce usable eval metrics. The
`step_750000` wait and HF export rows completed, then all real eval rows failed
quickly with non-OOM status `71`. Representative vLLM logs showed:
`FileNotFoundError: [Errno 2] No such file or directory: 'ninja'` followed by
`RuntimeError: Engine core initialization failed`. The `ninja` executable does
exist at `/home/ucloud/miniforge3/envs/hrm/bin/ninja`, but the scheduler/vLLM
subprocess environment did not include `/home/ucloud/miniforge3/envs/hrm/bin`
on `PATH`. The scheduler was stopped before `step_800000` became ready, leaving
no running eval jobs. To resume, clear the stop request, reset failed 750K eval
rows and the stopped 800K wait row as needed, then restart the scheduler with
`PATH=/home/ucloud/miniforge3/envs/hrm/bin:$PATH` or patch
`eval_scheduler/eval_scheduler/runtime.py` to prepend the selected
`python_bin`'s `bin` directory to subprocess `PATH`.

Operational correction, 2026-07-01. Confidence: high. For vLLM/FA4 eval
scheduler runs, launch both scheduler and monitor from inside the `hrm` conda
environment. Using an absolute `python_bin` is not sufficient because vLLM
startup also shells out to executables such as `ninja`. The expected launch
prefix is:

```bash
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
export PATH=/home/ucloud/miniforge3/envs/hrm/bin:$PATH
```

After that, use `python -m eval_scheduler run ...` and
`python -m eval_scheduler monitor ...`. Prefer a clean replacement plan over
the failed `20260630_202739` plan because that plan consumed all retries for
most 750K eval rows under the wrong environment.

Tool-calling diagnosis, 2026-07-01. Confidence: high from local inspection of
DFM7 tokenized analytics, rendered Gemma chat examples, current BFCL eval logs,
and the proxy/eval code. DFM6/DFM7 fixed the mechanics of preserving native
Gemma tool declarations and assistant tool calls, but it did not fully fix the
training-data contract or the BFCL-shaped supervision distribution.

Verified implementation facts:

- `scripts/build_dfm6_chat_source_tree.py` and
  `scripts/build_dfm7_chat_source_tree.py` prefer direct message-format sources
  for chat/tool datasets, so `messages`, `tools`, `tool_calls`,
  `tool_responses`, and reasoning fields are preserved when present.
- `scripts/tokenize_chat_template.py` reads `messages` plus top-level `tools`,
  normalizes `function_calls` into `tool_calls`, converts `environment` to
  `tool`, and emits supervised examples for assistant messages with content or
  tool calls.
- `data_io/chat_templates/gemma4_native_chat.jinja` renders native Gemma
  `<|tool>declaration:...<tool|>`, `<|tool_call>call:...<tool_call|>`, and
  `<|tool_response>...<tool_response|>` tokens.
- The current EuroEval BFCL path is not the old text-only path. The scheduler
  rows for BFCL have `hrm_vllm_native_proxy=True`,
  `hrm_vllm_gemma_bfcl_tools=True`, and
  `hrm_vllm_gemma_bfcl_tool_mode=parser`. The proxy extracts BFCL's embedded
  functions, sends them as OpenAI-style `tools` to vLLM, and maps native Gemma
  tool calls back to BFCL JSON.

Observed DFM7 data/eval evidence:

- `data/tokenized_dfm7` contains native-capable tool sources, including
  Nemotron Agentic `tool_calling`, `interactive_agent`, and `search`, DOLCI
  tool-use slices, and DFM Dyna-Instruct `when2call` /
  `agentic-code-sft-mix-v1`.
- The specifically BFCL-like Nemotron `tool_calling` slice is small in the
  DFM7 sample: about `656.6M` sampled tokens across the five-epoch sample
  (`~131M/epoch`) and only about `32.8M` sampled response tokens across all
  five epochs (`~6.6M/epoch`). Most Nemotron Agentic tokens come from
  `interactive_agent`, which is multi-turn/policy/search-agent data rather
  than simple exact function-and-argument selection.
- DOLCI tool-use is sampled heavily, but rendered rows contain both native
  Gemma tool declarations/calls and system text instructing XML
  `<functions>` / `<function_calls>` output. This teaches two incompatible
  tool-call interfaces in the same example. A second DOLCI-specific issue is
  that `function_calls` are Python-call strings such as
  `serper_google_webpage_search(query='...', gl='us')`. The current tokenizer
  converts these into native `tool_calls`, but leaves `function.arguments` as a
  raw string because it only JSON-parses argument strings. The Gemma template
  therefore emits Python-ish kwargs verbatim instead of canonical structured
  Gemma arguments. A scan of the first 1,000 rows found DOLCI `tool_use_sa`
  with `1,814/1,814` assistant tool calls using string arguments and DOLCI
  `tool_use` with `4,813/4,813` string arguments.
- `dfm_dyna_instruct/when2call` rows currently render mostly as text-only
  "available tools" decision examples. They have no top-level `tools` and no
  native assistant `tool_calls`, so they are useful no-call/when-to-call
  auxiliary data but should not be counted as native tool-call SFT.
- Nemotron Agentic is structurally much healthier: in the first 1,000 rows of
  each file, `tool_calling`, `interactive_agent`, and `search` all had
  top-level `tools`, no XML tool-call prompt contract, and structured dict
  arguments for all observed assistant tool calls.
- `dfm_dyna_instruct/agentic-code-sft-mix-v1` is tool-adjacent coding-agent
  dialogue, but the inspected rows had no top-level `tools` and no assistant
  `tool_calls`; treat it as coding/agentic dialogue data, not native
  tool-call SFT.
- In the current DFM6-DFM7 750K BFCL eval logs, the proxy saw `250` tool
  requests and adapted `237` model responses into tool-call JSON, with only
  `13` not adapted. The low BFCL score is therefore mostly wrong function or
  wrong argument content, not simply failure to emit parseable native calls.

Interpretation:

- The training-data fix was real but partial: native tool calls survive
  tokenization, and the current BFCL eval uses native tool routing. The
  remaining issue is that the model receives too little clean BFCL-shaped
  response supervision, while a large part of the tool-use data is either
  conflicting XML-vs-native contract data or broader agentic workflow data.
- Older BFCL results from runs where the native proxy was disabled or saw
  `tool_requests=0` should not be used as evidence that the current native
  tool path is healthy.

Recommended DFM7/DFM8 fix:

1. Convert DOLCI and similar tool-use data to one contract: top-level `tools`
   plus assistant `tool_calls`, removing XML `<functions>` /
   `<function_calls>` instructions from the supervised prompt/target, and
   parsing Python-style function-call kwargs into structured argument dicts.
2. Add or upsample BFCL-shaped native tool-call SFT with exact schema
   selection, exact argument formation, no-tool cases, and multi-tool cases.
3. Keep `when2call` as auxiliary data, but do not treat it as native tool-call
   training unless converted to top-level `tools` and assistant `tool_calls`.
4. Add a BFCL smoke-analysis script that buckets failures into `no tool call`,
   `malformed`, `wrong function`, `wrong arguments`, and `correct`, using the
   proxy payload logs.

DOLCI native-tool conversion implementation, 2026-07-01. Confidence: high
from local conversion and rendered-row smoke test.
`scripts/prepare_dfm7_special_sources.py` now emits cleaned DOLCI tool-use
rows under `data/dfm7_special_sources/dolci_native_tool_use`. The converter:

- Reads `dolci_instruct_sft_tool_use` and `dolci_instruct_sft_tool_use_sa`.
- Moves DOLCI's message-embedded `functions` JSON into top-level `tools`.
- Rewrites system text away from XML `<functions>` /
  `<function_calls>` instructions toward native tool-call wording.
- Parses Python-style `function_calls` strings into assistant `tool_calls`
  with structured argument dicts.
- Normalizes JSON-schema `type: dict` to `type: object`.

The full special-source regeneration produced `228,865` converted DOLCI rows:
`227,261` from `dolci_instruct_sft_tool_use` and `1,604` from
`dolci_instruct_sft_tool_use_sa`. A rendered smoke row had no XML tool-call
contract in the prompt, did include native `<|tool>` declarations, and rendered
structured native arguments such as:

```text
<|tool_call>call:serper_google_webpage_search{gl:<|"|>us<|"|>,hl:<|"|>en<|"|>,num_results:5,query:<|"|>Ran Nakash only loss date Marco Huck<|"|>}<tool_call|>
```

A one-file tokenization smoke on the converted DOLCI SA file succeeded with
Gemma4 tokenizer/template, producing `4,542` supervised examples from `1,604`
conversations and `0` skipped rows:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python scripts/tokenize_chat_template.py \
  data/dfm7_chat_sources/dfm7_special_sources/dolci_native_tool_use/dolci_instruct_sft_tool_use_sa \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir logs/tokenize_smoke_dolci_native \
  --workers 1 \
  --skip-bad-json
```

`data_io/prefix_config_dfm7.yaml` now caps the old malformed DOLCI tool-use
prefixes to zero and samples the converted prefix instead:

```yaml
- prefix: dolci_instruct_sft_tool_use__
  max_per_file: 0
- prefix: dolci_instruct_sft_tool_use_sa__
  max_per_file: 0
- prefix: dolci_native_tool_use__
  max_per_file: 1000000
  repeat: 2
```

`when2call` conversion decision, 2026-07-01. Confidence: high from a full local
scan of `data/downloads/datasets/dfm_dyna_instruct/data/when2call/when2call.parquet`.
Do not convert `when2call` to native tool-call SFT as a format-only step. The
file has `3,648` assistant turns, no structured `tool_calls` /
`function_calls`, and no assistant messages matching a simple call-like target
pattern. It is useful as auxiliary no-call / ask-clarification / direct-answer
decision data, but converting it into native tool calls would require synthetic
label generation.

Additional BFCL-shaped data candidates, 2026-07-01. Confidence: medium from HF
dataset cards and one-row streaming schema inspection where accessible.

- `Salesforce/xlam-function-calling-60k`: high-priority candidate if access is
  available. The card reports `60,000` APIGen examples, `cc-by-4.0`, gated
  access, verified by format checking, execution, and semantic verification,
  with fields `query`, `tools`, and `answers`. This is close to BFCL-style
  exact function/argument supervision and should convert cleanly to native
  Gemma tool calls.
- `glaiveai/glaive-function-calling-v2`: accessible, `apache-2.0`, `113k`
  rows, but stored as text with a `system` function block and `chat` strings
  containing `<functioncall>` markers. It is usable after a parser/converter,
  but less directly native than xLAM or Nemotron.
- `Team-ACE/ToolACE`: accessible and BFCL-shaped at the task level. A streamed
  row had a system prompt with JSON tool definitions and conversations where
  assistant tool calls appear as bracketed strings such as
  `[Market Trends API(...)]`, followed by tool responses. It needs a parser
  similar to DOLCI but may add useful multi-tool / no-tool coverage.
- `gorilla-llm/Berkeley-Function-Calling-Leaderboard` and BFCL-derived
  datasets are primarily eval-shaped. Treat as eval or decontamination-sensitive
  synthetic-seed material unless a clearly train-safe split is identified.

Clean replacement launch, 2026-07-01. Confidence: high from local tmux,
scheduler status, process list, and vLLM logs. A replacement plan was created:

```text
logs/scheduler/dfm6_dfm7_XL_gas2_steps750k_800k_vllm_hrmenv_20260701_062711
```

It uses fresh log roots and fresh HF export directories with the `_hrmenv_`
suffix, targets W&B project `DFM5` run id `dfm6-dfm7-xl-gas2`, and keeps the
same DFM6 stopfix vLLM runtime profile. It was launched from tmux windows
`hrm-0:dfm6dfm7-scheduler` and `hrm-0:dfm6dfm7-monitor` after:

```bash
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
export PATH=/home/ucloud/miniforge3/envs/hrm/bin:$PATH
```

The scheduler pane printed:

```text
Python: /home/ucloud/miniforge3/envs/hrm/bin/python
Ninja: /home/ucloud/miniforge3/envs/hrm/bin/ninja
```

Verified startup: `step_750000` wait completed, `export_hf` completed, and the
first eight EuroEval jobs started. A representative vLLM log reached
`Application startup complete`, reported `Using FlashAttention version 4`, and
served `/v1/chat/completions` requests. No `ninja` startup error was present in
the replacement logs at verification time. `step_800000` was still waiting for
the checkpoint.

Retry note, 2026-07-01. Confidence: high from current scheduler status and
vLLM logs. In the clean replacement plan, three EuroEval first attempts
(`nordjylland-news`, `danish-citizen-tests`, `hellaswag-da`) retried with
status `1` while no jobs were marked failed. This was not the old `ninja`
environment issue. Logs showed vLLM memory pressure while co-running with
training: one server had free memory `49.63/178.34 GiB`, just below requested
`gpu_memory_utilization=0.28` (`49.94 GiB`), and another failed sampler warmup
with only about `828 MiB` free after startup. If these retries continue, lower
the co-running vLLM utilization for remaining/future rows to about `0.25` or
schedule on GPUs with more headroom; batch-size changes alone do not solve
startup KV-cache reservation failures.

Hard stop and reset, 2026-07-01. Confidence: high from local process list,
`nvidia-smi`, and scheduler status. The clean replacement plan above was
stopped hard after the scheduler had already drained:

```text
jobs pending=405 running=0 done=27 failed=0 skipped=2
stop_requested=logs/scheduler/dfm6_dfm7_XL_gas2_steps750k_800k_vllm_hrmenv_20260701_062711/stop.request
```

`python -m eval_scheduler plan reset-running --plan-dir ...` reported
`reset_running_jobs 0`. The remaining monitor/status processes tied to the
plan were killed by exact plan-path match. No eval/vLLM processes remained;
`nvidia-smi` showed only the active DFM6-DFM7 training ranks. Future/retry
pending rows were patched so non-judge vLLM rows use
`vllm_gpu_memory_utilization=0.25`; judge rows remain at `0.18`.
Verification after patching showed pending utilization counts:
`0.25 -> 389` and `0.18 -> 16`, with no pending/running row at `0.28`.
Completed historical rows were left untouched. Backups were written in the
plan directory, including
`plan.tsv.before_hardstop_util025_20260701_064639`. To resume this exact plan,
remove the `stop.request` file and restart from inside the `hrm` conda
environment; do not restart from the old non-hrm failed plan.

DFM6-DFM7 next-four eval scheduler, 2026-07-01. Confidence: high from local
plan creation, scheduler status, and tmux process inspection. After the
`step_750000`/`step_800000` replacement plan completed cleanly (`432` done,
`2` skipped, no failures), a new future-checkpoint plan was created for the
next four 50K increments:

```text
logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253
```

Queued checkpoints and corrected DFM7 epoch x-values:

| Checkpoint | Eval epoch |
| --- | ---: |
| `step_850000` | `3.510922004935317` |
| `step_900000` | `3.7075575251696673` |
| `step_950000` | `3.9041930454040177` |
| `step_1000000` | `4.100828565638368` |

Plan settings follow the successful HRM-env/vLLM path: W&B project `DFM5`, run
id `dfm6-dfm7-xl-gas2`, checkpoint path
`checkpoints/dfm7/XL-gas2-from-dfm6-epoch3`, EuroEval first, standard batch
`64`, DFM batch `32`, DFM IFEval-DA batch `32`, EuroEval batch `32`, judged
DFM tasks batch/max-connections `16`, `unsloth/gemma-4-E4B-it` local judge,
Gemma4 native chat template, FA4/vLLM, global
`vllm_gpu_memory_utilization=0.25`, and judged-task utilization `0.18`.

Each checkpoint uses a separate port base so later checkpoints can start
opportunistically while tail tasks from an earlier checkpoint are still
running: `41000`, `42000`, `43000`, and `44000`.

Tmux launch:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253 \
  --gpus 0,1,2,3,4,5,6,7

/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30 \
  --rich
```

The scheduler is in tmux window `hrm-0:4` (`dfm6dfm7-next4`) and the Rich
monitor is in tmux window `hrm-0:5` (`mon-next4`). Initial status was
`pending=860`, `running=4`, `done=0`, `failed=0`, `skipped=4`, with the four
running rows being `wait_checkpoint` for `850K`, `900K`, `950K`, and `1000K`.

## DFM7 Zero Or Disabled Sources

DFM7 source check for six questioned datasets, 2026-06-30. Confidence: high
from local inspection of `data_io/prefix_config_dfm7.yaml`, downloaded source
schemas, and tokenized `tokens.npy` / `inst_len.npy` arrays. Superseded
2026-06-30 by the corrected conversion and sampling run below.

Current status in `data/tokenized_dfm7`:

| Source | Tokenized examples | Tokenized tokens | Current sampled contribution | Reason |
| --- | ---: | ---: | --- | --- |
| `danish_wildchat4_8m` | 0 | 0 | 0 | Source rows contain `first_user_message` and `translated_first_user_message`, not assistant responses. The chat SFT tokenizer emits no supervised examples. |
| `ai_arena_udtraek` | 0 | 0 | 0 | Source rows contain `conversation_a` / `conversation_b` branches. The generic tokenizer does not yet adapt those branch columns into `messages`, so no examples are emitted. |
| `allenai_rlvr_gsm` | 0 | 0 | 0 | Source rows contain one user `messages` entry plus `ground_truth`; there is no assistant message. Needs a converter from final question + `ground_truth` to a supervised answer. |
| `allenai_rlvr_math` | 0 | 0 | 0 | Same one-message + `ground_truth` schema issue as RLVR GSM. Needs a boxed-final-answer converter. |
| `nemotron_swe` | 2,872,238 | 85,460,456,586 | 0 | Tokenized successfully, but `data_io/prefix_config_dfm7.yaml` sets `max_per_file: 0`. |
| `synquid_wildchat_100k_qwen_messages` | 129,688 | 204,013,378 | 0 | Tokenized successfully, but `data_io/prefix_config_dfm7.yaml` sets `max_per_file: 0`, likely because broader WildChat was intended to replace it. |

Superseded implication:

- The current DFM7 sample does not include any of these six sources.
- `nemotron_swe` and `synquid_wildchat_100k_qwen_messages` can be included by
  changing the sampling config and resampling, subject to caps.
- `danish_wildchat4_8m`, `ai_arena_udtraek`, and the two RLVR sources need
  source-specific conversion/adapters before resampling; simply changing repeat
  is not sufficient.

Corrected DFM7 source status, 2026-06-30. Confidence: high from local
conversion/tokenization/sample output.

- `danish_wildchat4_8m` remains excluded. It contains first-user-message style
  rows without assistant targets and is not useful as supervised SFT without
  additional generation.
- `nemotron_swe` remains excluded and is also excluded from the tokenized union
  builder so it cannot be inherited accidentally from `data/tokenized_dfm6`.
  The current reason is practical context/length risk and excessive source
  size for the intended DFM7 mix.
- `ai_arena_udtraek` is now adapted by
  `scripts/prepare_dfm7_special_sources.py`: it extracts branch conversations
  from `conversation_a` and `conversation_b`, preserving system/user/assistant
  chat turns. The corrected tokenized union contains 4,569 supervised examples
  and 6,370,820 tokens.
- `allenai_rlvr_gsm` and `allenai_rlvr_math` are now converted from one-message
  + `ground_truth` rows into supervised instruction/response rows with boxed
  final answers. The corrected tokenized union contains 7,473 / 7,498 examples
  and 682,485 / 806,707 tokens respectively.
- `synquid_wildchat_100k_qwen_messages` is now included in full rather than
  capped at 50K rows. The corrected tokenized union contains 129,688 examples
  and 204,013,378 tokens.
  or cap values will not add useful supervised tokens.

Recommended fixes:

1. Convert `allenai_rlvr_gsm` and `allenai_rlvr_math` into two-message math
   examples with explicit answer contracts. Prefer boxed final answers for the
   dominant freeform math style.
2. Convert `ai_arena_udtraek` by extracting assistant turns from both
   `conversation_a` and `conversation_b`, preserving preceding history and
   skipping prompt-only rows.
3. Treat `danish_wildchat4_8m` as translation / prompt-seed data, not direct
   chat SFT. It can become translation examples
   `first_user_message -> translated_first_user_message`, but it does not
   contain assistant answers to the translated user requests.
4. Re-enable `synquid_wildchat_100k_qwen_messages` if we want immediate
   WildChat-style contribution while the 4.8M Danish WildChat adapter is still
   unresolved.
5. Include `nemotron_swe` only with a deliberate cap; the available tokenized
   pool is very large and would dominate if uncapped.

Conversion update, 2026-06-30. Confidence: high from local script execution and
tokenized array inspection.

Applied decisions:

- `danish_wildchat4_8m` is excluded from DFM7. It is no longer linked by
  `scripts/build_dfm7_chat_source_tree.py`, is no longer selected by
  `scripts/build_tokenized_dfm7_tree.py`, and has `max_per_file: 0` in
  `data_io/prefix_config_dfm7.yaml` as a guard against stale tokenized outputs.
- `ai_arena_udtraek` is converted by
  `scripts/prepare_dfm7_special_sources.py` into normal `messages` JSONL,
  extracting both `conversation_a` and `conversation_b` branches and preserving
  assistant turns with their preceding history. The converter wrote `2,997`
  branch rows; tokenization yielded `4,569` supervised assistant-turn examples
  and `6,370,820` tokens in the DFM7 union.
- `allenai_rlvr_gsm` is converted from one-message prompt + `ground_truth` rows
  into direct boxed-answer math examples. The converter wrote and tokenized
  `7,473` examples, `682,485` tokens.
- `allenai_rlvr_math` is converted the same way, yielding `7,498` examples,
  `806,707` tokens.
- `nemotron_swe` remains excluded with `max_per_file: 0`. The DFM6 sampling
  notes found the huge SWE artifact unsuitable under the current 4k context
  PrefixLM truncation rule; revisit only through a dedicated windowing or
  conversion path.
- `synquid_wildchat_100k_qwen_messages` is restored to the DFM5/DFM6 policy of
  `max_per_file: 50000`, because the broader `danish_wildchat4_8m` replacement
  is now excluded.

Operational note:

- Superseded 2026-07-01: the DFM7 tokenized union was rebuilt after these
  changes, then fully resampled into the canonical `data/sampled_dfm7` path.
  Do not use `reuse_tokens=true` for future updates that change the tokenized
  union, because the concatenated `tokens.npy` backing file changes shape.

Verified safe resample pattern:

```bash
cd /work/dfm/HRM-Text/data_io
python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm7 \
  output_path=../data/sampled_dfm7_rebuild_tmp \
  epochs=5 \
  concat_workers=4 \
  prefix_config_path=prefix_config_dfm7.yaml \
  > ../data/show_analytics_dfm7_rebuild_tmp.md
```

After validating `../data/sampled_dfm7_rebuild_tmp/metadata.json`, the rebuild
was moved into `data/sampled_dfm7` and `config/data/dfm7.yaml` was kept pointed
at the canonical path.

## Candidate Dataset Scan

HF namespace scan, 2026-06-30. Confidence: medium from Hugging Face API
metadata/cards and local DFM6 prefix/download manifest comparison. Scanned:
`danish-foundation-models`, `synquid`, `oliverkinch`, and `schneiderkamplab`.
Avoid double-adding datasets already present in DFM6 unless the candidate is a
clear expanded replacement.

Current DFM6 already covers these families from the scanned namespaces:

- `danish-foundation-models/danish-dynaword` via raw/derived DynaWord and
  DynaWord transformation datasets.
- `danish-foundation-models/laerebogen`.
- `synquid/wiki-instruct-da`, `synquid/danish-verifiable-reasoning`,
  `synquid/translation-100k`, `synquid/ifbench-train`,
  `synquid/mt-da-deepseek`, and `synquid/wildchat-100k-qwen-messages`.
- `oliverkinch/instruct-bt`, `oliverkinch/multi-wiki-qa-high-quality-subset`,
  `oliverkinch/*-bt`, `oliverkinch/machine-translation-da-*`, and
  `oliverkinch/eur-lex-sum-instruct`.
- `schneiderkamplab/common-pile-*`, `schneiderkamplab/danish-dynaword-*`,
  `schneiderkamplab/transformations-*`, and `schneiderkamplab/sapient-synth-*`.

High-priority DFM7 candidates:

| Dataset | Category | DFM6 status | DFM7 recommendation |
| --- | --- | --- | --- |
| `danish-foundation-models/dfm-dyna-instruct` | Mixed Danish/English SFT, code, tool-use, refusals | Partly overlaps DFM6; also has new `agentic-code-sft-mix-v1`, `when2call`, `da-refusals`, and `apertus-sft-mixture` | Use as the canonical expanded DFM instruction source if possible, but avoid double-counting existing constituents. Either replace the overlapping individual DFM6/Synquid sources with this collection pinned to a revision, or import only new configs. |
| `synquid/agentic-code-sft-mix-v1` | English code, agentic coding, tool-use | New; also a constituent of `dfm-dyna-instruct` | Include if not using full `dfm-dyna-instruct`. Strong target for code/tool gaps. Card reports `24,192` rows, filtered from NVIDIA code/SWE/OpenCode sources, with `messages`, optional `tools`, and metadata. License metadata is `other`; constituent license review needed. |
| `oliverkinch/danish-qa` | Danish QA/instruction | New | Include after schema/sample inspection. Large relative to other Oliver Danish additions (`100K<n<1M`), CC-BY-4.0 metadata, likely useful for Danish factual QA. |
| `oliverkinch/danish-summarization` | Danish summarization | New | Include, capped. It contains `eur_lex` and `nordjylland` configs; Nordjylland is large. On 2026-06-30 the DFM7 planning decision changed to not treat provenance review as a blocker for this source. |
| `oliverkinch/da-instruct-dynaword`, `oliverkinch/da-instruct-dynaword-hq`, `oliverkinch/da-instruct-dynaword-contemporary`, and `oliverkinch/da-instruct-dynaword-contemporary-hq` | Danish DynaWord instruction/backtranslation | New/expanded relative to `dynaword-bt` | Include all four for breadth, with de-duplication/caps as needed. Supersedes the earlier narrower recommendation to prefer only HQ variants. |
| `oliverkinch/autodata-da-sft` | Danish synthetic SFT from DynaWord/autodata | New | Include small capped slice after sample inspection; license metadata is `other`. |
| `danish-foundation-models/danish-wildchat4.8M` | Large Danish translated WildChat | Expanded replacement for the capped `synquid/wildchat-100k-qwen-messages` idea | Include as the expanded WildChat source for DFM7, replacing the narrow 100k WildChat source if used. Supersedes the earlier privacy/provenance-blocker stance for this planning pass. |
| `danish-foundation-models/ai-arenaen-conversations` / `ai_arena_udtraek` | Danish human conversation/preference data | New | Include as Danish dialogue/alignment data. Supersedes the earlier review-only stance for this planning pass. |
| `danish-foundation-models/multilingual-gsm-symbolic` | Math/reasoning, multilingual | New | Use as eval or seed/source inspiration. Do not train on Danish test splits if used for evaluation. English train splits may be usable; Danish appears benchmark-like rather than train-oriented. |
| `danish-foundation-models/kaenguruen` | Danish math competition MCQ | New | Include for DFM7 training by current policy decision. Convert to explicit Danish MCQ instruction rows preserving choices and target letter. Also keep as a separate eval, but mark DFM7 scores as non-held-out if trained on it. |

Medium/conditional candidates:

- `kobprof/skolegpt-instruct`: Danish instruction SFT from a quality-filtered
  translated OpenOrca subset plus SkoleGPT survey instructions. Consider for
  the next DFM7 rebuild or DFM8, especially if we want more school/education
  and Danish instruction-following coverage. It is probably worth integrating
  with a cap after schema/license/sample inspection, but the expected marginal
  value is lower if the active mix already contains substantial OpenOrca-like
  translated instruction data. Confidence: medium from the public dataset/GitHub
  description, not yet from local rows.
- `oliverkinch/danish-personas`: useful as synthetic persona/control data, but
  not direct instruction supervision unless used to generate dialogue/task
  variants.
- `oliverkinch/eur-lex-sum`, `dst-table-prompts`, `danmarks-statistik`,
  `tidsskrift-dk`, `tidsskrift-dk-en`, and `danish-university-portals`: raw or
  narrow task sources already partly represented by BT/instruct derivatives.
  Prefer using existing instruction derivatives unless DFM7 adds a conversion
  pass for summarization/QA/table reasoning.
- `danish-foundation-models/croco-munin-apertus-8b-da` and `*-gold`:
  preference pairs, not SFT. Useful only if DFM7 includes DPO/preference
  training.
- `schneiderkamplab/DA-Refusals`: include as a small safety/refusal slice if
  not already pulled through `dfm-dyna-instruct`; adult/NSFW tags require
  safety handling.

Likely exclude from training:

- Superseded 2026-06-30: earlier notes excluded
  `danish-foundation-models/kaenguruen` because its access form contains a
  no-training confirmation. Current DFM7 policy decision is to include
  Kaenguruen for training.
- `danish-foundation-models/ifeval-da`, `global-piqa-da`, `linguistic-quality`,
  `synquid/gsm8k-da`, `synquid/wmt24pp`, `schneiderkamplab/SDU-Daisy`,
  `schneiderkamplab/danish-tool-calling-benchmark`, and `oliverkinch/da-bird`:
  better treated as eval/diagnostic or synthetic-data seed material, not direct
  training data, to avoid benchmark contamination.
- `danish-foundation-models/danish-gigaword` and `oliverkinch/danish_wikipedia`:
  raw continuation corpora. Use only if DFM7 explicitly adds raw continuation or
  a conversion/audit pipeline; otherwise prefer instruction/summarization/QA
  derivatives.
- `synquid/wildchat-100k-qwen`: superseded by
  `synquid/wildchat-100k-qwen-messages`, already used in DFM6.

Operational notes:

- If `dfm-dyna-instruct` is used, pin a revision and import by `source`/`task`
  so overlapping DFM6 constituents can be de-duplicated.
- Superseded 2026-06-30: earlier notes required row-level provenance/PII review
  for WildChat/AI Arena before inclusion. Current DFM7 planning says not to use
  provenance as a blocker for these sources; still de-duplicate and cap by
  sampling policy.
- For math, keep benchmark-like datasets out of training unless they provide a
  documented train split that is not part of our eval suite.

## Candidate DFM Evals

Eval-oriented dataset scan, 2026-06-30. Confidence: medium from Hugging Face
metadata and local `dfm-evals/dfm_evals/tasks` inspection. Several datasets
from the scanned namespaces should stay out of training but are good candidates
for new or expanded DFM eval tasks.

Recommended new or expanded DFM eval integrations:

| Dataset | Proposed DFM eval | Why it helps | Notes |
| --- | --- | --- | --- |
| `danish-foundation-models/multi-ifeval` | `multi_ifeval` with at least `da`, optionally `en`, `de`, `sv`, `no`, `is` slices | Better instruction-following coverage than the current Danish-only IFEval path and useful multilingual comparison | Same IFEval-style schema as `ifeval-da`; likely easiest high-value addition. Keep language slices separate in metrics. |
| `danish-foundation-models/global-piqa-da` | Danish PIQA / physical commonsense | Danish commonsense gap; pairs naturally with existing English PIQA | Need inspect exact schema/scorer target before implementation. |
| `danish-foundation-models/multilingual-gsm-symbolic` | Danish GSM-Symbolic and possibly English GSM-Symbolic | Math robustness under symbolic perturbations; direct signal for Danish math reasoning | Use `dan` test splits for eval only. English train splits may be separate training candidates, but do not mix eval splits into training. |
| `synquid/gsm8k-da` | Danish GSM8K | Direct Danish arithmetic word-problem eval | Test split only; keep out of training. Scorer can mirror current `GSM8k` with Danish prompt text. |
| `synquid/wmt24pp` | WMT24++ Danish translation | Better translation eval than only one local translation slice | Use `en-da_DK` and ideally `da-en` only if available or construct paired direction from available data; metrics: chrF3++, chrF3, BLEU, possibly BERTScore. |
| `danish-foundation-models/linguistic-quality` | Danish linguistic quality / acceptability | Complements DALA with a small curated Danish quality signal | Manual gated; inspect schema before implementation. |

## Prep And Tokenization Notes

DFM7 prep/tokenization behavior, 2026-06-30. Confidence: high from local script
inspection and successful local run.

- DFM7 uses the Python chat-template tokenizer path
  `scripts/tokenize_chat_template.py`, not the older Rust tokenizer. The script
  is appropriate for Gemma-4-template chat rendering and can run with
  `TOKENIZER_WORKERS=16`.
- `scripts/tokenize_chat_template.py` now prunes Parquet columns before
  tokenization. For chat/message datasets it reads only `messages` plus `tools`
  if present, and for HRM triplets it reads only
  `condition`/`instruction`/`response`. This avoids reading large unused
  provenance columns.
- Partially written tokenized output directories are removed before a file is
  reprocessed; `metadata.json` is still written last. A directory without
  matching metadata is therefore treated as incomplete and restarted.
- `dfm_dyna_instruct/data/apertus-sft-mixture/apertus-sft-mixture.parquet` is a
  pathological single input for this tokenizer: the full file is 9.35 GB with
  98 row groups and 3,942,208 rows. Its `messages` column is only about 110 MB,
  but its source-side `token_count` sums to about 2.30B tokens, so processing it
  as one file would accumulate a very large Python token list before writing.
- `scripts/shard_dfm7_large_parquets.py` shards that Apertus file by row group,
  writing 98 Parquet shards with only the `messages` column under
  `data/dfm7_special_sources/dfm_dyna_instruct_apertus_sft_mixture_shards`.
  The shard set is about 3.0 GB.
- `scripts/build_dfm7_chat_source_tree.py` excludes the monolithic Apertus file
  and links the shards under
  `data/dfm7_chat_sources/dfm_dyna_instruct/data/apertus-sft-mixture-shards`,
  preserving the `dfm_dyna_instruct__` sampling prefix and avoiding duplicate
  tokenization via the `dfm7_special_sources__` wrapper.
- Verified run: after sharding, 98 Apertus shards tokenized with 16 workers in
  688.2 seconds. The two largest shards (`part-0002`, `part-0003`) formed the
  tail and reached roughly 10-15 GB RSS each; this is acceptable on the current
  machine but is the main reason the original monolithic file should not be
  used.
- Superseded by the 2026-07-01 tool-use rebuild: the 2026-06-30 DFM7 sample
  reported `total_length=66,705,562,253`. The fixed canonical sample now
  reports `total_length=66,657,336,296` with 5 epochs, i.e. about 333.29B
  sampled token positions. The physical sampled directory is about 540G on the
  current filesystem.
- Absolute per-epoch token-count comparison from local sampled metadata:

  | Dataset | Sampled path | Tokens per epoch | Vs. original Sapient |
  | --- | --- | ---: | ---: |
  | Original Sapient | `data/sampled_original_sapient` | 14,035,178,678 | 1.00x |
  | DFM5 | `data/sampled_dfm5` | 35,605,979,095 | 2.54x |
  | DFM6 | `data/sampled_dfm6` | 62,819,933,768 | 4.48x |
  | DFM7 | `data/sampled_dfm7` | 66,657,336,296 | 4.75x |

- Per-epoch bucket comparison using mutually exclusive buckets
  `Danish`, `English/general`, and `Math/tool/code`, where
  `Math/tool/code` has precedence over Danish for Danish math/tool/code
  sources. Original Sapient, DFM5, and DFM7 are computed from saved sampling
  analytics. DFM6 is estimated from tokenized task lengths plus
  `data_io/prefix_config_dfm6.yaml` because no saved `show_analytics_dfm6.md`
  exists; the estimator's raw total matches `data/sampled_dfm6/metadata.json`
  after a negligible scale factor (`1.00000006`).

  | Dataset | Danish | English/general | Math/tool/code | Total |
  | --- | ---: | ---: | ---: | ---: |
  | Original Sapient | 0.00B | 9.70B | 4.34B | 14.04B |
  | DFM5 | 7.77B | 19.21B | 8.63B | 35.61B |
  | DFM6 | 19.71B | 21.31B | 21.80B | 62.82B |
  | DFM7 | 23.60B | 21.31B | 21.80B | 66.71B |

  Percentage view:

  | Dataset | Danish | English/general | Math/tool/code |
  | --- | ---: | ---: | ---: |
  | Original Sapient | 0.0% | 69.1% | 30.9% |
  | DFM5 | 21.8% | 53.9% | 24.2% |
  | DFM6 | 31.4% | 33.9% | 34.7% |
  | DFM7 | 35.4% | 31.9% | 32.7% |

- High-level sampled-token rollup across all 5 epochs:
  Danish/Danish-facing additions 118.09B tokens (23.62B/epoch, 35.41%),
  math/reasoning 76.40B (15.28B/epoch, 22.91%), general SFT/instruction
  65.52B (13.10B/epoch, 19.64%), inherited Sapient-style/synthetic 44.05B
  (8.81B/epoch, 13.21%), code/tool/agentic 21.42B (4.28B/epoch, 6.42%), and
  summarization 8.05B (1.61B/epoch, 2.41%).
- Zero-token categories in the 2026-06-30 sample:
  `danish_wildchat4_8m`, `ai_arena_udtraek`, `allenai_rlvr_gsm`,
  `allenai_rlvr_math`, `nemotron_swe`, and
  `synquid_wildchat_100k_qwen_messages`. `synquid_wildchat_100k_qwen_messages`
  is intentionally capped to zero in `prefix_config_dfm7.yaml`; the others
  need adapter/sampling review before relying on them.

Durable prep command from repo root:

```bash
TOKENIZER_WORKERS=16 bash scripts/prepare_dfm7_data.sh
```
| `danish-foundation-models/kaenguruen` | Danish math competition eval | Strong Danish math benchmark | Also included for DFM7 training by current policy decision. Keep eval metrics separate because training/eval overlap makes it non-held-out for DFM7. |
| `oliverkinch/da-bird` | Danish text-to-SQL / table QA | Adds structured reasoning/tool-adjacent SQL coverage | Treat as eval first; could later seed synthetic training data if no overlap with eval split. |
| `schneiderkamplab/danish-tool-calling-benchmark` | Danish/English tool-calling eval | Directly targets the current BFCL/tool-format gap | Existing DFM eval BFCL code can likely be reused/adapted; keep separate Danish and English metrics. |
| `schneiderkamplab/SDU-Daisy` | Danish domain QA | Small Danish cultural/domain QA probe | Because the split is named `train`, use as eval only if we agree it is benchmark-like and not part of training. |

Lower-priority eval/diagnostic candidates:

- `oliverkinch/danish-qa`: primarily a training candidate, but a held-out split
  could become a broad Danish factual QA eval if we create a deterministic
  train/eval split.
- `oliverkinch/synthetic-qa` and `oliverkinch/synthetic-qa-context-qa`: useful
  as QA smoke tests or held-out synthetic diagnostics, but less valuable than
  real Danish benchmarks unless the schemas reveal strong coverage.
- `schneiderkamplab/sapient-synth-platypus-scibench`: possible science
  reasoning diagnostic, but lower priority than GSM-Symbolic and standard
  science/math evals.

Implementation guidance:

- Add these under `dfm-evals/dfm_evals/tasks`, not `evaluation/benchmarks.py`,
  unless we intentionally want card-comparable standard evals.
- Register each task and add shard support up front for anything above a few
  hundred examples.
- Keep benchmark-like datasets in eval-only manifests so DFM7 training cannot
  accidentally sample them.
- Prefer stable metric names under `dfm_eval/<task>/<metric>/mean` and add
  headline-average membership only after a smoke run verifies scoring.

## Build Artifacts

DFM7 initial build scaffolding, 2026-06-30. Confidence: high from local file
edits, medium until full download/tokenization/sample execution.

Created separate DFM7 artifacts and commands:

- Training config: `config/data/dfm7.yaml` points at `data/sampled_dfm7`.
- Sampling config: `data_io/prefix_config_dfm7.yaml` starts from the DFM6
  policy and adds DFM7-specific broader Danish instruction/chat/math sources.
- Source tree builder: `scripts/build_dfm7_chat_source_tree.py` writes
  `data/dfm7_chat_sources`.
- Tokenized union builder: `scripts/build_tokenized_dfm7_tree.py` writes
  `data/tokenized_dfm7`.
- Special-source converter: `scripts/prepare_dfm7_special_sources.py` prepares
  benchmark-shaped training rows such as Kaenguruen as explicit
  instruction/response JSONL.
- End-to-end preparation script: `scripts/prepare_dfm7_data.sh`.

Gemma 4 template invariant:

- DFM7 must use `data_io/chat_templates/gemma4_native_chat.jinja` throughout.
- `scripts/prepare_dfm7_data.sh` checks the template path and exits if a
  different template is supplied.
- `scripts/prepare_dfm7_data.sh` also defaults to the Gemma 4 tokenizer at
  `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json` and rejects
  non-Gemma tokenizer paths.
- Tokenization output goes through `scripts/tokenize_chat_template.py`; do not
  use the legacy Rust HRM marker-tokenizer for DFM7.

Incremental DFM7 correction, 2026-06-30. Confidence: high from local command
output. An initial `scripts/prepare_dfm7_data.sh` run mistakenly built a full
DFM6-plus source tree and began retokenizing 10,528 files. The largest inherited
groups were `sapient_cleaned` (4,891 files),
`converted_sources_dfm4_summarization` (4,019 files), and `export-upload`
(1,431 files). That run was stopped after 155 files and its partial
`data/tokenized_dfm7_jinja` output was deleted because it had also used the old
65k BPE tokenizer path. The DFM7 prep path now uses
`scripts/build_dfm7_chat_source_tree.py --new-only` and
`scripts/build_tokenized_dfm7_tree.py --base-tokenized data/tokenized_dfm6`, so
DFM7 reuses the existing Gemma-tokenized DFM6 tree and tokenizes only new DFM7
additions. Current new-only source-tree verification found only
`dfm7_special_sources/kaenguruen/train.jsonl`; the remaining DFM7 additions
must still be downloaded before tokenization.

DFM7 source-format notes:

- Preferred training schema is `messages` with assistant responses/tool calls.
- Flat instruction data should use `condition`, `instruction`, `response`.
- `scripts/tokenize_chat_template.py` now has a generic fallback for common HF
  fields such as `instruction/prompt/question` plus
  `response/completion/answer/target`, but dataset-specific converters are
  still preferred for MCQ/tool/math sources where the answer contract matters.
- Kaenguruen is converted to a Danish MCQ prompt that asks for
  `Svar: <bogstav>`, preserving answer choices instead of relying on generic
  question/answer extraction.

DFM7 novel eval scaffolding, 2026-06-30. Confidence: high for local imports
once tests pass; medium for task schemas that still need full smoke evals.

- New task module: `dfm-evals/dfm_evals/tasks/dfm7.py`.
- New suite config: `config/dfm_evals_dfm7_novel.yaml`.
- Added task wrappers for MultiIFEval, Danish GSM8K, GSM-Symbolic,
  Kaenguruen, Global PIQA DA, linguistic quality, SDU Daisy, DA-BIRD, and the
  Schneiderkamplab Danish/English tool-calling benchmark.
- Prompt policy:
  - MCQ tasks request a single option letter.
  - GSM-style tasks request a short final numeric answer and use a numeric
    extractor that accepts boxed or final numeric answers.
  - Translation/summarization tasks keep existing DFM eval prompts.
  - Tool-calling eval uses Inspect tool-call messages and a parser-aligned
    scorer rather than loose text matching.



DFM6-DFM7 1050K-1200K eval scheduler restart, 2026-07-05. Confidence: high from
local plan edit, scheduler status, tmux inspection, and process/GPU inspection.

- Reused plan directory:
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253`.
- The plan was locked, backed up, and edited so stale `running` wait rows for
  `step_1050000`, `step_1100000`, `step_1150000`, and `step_1200000` were reset
  to `pending`. The `step_1250000` block was marked `skipped` for this launch.
- The stop flag was cleared. Initial active rows are the four checkpoint waits;
  the actual checkpoint directories were not present at launch, so the scheduler
  is expected to wait until each full checkpoint is written.
- The scheduler was launched from inside the `hrm` conda environment in tmux
  window `hrm-0:4` (`dfm7-eval-1050-1200`):

```bash
cd /work/dfm/HRM-Text
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253 \
  --gpus 0,1,2,3,4,5,6,7
```

- The Rich monitor was launched in tmux window `hrm-0:5` (`dfm7-mon-1050-1200`):

```bash
cd /work/dfm/HRM-Text
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30 \
  --rich
```

- At launch, training was independently active from
  `resume_checkpoint_tag=ephemeral_step_1028500`, consuming the GPUs; the
  scheduler itself had only checkpoint-wait rows active.
- Follow-up on 2026-07-05: the existing `step_1250000` block was re-added to
  the live plan. Its rows were changed from `skipped` back to `pending`, except
  for the intentionally skipped EuroEval `valeu-da` row. The live scheduler
  picked up `wait-01737` for `step_1250000` at `2026-07-05T09:42:09+02:00`.

## DFM6-DFM7 840K Format Smoke

Step 840000 smoke test, 2026-07-02. Confidence: high from local HF export,
vLLM server, OpenAI tool-call requests, and BFCL proxy smoke outputs.

- Exported EMA checkpoint:
  `exports/dfm6_dfm7_XL_gas2_step_840000_ema_hf_smoke_20260702_083848`
  from `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3` with
  `conversion/convert_to_hf.py --ckpt_tag step_840000 --ckpt_use_ema true`.
- Smoke outputs were written to
  `logs/smoke/dfm6_dfm7_step840000_math_tool_20260702_083929/`.
- vLLM must see `/home/ucloud/miniforge3/envs/hrm/bin` on `PATH`; otherwise
  FlashInfer sampling JIT fails with `FileNotFoundError: ninja`.
- For OpenAI `tool_choice=auto`, vLLM must be launched with
  `--enable-auto-tool-choice --tool-call-parser gemma4`; without those flags
  tool requests fail with HTTP 400 before model inference.

Observed behavior:

- MCQ math format is correct on the probe: the model returned exactly `B` for
  a one-letter arithmetic multiple-choice prompt.
- Freeform math still did not follow the desired boxed-final-answer contract.
  GSM/MATH-style prompts that explicitly requested `\boxed{...}` produced
  correct arithmetic but ended with `$34$`, `$42$`, or prose instead of a final
  boxed answer.
- Tool calling is structurally active with the Gemma4 parser. The first tool
  call is usually the right function/arguments for simple calculator/weather
  prompts, and a no-tool greeting produced no tool call.
- Tool-call stopping/control is still weak. With larger generation budgets the
  model repeats tool calls and can add spurious calls; at short budgets
  (`max_tokens` 16-24) the first call is cleaner but may omit a required
  argument at 16 tokens.
- The BFCL proxy path also converts a BFCL-shaped prompt into native tools and
  returns parser-compatible JSON content, but the calculator smoke still
  repeated the same tool call twice. This suggests the remaining issue is model
  generation/stopping quality, not a complete eval-pipeline mismatch.

DFM7 math-format source audit, 2026-07-02. Confidence: high from local
sampling-config inspection, `data/show_analytics_dfm7.md`, and source-row
sampling. Audit files:
`logs/dfm7_math_format_audit_20260702_corrected.json`.

- The fixed DFM7 RLVR converters do teach boxed-final answers, but their weight
  is far too small to dominate the math response contract. Sampled target
  tokens over 5 epochs:
  - `allenai_rlvr_gsm`: 3.10M target tokens.
  - `allenai_rlvr_math`: 3.66M target tokens.
  - Combined boxed RLVR: 6.76M target tokens over 5 epochs, or 1.35M per
    epoch.
- Major inherited math-ish sources still dominate the target-token budget and
  use mixed/non-boxed answer styles:
  - `openmathinstruct2`: 10.66B target tokens over 5 epochs. Sampled
    `cot.parquet` rows contained `\boxed{...}` often, but only about 3.1% of
    sampled rows ended with a boxed answer; `direct.parquet` rows were mostly
    bare answers.
  - `dmmath`: 11.28B target tokens over 5 epochs. Sampled rows were bare
    numeric direct answers.
  - `ampsmathematica`: 444M target tokens over 5 epochs. Sampled rows were
    `$...$` LaTeX answers, not boxed.
  - `flan`: 24.01B target tokens over 5 epochs. Sampled GSM8K CoT rows used
    prose answer styles such as `The answer: 24.`, not boxed finals.
- Just `openmathinstruct2 + dmmath + ampsmathematica + flan` contribute
  about 46.40B target tokens over 5 epochs, or 9.28B target tokens per epoch.
  That is roughly 6,861x the target-token weight of the corrected boxed RLVR
  sources.
- Conclusion: more DFM7 training can improve math ability, but the current
  DFM7 mix should not be expected to reliably learn the desired freeform math
  output contract (`reasoning, then exactly one final \boxed{...}`) from the
  data as sampled. The boxed-contract signal exists but is swamped by inherited
  bare/prose/`$...$` math answer formats.

## DFM6-DFM7 Progress Assessment

Assessment on 2026-07-03 after fixing the 900K BFCL shard and before the
950K+ queued evaluations. Confidence: high for numbers taken from local
reports and scheduler state; confidence: medium for trend interpretation.
The initial same-day interpretation that "math is mixed" and "HumanEval is
noisy" was too conservative because it over-emphasized one 750K->900K headline
slice and under-emphasized the actual before/after DFM7-switch comparison.

- The active run is `DFM6-DFM7-XL-gas2` in the `DFM5` W&B project. W&B summary
  inspection showed it running around step 907K with `train/loss` about 1.066.
- The eval scheduler has completed the 900K rerun, including BFCL-v2 and all
  v4 averages/reports, and is waiting on future checkpoints 950K, 1000K,
  1050K, 1100K, 1150K, 1200K, and 1250K.
- Overall training progress is strong from early checkpoints to 900K:
  - Danish headline average rose from about 32.0 at 50K to about 51.1 at 900K.
  - English headline average rose from about 33.9 at 50K to about 66.6 at 900K.
  - Math/code headline average rose from about 6.5 at 50K to about 31.2 at
    900K, but this section is noisy because BFCL-v2 has been unstable and
    sparse.
- Since the DFM7 switch, the corrected interpretation is:
  - MATH has improved materially, roughly from the low 30s to about 49 on the
    current evaluated checkpoints.
  - HumanEval has also improved materially, roughly from the mid 40s to the low
    50s on the relevant post-switch comparison.
  - English and Danish headline averages look near-converged, but that hides
    different sub-suite behavior. W&B `suite_avg_v3` rows show continued
    movement across the DFM7-relevant 700K-900K window:
    - Standard: 0.6891 -> 0.6963 -> 0.7011 -> 0.7068 -> 0.7078.
    - DFM-evals: 0.5851 -> 0.6008 -> 0.5914 -> 0.5936 -> 0.6241.
    - EuroEval: 0.5209 -> 0.5365 -> 0.5527 -> 0.5581 -> 0.5583.
    W&B query caveat: 850K and 900K suite rows were logged as separate
    one-suite rows at different internal `_step`s, so querying all suite keys
    in one sparse-history request can miss them. Query each suite key separately
    or group by `suite_avg_v3/train_step`.
  - Tool calling is not solved: the corrected 900K BFCL-v2 rerun scored about
    2.32% tool-calling accuracy. The earlier 750K BFCL spike should not be
    treated as evidence of stable tool-calling competence.
- Interpretation: DFM7 has not caused broad degradation and appears to have
  helped math/code more than the original headline summary suggested. The main
  unresolved targeted gap is still native tool calling. If 950K and 1000K do
  not move BFCL-v2 materially above the low single digits, the remaining
  problem is probably data density/format alignment rather than insufficient
  continuation alone.

## DFM6-DFM7 Late-Epoch Cooldown Option

Planning note, 2026-07-05. Confidence: high for code-path inspection; medium
for optimization judgement until tried.

- The run is already in epoch 5 after resuming from
  `ephemeral_step_1028500`; the checkpoint state records `epoch: 5`,
  `global_batch_size: 262144`, `gradient_accumulation_steps: 2`, and
  `local_batch_size: 16384`.
- If we want a conservative "cooldown" after the fourth epoch, prefer doubling
  effective batch by changing:
  - `global_batch_size=524288`
  - `gradient_accumulation_steps=4`
  This keeps the per-rank microbatch unchanged:
  `524288 / (8 * 4) = 16384`, so GPU memory should stay close to the current
  run.
- Do not double `global_batch_size` while keeping `gradient_accumulation_steps=2`
  unless we explicitly want to test memory pressure; that would double the
  local microbatch to `32768` tokens per rank and may OOM.
- Resume behavior caveat: `pretrain.py` stores checkpoint metadata including
  `local_batch_size`, `batch_in_epoch`, and row cursors. If local batch size is
  unchanged, resume can continue with batch-based skipping. If local batch size
  changes, the code falls back to row-cursor resume. Keeping local batch fixed
  via gradient accumulation is therefore the safer path.
- Optimization caveat: doubling batch halves the number of optimizer updates
  per remaining token. This is a real cooldown in gradient-noise/update-rate
  terms, but it also changes the update budget. If the goal is only gentler
  finishing, lowering LR is the simpler knob; if the goal is smoother late
  training without increasing memory, larger gradient accumulation is a
  reasonable option.

Follow-up, 2026-07-05. Confidence: high for W&B train/eval metric inspection;
medium for optimization judgement.

- Recent W&B train metrics do not show an obvious instability that requires an
  aggressive cooldown. In 25K-step windows through about 1.03M steps, loss is
  noisy but broadly around `1.01-1.03`, and exact accuracy is broadly around
  `0.28`.
- Suite averages through 1.0M show saturation/noise rather than clear
  overtraining:
  - Standard: `0.7068` at 850K, `0.7078` at 900K, `0.7085` at 950K, `0.7076`
    at 1.0M.
  - DFM-evals: `0.5936` at 850K, `0.6241` at 900K, `0.6163` at 950K,
    `0.6101` at 1.0M.
  - EuroEval: `0.5581` at 850K, `0.5583` at 900K, `0.5574` at 950K,
    `0.5812` at 1.0M.
- Therefore, annealing all the way to an effective `3e-8` is probably too
  aggressive if the goal is continued capability gain. It would mostly freeze
  the model near the end. A more reasonable cooldown would be a modest LR drop
  (`1e-4` to `1.5e-4`) or a cosine tail with a nonzero floor (`lr_min_ratio`
  around `0.05-0.1`), optionally combined with the safer doubled effective
  batch path above.
- Code caveat: `pretrain.py` computes LR from current `train_state.step`,
  `total_steps`, `lr`, and `lr_min_ratio`. Switching from the current flat
  `lr_min_ratio=1` to a tiny floor mid-run applies the cosine schedule
  immediately at the current global step, not only at the final few steps.

Preferred late cooldown variant, 2026-07-05. Confidence: high for local
schedule calculation from `pretrain.py`.

- A practical delayed-cosine cooldown can be implemented without code changes
  by setting:
  - `lr=3e-4`
  - `lr_warmup_steps=1050000`
  - `lr_min_ratio=0.05` or `0.1`
- With DFM7 `total_length=66657336296`, `epochs=5`, and
  `global_batch_size=262144`, `pretrain.py` computes `total_steps=1271385`.
  Therefore the cosine tail starts at 1.05M and lasts about 221K steps.
- Approximate LR values:
  - `lr_min_ratio=0.05`: 1.10M `2.66e-4`, 1.15M `1.79e-4`, 1.20M `8.21e-5`,
    1.25M `2.15e-5`, final `1.5e-5`.
  - `lr_min_ratio=0.1`: 1.10M `2.67e-4`, 1.15M `1.85e-4`, 1.20M `9.35e-5`,
    1.25M `3.62e-5`, final `3.0e-5`.
- This is preferable to annealing toward `3e-8`: it meaningfully cools the last
  fifth of training while still allowing learning. `lr_min_ratio=0.1` is the
  more conservative default; `0.05` is a stronger final cooldown.

## Six-Epoch DFM7 Sample

Sampling note, 2026-07-05. Confidence: high for local command output and
byte-for-byte verification.

- The five-epoch DFM7 sample lives at `data/sampled_dfm7` and contains
  `epoch_0` through `epoch_4`.
- A six-epoch extension was sampled into a separate directory,
  `data/sampled_dfm7_6epochs`, rather than mutating the active training
  dataset in place.
- The new Hydra data config is `config/data/dfm7_6epochs.yaml`.
- `data/sampled_dfm7_6epochs/tokens.npy` is a symlink to
  `../sampled_dfm7/tokens.npy`; the sampler was run with `reuse_tokens=true`,
  so the 509G backing token file was not recopied.
- Command used:

```bash
mkdir -p logs data/sampled_dfm7_6epochs
ln -s ../sampled_dfm7/tokens.npy data/sampled_dfm7_6epochs/tokens.npy
cd data_io
PYTHONUNBUFFERED=1 ionice -c2 -n7 nice -n 10 python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm7 \
  output_path=../data/sampled_dfm7_6epochs \
  epochs=6 \
  concat_workers=1 \
  reuse_tokens=true \
  prefix_config_path=prefix_config_dfm7.yaml \
  > ../data/show_analytics_dfm7_6epochs.md \
  2> ../logs/dfm7_sample_6epochs.stderr.log
```

- Resulting metadata:
  - `max_seq_len: 4097`
  - `total_length: 66657268330`
  - tokenizer: `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`
  - chat template: `data_io/chat_templates/gemma4_native_chat.jinja`
- Verification: all first five epoch index arrays in `data/sampled_dfm7` and
  `data/sampled_dfm7_6epochs` are byte-identical:
  `epoch_0..epoch_4/{inst_start,inst_len,resp_start,resp_len}.npy`.
- If we want to keep using `data=dfm7` instead of the separate
  `data=dfm7_6epochs` config, it is sufficient to copy
  `data/sampled_dfm7_6epochs/epoch_5` into `data/sampled_dfm7/epoch_5` and
  optionally replace `data/sampled_dfm7/metadata.json` with the six-epoch
  metadata. The token backing file is the same. The training command must still
  be restarted/resumed with `epochs=6`; an already-started `epochs=5` process
  will not extend itself just because `epoch_5` appears on disk.
- Follow-up, 2026-07-05. Confidence: high for local command output.
  `epoch_5` and the six-epoch `metadata.json` were copied into
  `data/sampled_dfm7`. The active `data=dfm7` path now contains
  `epoch_0..epoch_5`. Verification showed all four copied `epoch_5` arrays and
  `metadata.json` are byte-identical to `data/sampled_dfm7_6epochs`.
- Follow-up cleanup, 2026-07-05. Confidence: high for local command output.
  After the in-place copy was verified, the staging directory
  `data/sampled_dfm7_6epochs` was removed. The temporary Hydra config
  `config/data/dfm7_6epochs.yaml` was also removed so it cannot point to a
  deleted dataset path. The tiny analytics/log artifacts were kept:
  `data/show_analytics_dfm7_6epochs.md` and
  `logs/dfm7_sample_6epochs.stderr.log`.

## DFM6-DFM7 Step-1050K EuroEval IFEval NLTK Recovery

Recovery note, 2026-07-05. Confidence: high from local scheduler/log output.

- In the active 850K-1250K scheduler plan, two `step_1050000` EuroEval batched
  IFEval rows failed after generation during local scoring:
  - `eval-00879`: `euroeval:ifeval-da`, shard `8/20`
  - `eval-00888`: `euroeval:ifeval`, shard `17/20`
- The failure was a missing NLTK scorer resource, not vLLM/FA4/OOM:
  `LookupError: Resource 'punkt_tab' not found`, attempted path
  `tokenizers/punkt_tab/english/`.
- Fixed in the `hrm` environment by downloading NLTK data into the user-level
  shared path:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python - <<'PY'
import nltk
for pkg in ["punkt_tab", "punkt"]:
    nltk.download(pkg, download_dir="/home/ucloud/nltk_data", quiet=False)
PY
```

- Verified resource locations:
  - `/home/ucloud/nltk_data/tokenizers/punkt_tab/english`
  - `/home/ucloud/nltk_data/tokenizers/punkt/english.pickle`
- The plan was locked, `eval-00879` and `eval-00888` were reset from
  `failed`/attempt `6` to `pending`/attempt `0`, and then unlocked. The
  scheduler immediately picked both rows back up as `running`.

## DFM6-DFM7 Early Final Epoch Eval

Scheduling note, 2026-07-08. Confidence: high from local checkpoint metadata
and scheduler status.

- Because `data/sampled_dfm7` was extended to six epoch index sets after the
  run was already configured for `epochs=5`, the run finished earlier than the
  pending `step_1250000` eval target.
- The last regular completed checkpoint is `epoch_5` in
  `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3`, with checkpoint metadata
  `step: 1229504`, `epoch: 5`, `data_path: data/sampled_dfm7`.
- An eval subgraph for `ckpt_tag=epoch_5` was appended to the existing
  scheduler plan
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253`
  with `eval_epoch=5.0`, W&B run `DFM5/dfm6-dfm7-xl-gas2`, and the same
  HRM-env/vLLM/FA4 settings as the 850K-1200K campaign:
  vLLM utilization `0.25`, Gemma4 native chat template, EuroEval-first order,
  standard batch `64`, DFM batch `32`, DFM IFEval batch `32`, EuroEval batch
  `32`, judged-task vLLM utilization `0.18`.
- HF export target:
  `exports/dfm6_dfm7_XL_gas2_epoch_5_ema_hf_hrmenv_202253`.
- Scheduler status after append showed `wait-01954` completed,
  `export-01955` completed, and the first `epoch_5` EuroEval shards running on
  all eight GPUs.
- The old `step_1250000` wait row remains in the plan. It is obsolete after
  the early finish and can be marked skipped later; it does not block the
  appended `epoch_5` eval subgraph.
