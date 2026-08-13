---
type: Operational Record
title: 2026-08-07 FlexOlmo Comparison Evals — Complete Results
description: 'Part of DFM5 XXS Step-50K Full Eval: 2026-08-07 FlexOlmo Comparison
  Evals — Complete Results.'
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
# 2026-08-07 FlexOlmo Comparison Evals — Complete Results

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high for eval results and rescore analysis; medium for FlexOlmo paper comparison (paper only reports aggregates).

## Eval Setup- Model: `exports/dfm8_XL_step1650000_ema_hf/` (identical to published `schneiderkamplab/HRM-Mimir-v1`)
- Framework: dfm-evals (inspect_ai) with vLLM backend, FLASH_ATTN, enforce-eager
- All evals 0-shot, temperature=0, sample_shuffle=4242
- W&B: project=DFM5, run_id=dfm8-xl-from-dfm6-dfm7-epoch5-clean-full, epoch=6.564012269760203

## MC9 (9 MCQ tasks, 0-shot)
| Task | Score | Notes |
|------|-------|-------|
| ARC-Easy | 87.46% | 2376 samples |
| ARC-Challenge | 77.30% | 1172 samples |
| BoolQ | 88.04% | 3270 samples |
| CommonsenseQA | 74.04% | 1221 samples |
| HellaSwag | 62.11% | 10042 samples |
| PIQA | 0% (77.09% rescored) | Model outputs bare "A" not "ANSWER: A" — scorer format issue |
| Winogrande | 72.85% | 1267 samples |
| OpenBookQA | 79.60% | 500 samples |
| SocialIQa | 50.46% | 1954 samples — genuinely weak (near random for 3-choice) |

- **MC9 (original)**: 65.76% (PIQA=0 drags down)
- **MC9 (rescored PIQA)**: 74.33%
- **FlexOlmo MC9 (pub)**: 68.7%, **(full)**: 70.8%
- Mimir beats FlexOlmo by +3.5pp (rescored)

## Gen5 (5 generative QA tasks, 0-shot)
| Task | Score | Format Issue? |
|------|-------|---------------|
| SQuAD | 80.14% F1 | No — concise answers |
| CoQA | 62.45% F1 | No — 9.4% verbose but mostly concise |
| NQ-Open | 12.50% F1 | No — genuine knowledge gap, wrong facts |
| TriviaQA | 21.22% F1 | No — mostly short answers, wrong facts |
| DROP | 83.53% F1 / 79.97% EM | (few-shot standard eval, not 0-shot) |

## Code4 (4 code generation tasks)
| Task | Score | Notes |
|------|-------|-------|
| HumanEval+ | 49.39% | 164 samples, file-based sandbox |
| MBPP | 53.31% | 1285 samples, 3-shot prompt with test cases |
| MBPP+ | 3.6% → **61.16%** (fixed) | Original prompt missing test cases — model couldn't see function names. Fixed by adding test_list_str to prompt. |

## FlexOlmo Extras
| Task | Original | Rescored | Format Issue? |
|------|----------|----------|---------------|
| MMLU-Pro | 24.81% | ~38% (with fix) | YES — 57% use `\boxed{}`, 31% boxed-only not scored. Scoring fix applied. |
| AGIEval | 37.59% | **50.71%** | YES — 17% bare letters not scored. Beats FlexOlmo full (45.1%)! |
| BBH | 28.91% | **45.17%** | YES — 28% bare letters not scored. Near FlexOlmo full (46.4%). |

## Key Findings1. **PIQA**: 0%→77% — pure scoring format issue (bare letter "A" not "ANSWER: A")
2. **AGIEval**: 37.6%→50.7% — 17% bare letters not scored by choice scorer
3. **BBH**: 28.9%→45.2% — 28% bare letters not scored by bbh_scorer
4. **MBPP+**: 3.6%→61.2% — prompt was missing test cases (function name mismatch in 90.3% of failures)
5. **MMLU-Pro**: 24.8%→~38% — 31% of answers use `\boxed{LETTER}` format ignored by `inspect_ai`'s `parse_answers`. Fixed via monkey-patch in `flexolmo.py`. Remaining gap to FlexOlmo (41.3%) is genuine knowledge.
6. **NQ-Open/TriviaQA**: Genuine knowledge gap — model gives wrong facts
7. **SocialIQa**: Genuine reasoning gap — near random (50.5% for 3-choice)

## Log Locations- FlexOlmo comparison evals: `logs/dfm_evals/dfm8_XL_step1650000_flexolmo_20260807_131731/`
- MC9 missing 5 tasks: `logs/dfm_evals/dfm8_XL_step1650000_mc9_missing_5/`
- MBPP+ rerun (fixed): `logs/dfm_evals/dfm8_XL_step1650000_mbpp_plus_rerun/`
- Previous standard (few-shot) evals: `logs/eval/dfm8_XL_steps1250k_1450k_vllm_hrmenv/step_1650000/standard_shards/`

## Code Changes- `dfm-evals/dfm_evals/tasks/code4.py`: MBPP+ prompt now includes test_list_str (same format as MBPP wrapper)
- `dfm-evals/dfm_evals/tasks/flexolmo.py`: Monkey-patches `inspect_ai.solver._multiple_choice.parse_answers` to also extract `\boxed{LETTER}` and bare-letter answers (fixes MMLU-Pro, AGIEval, and other MC tasks)
- `eval_scheduler/eval_scheduler/catalog.py`: temporarily modified for targeted runs, restored to full DFM_DEFAULT
