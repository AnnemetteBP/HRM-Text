---
type: Technical Reference
title: LUMI ROCm Backend Implemented + Verified, 2026-06-17
description: 'Part of FlashAttention on B200: LUMI ROCm Backend Implemented + Verified,
  2026-06-17.'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200.md
---
# LUMI ROCm Backend Implemented + Verified, 2026-06-17

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Confidence: high for live GPU-node runs on LUMI dev-g (MI250X).

A new `rocm` accelerator backend was added and verified end-to-end on LUMI:

- `models/accelerator.py`: `AcceleratorType` now includes `"rocm"`; HIP-aware
  availability check (`torch.version.hip is not None and torch.cuda.is_available()`);
  treated as CUDA-like for device/memory/sync (`device.type == "cuda"` under ROCm).
- `models/flash_attention_prefixlm_rocm.py` (new): PrefixLM split (bidirectional
  prefix + causal) mirroring the FA4 module, calling FA2
  `flash_attn.flash_attn_varlen_func` (ROCm CK varlen kernel).
- `models/flash_attention_prefixlm_dispatch.py`: added `case "rocm"`.
- `pretrain.py`: `pin_memory` now includes `rocm`; the distributed guard already
  allows `rocm` (NCCL backend maps to RCCL on ROCm). `apply_fsdp` was made
  torch-version-adaptive: `set_gradient_divide_factor` (newer torch on B200) vs.
  `set_reduce_scatter_divide_factor` (torch 2.7.1 on LUMI), and
  `set_force_sum_reduction_for_comms` is now optional via `hasattr`. This was
  required because LUMI's torch 2.7.1 lacks the newer FSDP2 method names.

Verified on LUMI (container
`lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif`, torch `2.7.1+rocm6.2.4`):

- `flash_attn_varlen_func` bf16 forward+backward on `AMD Instinct MI250X` is finite.
- Tiny `pretrain.py` epoch on 1 GCD with `accelerator_type=rocm` + FSDP + bf16
  completes and writes a sharded checkpoint.
- Tiny `pretrain.py` epoch on 8 GCDs (full node) completes; 8 RCCL ranks shard
  and write 8 `.distcp` shards + 8 carry files.
- Real L config (24 layers, hidden 1280) on 8 GCDs builds with no OOM at
  `global_batch_size=172032`, `gradient_accumulation_steps=4` (per-rank
  microbatch 5376 tokens). Observed `~3.6 s/step` over 308 steps; total schedule
  is `326336` steps for `data/sampled_original_sapient`
  (`total_length=14,035,178,678`, `max_seq_len=4097`). Estimated full run
  `~13-14 days` on one node -> must checkpoint-by-step and resume across jobs, or
  scale to more nodes.

Operational notes:

- Singularity needs explicit binds:
  `-B /project/project_465002606 -B /scratch/project_465002606 -B /flash/project_465002606`.
- The container lacks `hydra-core` and `coolname`; a venv with
  `--system-site-packages` at `${REPO}/.venv-lumi` supplies them while reusing the
  container's torch + flash_attn. Launch with `python -m torch.distributed.run`
  (the venv has no `torchrun` shim).
- Set `MIOPEN_USER_DB_PATH` / `MIOPEN_CUSTOM_CACHE_DIR` to a writable scratch path.
- `adam_atan2` is a vendored local module; no pip dependency needed.
- Data location: `/scratch/project_465002606/data/sampled_original_sapient`
  (finalized `tokens.npy` ~712 GB present as of 2026-06-17). Account
  `project_465002606`; GPU partitions `dev-g`, `small-g`, `standard-g` (mi250:8).

Runnable recipe: `scripts/lumi_train_original_sapient_l.sbatch` (auto-resumes
from the newest `step_*` checkpoint; `checkpoint_step_interval=2000`).

FlashAttention 3 was NOT used: it is NVIDIA Hopper-only and cannot run on MI250X.
