---
type: Operational Record
title: Demand-Driven Persistent vLLM Comparison, 2026-07-25
description: 'Part of DFM5 XXS Step-50K Full Eval: Demand-Driven Persistent vLLM Comparison,
  2026-07-25.'
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
# Demand-Driven Persistent vLLM Comparison, 2026-07-25

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high for implementation, unit tests, and measured baseline timing;
comparison results remain pending until the old 100K campaign and the
persistent rerun finish.

Completed EuroEval jobs in the fresh-server campaign showed material startup
overhead. Across 24 measured jobs, mean total duration was 134 seconds:
40 seconds (29.8%) in vLLM startup, 24 seconds (18.2%) in client/dataset
setup, and 70 seconds (52.0%) in evaluation. A representative MATH shard spent
roughly 20-25 seconds starting vLLM and 80 seconds generating.

The new scheduler option:

```bash
python -m eval_scheduler run \
  --plan-dir <plan-dir> \
  --gpus 0,1,2,3,4,5,6,7 \
  --persistent-vllm
```

enables demand-driven server reuse across standard, DFM, DFM-IFEval,
EuroEval, and batched EuroEval IFEval jobs. It is opt-in; the default
fresh-server path is unchanged. One lease is owned per GPU. A lease is reused
only when model/export path, checkpoint, EMA mode, Python, host, dtype, context
limit, GPU-memory utilization, attention backend, trust setting, complete
extra-argument set, CUDA root, and GPU all match. Mismatch or failed health
checks replace it. Server/client failures, OOMs, and callback exceptions
invalidate it before scheduler retry. Remaining leases are terminated when the
scheduler exits.

Lifecycle coverage is in `eval_scheduler/tests/test_server_pool.py`; static
compilation and five focused tests pass. The isolated no-W&B comparison plan is:

```text
logs/scheduler/dfm8_L_step100k_persistent_vllm_compare_20260725
```

It contains the same 216 `step_100000` workflow rows as the baseline. Tmux
window `hrm-0:8` waits for the existing fresh-server campaign to finish, then
runs this plan with persistent reuse and captures `/usr/bin/time`; `hrm-0:9`
monitors it. The final metric and timing comparison will be written to
`comparison.json` in that plan directory.
