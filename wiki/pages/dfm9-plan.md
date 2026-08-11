---
type: Training Data Plan
title: DFM9 Plan
description: DFM9 data rebuild and continuation plan focused on factual knowledge, code, and instruction coverage.
tags: [dfm9, data, training, factual-knowledge, code]
status: stable
last_updated: 2026-08-11
confidence: high
---
# DFM9 Plan

## Motivation

FlexOlmo comparison evals on DFM8 XL (step 1,650,000, published as HRM-Mimir-v1)
revealed genuine factual knowledge gaps:

| Task | Mimir | FlexOlmo (full) | Gap | Root cause |
| --- | ---: | ---: | ---: | --- |
| NQ-Open | 12.5% F1 | 19.6% | -7.1pp | Wrong facts |
| TriviaQA | 21.2% F1 | 57.1% | -35.9pp | Wrong facts (severe) |
| MMLU-Pro | 24.8% | 41.3% | -16.5pp | Mixed: ~13pp format (fixed via scoring patch), ~3.5pp genuine |

Weakest knowledge domains (across NQ-Open, TriviaQA, MMLU-Pro):
- Entertainment/Movies/TV/Music: 27-30% of wrong answers
- History: 12.7% MMLU-Pro accuracy (weakest subject)
- Law/Philosophy: 16.0-16.3% MMLU-Pro
- Geography: 9-11% of wrong answers
- Sports: 9% of wrong answers

Scoring fixes already applied (not data issues):
- MMLU-Pro: `\boxed{LETTER}` extraction patch in `flexolmo.py` → ~38% (from 24.8%)
- AGIEval: bare-letter rescoring → 50.7% (from 37.6%, beats FlexOlmo 45.1%)
- BBH: bare-letter rescoring → 45.2% (from 28.9%, near FlexOlmo 46.4%)
- PIQA: bare-letter rescoring → 77.1% (from 0%)

## Objectives

1. Raise FLAN factual-knowledge dataset caps to increase world-knowledge coverage
2. Keep Danish instruction quality from DFM8
3. Maintain math/reasoning/tool-calling gains from DFM8
4. Evaluate whether additional Wikipedia-derived QA sources should be added

## FLAN Factual-Knowledge Dataset Measurement

Update, 2026-08-07. Confidence: high from local pyarrow metadata reads of all
514 matching parquet files in
`data/downloads/datasets/sapient_cleaned/data_clustered/flan/`.

All factual-knowledge FLAN datasets passed source -> filtered -> tokenized with
100% survival (514/514 files). The DFM8 sampling config
(`data_io/prefix_config_dfm8.yaml`) applies `max_per_file: 5000` to all
`flan__`-prefixed files (generic FLAN), while `flan__cot_`-prefixed files (CoT
FLAN) are uncapped. All 514 matching factual-knowledge files are regular FLAN
(not CoT), so all are capped at 5,000 rows/file.

### Per-dataset breakdown

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

### Key factual datasets (TriviaQA + SQuAD + NQ + HotpotQA)

| Dataset | Available | Sampled@5K | Utilization |
| --- | ---: | ---: | ---: |
| TriviaQA | 393,373 | 30,651 | 7.8% |
| SQuAD | 1,008,245 | 80,000 | 7.9% |
| Natural Questions | 393,991 | 30,000 | 7.6% |
| HotpotQA | 1,941,930 | 140,000 | 7.2% |
| **Combined** | **3,737,539** | **280,651** | **7.5%** |

### Cap scenario analysis (regular FLAN, 18,196,516 available rows)

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

### Token impact (measured from tokenized npy files + source parquet metadata)

Confidence: high — measured directly from `inst_len.npy` + `resp_len.npy` in
`data/tokenized_dfm8/` and source row counts from
`data/downloads/datasets/sapient_cleaned/data_clustered/flan/`.

Key insight: tokenization happens BEFORE sampling. The tokenized tree contains
ALL rows. The `max_per_file: 5000` cap is applied at sampling time, reducing
the 18.2M available rows to ~2.0M sampled rows. The current factual FLAN
contribution to the 70.48B-token epoch is much smaller than the raw tokenized
tree suggests.

