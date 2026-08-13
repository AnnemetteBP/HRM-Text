---
type: Plan Record
title: Danish Education Data
description: 'Part of DFM8 Plan: Danish Education Data.'
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
# Danish Education Data

Part of [DFM8 Plan](/pages/dfm8-plan.md).

`kobprof/skolegpt-instruct` is a DFM8 candidate. It is described as Danish
instruction SFT from a quality-filtered translated OpenOrca subset plus
SkoleGPT survey instructions.

Plan:

1. Download and inspect rows locally before integration.
2. Convert to the canonical Gemma4 chat-template message format.
3. Cap initially rather than letting OpenOrca-like rows dominate if the active
   mix already contains similar translated instruction data.
4. Tag it as Danish education/general instruction data in analytics so its
   contribution can be tracked separately from other Danish SFT.

Risk: expected marginal value is medium, not guaranteed high, if the dataset is
mostly redundant with existing translated OpenOrca-like content.

Status, 2026-07-09. Confidence: high from local commands and manifests.

Supersedes the earlier 2026-07-09 note that `kobprof/skolegpt-instruct` was
only a planned source. It is now integrated into the local DFM8 build:

- Downloader entry: `scripts/download_training_datasets.py` as
  `kobprof_skolegpt_instruct`, HF repo `kobprof/skolegpt-instruct`, group
  `dfm8`.
- Converter: `scripts/convert_dfm8_skolegpt.py`.
- Converted source:
  `data/dfm8_special_sources/kobprof_skolegpt_instruct/train-00000.jsonl`.
- Tokenized task:
  `data/tokenized_dfm8/kobprof_skolegpt_instruct__train-00000.jsonl`.
- Sampling policy: `data_io/prefix_config_dfm8.yaml` with `repeat: 8`.

Verified local counts:

| Source slice | Rows/examples | Rendered Gemma4 tokens |
| --- | ---: | ---: |
| `kobprof/skolegpt-instruct` total | 21,580 | 10,967,033 |
| upstream `cot` | 4,593 | not separately counted |
| upstream `flan` | 5,571 | not separately counted |
| upstream `niv` | 5,623 | not separately counted |
| upstream `skolegpt_survey` | 162 | not separately counted |
| upstream `t0` | 5,631 | not separately counted |

The source schema is `id`, `system_prompt`, `question`, `response`, `source`.
The converter preserves `system_prompt` as a system message, `question` as the
user turn, and `response` as the assistant target. This keeps the intended
prompt contract instead of relying on generic field guessing.

Operational commands that worked from `/work/dfm/HRM-Text`:

```bash
python scripts/download_training_datasets.py --groups dfm8 --download
python scripts/convert_dfm8_skolegpt.py --force
python scripts/build_dfm8_chat_source_tree.py --force --new-only
TOKENIZERS_PARALLELISM=false python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir data/tokenized_dfm8_jinja \
  --workers 16 \
  --skip-bad-json
python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
```

Current DFM8 special-source integration status:

| Planned DFM8 addition | Local status |
| --- | --- |
| `teknium/OpenHermes-2.5` | downloaded, converted, tokenized; 1,001,551 rows; about 391.5M rendered tokens in current tokenized report |
| `giannor/dala_tv2r_it` | downloaded, converted, tokenized; 984,126 rows; 68.5M rendered tokens |
| `giannor/gec_dala_tv2r_it` | downloaded, converted, tokenized; 930,565 rows; 192.9M rendered tokens |
| `kobprof/skolegpt-instruct` | downloaded, converted, tokenized; 21,580 rows; 11.0M rendered tokens |
| broad Common Pile and DynaWord transformed rows | generated and audit/filtering is in progress; do not treat the current DFM8 sample as final until accepted-row filtering is complete |
