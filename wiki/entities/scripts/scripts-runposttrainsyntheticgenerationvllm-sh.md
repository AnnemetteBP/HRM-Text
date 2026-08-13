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

Starts one vLLM server per GPU and runs shard workers for synthetic generation.

Responsibilities:

- serve the configured Gemma teacher model over local OpenAI-compatible ports;
- claim request shards from `SHARD_ROOT/pending`;
- write generated JSONL responses to `GENERATED_ROOT`;
- pass `GENERATION_ENDPOINT=chat` to the generator by default;
- clean up vLLM servers on exit.

Update, 2026-06-05: vLLM servers are launched under `setsid`, and cleanup now
terminates the process group and escalates to `SIGKILL` if needed.
