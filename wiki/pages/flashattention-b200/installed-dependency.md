---
type: Technical Reference
title: Installed Dependency
description: 'Part of FlashAttention on B200: Installed Dependency.'
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
# Installed Dependency

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Accelerator dependencies are now optional rather than unconditional base requirements:

```text
CPU:       pyproject extra cpu
MPS:       pyproject extra mps
SM90/H100: requirements-sm90.txt / pyproject extra sm90
SM100/B200: requirements-sm100.txt / pyproject extra sm100
```

Base `pyproject.toml` dependencies no longer install `torch`, FlashAttention, `vllm`, or server dependencies unconditionally. Use accelerator extras for the runtime backend and separate `eval` / `server` extras for evaluation and API serving. Base `requirements.txt` no longer installs a FlashAttention package, so Apple/MPS environments do not try to build CUDA extensions.
