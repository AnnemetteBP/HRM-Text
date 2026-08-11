---
type: Plan Record
title: Objectives
description: 'Part of DFM8 Plan: Objectives.'
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
# Objectives

Part of [DFM8 Plan](/pages/dfm8-plan.md).

DFM8 should keep the DFM7 gains from Gemma4 tokenization, native tool-calling
data, and broader Danish instruction data, but fix two remaining training-data
contract problems:

- Freeform math should consistently teach the contract used by MATH-style evals:
  reasoning if useful, then exactly one final `\boxed{...}` answer.
- Native tool-calling should keep one clean Gemma4/OpenAI-compatible tool-call
  interface and avoid mixed XML/Python-call/string-argument supervision.

DFM8 should also add Danish education/school instruction coverage through
`kobprof/skolegpt-instruct`, pending local row/schema/license inspection.
