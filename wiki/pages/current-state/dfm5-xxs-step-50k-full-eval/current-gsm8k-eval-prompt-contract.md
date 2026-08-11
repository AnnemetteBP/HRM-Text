---
type: Operational Record
title: Current GSM8k Eval Prompt Contract
description: 'Part of DFM5 XXS Step-50K Full Eval: Current GSM8k Eval Prompt Contract.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Current GSM8k Eval Prompt Contract

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-23. Confidence: high from local inspection of
`evaluation/benchmarks.py`, `evaluation/config/dfm6_vllm_benchmarking.yaml`,
`evaluation/config/hrm_vllm_benchmarking.yaml`, and `evaluation/engines.py`.

Current standard GSM8k evals are zero-shot: `GSM8k.__init__()` loads
`gsm8k/main` test questions and sets `self.prompts = dataset["question"]`
without adding examples. The current standard vLLM configs override GSM8k to:

```yaml
generation_config:
  condition: "direct"
  max_tokens: 512
```

For the current DFM6/DFM7/DFM8 vLLM path, `prompt_mode: gemma_chat` renders the
raw question as a single Gemma user turn with `enable_thinking=False`; the
`condition` value is not inserted into the Gemma prompt. For the older HRM
prompt modes, `condition=direct` maps to the HRM direct condition token.

This supersedes older local notes that described GSM8k as using the global
`synth,cot` setting. Those notes describe an earlier/original-code comparison
or stale config state, not the current scheduler config.
