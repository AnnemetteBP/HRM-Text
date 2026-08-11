---
type: Operational Record
title: OLMo 3 optimizer/precision comparison (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: OLMo 3 optimizer/precision
  comparison (2026-06-03).'
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
# OLMo 3 optimizer/precision comparison (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

OLMo 3 optimizer/precision comparison, 2026-06-03. Confidence: high.

The local clone at `/tmp/OLMo-core` was inspected for the official OLMo 3
training scripts and optimizer initialization. Official OLMo 3 pretrain and
midtrain configs use `SkipStepAdamWConfig(...)` without passing an optimizer
`dtype` override, and configure data parallelism as HSDP/FSDP2 with
`param_dtype=DType.bfloat16` and `reduce_dtype=DType.float32`. Examples:
`src/scripts/official/OLMo3/OLMo-3-1025-7B-pretrain-1.py` and
`OLMo-3-1025-32B-pretrain.py`.

Superseded clarification: the initial note said OLMo 3 optimizer moments were
"not explicitly forced to fp32." The more precise reading of PyTorch FSDP2 is
that the optimizer parameters are fp32 in this setup. `SkipStepAdamW`
initializes `state["step"]` as `torch.float32`, while `state["exp_avg"]` and
`state["exp_avg_sq"]` are created with `torch.zeros_like(p, dtype=self.dtype)`.
Since the official OLMo 3 configs do not set `SkipStepAdamWConfig(dtype=...)`,
the Adam moment dtype follows the optimizer parameter tensor dtype at state
creation. OLMo-core applies FSDP2 before weight initialization and optimizer
construction; the model constructor default dtype is fp32, and PyTorch FSDP2
documents that `MixedPrecisionPolicy(param_dtype=bf16)` controls the unsharded
forward/backward parameter while "the optimizer step uses the sharded parameter
in the original dtype." Therefore, for the inspected OLMo 3 FSDP2 path, the
optimizer parameter dtype and Adam moments are fp32, forward/backward
materialization is bf16, gradient reduction is fp32, and step counters are fp32.

No EMA path was found in the official OLMo 3 scripts during this inspection.
This is relevant to HRM-Text because the DDP bf16-EMA issue here is specifically
an EMA shadow-weight precision problem, not simply an AdamW moment precision
question.
