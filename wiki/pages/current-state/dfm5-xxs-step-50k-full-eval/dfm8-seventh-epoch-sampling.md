---
type: Operational Record
title: DFM8 Seventh Epoch Sampling
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 Seventh Epoch Sampling.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 Seventh Epoch Sampling

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-17. Confidence: high from local commands and file validation.

The live full DFM8 sample directory was extended from 6 to 7 sampled epochs by
staging a fresh 7-epoch sample with token reuse, then moving only the new
`epoch_6` index directory and staged metadata into the live path:

```bash
mkdir -p data/sampled_dfm8_7epochs_stage
ln -sfn ../sampled_dfm8/tokens.npy data/sampled_dfm8_7epochs_stage/tokens.npy

(
  cd data_io &&
  python sample_tokenized.py \
    tokenized_path=../data/tokenized_dfm8 \
    output_path=../data/sampled_dfm8_7epochs_stage \
    epochs=7 \
    concat_workers=4 \
    prefix_config_path=prefix_config_dfm8.yaml \
    reuse_tokens=true \
    > ../data/show_analytics_dfm8_7epochs_stage.md
)

mv data/sampled_dfm8_7epochs_stage/epoch_6 data/sampled_dfm8/epoch_6
cp data/sampled_dfm8_7epochs_stage/metadata.json data/sampled_dfm8/metadata.json
```

Validation before moving showed `epoch_6` contains the four expected arrays,
each with shape `(218313891,)`, dtype `int64`, and size `1746511256` bytes:
`inst_start.npy`, `inst_len.npy`, `resp_start.npy`, and `resp_len.npy`.

The updated live `data/sampled_dfm8/metadata.json` has
`total_length=70479433697`. The staged token file was only a symlink to the live
`tokens.npy`; no token concatenation was rerun.
