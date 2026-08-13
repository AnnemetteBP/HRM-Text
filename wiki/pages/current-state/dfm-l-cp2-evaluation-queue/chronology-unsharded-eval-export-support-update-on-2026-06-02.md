---
type: Operational Record
title: Unsharded eval/export support update on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Unsharded eval/export
  support update on (2026-06-02).'
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
# Unsharded eval/export support update on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Unsharded eval/export support update on 2026-06-02. Confidence: high.

`simple_inference_engine.py` now supports both checkpoint layouts:

- sharded: `fsdp2_{tag}` plus `carry_{tag}.0.pt`
- unsharded: `unsharded_{tag}.pt` plus `carry_{tag}.0.pt`

This shared loader is used by standard evals (`evaluation/engines.py`), the
OpenAI-compatible HRM server (`scripts/hrm_openai_server.py`), and HF export
(`conversion/convert_to_hf.py`), so those paths can now load unsharded
checkpoints. Latest-checkpoint auto-detection scans both `fsdp2_epoch_*` and
`unsharded_epoch_*.pt`; explicit tags may be passed as `epoch_1`,
`fsdp2_epoch_1`, `unsharded_epoch_1`, or `unsharded_epoch_1.pt`.

The generic eval scheduler `scripts/schedule_checkpoint_evals.sh` now also
accepts either `fsdp2_${CKPT_TAG}` or `unsharded_${CKPT_TAG}.pt` when waiting
for a checkpoint. It still requires `carry_${CKPT_TAG}.{0..7}.pt` because the
training code stores carry state rank-locally. Validation performed after the
change: `python -m py_compile simple_inference_engine.py
conversion/convert_to_hf.py evaluation/engines.py`, `bash -n
scripts/schedule_checkpoint_evals.sh`, `git diff --check`, and a toy
state-dict smoke test confirming that model weights and AdamATan2 EMA optimizer
state restore through the unsharded `set_state_dict` path.
