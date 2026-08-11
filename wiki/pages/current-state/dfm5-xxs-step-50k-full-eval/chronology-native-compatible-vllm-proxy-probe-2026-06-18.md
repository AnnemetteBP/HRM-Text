---
type: Operational Record
title: Native-compatible vLLM proxy probe (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Native-compatible
  vLLM proxy probe (2026-06-18).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Native-compatible vLLM proxy probe (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Native-compatible vLLM proxy probe, 2026-06-18. Confidence: high for local code,
logs, and completed EuroEval result. Added `scripts/native_compatible_openai_proxy.py`,
an OpenAI-compatible proxy that:

- accepts EuroEval `/v1/chat/completions` and `/v1/completions` requests,
- flattens chat messages using the same rule as `scripts/hrm_openai_server.py`,
- forwards only native-shim-compatible fields (`model`, flattened
  `messages`/`prompt`, `temperature`, max tokens, non-empty `stop`), and
- strips `response_format`, `logprobs`, `top_logprobs`, `seed`, and other
  richer OpenAI-compatible fields before forwarding to the vLLM server.

The probe ran DFM5-L `step_550000` / EMA HF export through vLLM FA4 plus this
proxy on `scala-da`:

```text
run root: logs/euroeval/dfm5_L_step550000_vllm_native_proxy_scala_da_20260618_180830
export:   exports/dfm5_L_step550000_ema_hf
GPU:      7
vLLM:     --enforce-eager --attention-backend FLASH_ATTN
proxy:    scripts/native_compatible_openai_proxy.py
EuroEval: euroeval==17.4.0, litellm==1.89.2
W&B:      disabled
```

Result:

```text
native scala-da macro_f1:             52.60
direct patched-vLLM scala-da macro_f1:33.74
native-compatible vLLM proxy macro_f1:52.36
native-compatible vLLM proxy mcc:     31.72
failed instances:                     0
```

This confirms that the large `scala-da` direct-vLLM regression was caused by
EuroEval/vLLM structured-output semantics rather than HRM export quality,
FlashAttention, or prompt flattening. For parity with historical native
EuroEval numbers, route vLLM through the native-compatible proxy or implement
the same stripping behavior directly in the EuroEval runner. For measuring a
"real OpenAI/vLLM structured output" serving surface, direct vLLM remains a
different but valid evaluation mode and should be labeled separately.

Follow-up operational finding, 2026-06-18. Confidence: high for live process
inspection, vLLM logs, and proxy payload logs. The full DFM5-L `step_550000`
EuroEval rerun through the native-compatible vLLM proxy is genuinely using
vLLM, but the remaining slow tasks are not batching well. Live vLLM logs for
`cnn-dailymail`, `ifeval`, and `ifeval-da` showed `Running: 1 reqs,
Waiting: 0 reqs` and roughly 45-55 generated tokens/s. Proxy payload logs
showed EuroEval forwards `max_tokens=2048` for IFEval / IFEval-da and
`max_tokens=256` for CNN/DailyMail, with many requests using `max_tokens=1`
for scoring/probing calls. When the model does not stop early on IFEval, a
single sample can consume close to the 2048-token budget, so wall-clock time is
dominated by serial long decoding rather than by model load, startup, or Python
native inference.

Current run root:

```text
logs/euroeval/dfm5_L_step550000_vllm_native_proxy_euroeval_full_20260618_184836
```

The rerun should be considered standard-EuroEval comparable only while these
generation limits are left unchanged. Lowering IFEval max generation length or
forcing stronger stop conditions would likely speed it up, but would create a
different evaluation setting and should be labeled separately.
