---
type: Software Reference
title: '`scripts/run_sapient_anonymization_vllm_8gpu.sh`'
description: 'Part of Script Entities: `scripts/run_sapient_anonymization_vllm_8gpu.sh`.'
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
# `scripts/run_sapient_anonymization_vllm_8gpu.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-12. Confidence: high for local launch and current active run.

Starts eight single-GPU vLLM servers for the fresh Gemma 4 31B IT teacher at
`data/models/google/gemma-4-31B-it-fresh-20260604`, waits for the OpenAI
`/v1/models` endpoints, and launches one
`scripts/synthesize_anonymized_sapient_exclusions.py` shard worker per GPU.
The default ports are `8900` through `8907`, and the default served model name
is `posttrain-gemma-teacher`.

The first launch on 2026-06-12 failed because vLLM tried to import DeepGEMM
and asserted that `CUDA_HOME` was missing. The launcher now disables DeepGEMM
by default for this run with `VLLM_USE_DEEP_GEMM=0` and
`VLLM_MOE_USE_DEEP_GEMM=0`.

Active full run:

```bash
cd /work/dfm/HRM-Text
tmux attach -t sapient_anonymization_8gpu
```

Current active log root after the priority/concurrency update:

```text
logs/sapient_anonymization_20260613T082639
```
