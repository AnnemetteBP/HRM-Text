---
type: Operational Record
title: Follow-up GovReport truncation (2026-06-19)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up GovReport
  truncation (2026-06-19).'
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
# Follow-up GovReport truncation (2026-06-19)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up GovReport truncation, 2026-06-19. Confidence: high for local config
edit, plan reset, process inspection, and live logs. GovReport was patched in
`config/dfm_evals_hrm_single_tasks.yaml` to pass:

```text
max_report_chars=9000
```

All 16 GovReport rows in
`logs/scheduler/dfm5_L_step700000_vllm_main_20260619/plan.tsv` were reset to
`pending` with `attempt=0`, stale GovReport vLLM/client processes were
terminated, the stop flag was cleared, and the scheduler was relaunched in
tmux window `hrm-0:eval700govfix`. Live GovReport vLLM logs then showed
`POST /v1/chat/completions` returning `200 OK` instead of the previous
context-length `400 Bad Request`.

The likely root cause of the classification/tagging score collapse is prompt
formatting, not FA4. Native `scripts/hrm_openai_server.py` collapses
OpenAI-style chat messages into a single plain prompt with
`messages_to_prompt()`, prefixing non-user turns as `role: text`, and then
`SimpleEngine` tokenizes once as:

```text
<|im_start|><|object_ref_start|>{flattened prompt}<|im_end|>
```

The old vLLM chat template instead rendered each EuroEval few-shot user turn as
a separate HRM query and each assistant turn as a separate HRM answer:

```text
<|im_start|><|object_ref_start|>example<|im_end|>label<|box_end|><|im_start|><|object_ref_start|>query<|im_end|>
```

EuroEval sends few-shot classification examples as multi-turn chat messages, so
this produced a different token stream only for the tasks that degraded most.
`evaluation/chat_templates/hrm_direct_chat.jinja` was updated to flatten chat
messages like the native shim and wrap once. A local tokenizer check verified
that the patched template renders exactly:

```text
<|im_start|><|object_ref_start|>Example question?

assistant: positive

Classify this.<|im_end|>
```

for the corresponding three-message few-shot chat. A remaining reproducibility
detail is that the native run used `euroeval 17.4.0` / `litellm 1.89.2`, while
the vLLM wrapper run used the installed env versions `euroeval 17.3.0` /
`litellm 1.88.1`; future parity reruns should use the patched template and
match the EuroEval/LiteLLM versions.
