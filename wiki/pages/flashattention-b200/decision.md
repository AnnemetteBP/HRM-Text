---
type: Technical Reference
title: Decision
description: 'Part of FlashAttention on B200: Decision.'
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
# Decision

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Use FlashAttention 4, not FlashAttention 3, for B200/SM100.

Update on 2026-05-25: training now has an explicit accelerator selector:

```text
accelerator_type: sm90 | sm100 | mps | cpu | none
```

- `sm90`: restores the original H100/Hopper FA3 PrefixLM implementation from git commit `00b4fe5`, using `flash_attn_3`, direct `torch.ops.flash_attn_3.fwd`, and the custom PrefixLM forward/backward torch library ops.
- `sm100`: uses the current FA4/CUTE path from `flash_attn.cute.flash_attn_varlen_func`.
- `mps`: uses a dense PyTorch SDPA PrefixLM path and single-process training without NCCL/FSDP.
- `cpu` / `none`: uses the same dense PyTorch SDPA PrefixLM path on CPU and single-process training without NCCL/FSDP.

Confidence: high for the inspected git history and local dense-path smoke tests.
