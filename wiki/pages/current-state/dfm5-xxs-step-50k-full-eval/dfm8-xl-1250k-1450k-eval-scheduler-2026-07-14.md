---
type: Operational Record
title: DFM8-XL 1250K-1450K Eval Scheduler, 2026-07-14
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8-XL 1250K-1450K Eval Scheduler,
  2026-07-14.'
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
# DFM8-XL 1250K-1450K Eval Scheduler, 2026-07-14

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high from local plan creation and tmux/process inspection.

A five-checkpoint DFM8-XL eval plan was created and launched for:

```text
step_1250000, step_1300000, step_1350000, step_1400000, step_1450000
```

Plan directory:

```text
logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255
```

The plan targets W&B project/run:

```text
project: DFM5
run_id:  dfm8-xl-from-dfm6-dfm7-epoch5-clean-full
run:     DFM8-XL clean full from DFM6-DFM7 epoch5
```

Checkpoint path:

```text
checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5
```

The eval epoch values use the DFM8 continuation axis, with epoch `5.0` at
training step `1,229,504` and DFM8 epoch length
`70,479,308,606 / 262,144 = 268,857.2258` optimizer steps:

| Checkpoint | eval epoch |
| --- | ---: |
| `step_1250000` | `5.076233770311739` |
| `step_1300000` | `5.262206082742797` |
| `step_1350000` | `5.448178395173856` |
| `step_1400000` | `5.634150707604914` |
| `step_1450000` | `5.820123020035972` |

Operational settings:

- `vllm_gpu_memory_utilization=0.25`
- `standard_engine_backend=vllm`
- `hrm_server_backend=vllm`
- `hrm_vllm_native_proxy=True`
- `hrm_vllm_gemma_bfcl_tools=True`
- Gemma4 native chat template:
  `evaluation/chat_templates/gemma4_native_chat.jinja`
- EuroEval first queue order
- `max_retries=5`
- DFM IFEval-DA shards: `32`
- standard batch `64`, DFM batch `32`, IFEval batch `32`, EuroEval batch `32`
- judged DFM tasks use local `unsloth/gemma-4-E4B-it` judge server with
  `judged_batch=16`, `judged_max_connections=16`, and judge vLLM utilization
  `0.25`.

The scheduler was launched in tmux session `hrm-1` window `5`, and the Rich
monitor in window `6`:

```bash
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255 \
  --gpus 0,1,2,3,4,5,6,7

python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30 \
  --rich
```

Initial plain status reported all five checkpoint waits active:

```text
pending=1075 running=5 done=0 failed=0 skipped=5
```

Update, 2026-07-14. Confidence: high from scheduler status and
`judge-server.log` inspection.

The first `step_1250000` eval pass failed only for
`dfm:generative_talemaader`: all 8 shards hit managed judge-server OOM during
startup. The failure mode was co-located memory pressure on the same GPU:

```text
training process: roughly 122-130 GiB
HRM checkpoint vLLM eval server: roughly 45.9 GiB
Gemma E4B judge: OOM while loading
```

The live plan was patched under the scheduler lock:

- reset failed `step_1250000` `generative_talemaader` shards
  `eval-00174` through `eval-00181` to pending;
- set their HRM checkpoint vLLM server `vllm_gpu_memory_utilization` from
  `0.25` to `0.18`;
- applied the same `0.18` setting to the queued `generative_talemaader` shards
  for `step_1300000`, `step_1350000`, `step_1400000`, and `step_1450000`.

The judge settings remained unchanged:

```text
judge_server_model=unsloth/gemma-4-E4B-it
judged_batch=16
judged_max_connections=16
judged_vllm_gpu_memory_utilization=0.25
```

Future eval planning rule: when running training + an HRM vLLM eval server + a
same-GPU Gemma E4B judge on 180GB GPUs, use
`vllm_gpu_memory_utilization=0.18` for the HRM checkpoint server on judged
tasks such as `generative_talemaader`. The global `0.25` setting is too high in
this memory allocation situation because it can leave insufficient room for
judge startup after the training process and HRM server are resident.
