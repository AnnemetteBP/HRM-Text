---
type: Experiment Record
title: Separation Rules
description: 'Part of Original L Reproduction: Separation Rules.'
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
# Separation Rules

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

- Do not run `scripts/build_filtered_source_tree.py` or `scripts/convert_filtered_sources.py` for the original reproduction path.
- Do not point original reproduction sampling at `data/tokenized_mixed`.
- Do not point mixed-corpus training at `data/sampled_original_sapient`.
- Keep original checkpoints under `checkpoints/original_sapient/L`.
- Keep future mixed-corpus checkpoints under a separate path, for example `checkpoints/mixed/<run-name>`.
- Keep analytics files separate:

```text
Mixed corpus analytics:          data/show_analytics.md
Original Sapient analytics:      data/show_analytics_original_sapient.md
```
