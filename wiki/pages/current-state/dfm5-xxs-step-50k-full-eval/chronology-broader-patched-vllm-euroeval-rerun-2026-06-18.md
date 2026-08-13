---
type: Operational Record
title: Broader patched vLLM EuroEval rerun (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Broader patched
  vLLM EuroEval rerun (2026-06-18).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Broader patched vLLM EuroEval rerun (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Broader patched vLLM EuroEval rerun, 2026-06-18. Confidence: high for local
logs and merged metrics. The remaining 19 EuroEval datasets were rerun locally
without W&B sync using the patched template, vLLM FA4, and pinned
`euroeval==17.4.0` / `litellm==1.89.2`.

```text
scheduler root: logs/eval/dfm5_L_step550000_vllm_fa4_euroeval_template_fixed_19_20260618_173817
EuroEval root:  logs/euroeval/dfm5_L_step550000_vllm_fa4_euroeval_template_fixed_19_20260618_173817/step_550000
```

The queue completed with 18 successes and one failure. `valeu-en` failed after
four attempts because EuroEval found no candidate label for `1/53` outputs and
aborts that task on invalid labels. Including the separate patched
`angry-tweets` probe, patched vLLM has 19/20 merged EuroEval metrics.

Headline comparison:

```text
task                    native   old vLLM   patched vLLM
angry-tweets macro_f1    72.54      28.17          69.79
scala-da macro_f1        52.60      33.74          33.74
dansk micro_f1           36.65      14.95          36.79
multi-wiki-qa-da f1      79.90      78.29          79.89
nordjylland chr_f3pp     32.60      24.07          32.62
talemaader accuracy      39.38      28.44          19.38
citizen-tests accuracy   55.67      41.44          43.11
hellaswag-da accuracy    42.77      24.14          40.31
ifeval-da instr acc      52.27      52.72          51.82
valeu-da european_values missing     0.00           0.00
sst5 macro_f1            71.53      40.70          69.66
scala-en macro_f1        76.09      32.87          46.14
conll-en micro_f1        57.05      21.11          57.02
squad f1                 88.83      85.90          88.94
cnn-dailymail chr_f3pp   36.39      31.97          36.28
life-in-uk accuracy      51.64      29.69          36.33
hellaswag accuracy       48.24      25.78          32.89
ifeval instr acc         69.56      69.46          70.13
bfcl-v2 tool accuracy     0.00      23.12          22.84
valeu-en european_values 90.71    missing        missing
```

Interpretation: the prompt-template fix clearly resolves many prompt-shape
regressions (`angry-tweets`, NER, QA, summarization, IFEval), but not all
EuroEval parity issues. Remaining divergences (`scala-da`, `scala-en`,
`talemaader`, `citizen-tests`, `life-in-the-uk`, `hellaswag`, `bfcl-v2`, and
`valeu-en`) likely involve EuroEval/LiteLLM/vLLM output constraints,
label extraction, or task-specific prompt/decoding behavior rather than the
multi-turn chat-template issue alone.
