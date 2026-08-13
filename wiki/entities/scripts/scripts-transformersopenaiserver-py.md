---
type: Software Reference
title: '`scripts/transformers_openai_server.py`'
description: 'Part of Script Entities: `scripts/transformers_openai_server.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/transformers_openai_server.py`

Part of [Script Entities](/entities/scripts.md).

Small local OpenAI-compatible chat-completions server for Transformers models.

Responsibilities:

- serve `/health`, `/v1/models`, and `/v1/chat/completions`
- load text-capable image/text Transformers models with `AutoProcessor` and `AutoModelForImageTextToText`
- avoid vLLM when a model path depends on unavailable vLLM/FlashAttention APIs
- serialize generation through a process-local lock

Verified use, 2026-05-24: served `unsloth/gemma-4-E4B-it` as `gemma-4-e4b-judge` on `127.0.0.1:8099` for the `dfm_evals/generative-talemaader` judge model.

```bash
CUDA_VISIBLE_DEVICES=7 python scripts/transformers_openai_server.py \
  unsloth/gemma-4-E4B-it \
  --served-model-name gemma-4-e4b-judge \
  --host 127.0.0.1 \
  --port 8099 \
  --dtype bfloat16 \
  --attn-implementation sdpa \
  --max-new-tokens 512
```
