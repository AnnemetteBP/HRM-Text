---
type: Plan Record
title: Danish Linguistic Acceptability And GEC Data
description: 'Part of DFM8 Plan: Danish Linguistic Acceptability And GEC Data.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# Danish Linguistic Acceptability And GEC Data

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-09. Confidence: medium from Hugging Face API/card metadata and
sampled token estimates; high for the inspected schema fields.

Relevant `giannor/*` datasets should be considered for DFM8, but mostly as
Danish linguistic-acceptability, grammar-correction, and diagnostic-eval data,
not as large general instruction data.

Observed namespace shape:

- `giannor/dala`, `giannor/dala_medium`, `giannor/dala_large`,
  `giannor/dala_label_da`: Danish linguistic acceptability rows with `text`,
  `corruption_type`, and label fields. `giannor/dala` is CC-BY-4.0 and has
  train/validation/test/full-train style splits.
- `giannor/dala_gen_v2`, `giannor/dala_gen_v3`,
  `giannor/dala_gen_large_v3`, `giannor/dala_gen_large_v3_ci`,
  `giannor/dala_gen_tv2r`: paired `original`/`corrupted` rows with
  `corruption_type` and affected-token fields. These are candidates for
  Danish correction/rewrite SFT if license/provenance checks pass.
- `giannor/dala_tv2r_it` and `giannor/gec_dala_tv2r_it`: the selected TV2R
  instruction-formatted DaLA/GEC-DaLA datasets for DFM8. Local HF parquet
  metadata inspection on 2026-07-09 found train/validation/test splits and
  instruction-shaped rows with `direction` plus nested `samples.content` and
  `samples.response`.
- `giannor/dala_tv2r` and `giannor/dala_gen_tv2r`: non-instruction base
  variants. Keep as fallback sources for custom converters, but prefer the
  `*_it` instruction variants for DFM8.

Token estimates using the DFM6/DFM7 Gemma4 HF export tokenizer and rendered
Gemma4-chat rows:

| Dataset | Rows, all splits | Estimated tokens, all splits | Estimated train tokens |
| --- | ---: | ---: | ---: |
| `giannor/dala_tv2r_it` | 984,126 | 72.1M | 57.7M |
| `giannor/gec_dala_tv2r_it` | 930,565 | 209.1M | 167.3M |
| Combined selected TV2R instruction data | 1,914,691 | 281.1M | 225.0M |

DFM8 handling:

1. Fully include `giannor/dala_tv2r_it` and
   `giannor/gec_dala_tv2r_it` in DFM8 unless a row-level validation error is
   found. "Fully" here means all train/validation/test rows, so current
   DaLA/GEC-DaLA evals must be labeled train-contaminated for DFM8.
2. Preserve the instruction-tuned row structure:
   - user prompt = `direction` plus `samples.content`;
   - assistant target = `samples.response`;
   - metadata = `corruption_type`, affected-token fields when present, split,
     and source dataset.
3. Keep the non-instruction `dala_tv2r`/`dala_gen_tv2r` base variants as
   fallback only. Do not duplicate them in DFM8 unless we deliberately build a
   separate custom correction/acceptability converter.
4. Add DFM8 diagnostic eval slices by `corruption_type`, because recent smoke
   tests suggest Danish grammar/correction can improve even when aggregate
   Danish headline averages are nearly flat.
5. Cap these rows as a language-quality/GEC slice if the final DFM8 target size
   is small, but include every row at least once when possible. They should
   improve Danish grammar sensitivity, not dominate broad Danish instruction
   following.
