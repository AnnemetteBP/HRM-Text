---
type: Plan Record
title: FLAN Factual-Knowledge Dataset Measurement
description: 'Part of DFM9 Plan: FLAN Factual-Knowledge Dataset Measurement.'
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
# FLAN Factual-Knowledge Dataset Measurement

Part of [DFM9 Plan](/pages/dfm9-plan.md).

Update, 2026-08-07. Confidence: high from local pyarrow metadata reads of all
514 matching parquet files in
`data/downloads/datasets/sapient_cleaned/data_clustered/flan/`.

All factual-knowledge FLAN datasets passed source -> filtered -> tokenized with
100% survival (514/514 files). The DFM8 sampling config
(`data_io/prefix_config_dfm8.yaml`) applies `max_per_file: 5000` to all
`flan__`-prefixed files (generic FLAN), while `flan__cot_`-prefixed files (CoT
FLAN) are uncapped. All 514 matching factual-knowledge files are regular FLAN
(not CoT), so all are capped at 5,000 rows/file.

## Per-dataset breakdown
KILT and HotpotQA overlap because all KILT files are `kilt_tasks_hotpotqa_*`.

| Dataset | Files | Size (MB) | Total Rows | Capped@5K | Lost to cap |
| --- | ---: | ---: | ---: | ---: | ---: |
| TriviaQA | 10 | 87.20 | 393,373 | 30,651 | 362,722 |
| SQuAD | 16 | 1,431.67 | 1,008,245 | 80,000 | 928,245 |
| Natural Questions | 6 | 51.02 | 393,991 | 30,000 | 363,991 |
| HotpotQA | 28 | 719.55 | 1,941,930 | 140,000 | 1,801,930 |
| WebQuestions | 22 | 10.10 | 90,508 | 83,674 | 6,834 |
| KILT (overlap w/HotpotQA) | 22 | 470.75 | 1,887,943 | 110,000 | 1,777,943 |
| RACE | 72 | 7,303.26 | 3,032,286 | 360,000 | 2,672,286 |
| DROP | 10 | 677.06 | 379,650 | 49,174 | 330,476 |
| CoQA | 10 | 90.96 | 32,491 | 22,189 | 10,302 |
| QuAC | 4 | 1,008.79 | 346,435 | 20,000 | 326,435 |
| ROPES | 54 | 824.60 | 575,998 | 256,398 | 319,600 |
| WikiDialog | 4 | 9,593.53 | 8,098,906 | 20,000 | 8,078,906 |
| DREAM | 28 | 168.06 | 186,488 | 130,103 | 56,385 |
| BoolQ | 8 | 57.32 | 63,331 | 34,213 | 29,118 |
| ARC | 12 | 9.34 | 36,068 | 30,313 | 5,755 |
| OpenBookQA | 6 | 6.51 | 37,550 | 28,223 | 9,327 |
| SciQ | 28 | 167.14 | 312,745 | 137,900 | 174,845 |
| QASC | 56 | 126.13 | 421,790 | 241,831 | 179,959 |
| CommonsenseQA | 106 | 58.18 | 237,338 | 175,376 | 61,962 |
| PIQA | 8 | 30.37 | 107,362 | 40,000 | 67,362 |
| HellaSwag | 6 | 206.16 | 188,796 | 30,000 | 158,796 |
| Winogrande | 20 | 81.62 | 315,376 | 99,000 | 216,376 |
| **TOTAL (dedup)** | **514** | **22,708.57** | **18,200,657** | **2,039,045** | **16,161,612** |

## Key factual datasets (TriviaQA + SQuAD + NQ + HotpotQA)
| Dataset | Available | Sampled@5K | Utilization |
| --- | ---: | ---: | ---: |
| TriviaQA | 393,373 | 30,651 | 7.8% |
| SQuAD | 1,008,245 | 80,000 | 7.9% |
| Natural Questions | 393,991 | 30,000 | 7.6% |
| HotpotQA | 1,941,930 | 140,000 | 7.2% |
| **Combined** | **3,737,539** | **280,651** | **7.5%** |

## Cap scenario analysis (regular FLAN, 18,196,516 available rows)
| Cap | Sampled Rows | Utilization | Additional vs 5K |
| --- | ---: | ---: | ---: |
| 5,000 (current) | 2,034,904 | 11.2% | 0 |
| 10,000 | 3,448,906 | 19.0% | 1,414,002 |
| 50,000 | 7,726,130 | 42.5% | 5,691,226 |
| 100,000 | 9,991,968 | 54.9% | 7,957,064 |
| 500,000 | 12,097,610 | 66.5% | 10,062,706 |
| 1,000,000 | 13,720,598 | 75.4% | 11,685,694 |
| uncapped | 18,196,516 | 100.0% | 16,161,612 |

