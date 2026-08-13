---
type: Operational Record
title: DFM5-L 900K vLLM Eval Launch, 2026-06-20
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM5-L 900K vLLM Eval Launch, 2026-06-20.'
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
# DFM5-L 900K vLLM Eval Launch, 2026-06-20

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high for local plan creation, metadata inspection, and live
scheduler monitor output. The 900K DFM5-L vLLM plan was created with the same
canonical settings and launched:

```text
plan_dir:      logs/scheduler/dfm5_L_step900000_vllm_main_20260620
standard logs: logs/eval/dfm5_L_step900000_vllm_main_20260620
dfm logs:      logs/dfm_evals/dfm5_L_step900000_vllm_main_20260620
euro logs:     logs/euroeval/dfm5_L_step900000_vllm_main_20260620
W&B target:    DFM5 / oti1lisg / dfm5-L
eval_epoch:    4.96959231279355
```

Launch command:

```bash
cd /work/dfm/HRM-Text
scripts/create_dfm5_l_vllm_eval_plan.sh step_900000 4.96959231279355 20260620
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step900000_vllm_main_20260620 \
  --gpus 0,1,2,3,4,5,6,7
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step900000_vllm_main_20260620 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 10
```

The runner and monitor are in tmux windows:

```text
hrm-0:eval900main
hrm-0:mon900main
```

Initial monitor state after launch showed the checkpoint wait complete and the
HF export row running:

```text
jobs done=1 running=1 ready=0 blocked_pending=208 failed=0 skipped=1 total=211
running: export-00002 hrm-dfm5-L-vllm-native-proxy@step_900000:ema export:step_900000
```

Plan metadata verification showed `standard_engine_backend=vllm`,
`hrm_server_backend=vllm`, `hrm_vllm_native_proxy=True`, `vllm_dtype=bfloat16`,
`vllm_max_model_len=4096`, `vllm_attention_backend=FLASH_ATTN`,
`vllm_gpu_memory_utilization=0.35`, `euroeval_max_concurrent_calls=32`, and
the HRM direct chat template in `vllm_extra_args`.
