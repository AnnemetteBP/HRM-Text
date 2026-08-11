---
type: Operational Record
title: Possible `data_io` Relocation
description: 'Part of Current State: Possible `data_io` Relocation.'
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
# Possible `data_io` Relocation

Part of [Current State](/pages/current-state.md).

Verified on 2026-05-24. Confidence: high.

`data_io` is currently an untracked nested git checkout at `/work/dfm/HRM-Text/data_io`. Moving it to `/work/dfm/HRM-Text/external/data_io` is mostly a path refactor. Required updates include:

- root docs and agent notes that say `data_io/tokenizer` must be run from `data_io/tokenizer`;
- runnable scripts with hard-coded `REPO_ROOT / "data_io"` or `${REPO_ROOT}/data_io`, especially `scripts/prepare_40b_sapient_plus_danish.py` and `scripts/reproduce_original_sapient_l.sh`;
- cleanup safety guards in `scripts/cleanup_failed_training_run.sh`;
- wiki commands under `wiki/pages/*` and `wiki/entities/*`;
- any shell commands copied from prior notes that reference `data_io/trained_tokenizers/bpe/tokenizer.json`, `data_io/tokenizer`, or `data_io/sample_tokenized.py`.

Prefer adding one canonical variable such as `DATA_IO_DIR=${DATA_IO_DIR:-${REPO_ROOT}/external/data_io}` in scripts rather than scattering the new path.
