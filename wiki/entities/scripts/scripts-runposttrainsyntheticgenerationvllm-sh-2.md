---
type: Software Reference
title: '`scripts/run_posttrain_synthetic_generation_vllm.sh`'
description: 'Part of Script Entities: `scripts/run_posttrain_synthetic_generation_vllm.sh`.'
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
# `scripts/run_posttrain_synthetic_generation_vllm.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-04. Confidence: high for shell syntax and queue design;
medium for full execution until Gemma model path is provided.

Starts one vLLM OpenAI-compatible API server per GPU and runs one shard worker
per GPU. Default queue:

```text
data/synthetic_request_shards_posttrain_transform_refine/pending
```

Default behavior:

- `GPU_LIST=0,1,2,3,4,5,6,7`
- ports `8100..8107`
- `--tensor-parallel-size 1`
- `CLIENT_CONCURRENCY=32` per GPU worker
- atomically claims one shard at a time from `pending`
- writes generated JSONL rows to `data/generated_posttrain_transform_refine`
- moves completed shards to `done` and failed shards to `failed`

Command shape:

```bash
cd /work/dfm/HRM-Text
GEMMA_MODEL_PATH=<hf-id-or-local-path> \
SERVED_MODEL_NAME=posttrain-gemma-teacher \
scripts/run_posttrain_synthetic_generation_vllm.sh
```
