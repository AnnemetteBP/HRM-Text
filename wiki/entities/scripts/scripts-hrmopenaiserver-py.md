---
type: Software Reference
title: '`scripts/hrm_openai_server.py`'
description: 'Part of Script Entities: `scripts/hrm_openai_server.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/hrm_openai_server.py`

Part of [Script Entities](/entities/scripts.md).

OpenAI-compatible HTTP shim for one HRM checkpoint.

Responsibilities:

- load one HRM checkpoint epoch with `evaluation.engines.SimpleEngine`
- expose `/health`, `/v1/models`, `/v1/chat/completions`, and `/v1/completions`
- micro-batch concurrent OpenAI-compatible requests with `--batch-size` and `--batch-timeout-ms`
- trim returned text on OpenAI-style stop strings

Dependency note: `fastapi` and `uvicorn` were added to `pyproject.toml` for this shim. Confidence: high.

Verified syntax:

```bash
python -m py_compile scripts/hrm_openai_server.py
```

2026-06-12 EuroEval compatibility update. Confidence: high for local source
inspection and syntax check. EuroEval/LiteLLM sends OpenAI-style
`max_completion_tokens` for generation length limits; EuroEval's task configs
set short limits for classification/multiple-choice tasks and larger limits
for summarization, translation, instruction following, etc. The HRM
OpenAI-compatible server previously only read `max_tokens`, so
`max_completion_tokens` was silently ignored by Pydantic and missing requests
fell back to the server `--max-context` cap. `scripts/hrm_openai_server.py` now
accepts both `max_tokens` and `max_completion_tokens`, preferring
`max_tokens` if both are supplied. Verification:

```bash
cd /work/dfm/HRM-Text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile scripts/hrm_openai_server.py
```
