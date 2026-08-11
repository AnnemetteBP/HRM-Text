---
type: Policy Record
title: Original Plus Mixed Danish Instruction Rich
description: 'Part of Data Mix Policy: Original Plus Mixed Danish Instruction Rich.'
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
# Original Plus Mixed Danish Instruction Rich

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Verified locally on 2026-05-24 from:

- `data/show_analytics_original_sapient.md`
- `data/show_analytics_original_plus_mixed_danish_instruction_rich.md`
- `data/tokenized_original_plus_mixed/union_manifest.json`

The `original_plus_mixed_danish_instruction_rich` sample preserves the original Sapient portion almost exactly, then adds mixed/Danish sources on top.

Source union facts:

- `data/tokenized_original_plus_mixed/union_manifest.json` records `original_tasks: 5212`.
- All `5212` original Sapient tokenized tasks are present in the original+mixed union.
- `mixed_tasks_added: 226`.
- `include_mixed_sapient: false`, so duplicate Sapient tasks from the mixed tree are skipped rather than added twice.

Covered-token comparison across 4 epochs:

| Sample | Original Sapient covered tokens | Global covered tokens |
|---|---:|---:|
| `sampled_original_sapient` | `56,140,714,711` | `56,140,714,711` |
| `sampled_original_plus_mixed_danish_instruction_rich` | `56,140,181,363` | `110,736,199,356` |

Difference in the original Sapient portion: `-533,348` tokens, about `0.00095%`. This is consistent with sampling/shuffling boundary effects, not intentional reweighting of the original subset.

Per-category ratios for original Sapient categories in `original_plus_mixed_danish_instruction_rich` versus `original_sapient`:

| Category | Ratio |
|---|---:|
| `Platypus` | `1.000000` |
| `SYNTH` | `1.000000` |
| `acereason` | `0.999996` |
| `ampsmathematica` | `0.999924` |
| `dmmath` | `0.999944` |
| `flan` | `0.999960` |
| `openmathinstruct2` | `1.000217` |
| `openthoughts2` | `0.999905` |
| `sudoku_extreme` | `1.000000` |
| `tasksource` | `0.999956` |
| `textbookreasoning` | `1.000000` |

Task/file-level comparison:

- Matching original tasks: `5212 / 5212`
- Missing original tasks: `0`
- Exact same covered-token count: `2645 / 5212`
- Within `10,000` tokens: `4738 / 5212`
- Within `100,000` tokens: `5193 / 5212`
- Largest observed task difference: `openmathinstruct2__cot.parquet`, about `+902,328` covered tokens, ratio `1.000279`.

Conclusion: use `original_plus_mixed_danish_instruction_rich` when the goal is to keep the original Sapient training signal essentially unchanged while adding roughly `54.6B` extra covered tokens over 4 epochs from the mixed/Danish additions.

Confidence: high.
