---
type: Policy Record
title: DFM5 Danish Include Set
description: 'Part of Data Mix Policy: DFM5 Danish Include Set.'
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
# DFM5 Danish Include Set

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Last updated: 2026-06-12
Confidence: high
Scope: DFM5 policy/config decision implemented locally in
`data_io/prefix_config_dfm5.yaml`, `config/data/dfm5.yaml`, and
`scripts/build_tokenized_dfm5_tree.py`.

DFM5 keeps the current source-filtered Sapient subset at original Sapient task
names and original Sapient sampling rates, then adds the following Danish
families:

- `laerebogen_with_followups`
- `lexdk`
- `opus`
- all currently tokenized `oliverkinch_*` datasets, including translation
  datasets because the decision was phrased as `oliverkinch_*`
- all currently tokenized `synquid*` datasets, including translation and
  WildChat-Qwen messages because the decision was phrased as `synquid*`
- local `dbc` converted instruction/reference datasets
- exported Danish DynaWord task datasets:
  `export/danish-dynaword-denoising`,
  `export/danish-dynaword-paragraph-reordering`,
  `export/danish-dynaword-prefix-continuation`, and
  `export/danish-dynaword-span-filling`

DFM5 intentionally does not link the older raw `danish_dynaword__`,
`dfm2_dynaword_*`, or `dfm4_dynaword_paragraph_reorder__` tokenized tasks. The
four exported DynaWord task datasets supersede the older internal DynaWord task
trees for this mix. Update, 2026-06-12: `lexdk__` and `opus__` are now included
explicitly after user approval.
