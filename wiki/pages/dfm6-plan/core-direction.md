---
type: Plan Record
title: Core Direction
description: 'Part of DFM6 Plan: Core Direction.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# Core Direction

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Include:

- DFM6 is intended to be a strict superset of DFM5 at the source/data-policy
  level: every source family accepted into DFM5 should remain present unless a
  later explicit safety, quality, contamination, or licensing decision removes
  it.
- all new DFM post-training datasets that pass quality/audit checks;
- scaled-up Danish math and code data;
- scaled-up English math and code data;
- Danish tool-calling data;
- English tool-calling data.

Migration:

- Replace the current HRM/Sapient tokenizer with the intended Gemma 4 tokenizer.
- Render instruction-format data with the Gemma 4 chat template rather than the original Sapient/DFM5 instruction format.
- Because DFM6 changes tokenizer and chat-template rendering, “strict
  superset” means source coverage and sampling intent, not byte-identical
  tokenized artifacts or exactly identical rendered prompts.

Confidence: high for the user decision on 2026-06-20; medium for final caps
until the sampled DFM6 manifest is built and audited.

Clarification, 2026-06-20: no new DFM6 policy decision has been made to drop
any source family accepted into DFM5. Older DFM5 safety exclusions from the
original Sapient corpus still apply, but DFM6 should include the DFM5 accepted
set plus DFM6 additions. Any missing DFM5-accepted source in the DFM6 tokenized
union should therefore be treated as an implementation/audit issue unless it is
explicitly superseded. One current temporary omission is
`allenai_code_meta_reasoning`: it was left out of the direct chat source tree
because the local file is raw `id`/`text`/`token_count`, not a chat or
instruction row. Confidence: high from local notes and user clarification.

Sampled training size, 2026-06-25. Confidence: high from local metadata and
checkpoint configs. Current post-superset-fix `data/sampled_dfm6/metadata.json`
reports `total_length=62,819,933,768` tokens per epoch. Both
`checkpoints/dfm6/XL/all_config.yaml` and `checkpoints/dfm6/XL-gas2/all_config.yaml`
set `epochs=5`, so the nominal five-epoch DFM6 training exposure is
`314,099,668,840` tokens, or about `314.10B` tokens.

Resume point, 2026-06-28. Confidence: high from local checkpoint metadata.
The latest observed DFM6 XL-gas2 ephemeral checkpoint is
`checkpoints/dfm6/XL-gas2/fsdp2_ephemeral_step_566500`, with matching
`checkpoint_state_ephemeral_step_566500.json` and carry files for ranks 0-7.
The checkpoint state records `step=566500`, `epoch=3`,
`batch_in_epoch=172888`, `gradient_accumulation_steps=2`, and
`global_batch_size=262144`. The associated W&B run id used locally for
`dfm6-XL-gas2` is `39ht9plp`.

Eval scheduler restart, 2026-06-28. Confidence: high from local scheduler
status and process inspection. The combined DFM6 XL-gas2 plan
`logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627` contains
completed `step_550000` evals and pending checkpoint-wait subgraphs for
`step_600000`, `step_650000`, `step_700000`, and `step_750000`. Four stale
`running` wait rows were reset with:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler plan reset-running \
  --plan-dir logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627
```

The scheduler was restarted in tmux window `hrm-0:3`:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627 \
  --gpus 0,1,2,3,4,5,6,7
```

