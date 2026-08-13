---
type: Operational Record
title: DFM8 XL Future Eval Plan Extension
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 XL Future Eval Plan Extension.'
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
# DFM8 XL Future Eval Plan Extension

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-17. Confidence: high from local scheduler commands and
`plan.tsv` validation.

The active DFM8 XL eval scheduler plan was extended in place:

```text
logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255/plan.tsv
```

The following future checkpoint subgraphs were appended with
`python -m eval_scheduler plan create --append`:

| checkpoint | eval epoch |
|---|---:|
| `step_1500000` | `6.006095332467029` |
| `step_1550000` | `6.192067644898087` |
| `step_1600000` | `6.378039957329145` |
| `step_1650000` | `6.564012269760203` |
| `step_1700000` | `6.749984582191261` |
| `step_1750000` | `6.935956894622319` |

The appended rows use the same DFM8 settings as the `1250K`-`1450K` campaign:
standard evals through vLLM, EuroEval first, `max_retries=5`, W&B run
`dfm8-xl-from-dfm6-dfm7-epoch5-clean-full`, and
`unsloth/gemma-4-E4B-it` for judged DFM tasks. Spot-check validation confirmed
`generative_talemaader` keeps `initial_batch=16`,
`max_connections=16`, and per-task HRM checkpoint
`vllm_gpu_memory_utilization=0.18`.

After appending, scheduler status was:

```text
pending=1296 running=0 done=1080 failed=0 skipped=11
```