#### All factual FLAN datasets (22 datasets, 512 files)

| Cap | Unique rows | Tokens/epoch | % of epoch | vs current | Over 3 epochs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5K (current) | 2,024,644 | 0.93B | 1.3% | 1.0x | 2.8B |
| 10K | 3,424,643 | 1.69B | 2.4% | 1.8x | 5.1B |
| 50K | 7,697,098 | 4.32B | 6.1% | 4.6x | 13.0B |
| 100K | 9,962,936 | 5.59B | 7.9% | 6.0x | 16.8B |
| 500K | 12,068,578 | 6.59B | 9.4% | 7.1x | 19.8B |
| 1M | 13,691,566 | 7.45B | 10.6% | 8.0x | 22.3B |
| uncapped | 18,167,484 | 10.10B | 14.3% | 10.9x | 30.3B |

#### Key factual datasets only (TriviaQA + SQuAD + NQ + HotpotQA)

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

### Repetition analysis over training epochs

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

## Decision: 100K cap + repeat 2 for factual FLAN

Decided 2026-08-07. Confidence: high.

**Cap**: `max_per_file: 100000` for factual-knowledge FLAN files (up from 5,000).
**Repeat**: `repeat: 2` for factual-knowledge FLAN files (up from implicit 1).

This gives each unique factual row 2 × 3 = 6 exposures over 3 training epochs
(was 3), with ~10M unique rows (was ~2M).

Projected impact (all 22 factual FLAN datasets):
- Tokens/epoch: 5.59B × 2 = 11.18B (15.9% of epoch, was 1.3%)
- Over 3 epochs: 33.6B tokens (was 2.8B)
- Unique rows: 10.0M (was 2.0M)
- Exposures per row: 6x (was 3x)

Key factual datasets only (TriviaQA + SQuAD + NQ + HotpotQA):
- Tokens/epoch: 0.81B × 2 = 1.62B (2.3% of epoch, was 0.17%)
- Over 3 epochs: 4.9B tokens (was 0.36B)
- Unique rows: 3.3M (was 281K)
- Exposures per row: 6x (was 3x)

## Implementation Plan

### 1. Split FLAN prefix for selective cap raising

The current single `flan__` prefix applies one cap to all FLAN files. To apply
100K + repeat 2 only to factual-knowledge files while leaving other FLAN at 5K,
the FLAN files must be split into sub-prefixes in the tokenized tree.

Factual-knowledge FLAN files (100K cap, repeat 2):
- TriviaQA, SQuAD, Natural Questions, HotpotQA, WebQuestions, KILT, RACE,
  DROP, CoQA, QuAC, ROPES, WikiDialog, DREAM, BoolQ

Science/reasoning FLAN files (keep at current 5K cap, repeat 1):
- ARC, OpenBookQA, SciQ, QASC, CommonsenseQA, PIQA, HellaSwag, Winogrande

These already perform well in evals — no need to boost.

Implementation approach: create symlinks in `data/tokenized_dfm9/` that rename
factual FLAN files from `flan__...` to `flan_factual__...`, then use
`flan_factual__` prefix in the sampling config with `max_per_file: 100000` and
`repeat: 2`, while `flan__` stays at `max_per_file: 5000` for the rest.

### 2. Create prefix_config_dfm9.yaml

Copy `prefix_config_dfm8.yaml` and add:
```yaml
- prefix: flan_factual__
  max_per_file: 100000
  repeat: 2
- prefix: flan__
  max_per_file: 5000
```

The `flan_factual__` prefix must come before `flan__` so it matches first.

### 3. Build sampled data

```bash
cd /work/dfm/HRM-Text
python data_io/sample_tokenized.py \
  --tokenized-dir data/tokenized_dfm9 \
  --config data_io/prefix_config_dfm9.yaml \
  --output data/sampled_dfm9
```

### 4. Verify

