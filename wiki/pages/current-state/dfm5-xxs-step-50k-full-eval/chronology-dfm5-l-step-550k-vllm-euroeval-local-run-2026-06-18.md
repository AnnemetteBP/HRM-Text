---
type: Operational Record
title: DFM5-L step-550K vLLM EuroEval local run (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5-L step-550K
  vLLM EuroEval local run (2026-06-18).'
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
# DFM5-L step-550K vLLM EuroEval local run (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5-L step-550K vLLM EuroEval local run, 2026-06-18. Confidence: high for
local logs and merged metric files. A non-W&B-synced vLLM FA4 EuroEval run was
launched for `checkpoints/dfm5/L` `step_550000` using the EMA HF export at
`exports/dfm5_L_step550000_ema_hf`, `MAX_CONTEXT=4096`,
`EUROEVAL_BATCH_SIZE=16`, and `EUROEVAL_MAX_CONCURRENT_CALLS=32`.

```text
scheduler/log root: logs/eval/dfm5_L_step550000_20260618_vllm_fa4_local_euroeval
EuroEval root:      logs/euroeval/dfm5_L_step550000_20260618_vllm_fa4_local_euroeval/step_550000
native comparison:  logs/euroeval/dfm5_L_step550000_full_native_followup_20260617/step_550000
```

The queue finished with `19/20` EuroEval tasks successful. `valeu-en` failed
all three attempts because EuroEval found no candidate label for `1/53`
predictions and aborts VaLEU tasks on invalid outputs. The vLLM run should
therefore not be W&B-synced as a replacement for the native 550K EuroEval row.

Headline comparison against the native 550K EuroEval artifacts shows that vLLM
is not currently EuroEval-parity for many classification/tagging tasks:

```text
angry-tweets macro_f1:        native 72.54  vLLM 28.17
scala-da macro_f1:            native 52.60  vLLM 33.74
dansk micro_f1:               native 36.65  vLLM 14.95
multi-wiki-qa-da f1:          native 79.90  vLLM 78.29
nordjylland-news chr_f3pp:    native 32.60  vLLM 24.07
danske-talemaader accuracy:   native 39.38  vLLM 28.44
danish-citizen-tests accuracy:native 55.67  vLLM 41.44
hellaswag-da accuracy:        native 42.77  vLLM 24.14
ifeval-da instr accuracy:     native 52.27  vLLM 52.72
sst5 macro_f1:                native 71.53  vLLM 40.70
scala-en macro_f1:            native 76.09  vLLM 32.87
conll-en micro_f1:            native 57.05  vLLM 21.11
squad f1:                     native 88.83  vLLM 85.90
cnn-dailymail chr_f3pp:       native 36.39  vLLM 31.97
life-in-the-uk accuracy:      native 51.64  vLLM 29.69
hellaswag accuracy:           native 48.24  vLLM 25.78
ifeval instr accuracy:        native 69.56  vLLM 69.46
bfcl-v2 tool_calling_accuracy:native 0.00   vLLM 23.12
```

Interpretation: the vLLM export path is usable enough for some generative,
extractive QA, and instruction-following tasks, but the current OpenAI/vLLM
EuroEval prompt/decoding path is not equivalent to the native HRM evaluation
path for short-label classification and sequence-tagging tasks. Investigate
prompt formatting, chat template behavior, stopping/max-token policy, and
label-constrained decoding before trusting vLLM EuroEval classification scores.
