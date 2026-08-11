---
type: Plan Record
title: Build Requirements
description: 'Part of DFM8 Plan: Build Requirements.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# Build Requirements

Part of [DFM8 Plan](/pages/dfm8-plan.md).

- Use the Gemma4 tokenizer and `data_io/chat_templates/gemma4_native_chat.jinja`
  throughout.
- Keep DFM8 in separate paths, for example `data/tokenized_dfm8`,
  `data/sampled_dfm8`, and `config/data/dfm8.yaml`.
- Do not call trained-on benchmark splits held out. If a benchmark-like source
  is used for training, as planned for full TV2R instruction inclusion, mark
  corresponding eval scores as non-held-out/train-contaminated and add a clean
  replacement diagnostic if needed.
- Add analytics tables comparing DFM7 vs DFM8 by Danish, English,
  math/tool/code, strict boxed math, mixed math, MCQ math, and native tool-use
  buckets.
