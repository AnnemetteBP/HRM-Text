---
type: Policy Record
title: Objective
description: 'Part of Data Mix Policy: Objective.'
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
# Objective

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Replace or supplement Sapient's original cleaned corpus with a cleaner, more controllable mix while preserving HRM-Text's PrefixLM training format:

```text
instruction span + response span
```

This repo does not currently train on raw documents as ordinary causal-LM pretraining. Raw text must be converted to continuation rows:

```text
condition = direct
instruction = ""
response = document chunk
```

Primary evaluation goal, clarified on 2026-06-01: data-mix changes should aim
to be strong across all currently run evaluations, not just Danish evaluations.
This includes English factual/reasoning/reading-comprehension benchmarks
(`MMLU`, `Winogrande`, `ARC-C`, `BoolQ`, `DROP`, `HellaSwag`, `MATH`,
`GSM8k`), Danish dfm-evals (`danish-citizen-tests`, `dala`, `gec_dala`,
`wmt24pp-en-da`, `multi_wiki_qa`, `piqa`, `ifeval-da`,
`generative-talemaader`, summarization tasks such as `NordjyllandNews`), and
code/human-eval style tasks. Treat drops in any of these families as a
data-balance regression unless an ablation intentionally trades one family
against another.