Check `data/sampled_dfm9/metadata.json` for total tokens/epoch. Expected:
~70.5B + (11.18B - 0.93B) ≈ ~80.8B tokens/epoch (the factual FLAN increase
net of the existing 5K contribution).

### 5. Training

DFM9 training can resume from the DFM8 L epoch 3 checkpoint or start fresh.
Training config needs `data=dfm9` pointing to `data/sampled_dfm9`.

## Implementation Status

Update, 2026-08-07. Confidence: high from local file creation and process
inspection.

### Completed

1. **`data/tokenized_dfm9/`**: created with 10,722 symlinked entries from
   `tokenized_dfm8/` (later expanded to 11,413 with new sources, SWE windowed,
   and extension sources). 266 factual-knowledge FLAN files renamed from `flan__`
   to `flan_factual__` (includes main FLAN variants and niv2 task variants
   for TriviaQA, SQuAD, NQ, HotpotQA/KILT, WebQuestions, RACE, DROP, CoQA,
   QuAC, ROPES, WikiDialog, DREAM, BoolQ). Remaining 3,608 non-factual FLAN
   files kept as `flan__`. 6,848 non-FLAN entries symlinked as-is.

   Per-dataset factual file counts: bool=8, coqa=8, dream=28, drop=10,
   hotpot/kilt=28, natural_questions=4, quac=4, race=72, ropes=54,
   squad=16, trivia=8, web_questions=22, wiki_dialog=4. Total=266.

2. **`data_io/prefix_config_dfm9.yaml`**: created with 109 prefix entries
   (DFM8 had 108 + 1 new `flan_factual__` entry). Key change:
   ```yaml
   - prefix: flan_factual__
     max_per_file: 100000
     repeat: 2
   - prefix: flan__cot_        # unchanged, no cap
   - prefix: flan__             # unchanged, 5K cap
     max_per_file: 5000
   ```
   The `flan_factual__` prefix is placed before `flan__cot_` and `flan__`
   so it matches first.

3. **Sampling launched** in background (PID 1091371):
   ```bash
   cd data_io && ionice -c2 -n7 nice -n 10 python sample_tokenized.py \
     tokenized_path=../data/tokenized_dfm9 \
     output_path=../data/sampled_dfm9 \
     epochs=5 concat_workers=4 \
     prefix_config_path=prefix_config_dfm9.yaml \
     > ../data/show_analytics_dfm9.md 2> ../logs/tokenize/dfm9_sample_stderr.log
   ```
   Note: `reuse_tokens=true` is NOT safe because renaming `flan__` to
   `flan_factual__` changes the sorted task order, which changes per-task
   `mmap_base_offset` values in the combined `tokens.npy`.

### Sampling Complete

Update, 2026-08-07. Confidence: high from `metadata.json` and analytics report
output.

```text
metadata.json total_length: 79,938,703,078  (~79.94B tokens/epoch)
DFM8 was:                  70,479,433,697  (~70.48B tokens/epoch)
Increase:                   9,459,269,381  (~9.46B, +13.4%)
```

Factual FLAN category (`flan_factual`) in the analytics report:
- Total rows: 16,495,724 (3.5% of all rows)
- Total tokens: 9,603,096,705 (7.5% of all tokens)
- Covered rows over 5 epochs: 82,911,760 (7.1%)
- Covered tokens over 5 epochs: 50,997,831,112 (12.8%) = ~10.2B/epoch

Non-factual FLAN category (`flan`) remains at 5K cap:
- Covered tokens over 5 epochs: 21,639,449,658 (5.4%) = ~4.3B/epoch

The ~9.46B increase is slightly less than the projected ~10.25B because the
tokenized tree has 266 factual FLAN files (vs 514 in the source parquet
analysis). The actual token increase is proportional to the available
tokenized files.

Verified output:
```text
data/sampled_dfm9/
├── epoch_0/
├── epoch_1/
├── epoch_2/
├── epoch_3/
├── epoch_4/
├── metadata.json
└── tokens.npy
```

## New Source Additions (Code, Math, English Instruction)

