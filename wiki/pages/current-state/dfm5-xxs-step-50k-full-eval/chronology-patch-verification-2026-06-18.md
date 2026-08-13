---
type: Operational Record
title: Patch verification (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Patch verification
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
# Patch verification (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Patch verification, 2026-06-18. Confidence: high for local rerun logs and
merged metrics. A local, non-W&B vLLM FA4 probe reran the quick diverging
EuroEval task `angry-tweets` on DFM5-L `step_550000` after the chat-template
patch. The probe used the native run's EuroEval/LiteLLM versions via:

```text
EUROEVAL_BIN='uv run --no-project --with euroeval==17.4.0 --with litellm==1.89.2 python /work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py'
```

and vLLM server settings:

```text
HRM_HF_EXPORT_DIR=/work/dfm/HRM-Text/exports/dfm5_L_step550000_ema_hf
VLLM_EXTRA_ARGS='--enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/hrm_direct_chat.jinja'
VLLM_GPU_MEMORY_UTILIZATION=0.22
EUROEVAL_BATCH_SIZE=16
EUROEVAL_MAX_CONCURRENT_CALLS=32
WANDB_SYNC=0
```

Probe root:

```text
logs/euroeval/dfm5_L_step550000_vllm_fa4_angry_tweets_template_probe_20260618_173313/step_550000/angry-tweets
```

Result:

```text
native AngryTweets:       macro_f1=72.5364  mcc=59.8001
old vLLM AngryTweets:     macro_f1=28.1726  mcc=17.9991
patched vLLM AngryTweets: macro_f1=69.7931  mcc=57.6837
```

The patched vLLM path is therefore much closer to native on this previously
diverging classification task. The residual gap is small compared with the
pre-patch failure and may be due to remaining backend/version/output-format
differences; rerun a broader EuroEval subset before replacing native results.
