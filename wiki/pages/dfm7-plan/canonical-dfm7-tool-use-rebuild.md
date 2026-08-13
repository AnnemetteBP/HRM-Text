---
type: Plan Record
title: Canonical DFM7 Tool-Use Rebuild
description: 'Part of DFM7 Plan: Canonical DFM7 Tool-Use Rebuild.'
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
# Canonical DFM7 Tool-Use Rebuild

Part of [DFM7 Plan](/pages/dfm7-plan.md).

DFM7 tool-use rebuild, 2026-07-01. Confidence: high from local conversion,
audit, tokenization, and sampling commands.

Supersedes earlier references on this page to `data/sampled_dfm7_next`. The
canonical DFM7 training dataset is now `data/sampled_dfm7`, and
`config/data/dfm7.yaml` points there. The stale `data/sampled_dfm7_next` sample
was removed after the rebuilt canonical sample was verified.

What changed:

- The malformed original DOLCI tool-use rows are still present as tokenized
  inputs but are capped to zero in `data_io/prefix_config_dfm7.yaml` via
  `dolci_instruct_sft_tool_use__` and `dolci_instruct_sft_tool_use_sa__`.
- Corrected DOLCI native tool-use rows are generated as
  `dolci_native_tool_use`. The converter moves embedded function definitions to
  top-level `tools`, removes the old XML `<functions>/<function_calls>` response
  contract, normalizes tool schemas and names, and converts assistant targets to
  structured `tool_calls`.
- Three additional BFCL-shaped/native tool-call sources were integrated:
  `glaive_native_tool_use`, `toolace_native_tool_use`, and
  `xlam_native_tool_use`.
- `dfm_dyna_instruct_when2call` was not converted to native tool-call SFT. It
  remains auxiliary decision/no-call data because it does not contain assistant
  tool-call targets.
- Nemotron Agentic tool-use/search/interactive-agent sources were kept
  unconverted because they already contain top-level tools and structured
  assistant `tool_calls`.

Pre-tokenization audit:

- `scripts/audit_dfm7_tool_sources.py --fail-on-issues --json-out
  logs/dfm7_tool_audit_20260701.json` passed with zero converted-source issues.
- Audited converted source counts:
  - `dolci_native_tool_use`: 228,865 rows, 1,158,664 rendered examples,
    612,343 tool-call examples.
  - `glaive_native_tool_use`: 78,362 rows, 234,279 rendered examples,
    76,248 tool-call examples.
  - `toolace_native_tool_use`: 10,618 rows, 13,132 rendered examples,
    9,713 tool-call examples.
  - `xlam_native_tool_use`: 60,000 rows, 60,000 rendered examples,
    60,000 tool-call examples.
- The audit also checked unconverted tool-adjacent sources. Nemotron Agentic
  retained structured assistant tool calls; `when2call` and `agentic_code` were
  correctly identified as not native tool-call-response supervision.

Tokenization and sampling:

- DFM7 uses the Gemma4 tokenizer and chat template throughout:
  `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json` and
  `data_io/chat_templates/gemma4_native_chat.jinja`.
- Re-tokenization with `scripts/tokenize_chat_template.py` used 16 workers and
  produced 130 DFM7-added tokenized files with 7,460,205 rows and 99,552 skipped
  rows in 884.1 seconds.
- The rebuilt canonical sample metadata:
  `total_length=66657336296`, `max_seq_len=4097`,
  `template_mode=jinja_chat_template`, `enable_thinking=false`.
- `data/show_analytics_dfm7.md` reports 66.657B tokens in the sampled 5-epoch
  training array and 83.964B unique sampled tokens across source repetitions.
- Sampled tool-use additions:
  - `dolci_native_tool_use`: 8.103B sampled tokens over 5 epochs
    (7.403B target tokens).
  - `glaive_native_tool_use`: 777.6M sampled tokens over 5 epochs
    (676.3M target tokens).
  - `toolace_native_tool_use`: 126.1M sampled tokens over 5 epochs
    (110.8M target tokens).
  - `xlam_native_tool_use`: 334.8M sampled tokens over 5 epochs
    (295.9M target tokens).

Operational notes:

- Run DFM7 commands from the `hrm` conda environment. Launching the eval
  scheduler from outside that environment previously caused path/dependency
  issues.
- `scripts/backfill_dfm6_dfm7_xl_splice_wandb.py` now writes the target data
  path as `data/sampled_dfm7` in config and W&B summary metadata.
