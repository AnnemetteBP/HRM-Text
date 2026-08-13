---
type: Operational Record
title: Runtime Update 2026-05-24
description: 'Chronological record from dfm-evals: Runtime Update 2026-05-24.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Runtime Update 2026-05-24

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Runtime update, 2026-05-24: dfm-evals for the four original checkpoints was launched. The first attempt serialized OpenAI-compatible chat requests one at a time and was too slow. `scripts/hrm_openai_server.py` was updated to micro-batch concurrent requests, and `scripts/run_dfm_evals_on_checkpoints.sh` now defaults to `BATCH_SIZE=8`, `INSPECT_MAX_CONNECTIONS=8`, and `BATCH_TIMEOUT_MS=25`. The Danish citizen tests task is capped to `250` samples by the suite-level `--limit 250`; after restart, the server log showed batched generation groups of 4, confirming batching is active. Confidence: high.
