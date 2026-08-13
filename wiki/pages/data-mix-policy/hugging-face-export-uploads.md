---
type: Policy Record
title: Hugging Face Export Uploads
description: 'Part of Data Mix Policy: Hugging Face Export Uploads.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# Hugging Face Export Uploads

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Added on 2026-06-17. Confidence: high from successful uploader exit and
`huggingface_hub` repository inspection.

The local `export-upload/` tree currently maps one-to-one to 82 public Hugging
Face dataset repositories under `schneiderkamplab`:

- 12 previously uploaded post-training datasets were updated in place:
  Common Pile denoising/reordering/prefix/span tasks, Danish DynaWord
  denoising/reordering/prefix/span tasks, and the four
  `transformations-*` datasets.
- 70 new Sapient-exclusion synthetic replacement datasets were uploaded as
  `sapient-synth-*` repositories.

All 82 repositories were verified via the Hub API with `repo_type="dataset"`;
each returned `private=False`. The upload was run from `/work/dfm/HRM-Text`
with:

```bash
python scripts/upload_export_upload_to_hf.py \
  --org schneiderkamplab \
  --root export-upload \
  --log logs/hf_export_upload_all_82_20260617.log
```

Do not store the Hugging Face token in repo files or wiki pages.
