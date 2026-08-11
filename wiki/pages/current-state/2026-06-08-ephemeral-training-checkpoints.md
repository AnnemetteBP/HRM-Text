---
type: Operational Record
title: 2026-06-08 Ephemeral Training Checkpoints
description: 'Part of Current State: 2026-06-08 Ephemeral Training Checkpoints.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-08 Ephemeral Training Checkpoints

Part of [Current State](/pages/current-state.md).

Confidence: high for local code inspection and validation.

`pretrain.py` now supports opt-in ephemeral resumability checkpoints:

```text
ephemeral_checkpoint_step_interval: null
```

Set this to an integer `N` to save a resumability checkpoint every `N`
optimizer steps. Ephemeral checkpoints use the tag `ephemeral_step_<step>` and
the same checkpoint format as the run (`fsdp2_ephemeral_step_<step>` for
sharded, `unsharded_ephemeral_step_<step>.pt` for unsharded). After a
successful ephemeral save, older `ephemeral_step_*` artifacts are deleted. If
the same step also writes a regular `checkpoint_step_interval` checkpoint, the
regular `step_<step>` checkpoint is kept and older ephemeral checkpoints are
deleted instead of writing a duplicate ephemeral copy.

Resume accepts the same checkpoint path plus:

```text
resume_checkpoint_tag=ephemeral_step_<step>
```

The inference loader also accepts `ckpt_tag=ephemeral_step_<step>` for smoke
tests or evals. Validation run locally:

```bash
cd /work/dfm/HRM-Text
python -m py_compile pretrain.py simple_inference_engine.py
```