Update, 2026-08-07. Confidence: high from local file inspection and conversion.

Beyond FLAN cap raising, 7 new sources were added to close additional eval gaps
(code, math, English instruction-following) identified in the FlexOlmo comparison.

### Source audit

All sources audited for license, PII, and provenance before inclusion:

| Source | Repo ID | Rows (converted) | License | PII | Decision |
| --- | --- | ---: | --- | --- | --- |
| NuminaMath 1.5 | `AI-MO/NuminaMath-1.5` | 786K | MIT | No | Approved, cap 300K |
| Nemotron Terminal Corpus | `nvidia/nemotron-terminal-corpus` | 2.7M | NVIDIA | No | Approved, cap 200K |
| Code Meta Reasoning | `allenai/code_meta_reasoning` | 912K | Apache 2.0 (EU TDM) | No | Approved, cap 250K |
| Natural Instructions | `posttrain_natural_instructions` | 3.0M | OBSD (EU TDM) | Filtered | Approved, cap 500K, 96 PII tasks excluded |
| CoEdIT | `posttrain_coedit` | 70K | OBSD | No | Approved, uncapped |
| ASSET | `posttrain_asset` | 2.4K | CC-BY | No | Approved, uncapped |
| Nemotron SWE | `nvidia/nemotron-swe` | 2.03M (windowed) | NVIDIA | No | **Approved, cap 500K/file** — windowed converter drops system prompt+tools, truncates issue to 1500 tokens, sliding window of prior turns within 3584-token budget. 83.4% of rows fit 4096 after template overhead. |

PII-sensitive tasks excluded from natural_instructions (96 files): SMS, tweets,
Amazon reviews, hate speech, civil comments, Yelp, IMDb, sentiment140, etc.
Filter logic in `scripts/convert_dfm9_new_sources.py` (`PII_EXCLUDE_KEYWORDS`).

### Conversion

6 unconverted sources were converted via `scripts/convert_dfm9_new_sources.py`
to condition/instruction/response parquet format. Nemotron SWE was already
converted. Output in `data/converted_sources/<source>/`.

Conversion details:
- NuminaMath: problem→instruction, solution→response, condition="cot"
- Terminal Corpus: conversations→messages expansion (multi-turn extraction)
- Code Meta Reasoning: raw text→continuation, condition="direct"
- Natural Instructions: definition+inputs→instruction, targets→response
- CoEdIT: src→instruction, tgt→response
- ASSET: original→instruction, simplification→response

### Tokenization

Tokenized via `scripts/tokenize_chat_template.py` (same pipeline as DFM8/DFM9
existing data). Tokenizer: `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`,
chat template: `data_io/chat_templates/gemma4_native_chat.jinja`, 8 workers.

Output: `data/tokenized_dfm9_new/` (694 directories, one per parquet file).

### Prefix config updates

5 new entries + 1 update added to `data_io/prefix_config_dfm9.yaml` (now 114
prefix entries, was 109):

```yaml
# DFM9 new sources — conservative caps (~6B new tokens).
- prefix: numinamath_1_5__
  max_per_file: 300000
- prefix: nemotron_terminal_corpus__
  max_per_file: 200000
- prefix: posttrain_natural_instructions__
  max_per_file: 500000
- prefix: posttrain_coedit__
  repeat: 1
- prefix: posttrain_asset__
  repeat: 1
```

Updated: `nemotron_swe__` replaced by `nemotron_swe_windowed__` with `max_per_file: 500000`.
The old `nemotron_swe__` entries (11 dirs) were removed from `tokenized_dfm9` and replaced
with 9 new entries (1 agentless + 8 merged SWE shards).

