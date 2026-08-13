---
type: Software Reference
title: '`export/transformations-*/recreate_dataset.py`'
description: 'Part of Script Entities: `export/transformations-*/recreate_dataset.py`.'
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
# `export/transformations-*/recreate_dataset.py`

Part of [Script Entities](/entities/scripts.md).

Updated on 2026-06-11. Confidence: high for local file inspection and
`py_compile`.

Each transformation export folder has a self-contained recreation script using
only Python standard-library modules. The script defaults to local
`seeds/source_texts.jsonl.gz`, reads `generation_config.json` for the
source/target language defaults, calls an OpenAI-compatible teacher endpoint,
and judges generated candidates by default. It writes only judge-accepted rows
unless `--no-judge` is explicitly passed for debugging.

Smoke command shape from inside a transformation export folder:

```bash
python recreate_dataset.py \
  --base-url http://127.0.0.1:8100/v1 \
  --model posttrain-gemma-teacher \
  --rows 1000 \
  --output generated/train.jsonl.gz
```

Exact recreation is not expected because teacher sampling and judge outcomes
can vary, but seed selection, prompt templates, and task order are deterministic
for a fixed `--seed`.
- generates judged replacement rows into a separate regeneration output root;
- keeps servers alive across phases and tears them down on script exit.

Default important paths:

```text
MISSING_SHARD_ROOT=data/synthetic_request_shards_posttrain_transform_refine_v3_missing
GENERATED_ROOT=data/generated_posttrain_transform_refine
AUDIT_ROOT=logs/posttrain_transform_refine_generation/audits_to_1m_<timestamp>
REGEN_REQUEST_ROOT=data/synthetic_requests_posttrain_transform_refine_regen_from_audit
REGEN_SHARD_ROOT=data/synthetic_request_shards_posttrain_transform_refine_regen_from_audit
REGEN_GENERATED_ROOT=data/generated_posttrain_transform_refine_regen_from_audit
```

Launched on 2026-06-08 in tmux session `posttrain_to_1m`.
