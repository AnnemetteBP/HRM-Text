---
type: Plan Record
title: DFM9 Extension (HuggingFace Org Scan)
description: 'Part of DFM9 Plan: DFM9 Extension (HuggingFace Org Scan).'
tags:
- dfm9
- data
- training
- factual-knowledge
- code
status: stable
last_updated: 2026-08-18
confidence: high
part_of: /pages/dfm9-plan.md
---
# DFM9 Extension (HuggingFace Org Scan)

Part of [DFM9 Plan](/pages/dfm9-plan.md).

Update, 2026-08-08. Confidence: high from local file inspection and tokenization output.

## HuggingFace org scan
Scanned 8 HuggingFace organizations for additional Danish/relevant datasets:
`danish-foundation-models` (37 datasets), `schneiderkamplack` (95), `oliverkinch`
(~15), `synquid` (~8), `saattrupdan` (2), `KennethEnevoldsen` (6), `ordbogen` (0),
`odin` (0).

Only 2 new sources were worth adding:

| Source | HF Repo | Rows | License | PII | Decision |
| --- | --- | ---: | --- | --- | --- |
| croco-munin DPO→SFT | `croco-munin/apertus-8b-da-simpo-full-50k` | 49,988 | EU TDM | No | Approved — Danish DPO preference data converted to SFT (chosen response) |
| GSM Symbolic (Danish) | `google/multilingual_gsm_symbolic` | 2,100 | EU TDM | No | Approved — Danish subset of multilingual GSM8K-style math word problems |

Not recommended/skipped: oliverkinch/danish-personas (not instruction data),
synquid/glm-5.2-nvfp4-agentic-traces (too small, no license, overlaps
nemotron_swe), danish-wildchat 4.8M (user messages only), KennethEnevoldsen
(NER/raw text), saattrupdan (e-commerce/doc-NLI).

## Extension conversion
`scripts/convert_dfm9_extension.py` — downloads from HF, converts to
condition/instruction/response parquet.

- **croco-munin**: Input was JSONL (`preference_pairs.jsonl`, 285MB). Each row has
  `chosen` (list of message dicts). Converted: chosen user turn → instruction,
  chosen assistant turn → response, condition="sft".
  Output: `data/converted_sources/croco_munin_da_sft/data/croco_munin_da_50k.parquet`
  (49,988 rows).

- **GSM Symbolic**: Downloaded 59 parquet files, filtered to Danish subset
  (`danish` language column). Converted: question→instruction, answer→response,
  condition="cot".
  Output: `data/converted_sources/gsm_symbolic_da/data/gsm_symbolic_da.parquet`
  (2,100 rows).

## Extension tokenization
Tokenized via `scripts/tokenize_chat_template.py` (same pipeline). 52,088 rows,
0 skipped, 38 seconds, 42.2M tokens total. Output in `data/tokenized_dfm9_ext/`.
Symlinked into `data/tokenized_dfm9/` with prefixes `croco_munin_da_sft__` and
`gsm_symbolic_da__`.

## Extension prefix config
2 new entries added to `data_io/prefix_config_dfm9.yaml` (now 116 entries, was 114):

```yaml
- prefix: croco_munin_da_sft__
  repeat: 5
- prefix: gsm_symbolic_da__
  repeat: 5
```

`repeat: 5` chosen because both sources are small (50K + 2K rows) and benefit
from additional exposure.

## Extension token contributions (with repeat=5)
| Source | Rows | Raw tokens | Over 4096 | Tokens/epoch (×5) |
| --- | ---: | ---: | ---: | ---: |
| croco_munin_da_sft | 49,988 | 41.7M | 1 (0.0%) | ~208.5M |
| gsm_symbolic_da | 2,100 | 0.52M | 0 (0%) | ~2.6M |
| **Total extension** | **52,088** | **42.2M** | **1** | **~211M** |

## Re-sampling with extension
Old `data/sampled_dfm9/` removed and re-sampled with extension sources included.
10 epochs, seed=0.

```text
metadata.json total_length: 93,929,976,190  (~93.93B tokens/epoch)
Previous DFM9 (pre-extension): 93,718,826,298  (~93.72B tokens/epoch)
Extension increase:             211,149,892  (~211M, +0.23%)
DFM8 was:                      70,479,433,697  (~70.48B tokens/epoch)
Total increase vs DFM8:         23,450,542,493  (~23.45B, +33.3%)
```

Output: `data/sampled_dfm9/` with 10 epoch dirs + `tokens.npy` (754GB).

## Remaining steps
1. ~~Re-run DFM9 sampling~~ — done, 93.93B tokens/epoch (with extension)
2. Launch DFM9 training from DFM8 L epoch 3 checkpoint or fresh start
3. Training config: `data=dfm9` pointing to `data/sampled_dfm9/`
