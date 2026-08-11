---
type: Policy Record
title: Expansion Policy for Common Pile and Danish DynaWord Exports
description: 'Part of Data Mix Policy: Expansion Policy for Common Pile and Danish
  DynaWord Exports.'
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
# Expansion Policy for Common Pile and Danish DynaWord Exports

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Added on 2026-06-18. Confidence: high for the policy decision and local export
layout; medium for source availability until the source Parquet mirrors are
reconfirmed or re-downloaded.

The eight existing `common-pile-*` and `danish-dynaword-*` Hugging Face
datasets should be expanded in place, not published as `v2`, `diverse`, or
renamed variants. These datasets have not yet been consumed externally, so the
published repos can be updated freely.

Expansion rules:

- keep the current uploaded rows as accepted seed rows;
- sample additional source rows from other available files/components in
  `common-pile` and `danish-foundation-models/danish-dynaword`;
- use source-balanced and length-balanced sampling instead of a prefix scan;
- generate the same four task families: denoising, span filling, prefix
  continuation, and paragraph reordering;
- judge the new candidate rows with the same audit workflow;
- concatenate only accepted new rows with the existing accepted upload rows;
- update the same HF dataset repos and README/audit summaries in place.

Local note: `export-upload/` contains the compact uploaded rows, while
`export/` still contains larger generated data and audit artifacts. The compact
chat rows contain only `messages`, so future expansion should track source
provenance in aggregate metadata/audit summaries and should preserve the
existing accepted rows byte-for-byte unless there is an explicit cleanup
decision.

Preparation update, 2026-06-18. Confidence: high from local script execution
and Parquet metadata inventory. The expansion prep script is:

```bash
cd /work/dfm/HRM-Text
python scripts/prepare_common_dynaword_expansion.py
```

It writes a timestamped runbook under:

```text
logs/data_audits/common_dynaword_expansion/<timestamp>/
```

The 2026-06-18 runbook at
`logs/data_audits/common_dynaword_expansion/20260618T103912/` found 477
Common Pile source Parquet files across 12 source families and 45 DynaWord
source Parquet files across 45 source families. It also wrote
`target_tokens_by_dataset.json`, which raises the expansion audit targets to
200M estimated tokens for denoising/span/prefix tasks and 100M for paragraph
reordering tasks.

`scripts/rebalance_export_audits.py` now accepts
`--target-tokens-by-dataset <json>` so expansion audits can continue beyond the
old 100M/50M completion thresholds. `scripts/prepare_export_upload_from_export.py`
copies selected rebuilt `export/` folders into `export-upload/` as physical
copies, not links, before in-place HF upload.
