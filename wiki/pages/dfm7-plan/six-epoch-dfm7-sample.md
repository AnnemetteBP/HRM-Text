---
type: Plan Record
title: Six-Epoch DFM7 Sample
description: 'Part of DFM7 Plan: Six-Epoch DFM7 Sample.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# Six-Epoch DFM7 Sample

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Sampling note, 2026-07-05. Confidence: high for local command output and
byte-for-byte verification.

- The five-epoch DFM7 sample lives at `data/sampled_dfm7` and contains
  `epoch_0` through `epoch_4`.
- A six-epoch extension was sampled into a separate directory,
  `data/sampled_dfm7_6epochs`, rather than mutating the active training
  dataset in place.
- The new Hydra data config is `config/data/dfm7_6epochs.yaml`.
- `data/sampled_dfm7_6epochs/tokens.npy` is a symlink to
  `../sampled_dfm7/tokens.npy`; the sampler was run with `reuse_tokens=true`,
  so the 509G backing token file was not recopied.
- Command used:

```bash
mkdir -p logs data/sampled_dfm7_6epochs
ln -s ../sampled_dfm7/tokens.npy data/sampled_dfm7_6epochs/tokens.npy
cd data_io
PYTHONUNBUFFERED=1 ionice -c2 -n7 nice -n 10 python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm7 \
  output_path=../data/sampled_dfm7_6epochs \
  epochs=6 \
  concat_workers=1 \
  reuse_tokens=true \
  prefix_config_path=prefix_config_dfm7.yaml \
  > ../data/show_analytics_dfm7_6epochs.md \
  2> ../logs/dfm7_sample_6epochs.stderr.log
```

- Resulting metadata:
  - `max_seq_len: 4097`
  - `total_length: 66657268330`
  - tokenizer: `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`
  - chat template: `data_io/chat_templates/gemma4_native_chat.jinja`
- Verification: all first five epoch index arrays in `data/sampled_dfm7` and
  `data/sampled_dfm7_6epochs` are byte-identical:
  `epoch_0..epoch_4/{inst_start,inst_len,resp_start,resp_len}.npy`.
- If we want to keep using `data=dfm7` instead of the separate
  `data=dfm7_6epochs` config, it is sufficient to copy
  `data/sampled_dfm7_6epochs/epoch_5` into `data/sampled_dfm7/epoch_5` and
  optionally replace `data/sampled_dfm7/metadata.json` with the six-epoch
  metadata. The token backing file is the same. The training command must still
  be restarted/resumed with `epochs=6`; an already-started `epochs=5` process
  will not extend itself just because `epoch_5` appears on disk.
- Follow-up, 2026-07-05. Confidence: high for local command output.
  `epoch_5` and the six-epoch `metadata.json` were copied into
  `data/sampled_dfm7`. The active `data=dfm7` path now contains
  `epoch_0..epoch_5`. Verification showed all four copied `epoch_5` arrays and
  `metadata.json` are byte-identical to `data/sampled_dfm7_6epochs`.
- Follow-up cleanup, 2026-07-05. Confidence: high for local command output.
  After the in-place copy was verified, the staging directory
  `data/sampled_dfm7_6epochs` was removed. The temporary Hydra config
  `config/data/dfm7_6epochs.yaml` was also removed so it cannot point to a
  deleted dataset path. The tiny analytics/log artifacts were kept:
  `data/show_analytics_dfm7_6epochs.md` and
  `logs/dfm7_sample_6epochs.stderr.log`.
