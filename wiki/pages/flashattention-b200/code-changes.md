---
type: Technical Reference
title: Code Changes
description: 'Part of FlashAttention on B200: Code Changes.'
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
# Code Changes

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

- `models/accelerator.py`
  - owns the process-local accelerator selector.
- `models/flash_attention_prefixlm_v2.py`
  - keeps the original SM90/H100 FA3 PrefixLM implementation from commit `00b4fe5` in the historical public module.
  - adds only a thin accelerator check at the public `flash_attn_varlen_prefixlm` entrypoint; non-SM90 backends are delegated to `models/flash_attention_prefixlm_dispatch.py`.
  - keeps the `compute_aux_seq_tensors_scalars` entrypoint used by the dataset.
- `models/flash_attention_prefixlm_dispatch.py`
  - owns accelerator dispatch for SM100, MPS, CPU, and dense fallback implementations.
- `models/flash_attention_prefixlm_fa4.py`
  - owns the SM100/B200 FlashAttention 4/CUTE PrefixLM implementation.
- `models/flash_attention_prefixlm_dense.py`
  - owns the dense PyTorch SDPA PrefixLM fallback used by `mps`, `cpu`, and `none` when the Metal kernel does not support the current tensors.
- `models/flash_attention_prefixlm_common.py`
  - owns shared PrefixLM sequence metadata unpacking, active tensor slicing, shifted cu-seqlens construction, and sequence-index construction.

- `models/layers.py`
  - removed `flash_attn_with_kvcache`
  - cache path updates key/value tensors and uses `torch.nn.functional.scaled_dot_product_attention`
- `pretrain.py`
  - uses `accelerator_type` to select device, disable CUDA-only distributed/FSDP paths for MPS/CPU, and avoid torch.compile when requested.
  - supports `gradient_accumulation_steps`; `global_batch_size` remains the effective optimizer token batch, and the physical per-rank microbatch is `global_batch_size / world_size / gradient_accumulation_steps`. The code raises an error if this division is not exact.
