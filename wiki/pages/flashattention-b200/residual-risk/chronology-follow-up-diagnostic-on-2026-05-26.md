---
type: Technical Reference
title: Follow-up diagnostic on (2026-05-26)
description: 'Chronological record from Residual Risk: Follow-up diagnostic on (2026-05-26).'
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
# Follow-up diagnostic on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Follow-up diagnostic on 2026-05-26: added `scripts/compare_dense_custom_mps_attention.py` to compare dense MPS attention and the experimental custom MPS attention with identical model weights, carry, batches, and gradient accumulation. The script reports logits, microbatch losses, normalized metrics, and per-parameter gradient differences.

Results with current on-disk code:

```text
initial weights, optimizer_step=1:
  logits max_abs diff on first 512 tokens: 5.48362732e-06
  all four microbatch losses exactly matched at printed precision
  metric loss/accuracy/exact_accuracy matched
  largest gradient max_abs diff: 7.45058060e-09

initial weights, optimizer_step=1161:
  logits max_abs diff on first 512 tokens: 5.06639481e-06
  metric loss diff: 1.90734863e-06
  largest gradient max_abs diff: 1.86264515e-08

dense epoch-1 checkpoint, optimizer_step=1:
  metric loss/accuracy/exact_accuracy matched
  largest gradient max_abs diff: 6.05359674e-09

custom epoch-1 checkpoint, optimizer_step=1:
  metric loss diff: -4.76837158e-07
  metric accuracy/exact_accuracy matched
  largest gradient max_abs diff: 9.77888703e-09
```

Interpretation: the current on-disk custom kernel passes single-step dense equivalence at initial weights, at the bad batch index with initial weights, and at both dense-trained and custom-trained epoch-1 checkpoints. This does not clear the custom kernel used by the bad run, because that run imported `models/flash_attention_prefixlm_mps.py` at startup (`01:06`) and the file was edited later (`03:43`). Current diagnostics therefore test the latest file contents, not necessarily the exact in-memory Metal code that produced `smoke-xxs-custom-mps-bs16384-ga4`. Confidence: high for the diagnostic results; medium for the conclusion that the current file is single-step-correct but the bad run may have used an older in-memory kernel.
