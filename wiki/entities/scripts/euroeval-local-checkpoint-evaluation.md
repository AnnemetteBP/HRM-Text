---
type: Software Reference
title: EuroEval Local Checkpoint Evaluation
description: 'Part of Script Entities: EuroEval Local Checkpoint Evaluation.'
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
# EuroEval Local Checkpoint Evaluation

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-12. Confidence: high for local syntax checks and dry-runs;
medium until a full EuroEval run completes against a checkpoint.

`scripts/run_euroeval_on_checkpoint.sh` runs EuroEval against a local HRM
checkpoint through `scripts/hrm_openai_server.py`. The requested default scope
is Danish and English only:

```text
EUROEVAL_LANGUAGES=da,en
```

The wrapper intentionally does not override EuroEval's standard evaluation
policy by default. In particular, it leaves few-shot/zero-shot choice,
`num_iterations`, and `generative_type` unset unless the corresponding
environment variables are explicitly provided. EuroEval's upstream CLI default
is few-shot with 10 iterations, with internal zero-shot fallback for tasks that
require zero-shot evaluation. The wrapper still passes the local API endpoint,
API key, cache directory, max context length, `--save-results`, and the
requested language filters.

Outputs per checkpoint:

```text
logs/euroeval/.../<CKPT_TAG>/server.log
logs/euroeval/.../<CKPT_TAG>/euroeval.log
logs/euroeval/.../<CKPT_TAG>/euroeval_benchmark_results.jsonl
logs/euroeval/.../<CKPT_TAG>/merged_metrics.json
logs/euroeval/.../<CKPT_TAG>/merge_and_wandb_sync.log
```

`scripts/log_euroeval_to_wandb.py` flattens EuroEval JSONL results to W&B
metrics under `euroeval/<lang>/<task>/<dataset>/...` and records
`euroeval/epoch` as the step metric. It filters to `da` and `en` in the
checkpoint wrapper.

Operational update on 2026-06-12. Confidence: high. Installing EuroEval into
the `hrm` conda environment was done directly because editable install of the
repo extra failed under setuptools' flat-layout package discovery:

```bash
uv pip install euroeval
```

This installed `euroeval==17.3.0` and downgraded `scikit-learn` from `1.8.0`
to `1.6.1`. EuroEval's import guard refuses any visible top-level
`flash_attn` package on non-ROCm builds. This conflicts with the local FA4
install, which provides top-level `flash_attn` from the `flash-attn-4`
distribution. For API-only EuroEval, use
`scripts/euroeval_api_no_flash_attn_guard.py`; it hides `flash_attn` only from
EuroEval's import guard in the EuroEval process. The HRM server process still
runs normally with FA4 visible.

Concurrency update on 2026-06-12. Confidence: high for local source inspection
and syntax check. EuroEval 17.3.0's LiteLLM backend hard-codes
`max_concurrent_calls = 20`. `scripts/euroeval_api_no_flash_attn_guard.py` now
supports `EUROEVAL_MAX_CONCURRENT_CALLS`; when set, it monkeypatches
`LiteLLMModel.__init__` after construction to override
`self.buffer["max_concurrent_calls"]`.

Verification:

```bash
cd /work/dfm/HRM-Text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile scripts/euroeval_api_no_flash_attn_guard.py
```

Example launch using larger server and EuroEval concurrency:

```bash
cd /work/dfm/HRM-Text
EUROEVAL_BATCH_SIZE=32 EUROEVAL_MAX_CONCURRENT_CALLS=32 \
  scripts/run_original_sapient_l_euroeval_epochs.sh
```
