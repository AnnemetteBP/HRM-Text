---
type: Operational Record
title: DFM5-L 550K remaining vLLM/native-proxy EuroEval launch (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5-L 550K remaining
  vLLM/native-proxy EuroEval launch (2026-06-18).'
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
# DFM5-L 550K remaining vLLM/native-proxy EuroEval launch (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5-L 550K remaining vLLM/native-proxy EuroEval launch, 2026-06-18.
Confidence: high for local scheduler plan/status output. To finish the
standard-comparable 550K vLLM/native-proxy EuroEval comparison, a small pruned
`eval_scheduler` plan was launched for the three tasks that were missing from
the earlier vLLM/native-proxy merged metrics but present in the native 550K
run:

```text
conll-en
ifeval
ifeval-da
```

`valeu-da` was not included because the native 550K comparison run also lacks a
merged `valeu-da` metric.

Plan and log roots:

```text
plan_dir:  logs/scheduler/dfm5_L_step550000_vllm_native_proxy_remaining_euroeval_bs32_20260618_200914
euro_root: logs/euroeval/dfm5_L_step550000_vllm_native_proxy_remaining_euroeval_bs32_20260618_200914
```

The plan was created with full scheduler metadata, then pruned to only the
three `eval_euroeval` rows. Each row has `initial_batch=32`,
`fixed_retry_batch=true`, `hrm_server_backend=vllm`,
`hrm_vllm_native_proxy=true`, W&B sync disabled, and:

```text
HRM_HF_EXPORT_DIR=/work/dfm/HRM-Text/exports/dfm5_L_step550000_ema_hf
VLLM_EXTRA_ARGS=--enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/hrm_direct_chat.jinja
```

Launched in tmux session `hrm-0`:

```bash
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step550000_vllm_native_proxy_remaining_euroeval_bs32_20260618_200914 \
  --gpus 0,1,2

python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step550000_vllm_native_proxy_remaining_euroeval_bs32_20260618_200914 \
  --gpus 0,1,2 \
  --interval 10
```

Initial monitor after startup showed all three rows running:

```text
GPU0: ifeval-da, batch 32
GPU1: conll-en, batch 32
GPU2: ifeval, batch 32
```
