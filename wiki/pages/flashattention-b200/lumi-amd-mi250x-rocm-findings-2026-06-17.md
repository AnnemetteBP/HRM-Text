---
type: Technical Reference
title: LUMI / AMD MI250X (ROCm) Findings, 2026-06-17
description: 'Part of FlashAttention on B200: LUMI / AMD MI250X (ROCm) Findings, 2026-06-17.'
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
# LUMI / AMD MI250X (ROCm) Findings, 2026-06-17

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Confidence: high for live LUMI probes over `ssh lumi` (login node `uan01`,
user `frommoge`); medium for runtime GPU behavior not yet tested on a GPU node.

Context: a request to run the L training on LUMI "using FlashAttention 3"
is not viable. LUMI-G is AMD MI250X (CDNA2 / `gfx90a`, ROCm/HIP), and FA3 is
an NVIDIA Hopper (SM90) CUDA kernel. The user agreed to drop FA3 and build a
ROCm backend instead.

Live LUMI facts:

- Project `465002606` has `/scratch`, `/project`, `/flash` symlinks and GPU
  partition access to `dev-g`, `small-g`, `standard-g`, all `gpu:mi250:8`
  (8 GCDs/node). Account string for Slurm is `project_465002606`.
- Dataset path `/scratch/project_465002606/data/sampled_original_sapient/`
  is still being written: a temp `.tokens.npy.Omv9Zw` (~522 GB) was actively
  growing, `epoch_0..3` dirs exist, and `metadata.json` reports
  `max_seq_len=4097`, `total_length=14035178678`, `vocab_size=65536`. The
  final `tokens.npy` is not yet in place; training cannot start until the temp
  file is renamed/finalized.
- ROCm module: `rocm/6.3.4` (default) plus older versions.
- Prebuilt PyTorch-ROCm Singularity containers exist under
  `/appl/local/containers/sif-images/`. Newest tested:
  `lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif`.
- That container reports `torch 2.7.1+rocm6.2.4`, Python `3.12.11`,
  HIP `6.2.41134`, and ships `flash_attn 2.7.3` with
  `flash_attn.flash_attn_interface.flash_attn_varlen_func` available. The
  FA2 ROCm CK backend supports MI250X, so the CK varlen kernel is available
  in-container without a custom build.

Implication: add a new `rocm`/`gfx90a` accelerator backend that mirrors the
existing FA4 PrefixLM split-call structure but calls FA2 `flash_attn_varlen_func`.
PyTorch-ROCm exposes AMD GPUs as `torch.cuda` (`device.type == "cuda"`) and uses
RCCL via `backend="nccl"`, so the device/memory/FSDP plumbing mostly carries over;
the CUDA-capability checks in `models/accelerator.py` need a HIP-aware branch.
