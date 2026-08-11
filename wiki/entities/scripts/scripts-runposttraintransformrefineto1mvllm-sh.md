---
type: Software Reference
title: '`scripts/run_posttrain_transform_refine_to_1m_vllm.sh`'
description: 'Part of Script Entities: `scripts/run_posttrain_transform_refine_to_1m_vllm.sh`.'
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
# `scripts/run_posttrain_transform_refine_to_1m_vllm.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-08. Confidence: high for shell syntax and launch; medium for
end-to-end completion until the active run finishes.

All-8-GPU orchestration for reaching the `posttrain_transform_refine`
`1,000,000` synthetic instruction target with strict judge policy. It:

- starts one local vLLM Gemma 4 31B IT server per GPU;
- generates the pending `550,000` source-target-expanded rows with
  `JUDGE_QUALITY=1`;
- audits English-source generated rows in parallel across the eight servers;
- creates retry requests for every row marked `regenerate_required=true`;
