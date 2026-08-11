---
type: Operational Record
title: Canonical DFM5-L vLLM Eval Settings, 2026-06-19
description: 'Part of DFM5 XXS Step-50K Full Eval: Canonical DFM5-L vLLM Eval Settings,
  2026-06-19.'
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
# Canonical DFM5-L vLLM Eval Settings, 2026-06-19

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high for local code changes, `py_compile`, and throwaway plan
probes.

The working DFM5-L vLLM evaluation settings have been promoted into plan
creation so future checkpoint plans do not require manual `plan.tsv` edits
after failures.

Preferred command for upcoming DFM5-L checkpoint evals:

```bash
cd /work/dfm/HRM-Text
scripts/create_dfm5_l_vllm_eval_plan.sh step_750000 4.141326927327961 20260619
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step750000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7
```

The script accepts `CKPT_TAG EVAL_EPOCH [RUN_SUFFIX]` and writes a full
standard + DFM + DFM-IFEval + EuroEval plan. Environment variables can override
paths and W&B settings: `PLAN_DIR`, `CKPT_PATH`, `EXPORT_DIR`, `LOG_ROOT`,
`DFM_LOG_ROOT`, `EUROEVAL_LOG_ROOT`, `WANDB_PROJECT`, `WANDB_RUN_ID`,
`WANDB_RUN_NAME`, `MODEL_PREFIX`, `PORT_BASE`, and `FORCE`.

Canonical settings inserted into the plan:

```text
standard_config: evaluation/config/hrm_vllm_benchmarking.yaml
standard_engine_backend: vllm
hrm_server_backend: vllm
hrm_vllm_native_proxy: true
vllm_dtype: bfloat16
vllm_max_model_len: 4096
vllm_attention_backend: FLASH_ATTN
vllm_extra_args: --enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/hrm_direct_chat.jinja
global vllm_gpu_memory_utilization: 0.35
max_retries: 5
standard_batch: 64
dfm_batch: 32
ifeval_batch: 32
dfm_ifeval_shards: 32
euroeval_batch: 32
euroeval_max_concurrent_calls: 32
judge_model: openai/gemma-4-e4b-judge
judge_server_model: unsloth/gemma-4-E4B-it
judge_server_dtype: bfloat16
judge_server_attn_implementation: sdpa
judge_server_max_new_tokens: 64
```

Task-specific plan metadata now inserted automatically:

```text
generative_talemaader:
  initial_batch: 16
  max_connections: 16
  vllm_gpu_memory_utilization: 0.25
  managed judge server: unsloth/gemma-4-E4B-it

govreport:
  initial_batch: 32
  dfm_task_args:
    - max_report_chars=9000
```

Implementation details:

```text
scripts/create_dfm5_l_vllm_eval_plan.sh
eval_scheduler/eval_scheduler/plan.py
eval_scheduler/eval_scheduler/cli.py
```

`eval_scheduler plan create` now exposes these explicit options:

```text
--judged-batch
--judged-vllm-gpu-memory-utilization
--govreport-max-report-chars
```

The settings were verified with:

```bash
cd /work/dfm/HRM-Text
python -m py_compile \
  eval_scheduler/eval_scheduler/cli.py \
  eval_scheduler/eval_scheduler/plan.py \
  eval_scheduler/eval_scheduler/runtime.py

PLAN_DIR=/tmp/hrm_dfm5_script_probe \
LOG_ROOT=/tmp/hrm_dfm5_script_probe/eval \
DFM_LOG_ROOT=/tmp/hrm_dfm5_script_probe/dfm \
EUROEVAL_LOG_ROOT=/tmp/hrm_dfm5_script_probe/euro \
EXPORT_DIR=/work/dfm/HRM-Text/exports/dfm5_L_step_probe_ema_hf \
FORCE=1 \
scripts/create_dfm5_l_vllm_eval_plan.sh step_probe 0 probe
```

The probe showed `MMLU` batch `64` with vLLM utilization `0.35`, `GovReport`
batch `32` with `dfm_task_args=['max_report_chars=9000']`, and
`generative_talemaader` batch `16`, `max_connections=16`, judge server
`unsloth/gemma-4-E4B-it`, and vLLM utilization `0.25`.

