---
type: Plan Record
title: Evaluation Gates
description: 'Part of DFM6 Plan: Evaluation Gates.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# Evaluation Gates

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Use the existing DFM5-style sections, but add explicit tool-calling gates:

- Danish: DaLA, GEC-DaLA, Danish Citizen Tests, MultiWikiQA, NordjyllandNews, WMT24++ en-da, IFEval-DA, EuroEval Danish tasks, Danish tool-calling.
- English: ARC-C, BoolQ, DROP, HellaSwag, MMLU, Winogrande, GovReport, English EuroEval tasks.
- Math and code: GSM8K, MATH, HumanEval, BFCL-v2, Danish/English tool-calling.

Decision rule:

- Do not judge DFM6 only by the overall average.
- Track section averages plus individual bottleneck metrics.
- Treat GSM8K, HumanEval, and tool-calling as explicit go/no-go diagnostics because they are known DFM5 weak points.
