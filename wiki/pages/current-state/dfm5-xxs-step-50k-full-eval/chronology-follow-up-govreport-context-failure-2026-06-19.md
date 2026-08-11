---
type: Operational Record
title: Follow-up GovReport context failure (2026-06-19)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up GovReport
  context failure (2026-06-19).'
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
# Follow-up GovReport context failure (2026-06-19)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up GovReport context failure, 2026-06-19. Confidence: high for local
`dfm-evals.log`, `vllm.log`, scheduler `attempts.tsv`, and runtime inspection.
The 700K vLLM GovReport failures are context-window rejections, not GPU OOMs.
GovReport examples can have prompts near the 4096-token model limit while the
DFM eval task requests 512 output tokens. vLLM rejects such requests with HTTP
400, for example:

```text
This model's maximum context length is 4096 tokens.
However, you requested 512 output tokens and your prompt contains at least
3585 input tokens, for a total of at least 4097 tokens.
Please reduce the length of the input prompt or the number of requested output tokens.
```

The scheduler records these as status `73` because
`run_client_with_server_monitor()` treats the client BadRequest as a fatal
task/API error and terminates the paired vLLM server. Retrying with smaller
batch sizes does not help; GovReport needs either lower `max_tokens`, shorter
prompt/input truncation, or a larger model context length/export path.
