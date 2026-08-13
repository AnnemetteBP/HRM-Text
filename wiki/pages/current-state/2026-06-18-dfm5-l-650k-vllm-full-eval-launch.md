---
type: Operational Record
title: 2026-06-18 DFM5-L 650K vLLM Full Eval Launch
description: 'Part of Current State: 2026-06-18 DFM5-L 650K vLLM Full Eval Launch.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-18 DFM5-L 650K vLLM Full Eval Launch

Part of [Current State](/pages/current-state.md).

Confidence: high for local checkpoint/export inspection, scheduler plan
creation, and live scheduler status.

DFM5-L `step_650000` is fully written under `checkpoints/dfm5/L` and exported
for vLLM at:

```text
exports/dfm5_L_step650000_ema_hf
```

The correct W&B x-axis is on the real DFM5 sampled-token scale, not the
temporary local 550K vLLM comparison scale:

```text
650000 / (35605979095 / 196608) = 3.5891500036842335
```

Scheduler patch, 2026-06-18. Confidence: high for code inspection and
`py_compile`. `eval_scheduler plan create` now exposes:

```text
--standard-config
--standard-engine-backend
--standard-hf-export-dir
```

When `standard_engine_backend=vllm`, standard eval rows still wait on the real
FSDP checkpoint path, but `evaluation.main` receives the HF export path as
`ckpt_path`, uses the vLLM standard config, and gets scheduler-controlled vLLM
settings such as `gpu_memory_utilization`.

Launched plan:

```text
plan_dir: logs/scheduler/dfm5_L_step650000_vllm_20260618
standard logs: logs/eval/dfm5_L_step650000_vllm_20260618
dfm logs: logs/dfm_evals/dfm5_L_step650000_vllm_20260618
euroeval logs: logs/euroeval/dfm5_L_step650000_vllm_20260618
W&B project/run: DFM5 / oti1lisg / dfm5-L
monitor: tmux hrm-0 window 8 (mon650)
runner: tmux hrm-0 window 9 (eval650)
```

Plan shape:

```text
eval_standard: 85, batch 64, vLLM standard config
eval_dfm: 51, batch 32 except generative_talemaader batch 16
eval_dfm_ifeval: 32, batch 32
eval_euroeval: 18, batch 32
eval_euroeval_batched_ifeval: 2, batch 32
```

Launch command:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step650000_vllm_20260618 \
  --gpus 0,1,2,3,4,5,6,7
```

Monitor command:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step650000_vllm_20260618 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 10
```
