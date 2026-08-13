---
type: Technical Reference
title: In-Epoch Resume Cursors
description: 'Part of Model Architecture: In-Epoch Resume Cursors.'
tags:
- architecture
- hrm
- crm
- checkpoints
- inference
status: stable
last_updated: 2026-07-23
confidence: high
part_of: /pages/model-architecture.md
---
# In-Epoch Resume Cursors

Part of [Model Architecture](/pages/model-architecture.md).

Update 2026-06-20: step and ephemeral checkpoints now record row-cursor resume
metadata in addition to the existing `batch_in_epoch` field. This supports
changing `gradient_accumulation_steps` between interrupted runs without tying
the resume point to the old local dataloader batch size.

Implementation:

- `multipack_sampler.py` keeps the existing `iter()` API unchanged and adds
  `iter_with_info(start_index=0)`, which yields batch indices plus
  `global_row_start`, `global_row_end`, `global_numseq`, and
  `global_batch_totlen`.
- `dataset_new.py` keeps `set_start_batch()` and adds
  `set_start_row_cursor()`.
- `pretrain.py` writes `global_row_cursor_in_epoch`, `local_batch_size`,
  `gradient_accumulation_steps`, and `batch_in_epoch_exact` to
  `checkpoint_state_*.json`.
- Resume remains conservative: same-local-batch checkpoints with
  `batch_in_epoch_exact=true` use the old `batch_in_epoch` path; changed-local
  batch checkpoints, or checkpoints descended from a row-cursor resume, use the
  row cursor.

Validation:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python -m py_compile multipack_sampler.py dataset_new.py pretrain.py
```

A local smoke test with a temporary tiny sampled dataset verified that
`set_start_batch(1)` and `set_start_row_cursor(first_global_row_end)` resume at
the same next global row boundary. Confidence: high.
