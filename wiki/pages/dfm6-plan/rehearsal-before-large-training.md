---
type: Plan Record
title: Rehearsal Before Large Training
description: 'Part of DFM6 Plan: Rehearsal Before Large Training.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# Rehearsal Before Large Training

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Before committing a full DFM6 run:

1. Convert a tiny representative sample with the Gemma tokenizer/template.
2. Tokenize and sample it.
3. Decode samples and inspect formatting.
4. Train a short smoke model.
5. Export/serve the checkpoint.
6. Run a small standard, DFM, EuroEval, and tool-calling smoke eval.

This catches tokenizer/template/export/eval failures before spending a large training budget.