Update, 2026-06-19. Confidence: high for local script edit, plan inspection,
and live scheduler monitor output. `scripts/create_dfm5_l_vllm_eval_plan.sh`
now defaults to `CHECKPOINT_WAIT_SECONDS=60` so upcoming checkpoint evals start
within about one minute of the checkpoint becoming complete, rather than
waiting up to five minutes. The script also defaults to `SKIP_VALEU_DA=1`.
Rationale: the 700K `valeu-da` EuroEval row failed because EuroEval aborted
the full benchmark after one invalid predicted label:

```text
No candidate labels found for the predicted label in 1/53 of the samples.
Since this task does not allow invalid model outputs, we have to abort the evaluation.
```

`valeu-da` is not a dependency of headline averages because `valeu-*` rows are
excluded from `euroeval_average_job_ids` in `eval_scheduler/eval_scheduler/plan.py`.
Skipping it up front avoids a known plan-level failure while preserving all
dependency-critical standard, DFM, DFM-IFEval, and EuroEval rows. Set
`SKIP_VALEU_DA=0` when an explicit ValEU-da rerun is desired.

The 750K DFM5-L vLLM plan was created and launched:

```text
plan_dir:      logs/scheduler/dfm5_L_step750000_vllm_main_20260619
standard logs: logs/eval/dfm5_L_step750000_vllm_main_20260619
dfm logs:      logs/dfm_evals/dfm5_L_step750000_vllm_main_20260619
euro logs:     logs/euroeval/dfm5_L_step750000_vllm_main_20260619
W&B target:    DFM5 / oti1lisg / dfm5-L
eval_epoch:    4.141326927327961
```

Launch command:

```bash
cd /work/dfm/HRM-Text
scripts/create_dfm5_l_vllm_eval_plan.sh step_750000 4.141326927327961 20260619
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step750000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step750000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 10
```

The runner and monitor are in tmux windows:

```text
hrm-0:eval750main
hrm-0:mon750main
```

Initial monitor state after launch:

```text
done=0 running=1 ready=0 blocked_pending=209 failed=0 skipped=1 total=211
running: wait-00001 checkpoint:step_750000
```

At launch time, `checkpoints/dfm5/L/fsdp2_step_750000`,
`checkpoints/dfm5/L/unsharded_step_750000.pt`, and
`exports/dfm5_L_step750000_ema_hf` did not exist yet. The scheduler is waiting
for the checkpoint and should not start eval GPU work until the checkpoint is
complete and the HF export row has run.

Update, 2026-06-19. Confidence: high for local plan creation, metadata
inspection, and live scheduler monitor output. The 850K DFM5-L vLLM plan was
created using the same canonical settings and launched:

```text
plan_dir:      logs/scheduler/dfm5_L_step850000_vllm_main_20260619
standard logs: logs/eval/dfm5_L_step850000_vllm_main_20260619
dfm logs:      logs/dfm_evals/dfm5_L_step850000_vllm_main_20260619
euro logs:     logs/euroeval/dfm5_L_step850000_vllm_main_20260619
W&B target:    DFM5 / oti1lisg / dfm5-L
eval_epoch:    4.693503850971687
```

The epoch value was derived from the established 50K increment between 700K
and 750K:

```text
700K epoch: 3.865238465506098
750K epoch: 4.141326927327961
delta/50K:  0.276088461821863
850K epoch: 4.693503850971687
```

Launch command:

```bash
cd /work/dfm/HRM-Text
scripts/create_dfm5_l_vllm_eval_plan.sh step_850000 4.693503850971687 20260619
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_step850000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7
python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_step850000_vllm_main_20260619 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 10
```

The runner and monitor are in tmux windows:

```text
hrm-0:eval850main
hrm-0:mon850main
```

Initial monitor state after launch:

```text
done=0 running=1 ready=0 blocked_pending=209 failed=0 skipped=1 total=211
running: wait-00001 checkpoint:step_850000
```

Plan verification showed `MMLU` batch `64` with vLLM utilization `0.35`,
`GovReport` batch `32` with `dfm_task_args=['max_report_chars=9000']`, and
`generative_talemaader` batch `16`, `max_connections=16`, judge server
`unsloth/gemma-4-E4B-it`, and vLLM utilization `0.25`. `valeu-da` is skipped
up front per the current failure-avoidance policy.
