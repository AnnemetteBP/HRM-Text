---
type: Plan Record
title: DFM6 BFCL Tool-Calling Eval Smoke
description: 'Part of DFM6 Plan: DFM6 BFCL Tool-Calling Eval Smoke.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# DFM6 BFCL Tool-Calling Eval Smoke

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Last updated: 2026-06-23
Confidence: high
Scope: Local single-request BFCL smoke tests against DFM6 XL-GAS2
`step_200000` HF export while the main training run was active.

Problem found at `step_200000`: EuroEval `bfcl-v2` failed, blocking
`average-00210` and therefore preventing W&B headline averages. The failure was
not a model score of zero; vLLM rejected every proxied request with:

```text
"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

Reason: `scripts/native_compatible_openai_proxy.py --gemma-native-bfcl-tools`
converted the EuroEval BFCL plain-text function list into OpenAI `tools`, but
the DFM6 vLLM server was launched without vLLM tool parsing enabled.

Live smoke setup:

- GPU: `7`
- vLLM memory cap: `0.30` because `0.35` requested `62.42 GiB` and the GPU had
  about `59 GiB` free under training.
- Model: `/work/dfm/HRM-Text/exports/dfm6_XL_gas2_step200000_ema_hf`
- Test prompt: one BFCL-style request with `walmart.purchase` and
  `musical_scale`, question "What is the musical scale associated with C sharp
  major?"

Variant A, OpenAI tools plus vLLM parser:

```bash
VLLM_EXTRA_ARGS='--enforce-eager --attention-backend FLASH_ATTN \
  --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/gemma4_native_chat.jinja \
  --enable-auto-tool-choice --tool-call-parser gemma4'
```

Proxy mode: `--gemma-native-bfcl-tools`.

Result: request succeeded with `finish_reason=tool_calls`. The proxy converted
vLLM `message.tool_calls` to EuroEval-style text JSON:

```json
{"tool_calls":[{"function":"musical_scale","arguments":{}}]}
```

The function choice was correct; arguments were empty for this early checkpoint
and prompt.

Variant B, Gemma tool declarations as text without vLLM parser:

Proxy mode: `--gemma-native-bfcl-tools-as-text`. This injects a system message
containing Gemma-native `<|tool>declaration:...<tool|>` blocks and does not send
OpenAI `tools` to vLLM. The proxy postprocessor was widened to accept bare
Gemma-like `call:name{args}` outputs as well as wrapped
`<|tool_call>call:name{args}<tool_call|>` outputs.

Result: request succeeded and the proxy converted the bare tool-call text into
EuroEval-style JSON:

```json
{"tool_calls":[{"function":"musical_scale","arguments":{"key":"C sharp major","scale_type":"major"}}]}
```

Interpretation:

- vLLM's `gemma4` tool parser is the realistic OpenAI-compatible serving path
  and is now the default main DFM6 BFCL eval path. The scheduler appends
  `--enable-auto-tool-choice --tool-call-parser gemma4` at runtime when Gemma
  BFCL tools are enabled.
- The text-injection path is a useful diagnostic fallback. On this one smoke it
  produced better arguments, but it is less representative of real serving
  because vLLM does not see structured OpenAI `tools`.
- After changing BFCL eval settings, rerun the failed `step_200000` BFCL job and
  then allow/backfill `average-00210`.

Update 2026-06-23:

- Added scheduler metadata `hrm_vllm_gemma_bfcl_tool_mode`, defaulting to
  `parser`. Existing old plans that only have the Gemma chat template or
  `hrm_vllm_gemma_bfcl_tools=true` still resolve to parser mode.
- `scripts/run_euroeval_on_checkpoint.sh` now maps parser mode to
  `scripts/native_compatible_openai_proxy.py --gemma-native-bfcl-tools` and
  diagnostic text mode to `--gemma-native-bfcl-tools-as-text`.
- Superseded for later DFM6 checkpoints: co-running DFM6 vLLM evals initially
  used `vllm_gpu_memory_utilization=0.33`. This worked for `step_200000`, but
  at later training memory pressure around `bp_steps == 5`, `step_250000`
  failed at `0.33` with vLLM startup checks such as free memory
  `58.28 GiB < 58.85 GiB requested` and sampler warmup OOM.
- Replacement setting on 2026-06-23: use `vllm_gpu_memory_utilization=0.28`
  for regular co-running DFM6 vLLM eval jobs. This was later refined for
  judged `generative_talemaader`: keep `judged_batch=16` and
  `judged_max_connections=16`, but lower only
  `judged_vllm_gpu_memory_utilization` from `0.25` to `0.18`. The root cause
  was not batch pressure; the local `unsloth/gemma-4-E4B-it` judge OOMed
  during startup because the colocated HRM vLLM server had reserved too much KV
  cache. With `0.18`, the reset `step_250000` talemaader shards reached
  `completion 17/101 failed 0` at batch `16`.
- The active `step_250000` eval and upcoming `step_300000`, `step_350000`,
  `step_400000`, and `step_450000` plans were updated to `0.28` for regular
  vLLM rows and then to `0.18` for the judged talemaader rows only. Their GPU
  jobs also set `fixed_retry_batch=true` so retries do not silently halve batch
  size.
- The `step_250000` scheduler was stopped, its running rows were reset to
  pending attempt `0`, and it was relaunched. The restarted EuroEval rows
  launched with batch `32` and vLLM logs showed
  `gpu_memory_utilization: 0.28`; requests returned HTTP 200, and
  `danish-citizen-tests` completed successfully after the relaunch.
- The `step_200000` repair rerun completed successfully:
  `eval-00021` BFCL-v2 ended with status `0`, W&B synced
  `euroeval/en/tool-calling/bfcl-v2/tool_calling_accuracy=21.32`, and
  `average-00210` logged `467` W&B keys including `avg/overall=0.40875`.

Confidence: high from local scheduler code inspection, `py_compile`, `bash -n`,
plan metadata updates, and the live `step_200000` BFCL rerun startup logs.
