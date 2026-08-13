---
type: Technical Reference
title: MPS SDPA implementation inspection on (2026-05-25)
description: 'Chronological record from Residual Risk: MPS SDPA implementation inspection
  on (2026-05-25).'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200/residual-risk.md
---
# MPS SDPA implementation inspection on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

MPS SDPA implementation inspection on 2026-05-25:

- In this `torch==2.13.0.dev20260524` wheel, `torch.nn.functional.scaled_dot_product_attention` is a built-in op.
- Dispatch inspection shows an MPS-registered internal op:
  - `aten::_scaled_dot_product_attention_math_for_mps`
  - schema returns `(Tensor, Tensor)`
  - dispatch table has an `MPS` registration.
- The installed headers include MPS decode-attention Metal kernels at:
  - `/Users/petersk/Nobackup/miniconda3/envs/hrm/lib/python3.13/site-packages/torch/include/ATen/native/mps/kernels/DecodeAttention.h`
  - It defines `sdpa_vector`, `sdpa_vector_2pass_1`, and `sdpa_vector_2pass_2`, adapted from MLX.
  - The meta registration comments say `sdpa_vector_2pass_mps` and `sdpa_vector_fast_mps` are intentionally left out of meta handling, pointing to PyTorch issue `177603`.
- Profiling plain `F.scaled_dot_product_attention(q, k, v)` and a boolean-mask call on MPS showed `aten::_scaled_dot_product_attention_math`, `aten::bmm`, `_softmax`, and `_softmax_backward_data`, not `aten::_scaled_dot_product_attention_math_for_mps`.
- Directly calling `torch.ops.aten._scaled_dot_product_attention_math_for_mps(...)` works for a small MPS tensor and returns `(out, None)`.

Interpretation: for the dense PrefixLM fallback we use today, the observed speed likely comes from optimized MPS `bmm`/softmax primitives and PyTorch's generic math SDPA decomposition, not necessarily the dedicated MPS decode-attention vector kernels. Confidence: high for local dispatch/profiler observations; medium for exactly when PyTorch chooses the internal MPS SDPA op.