The monitor is running in the adjacent pane:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30
```

At restart time only regular checkpoints through `step_560000` existed, so
the expected state was `jobs done=216 running=4 ready=0 blocked_pending=860`:
the four active jobs are checkpoint waits for 600K/650K/700K/750K.

Eval scheduler vLLM startup failure, 2026-06-29. Confidence: high from local
logs and environment inspection. The `step_600000` eval rows in
`logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627` initially
failed because vLLM could not find CUDA/nvcc. After CUDA toolkit installation,
`/usr/local/cuda/bin/nvcc` exists and vLLM starts far enough to load the model.
The next failure is not the attention backend: logs show both
`Using FlashInfer for top-p & top-k sampling` and
`Using FlashAttention version 4`. FlashAttention 4 is the attention backend;
FlashInfer is only the sampler path selected by vLLM. The current root cause is
that FlashInfer's sampler JIT calls `ninja`, but the scheduler was relaunched
from a `(base)` shell whose `PATH` does not include
`/home/ucloud/miniforge3/envs/hrm/bin`, even though
`/home/ucloud/miniforge3/envs/hrm/bin/ninja` exists. The scheduler's
`python_bin` metadata selects the HRM Python interpreter, but native build
tools launched by subprocess name still resolve through `PATH`. Robust fix:
ensure the scheduler/vLLM environment prepends the directory containing
`python_bin(job)` before CUDA paths, or launch the scheduler from an activated
`hrm` shell. Do not disable FA4; if avoiding FlashInfer sampling is needed, use
`VLLM_USE_FLASHINFER_SAMPLER=0`, which only changes top-k/top-p sampling.

Follow-up, 2026-06-29. Confidence: high from local tmux and log inspection. The
scheduler was restarted without code changes from an activated `hrm` shell. The
successful launch command in tmux pane `hrm-0:3.1` was:

```bash
cd /work/dfm/HRM-Text
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627 \
  --gpus 0,1,2,3,4,5,6,7 \
  2>&1 | tee -a logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627/restart_20260629_hrm_env.log
```

Before restart, stale `running` rows from the failed environment attempt were
reset with:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler plan reset-running \
  --plan-dir logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627
rm -f logs/scheduler/dfm6_XL_gas2_steps550k_600k_stopfix_clean_20260627/stop.request
```

Fresh `step_600000` EuroEval vLLM logs show FlashInfer sampling and
FlashAttention 4 attention, and the server logs show successful
`POST /v1/chat/completions` requests. This confirms the failure was the launch
environment, not an FA4 problem.

Follow-up, 2026-06-29 GPU4/GPU5 EuroEval failures. Confidence: high from local
vLLM logs and `nvidia-smi`. After restarting from the `hrm` environment,
`euroeval:nordjylland-news` and `euroeval:danske-talemaader` repeatedly failed
on GPUs 4 and 5 while colocated with the ongoing DFM6 XL-gas2 training ranks.
The vLLM logs show FlashInfer sampling and FlashAttention 4 attention start
correctly, then fail during sampler warm-up:

```text
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 1024.00 MiB.
RuntimeError: CUDA out of memory occurred when warming up sampler with 1024 dummy requests.
Please try lowering `max_num_seqs` or `gpu_memory_utilization`.
```

The "GPU 0" in those logs is the single visible CUDA device inside each vLLM
process, corresponding to physical GPU4/GPU5 via `CUDA_VISIBLE_DEVICES`.
`nvidia-smi` showed those physical GPUs dominated by the training ranks
`pretrain.py` PIDs 24946/24947, leaving roughly 0.6-0.9 GiB at the exact
sampler warm-up point. This is an OOM from colocating vLLM server warm-up with
training memory pressure, not a missing `ninja`, missing CUDA, or FA4 issue.

Update 2026-06-18: DFM6 preparation files were added without touching the
current training run:

- `config/data/dfm6.yaml` points to the future `data/sampled_dfm6` output.
- `data_io/prefix_config_dfm6.yaml` records the selected source families and
  draft caps for a future token-analytics pass.
- `data_io/chat_templates/gemma4_native_chat.jinja` is a data-prep copy of the
  repo's Gemma-native evaluation chat template.

Confidence: high for local file paths; medium for draft sampling caps.

Accepted DFM6 source decision from 2026-06-18:

- Upscale/add `nemotron_agentic`, `nemotron_swe`, and
  `nemotron_instruction_reasoning_off`.
- Include AllenAI RLVR/OpenMath sources: `allenai_rlvr_gsm`,
  `allenai_rlvr_math`, and `allenai_open_math_2_50k_r1`.
- Include Tulu persona sources for code, math, and instruction following:
  `allenai_tulu_3_personas_code`, `allenai_tulu_3_personas_math`, and
  `allenai_tulu_3_personas_if`.
- Include DOLCI no-tools and tool-use sources:
  `dolci_instruct_sft_no_tools`, `dolci_instruct_sft_tool_use`, and
  `dolci_instruct_sft_tool_use_sa`.
- Include the expanded Common Pile and Danish DynaWord export datasets when
  available, replacing the earlier smaller versions in-place rather than under
  new dataset names.

Confidence: high for the user decision; medium for final token proportions.
