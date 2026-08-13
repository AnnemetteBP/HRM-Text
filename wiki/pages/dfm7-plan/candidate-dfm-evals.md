---
type: Plan Record
title: Candidate DFM Evals
description: 'Part of DFM7 Plan: Candidate DFM Evals.'
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
# Candidate DFM Evals

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Eval-oriented dataset scan, 2026-06-30. Confidence: medium from Hugging Face
metadata and local `dfm-evals/dfm_evals/tasks` inspection. Several datasets
from the scanned namespaces should stay out of training but are good candidates
for new or expanded DFM eval tasks.

Recommended new or expanded DFM eval integrations:

| Dataset | Proposed DFM eval | Why it helps | Notes |
| --- | --- | --- | --- |
| `danish-foundation-models/multi-ifeval` | `multi_ifeval` with at least `da`, optionally `en`, `de`, `sv`, `no`, `is` slices | Better instruction-following coverage than the current Danish-only IFEval path and useful multilingual comparison | Same IFEval-style schema as `ifeval-da`; likely easiest high-value addition. Keep language slices separate in metrics. |
| `danish-foundation-models/global-piqa-da` | Danish PIQA / physical commonsense | Danish commonsense gap; pairs naturally with existing English PIQA | Need inspect exact schema/scorer target before implementation. |
| `danish-foundation-models/multilingual-gsm-symbolic` | Danish GSM-Symbolic and possibly English GSM-Symbolic | Math robustness under symbolic perturbations; direct signal for Danish math reasoning | Use `dan` test splits for eval only. English train splits may be separate training candidates, but do not mix eval splits into training. |
| `synquid/gsm8k-da` | Danish GSM8K | Direct Danish arithmetic word-problem eval | Test split only; keep out of training. Scorer can mirror current `GSM8k` with Danish prompt text. |
| `synquid/wmt24pp` | WMT24++ Danish translation | Better translation eval than only one local translation slice | Use `en-da_DK` and ideally `da-en` only if available or construct paired direction from available data; metrics: chrF3++, chrF3, BLEU, possibly BERTScore. |
| `danish-foundation-models/linguistic-quality` | Danish linguistic quality / acceptability | Complements DALA with a small curated Danish quality signal | Manual gated; inspect schema before implementation. |
