---
type: Operational Record
title: DFM5-L 800K vLLM Eval Inserted Before 850K, 2026-06-19
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM5-L 800K vLLM Eval Inserted
  Before 850K, 2026-06-19.'
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
# DFM5-L 800K vLLM Eval Inserted Before 850K, 2026-06-19

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high for local plan creation and live scheduler monitor output.
The existing 850K scheduler was left running in its original tmux windows and
remains blocked on `step_850000`. A separate 800K plan was created and launched
with the same canonical DFM5-L vLLM settings:

```text
plan_dir:      logs/scheduler/dfm5_L_step800000_vllm_main_20260619
standard logs: logs/eval/dfm5_L_step800000_vllm_main_20260619
dfm logs:      logs/dfm_evals/dfm5_L_step800000_vllm_main_20260619
euro logs:     logs/euroeval/dfm5_L_step800000_vllm_main_20260619
W&B target:    DFM5 / oti1lisg / dfm5-L
eval_epoch:    4.417415389149824
```

Launch command:

```bash
cd /work/dfm/HRM-Text
scripts/create_dfm5_l_vllm_eval_plan.sh step_800000 4.417415389149824 20260619
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step800000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step800000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 10
```

The runner and monitor are in tmux windows:

```text
hrm-0:eval800main
hrm-0:mon800main
```

Initial live state after launch showed `wait_checkpoint` complete and the HF
export row running:

```text
jobs done=1 running=1 ready=0 blocked_pending=208 failed=0 skipped=1 total=211
running: export-00002 hrm-dfm5-L-vllm-native-proxy@step_800000:ema export:step_800000
```
