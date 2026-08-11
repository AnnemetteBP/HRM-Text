---
type: Technical Reference
title: Compression
description: 'Part of Model Architecture: Compression.'
tags:
- architecture
- hrm
- crm
- checkpoints
- inference
status: stable
last_updated: 2026-07-23
confidence: high
part_of: /pages/model-architecture.md
---
# Compression

Part of [Model Architecture](/pages/model-architecture.md).

There is no architectural compression between levels. Both levels use full token-sequence tensors and normal attention over the packed PrefixLM sequence. Any "hierarchy" currently comes from iterative cross-injection and truncated backpropagation scheduling, not from a shorter segment-level representation.
