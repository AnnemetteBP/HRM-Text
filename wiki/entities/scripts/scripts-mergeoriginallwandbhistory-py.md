---
type: Software Reference
title: '`scripts/merge_original_l_wandb_history.py`'
description: 'Part of Script Entities: `scripts/merge_original_l_wandb_history.py`.'
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
# `scripts/merge_original_l_wandb_history.py`

Part of [Script Entities](/entities/scripts.md).

Local-only W&B datastore merge helper for the original Sapient L run.

Responsibilities:

- read the original training W&B datastore for run `76sygh18`
- read the corrected eval backfill datastore for the same run
- omit the first bad eval backfill datastore with dotted metric keys
- write a merged local `.wandb` datastore and an inspection-friendly `history.jsonl`
- copy local `files/` and `logs/` sidecars from the original training run
- optionally rewrite local run id, project, and display name for a separate upload
- drop bad dotted eval summary updates from the corrected eval-backfill datastore before writing the merged copy
- avoid mutating or deleting any original W&B run directory

Verified command:

```bash
cd /work/dfm/HRM-Text
scripts/merge_original_l_wandb_history.py --force
```

Prepare a separate local copy for the ongoing mixed-run project:

```bash
scripts/merge_original_l_wandb_history.py \
  --output-dir wandb/merged-20260524-76sygh18-clean-for-ongoing \
  --target-project "Original Plus Mixed Danish Instruction Rich L" \
  --target-run-id origLclean \
  --target-run-name original-sapient-L-clean-history \
  --force
```

Verified output:

```text
wandb/merged-20260524-76sygh18-clean/run-76sygh18-clean-merged.wandb
wandb/merged-20260524-76sygh18-clean/history.jsonl
wandb/merged-20260524-76sygh18-clean/manifest.json
wandb/merged-20260524-76sygh18-clean-for-ongoing/run-origLclean.wandb
```
