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
last_updated: 2026-08-17
confidence: high
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

## TV2R provenance resolution (2026-08-17)

The earlier claim that the underlying TV2R source was untraced is now
**superseded** for these two selected derivatives:

- Their 1,914,691 rows expand exactly 492,063 unique clean sentences. DaLA
  pairs clean/corrupted sentences with `ja`/`nej`; GEC-DaLA maps corrupted
  sentences back to the clean sentence.
- The clean sentences trace to the `tv2r` component of Danish Gigaword, carried
  into Danish DynaWord. The pinned local DynaWord revision is
  `7e97f781b6843de62827275d5facc0a8799df80c`; it contains 49,134 source
  documents with stable IDs such as `tv2r_114943`.
- An exact checked example maps the Giannor sentence beginning `Line Siig,
  frivillig Sex & Samfund-Ung` to DynaWord article `tv2r_114943`.
- The pinned DynaWord TV2R card identifies TV 2 Regionerne as content owner and
  declares CC-BY-SA 4.0. Its embedded prose says CC-BY 4.0, so project policy is
  to retain the stricter CC-BY-SA treatment rather than resolve the
  inconsistency in the permissive direction.

The instruction datasets do not preserve the upstream `tv2r_*` article ID.
Exact per-row article mappings can be reconstructed from clean-text matching,
but they are not directly joinable from the converted metadata. Preserve TV2R,
Danish Gigaword, and DynaWord attribution with any dataset/model documentation
and retain the source revision above.

The earlier concern about the unlicensed Giannor-added layer is also
**superseded as of 2026-08-17**. The project owner confirmed that Giannor works
as part of the DFM project, so the sentence selection, synthetic
corruption/correction metadata, labels, and instruction wrappers are treated as
DFM project-generated contributions. No Article 3 fallback is required for
these two datasets; the retained TV2R text remains subject to the source
attribution and conservative CC-BY-SA treatment described above.
