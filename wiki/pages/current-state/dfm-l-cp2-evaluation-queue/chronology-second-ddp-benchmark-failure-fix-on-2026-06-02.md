---
type: Operational Record
title: Second DDP benchmark failure/fix on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Second DDP benchmark
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
# Second DDP benchmark failure/fix on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Second DDP benchmark failure/fix on 2026-06-02. Confidence: high.

After the dtype fix, DDP failed with:

```text
RuntimeError: Expected to have finished reduction in the prior iteration before starting a new one.
Parameter indices which did not receive grad for rank 0: 96
```

This is expected for HRM BP warmup/control flow: early steps deliberately run
only a subset of H/L cycles under grad, so some parameters are unused on a given
iteration. `pretrain.py` now exposes `ddp_find_unused_parameters`, defaulting to
`true`, and passes it to `DistributedDataParallel(...)`. The flag only affects
`distributed_strategy=ddp`; FSDP remains the default and is unchanged.
Validation after the fix: `python -m py_compile pretrain.py`, `git diff
--check`, and loading `config/cfg_pretrain.yaml` showed
`ddp_find_unused_parameters: true`.
