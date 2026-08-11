---
type: Experiment Record
title: Full Plan
description: 'Part of Original L Reproduction: Full Plan.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction.md
---
# Full Plan

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

1. Let original Sapient tokenization finish.
2. Verify tokenized file count and output size.
3. Sample original Sapient tokenized data with the original `data_io/prefix_config.yaml`.
4. Inspect `data/show_analytics_original_sapient.md`.
5. Launch the L reproduction run with `data=original_sapient`.
6. Save checkpoints under a reproduction-specific path.
7. Evaluate/export from that checkpoint path, not from mixed-corpus checkpoints.
