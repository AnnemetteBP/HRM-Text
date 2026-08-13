---
type: Software Reference
title: '`scripts/reproduce_original_sapient_l.sh`'
description: 'Part of Script Entities: `scripts/reproduce_original_sapient_l.sh`.'
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
# `scripts/reproduce_original_sapient_l.sh`

Part of [Script Entities](/entities/scripts.md).

Runnable command ledger for the original Sapient HRM-Text L reproduction run.

Responsibilities:

- download the Sapient cleaned corpus with `scripts/download_training_datasets.py --groups sapient --download`
- tokenize `data/downloads/datasets/sapient_cleaned/data_clustered` and `data/downloads/datasets/sapient_cleaned/data` directly into `data/tokenized_original_sapient`
- verify the expected `5212` tokenized metadata files
- sample into `data/sampled_original_sapient` with `epochs=4`
- launch the L-size `torchrun` command with `data=original_sapient`, `arch/size@arch=L`, `global_batch_size=172032`, and checkpoints under `checkpoints/original_sapient/L`
- use Hydra append overrides for optional train fields: `+project_name=...`, `+run_name=...`, and `+checkpoint_path=...`

Usage:

```bash
scripts/reproduce_original_sapient_l.sh --help
scripts/reproduce_original_sapient_l.sh sample
scripts/reproduce_original_sapient_l.sh train
```
