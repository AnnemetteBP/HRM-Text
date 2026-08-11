---
type: Operational Record
title: Follow-up root cause (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up root
  cause (2026-06-18).'
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
# Follow-up root cause (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up root cause, 2026-06-18. Confidence: high for local log and code
inspection. The bad vLLM EuroEval run did use FlashAttention: vLLM server logs
record `attention_backend: FLASH_ATTN`, `Using AttentionBackendEnum.FLASH_ATTN
backend`, and `Using FlashAttention version 4`.
