---
type: Operational Record
title: EuroEval vLLM parity diagnosis (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: EuroEval vLLM
  parity diagnosis (2026-06-18).'
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
# EuroEval vLLM parity diagnosis (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

EuroEval vLLM parity diagnosis, 2026-06-18. Confidence: high for version/split
checks and local result files; medium for the structured-output explanation
until request payloads are captured. The remaining vLLM/native divergences do
not appear to come from mismatched EuroEval versions, task splits, few-shot
settings, or failed-instance counts. Native and patched-vLLM reruns use the same
`euroeval 17.4.0` / `litellm 1.89.2` versions, and the divergent tasks inspected
(`scala-da`, `scala-en`, `danske-talemaader`, `danish-citizen-tests`,
`hellaswag`, `life-in-the-uk`) have zero failed instances in both native and
patched-vLLM outputs.

The strongest current hypothesis is endpoint semantics. The native
`scripts/hrm_openai_server.py` shim flattens messages and ignores most
OpenAI-compatible extras, while vLLM is a fuller OpenAI-compatible endpoint and
can honor structured-output, tool-calling, and constrained-decoding request
fields sent through LiteLLM/EuroEval. vLLM logs also show structured-output
bitmask kernel activity. This explains why `bfcl-v2` improves under vLLM
(proper tool-call interface) while label/classification tasks can still diverge
after prompt flattening is fixed, and why `valeu-en` can abort from one invalid
label output under vLLM despite native succeeding.

Next diagnostic step: capture the exact OpenAI request payload for one remaining
divergent task, especially `scala-da` or `scala-en`, and compare which fields
native ignores versus vLLM honors (`response_format`, `tools`, `tool_choice`,
`logit_bias`, structured-output constraints, stop strings, and max-token
settings). For parity, consider a native-compatible vLLM shim that strips these
extras and forwards only the flattened prompt/generation settings to vLLM.
