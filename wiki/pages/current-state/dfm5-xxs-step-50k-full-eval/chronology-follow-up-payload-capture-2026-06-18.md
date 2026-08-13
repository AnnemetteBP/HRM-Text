---
type: Operational Record
title: Follow-up payload capture (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up payload
  capture (2026-06-18).'
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
# Follow-up payload capture (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up payload capture, 2026-06-18. Confidence: high for local captured
request JSON and code inspection. Added `scripts/capture_openai_payloads.py`, a
small OpenAI-compatible capture server that logs raw `/v1/chat/completions` and
`/v1/completions` payloads to JSONL and returns dummy responses. It was used to
capture `scala-da` EuroEval requests with:

```text
uv run --no-project --with euroeval==17.4.0 --with litellm==1.89.2 \
  python scripts/euroeval_api_no_flash_attn_guard.py \
  --model payload-capture-scala-da \
  --api-base http://127.0.0.1:18181/v1 \
  --api-key inspectai \
  --cache-dir logs/debug/euroeval_payload_capture_20260618_180154/cache \
  --max-context-length 4096 \
  --force --no-progress-bar --save-results \
  --language da --dataset scala-da
```

Capture root:

```text
logs/debug/euroeval_payload_capture_20260618_180154
```

The first real `scala-da` requests include:

```text
endpoint: /v1/chat/completions
keys: logprobs, max_completion_tokens, messages, model, response_format, seed,
      stop, temperature, top_logprobs
max_completion_tokens: 10
temperature: 0.0
stop: []
logprobs: true
top_logprobs: 8
seed: 4242
response_format:
  type: json_schema
  json_schema.strict: true
  schema:
    required: ["label"]
    properties.label.enum: ["ja", "nej"]
```

The native `scripts/hrm_openai_server.py` request model only consumes
`model`, `messages`, `temperature`, `max_tokens` / `max_completion_tokens`, and
`stop`. It ignores `response_format`, `logprobs`, `top_logprobs`, and `seed`.
The vLLM OpenAI server can honor strict JSON-schema response formats and uses
structured-output constrained decoding. Therefore, for `scala-da`, the
remaining vLLM/native divergence is not just a prompt-template issue; vLLM and
native are evaluating different decoding semantics. The earlier "medium"
structured-output hypothesis is confirmed for `scala-da`.
