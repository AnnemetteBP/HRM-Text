---
type: Operational Record
title: 2026-06-11 Transformation Export Reproducibility Update
description: 'Part of Current State: 2026-06-11 Transformation Export Reproducibility
  Update.'
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
# 2026-06-11 Transformation Export Reproducibility Update

Part of [Current State](/pages/current-state.md).

Confidence: high for local file inspection, script compilation, and row-count
scan.

The four transformation export folders under `export/` now carry practical
reproducibility metadata and seed material:

```text
export/transformations-danish-danish
export/transformations-danish-english
export/transformations-english-danish
export/transformations-english-english
```

Each folder contains:

- `data/*.jsonl.gz`: accepted-only chat `messages` rows.
- `seeds/source_texts.jsonl.gz`: the local source-text pool for that language
  side.
- `seeds/source_manifest.json`: the seed-pool manifest copied from
  `data/posttrain_transform_refine_seed_texts/manifest.json`.
- `generation_config.json`: source/target language, seed count, teacher-model
  family, task families, and selection policy.
- `accepted_selection_summary.json`: row count and accepted-only export rule.
- `recreate_dataset.py`: a standalone Python standard-library script that
  defaults to the local seed file and local language-pair config.

The shipped transformation data is accepted-only by construction:
`scripts/build_expert_exports.py` writes rows only when `accepted is True`,
drops base generated rows whose `id` appears as a regenerated `original_id`,
and includes accepted regeneration rows when present. The resulting exported
row counts are:

```text
transformations-danish-danish:   208,117
transformations-danish-english:  211,401
transformations-english-danish:  246,288
transformations-english-english: 248,474
```

Together these contain `914,280` accepted chat rows. The exported row schema is
uniform:

```json
{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```

The recreation scripts now judge generated candidates by default using the same
OpenAI-compatible endpoint/model unless `--no-judge` is explicitly passed. Only
judge-accepted rows are written in the default path. Exact byte-for-byte
recreation remains impossible in practice because teacher sampling, vLLM
scheduling, and judge decisions can vary; the scripts instead make seed
selection, task order, prompt templates, and local provenance reproducible.

The seed archives are ordinary files, not symbolic links. Locally, matching
language-pair folders share the same inode via hard links to avoid duplicate
disk use, but each uploaded folder still presents a normal
`seeds/source_texts.jsonl.gz` file.
