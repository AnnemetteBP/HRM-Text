---
type: Operational Record
title: Scheduler integration follow-up (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Scheduler integration
  follow-up (2026-06-18).'
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
# Scheduler integration follow-up (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Scheduler integration follow-up, 2026-06-18. Confidence: high for local code
inspection, syntax checks, and a throwaway plan probe. The manual vLLM/proxy
EuroEval launch path has been promoted into `eval_scheduler plan create` for
internal HRM checkpoints. New plan options:

```text
--hrm-server-backend simple|vllm
--hrm-hf-export-dir /path/to/exported_hf_checkpoint
--hrm-vllm-native-proxy
--vllm-gpu-memory-utilization FLOAT
--vllm-extra-args "..."
--vllm-max-model-len INT
```

For DFM5-L vLLM/native-proxy EuroEval jobs, create plans with:

```bash
python -m eval_scheduler plan create \
  --run-euroeval \
  --hrm-server-backend vllm \
  --hrm-hf-export-dir /work/dfm/HRM-Text/exports/dfm5_L_step550000_ema_hf \
  --hrm-vllm-native-proxy \
  --euroeval-batch 32 \
  --vllm-gpu-memory-utilization 0.22 \
  --vllm-extra-args "--enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/hrm_direct_chat.jinja"
```

Verified commands:

```bash
cd /work/dfm/HRM-Text
python -m py_compile \
  eval_scheduler/eval_scheduler/cli.py \
  eval_scheduler/eval_scheduler/plan.py \
  eval_scheduler/eval_scheduler/runtime.py

rm -rf /tmp/hrm_eval_plan_probe
python -m eval_scheduler plan create \
  --plan-dir /tmp/hrm_eval_plan_probe \
  --ckpt-path checkpoints/dfm5/L \
  --ckpt-tag step_probe \
  --eval-epoch 0 \
  --log-root /tmp/hrm_eval_plan_probe/log \
  --dfm-log-root /tmp/hrm_eval_plan_probe/dfm \
  --euroeval-log-root /tmp/hrm_eval_plan_probe/euro \
  --wandb-run-id probe \
  --wandb-run-name probe \
  --model-prefix hrm-dfm5-L-vllm-native-proxy \
  --run-euroeval \
  --hrm-server-backend vllm \
  --hrm-hf-export-dir /work/dfm/HRM-Text/exports/dfm5_L_step550000_ema_hf \
  --hrm-vllm-native-proxy \
  --vllm-gpu-memory-utilization 0.22 \
  --vllm-extra-args "--enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/hrm_direct_chat.jinja" \
  --euroeval-batch 32 \
  --force
```

The probe wrote `/tmp/hrm_eval_plan_probe/plan.tsv`; an `eval_euroeval` row
contained `hrm_server_backend: vllm`, `hrm_hf_export_dir`,
`hrm_vllm_native_proxy: true`, `vllm_gpu_memory_utilization: 0.22`, and the
FA/chat-template `vllm_extra_args`.
