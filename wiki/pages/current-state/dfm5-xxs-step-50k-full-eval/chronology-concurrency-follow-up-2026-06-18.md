---
type: Operational Record
title: Concurrency follow-up (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Concurrency follow-up
  (2026-06-18).'
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
# Concurrency follow-up (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Concurrency follow-up, 2026-06-18. Confidence: high for local code inspection,
process environment inspection, and live vLLM logs. `eval_scheduler plan
create` now accepts:

```text
--euroeval-max-concurrent-calls INT
```

The value is written to plan metadata and passed by
`eval_scheduler/eval_scheduler/runtime.py` as
`EUROEVAL_MAX_CONCURRENT_CALLS` to `scripts/run_euroeval_on_checkpoint.sh`.
`scripts/euroeval_api_no_flash_attn_guard.py` already uses this environment
variable to override EuroEval's `LiteLLMModel.buffer["max_concurrent_calls"]`.

The running 550K `ifeval` and `ifeval-da` jobs were stopped after `conll-en`
finished, the interrupted serial log directories were moved aside with a
`serial_interrupted_YYYYmmdd_HHMMSS` suffix, and the two IFEval rows were
relaunched with `euroeval_max_concurrent_calls=32`.

Process environment inspection confirmed both the `uv run` parent and child
Python EuroEval processes had:

```text
EUROEVAL_BATCH_SIZE=32
EUROEVAL_MAX_CONCURRENT_CALLS=32
```

However, live vLLM logs still showed only:

```text
Running: 1 reqs, Waiting: 0 reqs
```

for both `ifeval` and `ifeval-da`. Interpretation: the scheduler and LiteLLM
concurrency setting are no longer the limiting factor; EuroEval's IFEval task
path is feeding very small `generate()` batches, often a single long-generation
sample, so LiteLLM has little or nothing to fan out. Increasing actual
throughput for IFEval likely requires task-level sharding/subsetting or a
custom IFEval runner/evaluator that batches multiple prompts before calling the
OpenAI endpoint.
