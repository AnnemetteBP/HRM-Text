---
type: Technical Reference
title: Why
description: 'Part of FlashAttention on B200: Why.'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200.md
---
# Why

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

- FA3/Hopper source and wheels were tried and did not produce a viable B200 runtime.
- Local experiments hit kernel/runtime issues and then CUTE/WGMMA architecture macro failures when trying to force SM100 behavior through the Hopper path.
- FA4 has explicit Blackwell/SM100 code paths under `flash_attn/cute`.
