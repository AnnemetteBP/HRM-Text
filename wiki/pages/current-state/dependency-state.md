---
type: Operational Record
title: Dependency State
description: 'Part of Current State: Dependency State.'
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
# Dependency State

Part of [Current State](/pages/current-state.md).

- FlashAttention 3 was attempted but rejected for B200 because the Hopper FA3 path did not produce a viable Blackwell runtime.
- FlashAttention 4 from `Dao-AILab/flash-attention`, subdirectory `flash_attn/cute`, is installed and smoke-tested.
- `requirements.txt`, `docker/requirements/torch_extensions.txt`, `pyproject.toml`, and `uv.lock` were updated for FA4.