Windowing conversion (`scripts/convert_nemotron_swe_windowed.py`):
- **Agentless**: Flexible fit (inst+resp ≤ 4096 raw tokens). 135K rows, 265M tokens, 100% fit 4096.
- **SWE**: Sliding window — drop system prompt (~1720 tokens), drop tools (~2K template overhead),
  truncate user issue to 1500 tokens, 3584-token context budget, 512-token response limit.
  1.9M rows produced, 30B tokens. After chat template tokenization, 83.4% fit 4096
  (16.6% dropped by sampler's truncate mode — template adds ~5-7 tokens/message overhead
  not counted by converter's raw token budget).
- 64 tokenization shards merged into 8 files for effective per-file capping (8 × 500K = 4M cap).

`allenai_code_meta_reasoning__` was already in config at 250K but not previously
tokenized — now tokenized and active.

### Re-sampling Complete

Update, 2026-08-08. Confidence: high from `metadata.json` and sampler report.

DFM9 re-sampled with all new sources (including SWE windowed). 10 epochs, seed=0.

```text
metadata.json total_length: 93,718,826,298  (~93.72B tokens/epoch)
DFM8 was:                  70,479,433,697  (~70.48B tokens/epoch)
DFM9 first sampling was:   79,938,703,078  (~79.94B tokens/epoch)
Increase vs DFM8:           23,239,392,601  (~23.24B, +33.0%)
```

New source contributions per epoch (from sampler coverage report):

| Source | Rows (after cap) | Tokens/epoch | % of epoch |
| --- | ---: | ---: | ---: |
| nemotron_swe_windowed | 4,135,210 | 10,417,511,228 | 11.1% |
| allenai_code_meta_reasoning | 911,517 | 1,286,748,011 | 1.4% |
| nemotron_terminal_corpus | 312,865 | 986,121,784 | 1.1% |
| posttrain_natural_instructions | 2,729,950 | 723,722,346 | 0.8% |
| numinamath_1_5 | 786,435 | 361,647,178 | 0.4% |
| posttrain_coedit | 70,783 | 4,210,935 | <0.1% |
| posttrain_asset | 2,359 | 150,768 | <0.1% |
| **Total new** | **~8.0M** | **~13.8B** | **~14.7%** |

Factual FLAN (from first sampling, unchanged): ~10.2B tokens/epoch (repeat=2, 100K cap).

Output: `data/sampled_dfm9/` with 10 epoch dirs + `tokens.npy` (754GB).

### Training-host migration footprint (2026-08-10)

Confidence: high (verified against the local sampled tree and `dataset_new.py`).

- The complete 10-epoch sampled training tree is `data/sampled_dfm9/`: 42 regular
  files, 886,672,532,932 bytes total (826 GiB by `du`), with an
  808,954,206,220-byte `tokens.npy` and four 1,942,958,160-byte index arrays in
  each of `epoch_0` through `epoch_9`.
- Core training only reads `metadata.json`, `tokens.npy`, and the four arrays for
  the active epoch. It does not open the tokenizer path embedded in metadata.
- `data/tokenized_dfm9*` is not needed to train from the sampled tree. Transfer
  it only when the destination must reproduce or change sampling.
- Preserve the Gemma tokenizer JSON named by metadata for export/evaluation, or
  deliberately update that path on the destination. The Gemma model weights are
  not needed for HRM training.
- Superseded on 2026-08-10: `config/data/dfm9.yaml` has now been added and points
  to `data/sampled_dfm9`. No DFM9 checkpoint currently exists in this working
  tree; transfer a full checkpoint separately if continuing rather than starting
  a new run.

## DFM9 Extension (HuggingFace Org Scan)

Update, 2026-08-08. Confidence: high from local file inspection and tokenization output.

### HuggingFace org scan

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

### Extension conversion

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

### Extension tokenization

Tokenized via `scripts/tokenize_chat_template.py` (same pipeline). 52,088 rows,
0 skipped, 38 seconds, 42.2M tokens total. Output in `data/tokenized_dfm9_ext/`.
Symlinked into `data/tokenized_dfm9/` with prefixes `croco_munin_da_sft__` and
`gsm_symbolic_da__`.

### Extension prefix config

2 new entries added to `data_io/prefix_config_dfm9.yaml` (now 116 entries, was 114):

```yaml
- prefix: croco_munin_da_sft__
  repeat: 5
- prefix: gsm_symbolic_da__
  repeat: 5
```

`repeat: 5` chosen because both sources are small (50K + 2K rows) and benefit
from additional exposure.

### Extension token contributions (with repeat=5)

| Source | Rows | Raw tokens | Over 4096 | Tokens/epoch (×5) |
| --- | ---: | ---: | ---: | ---: |
| croco_munin_da_sft | 49,988 | 41.7M | 1 (0.0%) | ~208.5M |
| gsm_symbolic_da | 2,100 | 0.52M | 0 (0%) | ~2.6M |
| **Total extension** | **52,088** | **42.2M** | **1** | **~211M** |

### Re-sampling with extension

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

### Remaining steps

1. ~~Re-run DFM9 sampling~~ — done, 93.93B tokens/epoch (with extension)
2. Launch DFM9 training from DFM8 L epoch 3 checkpoint or fresh start
3. Training config: `data=dfm9` pointing to `data/sampled_dfm9/`

## DFM8 XL Epoch-7 To DFM9 Continuation Command

Update, 2026-08-10. Confidence: high from checkpoint shard/sidecar inspection,
sampled-data inspection, trainer resume-code inspection, and successful Hydra
configuration composition. The command has not yet been launched.

The newest complete DFM8 XL epoch checkpoint is
`checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5/fsdp2_epoch_7`. Its sidecar records
global step `1768071`, completed epoch `7`, global batch size `262144`, gradient
accumulation `2`, and exact epoch-boundary state. All eight FSDP shards and all
eight carry files are present.

Resuming `epoch_7` gives `start_epoch=8`; the trainer then loads sampled dataset
directory `data/sampled_dfm9/epoch_7`. Therefore `epochs=8` trains exactly one
DFM9 continuation epoch and writes `epoch_8`. Use a separate checkpoint tree so
DFM8 checkpoint artifacts remain intact.

Superseded, 2026-08-10: the initial command used a new W&B run named
`DFM9-XL from DFM8 epoch7`. The subsequent operational decision is to continue
the existing `DFM8-XL clean full from DFM6-DFM7 epoch5` history instead, using
run ID `dfm8-xl-from-dfm6-dfm7-epoch5-clean-full` in project `DFM5`.

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm9 \
  arch/size@arch=XL \
  lr=3e-4 \
  lr_min_ratio=1 \
  lr_warmup_steps=2000 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=0.9999 \
  global_batch_size=262144 \
  gradient_accumulation_steps=2 \
  epochs=8 \
  training_total_steps=2127489 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  checkpoint_format=sharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=true \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=500 \
  checkpoint_path=checkpoints/dfm9/XL-from-dfm8-epoch7 \
  resume_checkpoint_path=checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5 \
  resume_checkpoint_tag=epoch_7 \
  resume_step=1768071 \
  resume_epoch=7 \
  reset_ema_on_resume=false \
  upcast_optimizer_state_on_resume=false \
  project_name=DFM5 \
  run_name="DFM8-XL clean full from DFM6-DFM7 epoch5" \
  wandb_run_id=dfm8-xl-from-dfm6-dfm7-epoch5-clean-full \
  wandb_resume=allow
```

DFM9 contains `93,929,976,190` tokens per epoch. At global batch size `262144`,
the coarse token-ratio estimate is about `358,314` optimizer steps, placing the
next epoch boundary near global step `2,126,385`; the actual packed-batch count
and resulting checkpoint step are authoritative.

### Scheduled After DFM8 L Epoch 3

Update, 2026-08-10. Confidence: high from direct sampler iteration and atomic
inspection/mutation of the active scheduler plan.

The continuation is queued in
`logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv` as an eight-segment
train/evaluate campaign. Direct sampler iteration showed that the DFM8 L third
epoch starts at step `537300` and contains `268645` optimizer steps, so its
exact endpoint is `805945`. This supersedes the legacy plan's incorrect
`806365` estimate.

The first DFM9 row, `dfm9-xl-train-1800000`, therefore depends on terminal
completion of `campaign-train-806365`, rather than on the stale `step_806365`
checkpoint or its evaluation teardown. The L process naturally exhausts the
dataset and fully writes `epoch_3` at step `805945`; only the scheduler's
subsequent check for the nonexistent `step_806365` is expected to mark that
legacy row failed. Using terminal dependency semantics lets DFM9 start after
the completed epoch despite that stale verification target. The old DFM8 L
continuation remains behind `campaign-teardown-806365` and cannot race DFM9
for the GPUs.

Direct iteration of the DFM9 `epoch_7` multipack sampler with eight ranks,
`16384` tokens per rank/microbatch, and GAS 2 produced `718837` complete
microbatches. This is `359418` optimizer steps plus one trailing microbatch that
cannot form a GAS-2 update. Starting at DFM8 XL step `1768071` therefore gives
the exact optimizer endpoint `2127489`.

The scheduler campaign stops and evaluates at steps `1800000`, `1850000`,
`1900000`, `1950000`, `2000000`, `2050000`, `2100000`, and the exact epoch
endpoint `2127489`. Each block includes standard, DFM, and EuroEval tasks,
checkpoint export, merging, W&B sync/averaging, a terminal GPU-eval barrier,
and persistent-vLLM teardown. The next training segment starts after that
teardown; CPU-side merges and finalization do not unnecessarily hold the GPUs.

The final scheduler segment injects `stop_after_step=2127489` and verifies the
complete sharded `step_2127489` checkpoint under
`checkpoints/dfm9/XL-from-dfm8-epoch7`. This checkpoint has the same trained
weights as natural exhaustion of DFM9 sampled epoch `epoch_7`; because the
scheduler stops immediately after the final optimizer update, its tag is a
step tag rather than the standalone command's natural `epoch_8` tag.

Progress/LR endpoint correction, 2026-08-11. Confidence: high from code
inspection, Hydra composition, and atomic inspection of all queued training
rows. The default `pretrain.py` total was `epochs * current_dataset_steps`,
which is wrong when a run starts at a nonzero global step and switches to a new
dataset: it displayed approximately eight DFM9 epochs instead of the DFM8
global starting step plus one DFM9 epoch. `PretrainConfig` now has an optional
`training_total_steps` field. When supplied, it is the global `tqdm` denominator
and cosine-LR endpoint; when omitted, legacy behavior is unchanged. All eight
DFM9 scheduler training rows specify `training_total_steps=2127489`. The first
row was already running when this correction was installed, so its in-process
bar retains the old denominator until step `1800000`; every subsequent segment
will display the correct `.../2127489` total. This run uses
`lr_min_ratio=1`, so the old denominator did not alter its constant learning
rate.

Evaluation x-axis values are computed as
`7 + (checkpoint_step - 1768071) / 359418`, giving fractional epochs for the
50K checkpoints and exactly `8.0` at the final checkpoint. Non-judged vLLM
jobs use utilization `0.9`; `generative_talemaader` uses the established
`unsloth/gemma-4-E4B-it` judge with batch `32`, 32 connections, and vLLM
utilization `0.65`.

The queued command logs directly into the existing W&B run
`peter-sk-sdu/DFM5/dfm8-xl-from-dfm6-dfm7-epoch5-clean-full` with
`wandb_resume=allow`. The checkpoint's authoritative training step remains
`1768071`; do not raise `resume_step` merely to match W&B. Direct API inspection
on 2026-08-10 found that later eval/backfill records had advanced the run's
internal history step to `1768093`. With the default five-step logging interval,
W&B may reject continuation records at steps `1768075`, `1768080`, `1768085`,
and `1768090`, then accepts training metrics from `1768095` onward. This small
logging gap is preferable to skipping 22 training steps or misaligning model,
optimizer, and data-loader state.

## Open Questions

- Should DFM9 be a full rebuild or an incremental adjustment to DFM8?
- Should the model continue from DFM8 L epoch 3 checkpoint or start fresh?
- Are there additional Wikipedia-derived QA sources worth adding beyond FLAN?
- Should sub-prefixing also separate science from commonsense FLAN?
