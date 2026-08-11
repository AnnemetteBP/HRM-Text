---
type: Technical Reference
title: vLLM DFM Judge-Backed Eval Memory
description: 'Part of Model Architecture: vLLM DFM Judge-Backed Eval Memory.'
tags:
- architecture
- hrm
- crm
- checkpoints
- inference
status: stable
last_updated: 2026-07-23
confidence: high
part_of: /pages/model-architecture.md
---
# vLLM DFM Judge-Backed Eval Memory

Part of [Model Architecture](/pages/model-architecture.md).

2026-06-18 operational note, Confidence: high:

For `generative_talemaader` under `scripts/schedule_checkpoint_evals.sh`, the DFM runner starts a Gemma judge on the same GPU as the target model unless `JUDGE_GPU` is overridden:

```bash
CUDA_VISIBLE_DEVICES="${judge_gpu}" "${PYTHON_BIN}" scripts/transformers_openai_server.py ...
start_target_server "${gpu}" ... "${effective_batch_size}" ...
```

When the DFM5-L `step_550000` vLLM FA4 eval was co-located with active 8-GPU training, `VLLM_GPU_MEMORY_UTILIZATION=0.35` failed for `generative_talemaader` before any requests were served. The judge used about 15.8 GiB per GPU, leaving only about 55-56 GiB free, while vLLM requested about 62.4 GiB at utilization 0.35:

```text
ValueError: Free memory on device cuda:0 (55.04/178.34 GiB) on startup is less than desired GPU memory utilization (0.35, 62.42 GiB).
```

The scheduler then halved the task batch from 16 to 8 on retry, but batch backoff cannot fix this class of failure because it occurs during vLLM startup memory reservation. The working restart used:

```bash
VLLM_GPU_MEMORY_UTILIZATION=0.25
STANDARD_VLLM_GPU_MEMORY_UTILIZATION=0.25
DFM_BATCH_SIZE=16
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16
CKPT_PATH=/work/dfm/HRM-Text/checkpoints/dfm5/L
CKPT_TAG=step_550000
```

With utilization 0.25, shard 0 reached `/health`, used FlashAttention 4, and reported about 42 GiB available KV cache. GPU memory remained tight because each judged shard colocates training, the judge server, and target vLLM on one GPU.

2026-06-18 native-vs-vLLM `step_550000` comparison, Confidence: high for
local merged metrics:

The fixed vLLM FA4 path aligns closely with the native/simple HRM eval path on
standard benchmarks. Relevant local roots:

- Native: `logs/eval/dfm5_L_step550000_full_native_followup_20260617`
- vLLM FA4 remaining: `logs/eval/dfm5_L_step550000_vllm_fa4_remaining_6gpu_20260618_144432`
- Fixed FA4 MMLU local run: `logs/eval/dfm5_L_step550000_vllm_fa4_local_mmlu_piqa_20260618_143153`

The earlier `vllm_eval/MMLU/acc ~= 0.334` result is superseded by the fixed FA4
run; it came from the broken/non-FA4 path. The fixed MMLU result is
`macro_acc=0.52782`, matching native `eval/MMLU/acc=0.528775` within about
`0.001`.

Selected standard deltas, vLLM minus native:

| Task | Native | vLLM FA4 | Delta |
|---|---:|---:|---:|
| ARC acc | 0.6928 | 0.6903 | -0.0025 |
| BoolQ acc | 0.8456 | 0.8443 | -0.0013 |
| DROP F1 | 0.7716 | 0.7724 | +0.0008 |
| GSM8k acc | 0.35861 | 0.35861 | ~0 |
| HellaSwag acc | 0.5202 | 0.5199 | -0.0003 |
| MATH acc | 0.4764 | 0.4788 | +0.0024 |
| MMLU macro acc | 0.5288 | 0.5278 | -0.0010 |
| Winogrande acc | 0.6559 | 0.6519 | -0.0040 |

DFM overlap is also close for deterministic/simple tasks:
`danish_citizen_tests` `0.6330` vs `0.6404`, `dala` macro-F1 `0.4314` vs
`0.4310`, `gec_dala` exact match `0.0479` vs `0.0518`, `multi_wiki_qa` F1
`0.8507` vs `0.8491`, and `wmt24pp_en_da` chrF++ `0.5123` vs `0.5135`.
`generative_talemaader` differs more (`0.0` native vs `0.1238` vLLM FA4 with
the current judge-backed run), so treat that one as requiring separate output
inspection rather than as a pure engine-equivalence check.

The active HRM network is `models/baselines/hrm_nocarry_bp_warmup.py`.

It has two recurrent Transformer blocks:

- `L_level`: low/local recurrent block.
- `H_level`: high/global recurrent block.

Both levels operate on token-aligned hidden states with the same sequence positions and hidden width. There is no segment pooling, bottleneck, learned compression, or reduced-length workspace between levels in the current implementation.

The interaction is additive injection:

```python
return self.core(hidden_states + input_injection, **kwargs)
```

During forward:

- `z_H` starts as the token embeddings `x`.
- `z_L` starts from a learned vector buffer `zL_init`, broadcast across token positions by PyTorch broadcasting.
- Each L update receives current `z_H` as additive input.
- Each H update receives current `z_L` as additive input.
- The model returns final `z_H` to the language-model head.
- `initial_carry()` returns `None`; there is no persistent recurrent carry across training batches.
