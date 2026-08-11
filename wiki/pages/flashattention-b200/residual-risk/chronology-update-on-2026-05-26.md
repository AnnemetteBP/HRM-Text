---
type: Technical Reference
title: Update on (2026-05-26)
description: 'Chronological record from Residual Risk: Update on (2026-05-26).'
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
# Update on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Update on 2026-05-26: `models/accelerator.py` now owns runtime accelerator availability validation, not just name-to-device mapping. `sm90`/`sm100` require `torch.cuda.is_available()`, a valid local rank, and matching CUDA major capability `9.x`/`10.x`; `mps` requires `torch.backends.mps.is_available()`; `cpu` and `none` resolve to CPU and are always valid. The debug training script can still bypass validation for its explicit `--allow-mps-cpu-fallback` development mode. Verified by `py_compile` on `models/accelerator.py`, `pretrain.py`, and `scripts/debug_nan_training_step.py`, plus CPU/none helper checks. Confidence: high.
