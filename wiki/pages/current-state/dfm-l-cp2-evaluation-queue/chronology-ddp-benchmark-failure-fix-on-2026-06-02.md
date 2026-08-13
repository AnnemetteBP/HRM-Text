---
type: Operational Record
title: DDP benchmark failure/fix on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DDP benchmark
  failure/fix on (2026-06-02).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# DDP benchmark failure/fix on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DDP benchmark failure/fix on 2026-06-02. Confidence: high.

The first `dfm4-L-ddp` launch failed before completing the first step with FA4:

```text
AssertionError: inputs must be float16, bfloat16, fp8 e4m3fn, or fp8 e5m2
```

The cause was that the new DDP path left the model in fp32. The FSDP path uses
FSDP mixed precision to provide bf16 parameters/activations, but DDP has no such
policy here. The DDP branch in `create_model_and_carry` now casts the model to
`fwd_bwd_dtype` before wrapping it in `DistributedDataParallel` and before
creating AdamATan2. Validation after the fix: `python -m py_compile
pretrain.py` and `git diff --check`.
