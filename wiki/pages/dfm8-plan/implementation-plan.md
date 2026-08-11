---
type: Plan Record
title: Implementation Plan
description: 'Part of DFM8 Plan: Implementation Plan.'
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
# Implementation Plan

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-09. Confidence: medium. This is the concrete build plan for
turning DFM8 from planning notes into a sampleable dataset.

DFM8 should be built as a full Gemma4-template dataset, not as an incremental
patch over DFM7. The implementation should keep all DFM8 paths separate until
validation succeeds:

- raw/downloaded sources: `data/downloads/datasets/*`
- DFM8 converted chat sources: `data/dfm8_chat_sources`
- DFM8 tokenized sources: `data/tokenized_dfm8`
- DFM8 sampled epochs: `data/sampled_dfm8`
- DFM8 sampling config: `data_io/prefix_config_dfm8.yaml`
- training config: `config/data/dfm8.yaml`
- validation logs: `logs/dfm8_*`

High-level build order:

1. Freeze source policy.
   - Include all DFM7 sources that were accepted after the DFM7 fixes unless
     superseded by a DFM8 converter.
   - Include OpenHermes 2.5 as an allowed English SFT source.
   - Fully include `giannor/dala_tv2r_it` and
     `giannor/gec_dala_tv2r_it`.
   - Include `kobprof/skolegpt-instruct` if local row inspection confirms it
     is useful and not mostly redundant.
   - Include the DFM7 native tool-call sources, but regenerate/fix any source
     whose rendered assistant target is not one canonical Gemma4/native tool
     call representation.
2. Download/update raw sources.
   - Extend `scripts/download_training_datasets.py` with DFM8 groups for
     `openhermes`, `giannor_tv2r_instruction`, `skolegpt`, and any new
     synthetic/exported sources.
   - Keep HF dataset revisions in the manifest where practical.
   - Do not write credentials into scripts or wiki pages.
3. Build DFM8 source converters.
   - Add a DFM8 source-tree builder rather than overloading
     `scripts/build_dfm7_chat_source_tree.py`.
   - Every converted row should become a Gemma4-chat source row with explicit
     analytics tags: language, source family, task family, answer contract,
     tool-use contract, and synthetic/teacher/deterministic origin.
   - Render sample rows through `data_io/chat_templates/gemma4_native_chat.jinja`
     before tokenization and fail fast on malformed rows.
4. Run source audits before tokenization.
   - Math audit: boxed/freeform/MCQ/prose/mixed-format rates.
   - Tool audit: valid top-level tools, valid assistant `tool_calls`, no XML
     leftovers, no Python-call string targets, no repeated calls unless intended.
   - Format audit: exact JSON/table/bullet/sentence-count contracts.
   - Danish grammar audit: DaLA/GEC corruption types and expected responses.
   - OpenHermes audit: source/category counts and examples.
5. Tokenize.
   - Use the Gemma4 tokenizer, not the old Sapient BPE tokenizer.
   - Use the non-Rust/Gemma-compatible tokenizer path that handled DFM6/DFM7.
   - Restart partially tokenized files from scratch; do not trust incomplete
     outputs.
6. Sample.
   - Create `data_io/prefix_config_dfm8.yaml` with stable category weights.
   - Produce at least five sampled epochs initially, with the option to append
     more epochs later by copying epoch index files and updating metadata as in
     DFM7.
   - Report source/category token counts before training.
7. Validate sampled rows.
   - Inspect rendered examples from every major category and source.
   - Run a small tokenizer/template smoke to verify BOS/EOS/chat-template
     behavior.
   - Run a source-distribution report by Danish, English, math/code/tool,
     OpenHermes, TV2R-GEC, DynaWord/Common-Pile transforms, tool calling, and
     strict boxed math.
8. Train readiness.
   - Only after the audits pass, add `config/data/dfm8.yaml` pointing to
     `data/sampled_dfm8`.
   - Keep DFM8 W&B runs separate from DFM6/DFM7 unless deliberately resuming
     from a DFM7 checkpoint, in which case the run name should state the data
     switch.

Suggested implementation artifacts:

| File | Purpose |
| --- | --- |
| `scripts/build_dfm8_chat_source_tree.py` | Build symlink/source tree and run DFM8 converters. |
| `scripts/convert_dfm8_openhermes.py` | Convert OpenHermes ShareGPT rows into Gemma4 chat rows with source/category tags. |
| `scripts/convert_dfm8_giannor_tv2r.py` | Convert the two selected TV2R instruction datasets, preserving their `direction`, `content`, `response`, and corruption metadata. |
| `scripts/audit_dfm8_sources.py` | Unified source audit for math/tool/format/Danish-GEC/OpenHermes categories. |
| `scripts/report_dfm8_mix.py` | Token and sampled-count report by source and category. |
| `data_io/prefix_config_dfm8.yaml` | Sampling weights/caps. |
| `config/data/dfm8.yaml` | Training data path. |

Validation gates:

- `giannor/dala_tv2r_it` and `giannor/gec_dala_tv2r_it` full inclusion must be
  visible in the final token report. The current estimate is about 281.1M
  rendered tokens across all splits.
- If all TV2R splits are included, existing DaLA/GEC-DaLA eval metrics should
  be marked as train-contaminated for DFM8. Create a new held-out diagnostic
  from another source or a freshly generated small set if we need clean Danish
  grammar evals.
- OpenHermes full inclusion must be visible in the token report. Current
  estimate is about 430M rendered tokens.
- Strict boxed freeform math must have enough sampled weight to dominate
  mixed-format freeform math.
- Native tool-calling samples must pass rendered-template audits before
  tokenization.
- Broad Common Pile and DynaWord transformed data must be sampled by accepted
  rows and balanced targets, not by whichever files happened to finish earlier.
