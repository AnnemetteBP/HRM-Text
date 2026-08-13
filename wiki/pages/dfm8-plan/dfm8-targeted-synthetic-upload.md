---
type: Plan Record
title: DFM8 Targeted Synthetic Upload
description: 'Part of DFM8 Plan: DFM8 Targeted Synthetic Upload.'
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
# DFM8 Targeted Synthetic Upload

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-11. Confidence: high from local upload command exit status,
`export-upload-dfm8-synthetic/build_summary.json`, and Hugging Face commit URLs
printed by the uploader.

The completed DFM8 targeted synthetic generation produced `4,800,000`
candidate rows. The audit wrote `4,580,233` decisions for generated rows that
passed the generator-side `ok` check. Of those audited decisions, `3,809,300`
had `keep=true` and `770,933` had `keep=false`. The upload builder emitted
only the `keep=true` rows across six standalone Hugging Face dataset repos
under `schneiderkamplab`.

The successful upload command was run from `/work/dfm/HRM-Text` with the token
provided only via the `HF_TOKEN` environment variable:

```bash
PYTHONPATH=/work/dfm/HRM-Text/dfm8_synthetic \
  python -m dfm8_synthetic.cli upload \
    --root export-upload-dfm8-synthetic \
    --org schneiderkamplab \
    --commit-message "Upload complete DFM8 targeted synthetic datasets"
```

Upload log:

```text
logs/hf_upload_dfm8_synthetic_20260711T191006.log
```

Uploaded repos and commits:

| Dataset | Accepted rows | Commit |
| --- | ---: | --- |
| `schneiderkamplab/dfm8-synthetic-code-debugging` | `340,711` | `87e99f9815c1c4b484fecb4485a24e5c18277b1b` |
| `schneiderkamplab/dfm8-synthetic-constrained-format-following` | `838,905` | `61850112550ef6631d04f89eb575b7bddc80cbd2` |
| `schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls` | `825,861` | `3b528aa7510d3a7a5fea22a2b33e89b1a1a0d09c` |
| `schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat` | `414,196` | `e345d051a5d8714975de3bb19b137e357d76d92c` |
| `schneiderkamplab/dfm8-synthetic-native-tool-calling` | `836,675` | `3c2d177835beb79749a45143fd250fcedad5a6c9` |
| `schneiderkamplab/dfm8-synthetic-strict-math-answer-contract` | `552,952` | `14ff86ffae606f6dee4e959d0a4fe2c5a3b5c1bd` |

Do not store Hugging Face tokens in repo files or wiki pages.
