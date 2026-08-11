---
type: Plan Record
title: DFM6-DFM7 Eval Scheduling
description: 'Part of DFM7 Plan: DFM6-DFM7 Eval Scheduling.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# DFM6-DFM7 Eval Scheduling

Part of [DFM7 Plan](/pages/dfm7-plan.md).

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
