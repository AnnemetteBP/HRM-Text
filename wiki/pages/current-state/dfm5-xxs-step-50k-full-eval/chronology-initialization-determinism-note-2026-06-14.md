---
type: Operational Record
title: Initialization determinism note (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Initialization
  determinism note (2026-06-14).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Initialization determinism note (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Initialization determinism note, 2026-06-14. Confidence: high for inspected
code and local Python signatures; medium for the FSDP2 global-initialization
equivalence implication. `pretrain.py` seeds once before model construction:

```python
torch.random.manual_seed(config.seed + RANK)
```

The model uses PyTorch RNG-consuming initializers such as
`trunc_normal_init_(tensor.normal_())` in `models/common.py`, `LinearInit`,
`ScaledEmbeddingInit`, and `zL_init`. Therefore initialization is deterministic
for a fixed command, seed, world size, rank mapping, PyTorch/CUDA stack, and
model construction order. It is not guaranteed to be bit-identical if world
size or distributed strategy changes.

DDP wraps the model with PyTorch `DistributedDataParallel(..., init_sync=True)`
by default, so DDP should broadcast rank-0 initialized parameters and buffers
to all ranks at construction. In contrast, the current FSDP2 call path uses
`fully_shard(...)`, whose inspected signature has no `sync_module_states`
argument, and the code only explicitly broadcasts buffers before sharding.
That means the current FSDP2 global initial parameter tensor may be assembled
from rank-local initializations seeded with `seed + RANK`, while DDP starts
from rank 0's initialization. Both are deterministic, but they are not
necessarily the same initial model.

FSDP parameter dtype clarification, 2026-06-14. Confidence: high for inspected
code and local PyTorch `MixedPrecisionPolicy` docstring. In the current FSDP
path, `fwd_bwd_dtype=bfloat16` is passed as `MixedPrecisionPolicy.param_dtype`.
This controls the unsharded/all-gathered parameter dtype used for
forward/backward computation. It does **not** mean the optimizer/master
sharded parameters are bf16. PyTorch's local docstring says FSDP keeps
high-precision sharded parameters in memory and the optimizer step uses the
sharded parameter in the original dtype. Since HRM model parameters are
constructed without a bf16 default dtype override, the original trainable
parameter dtype is fp32. Therefore current FSDP training uses fp32 sharded
weights/optimizer parameters with bf16 compute parameters. This is conceptually
closest to DDP with `ddp_params_precision=fp32` plus bf16 autocast, not DDP
with persistent bf16 parameters.