356 of 510 regular FLAN files have more than 5,000 rows and are actively capped.
The biggest absolute losses are WikiDialog (8.1M -> 20K), RACE (3.0M -> 360K),
HotpotQA/KILT (1.9M -> 140K/110K), and SQuAD (1.0M -> 80K).

## Token impact (measured from tokenized npy files + source parquet metadata)
Confidence: high — measured directly from `inst_len.npy` + `resp_len.npy` in
`data/tokenized_dfm8/` and source row counts from
`data/downloads/datasets/sapient_cleaned/data_clustered/flan/`.

Key insight: tokenization happens BEFORE sampling. The tokenized tree contains
ALL rows. The `max_per_file: 5000` cap is applied at sampling time, reducing
the 18.2M available rows to ~2.0M sampled rows. The current factual FLAN
contribution to the 70.48B-token epoch is much smaller than the raw tokenized
tree suggests.

### All factual FLAN datasets (22 datasets, 512 files)
| Cap | Unique rows | Tokens/epoch | % of epoch | vs current | Over 3 epochs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5K (current) | 2,024,644 | 0.93B | 1.3% | 1.0x | 2.8B |
| 10K | 3,424,643 | 1.69B | 2.4% | 1.8x | 5.1B |
| 50K | 7,697,098 | 4.32B | 6.1% | 4.6x | 13.0B |
| 100K | 9,962,936 | 5.59B | 7.9% | 6.0x | 16.8B |
| 500K | 12,068,578 | 6.59B | 9.4% | 7.1x | 19.8B |
| 1M | 13,691,566 | 7.45B | 10.6% | 8.0x | 22.3B |
| uncapped | 18,167,484 | 10.10B | 14.3% | 10.9x | 30.3B |

### Key factual datasets only (TriviaQA + SQuAD + NQ + HotpotQA)
These are the datasets directly tested in FlexOlmo evals. They saturate at
500K cap (all rows fit within 500K/file).

| Cap | Unique rows | Tokens/epoch | vs current | Over 3 epochs |
| --- | ---: | ---: | ---: | ---: |
| 5K (current) | 280,651 | 0.12B | 1.0x | 0.36B |
| 10K | 523,875 | 0.21B | 1.9x | 0.63B |
| 50K | 1,990,291 | 0.53B | 4.6x | 1.6B |
| 100K | 3,277,764 | 0.81B | 7.0x | 2.4B |
| 500K+ | 3,737,539 | 1.01B | 8.8x | 3.0B |

Current key factual datasets contribute only **0.17% of the 70.5B epoch**.
Even fully uncapped, they'd be 1.43% of the epoch. The model sees each unique
factual example only 3 times (once per training epoch) — this is very little
exposure for learning facts.

## Repetition analysis over training epochs
DFM8 training: 70.48B tokens/epoch, 3 training epochs = 211.4B total tokens.

FLAN factual has `repeat=1` (no explicit repeat in prefix config). Each unique
row appears once in the sampled set. Over 3 training epochs, each row is seen
exactly 3 times. Raising the cap increases UNIQUE coverage, not repetition:

| Cap | Unique rows | Times each row seen | Total factual exposure |
| --- | ---: | ---: | ---: |
| 5K (current) | 2.0M | 3x | 2.8B tokens |
| 100K | 10.0M | 3x | 16.8B tokens |
| uncapped | 18.2M | 3x | 30.3B tokens |

The model currently sees only ~281K unique TriviaQA/SQuAD/NQ/HotpotQA rows,
each 3 times. At 100K cap it would see ~3.3M unique rows, each 3 times — 12x
broader factual coverage with the same repetition depth.

**Implication**: 3 exposures per fact may be insufficient for durable
memorization. Consider either:
- Increasing `repeat` for factual FLAN (e.g., `repeat: 2` or `repeat: 3`) to
  increase per-fact exposure
- Increasing training epochs
- Both

With `repeat: 3` and 100K cap: 10M unique rows × 3 repeats × 3 epochs = 90M
row-passes, ~50.4B tokens total — comparable to the current full-FLAN-uncapped
contribution but with 12x more unique factual rows.
