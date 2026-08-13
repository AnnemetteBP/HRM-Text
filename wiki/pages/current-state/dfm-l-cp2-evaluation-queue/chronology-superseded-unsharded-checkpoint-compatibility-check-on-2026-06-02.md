---
type: Operational Record
title: 'Superseded: Unsharded checkpoint compatibility check on (2026-06-02)'
description: 'Chronological record from DFM L CP2 Evaluation Queue: Superseded: Unsharded
  checkpoint compatibility check on (2026-06-02).'
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
# Superseded: Unsharded checkpoint compatibility check on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Superseded: Unsharded checkpoint compatibility check on 2026-06-02. Confidence: high.

The current eval/export path does not yet load `checkpoint_format=unsharded`
checkpoints. `evaluation/engines.py`, `scripts/hrm_openai_server.py`, and
`conversion/convert_to_hf.py` all go through `simple_inference_engine.py`.
That loader currently resolves latest checkpoints by scanning
`fsdp2_epoch_*`, checks for `fsdp2_{tag}` plus `carry_{tag}.0.pt`, and calls
`torch.distributed.checkpoint.load(...)` on `fsdp2_{tag}`. Therefore standard
evals and HF export currently require sharded `fsdp2_{tag}` checkpoints unless
`simple_inference_engine.py` is extended to detect/load `unsharded_{tag}.pt`.
