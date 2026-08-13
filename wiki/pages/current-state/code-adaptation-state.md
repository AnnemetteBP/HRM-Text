---
type: Operational Record
title: Code Adaptation State
description: 'Part of Current State: Code Adaptation State.'
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
# Code Adaptation State

Part of [Current State](/pages/current-state.md).

- `models/flash_attention_prefixlm_v2.py` now uses FA4 varlen APIs.
- `models/layers.py` now uses PyTorch SDPA for cache attention instead of FA3 kvcache.
- Py-compile and CUDA smoke tests passed earlier for PrefixLM attention and cache attention.
