---
type: Plan Record
title: Open-Model Precedent
description: 'Part of DFM7 Plan: Open-Model Precedent.'
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
# Open-Model Precedent

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Open-model precedent for math answer contracts, 2026-06-30. Confidence: medium
from inspected public OLMES configs and OLMo 3 public materials. Recent open
training/eval stacks do not rely on an implicit benchmark name hidden from the
model. They make the expected output contract visible through task-specific
few-shot examples, task-specific prompt templates, answer extractors, and/or
format rewards/verifiers.

Observed examples:

- OLMES has separate task configs for GSM8K, Minerva/MATH-style math, MMLU CoT,
  styled math, and reasoning suites. OLMo 3 GSM8K configs use `STD:GSM8k`
  few-shot examples, explicit stop sequences, repeated stochastic samples, and
  `answer_format_correct_cutoff` metadata for format compliance. The OLMo 3
  base-chat suite tracks `gsm8k::olmo3:midtrain`,
  `minerva_math::olmo3:midtrain`, `styled_math500::olmo3:midtrain`, and
  `mmlu:cot::olmo3:midtrain` separately.
- OLMES/Tulu thinker configs explicitly distinguish GSM8K CoT LaTeX variants
  such as `gsm8k::zs_cot_latex`, rather than assuming the model will infer the
  desired final-answer syntax from the dataset name.
- The OLMo 3 report describes math/code improvements from generated/verifiable
  data: programmatically generated problems, thinking traces distilled from
  stronger models, and correctness filtering with output verifiers. This is
  consistent with making the final-answer contract machine-checkable.

DFM7 implication: if we want comparable HRM standard scores, keep the official
eval path fixed and adapt training data toward that path. If we want a stronger
native DFM math eval, add explicit prompt templates and report it as a separate
variant. In either case, the data should not mix bare integers, prose-only
answers, `<think>` continuations, and boxed answers without an explicit
instruction telling the model which format is desired.
