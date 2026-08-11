---
type: Software Reference
title: '`scripts/resume_posttrain_transform_refine_to_1m_after_generation.sh`'
description: 'Part of Script Entities: `scripts/resume_posttrain_transform_refine_to_1m_after_generation.sh`.'
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
# `scripts/resume_posttrain_transform_refine_to_1m_after_generation.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-09. Confidence: high for local launch output.

Recovery helper for the already-completed phase-1 synthetic generation run. It
assumes the original vLLM teacher servers remain alive on ports `8100`-`8107`
and runs phases 2-4 directly:

- audit English-source generated rows from
  `data/generated_posttrain_transform_refine`;
- build regeneration requests for rows marked by the judge;
- shard and run judged regeneration without restarting the existing servers.

Verified active launch:

```bash
cd /work/dfm/HRM-Text
bash scripts/resume_posttrain_transform_refine_to_1m_after_generation.sh \
  2>&1 | tee logs/posttrain_transform_refine_to_1m_resume_20260609T083026.log
```
