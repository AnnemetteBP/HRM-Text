---
type: Plan Record
title: Danish DAISY Eval Candidate
description: 'Part of DFM8 Plan: Danish DAISY Eval Candidate.'
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
# Danish DAISY Eval Candidate

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-09. Confidence: medium from the Hugging Face dataset card.

Add `schneiderkamplab/SDU-Daisy` as a DFM8 evaluation candidate, not a training
source by default. The dataset card describes SDU DAISY as a Danish cultural
benchmark over the official Danish Culture Canon, with QA/text-generation
tasks, parquet format, Danish language, MIT license, and 592 train examples.
It is small enough to run as a full diagnostic eval.

Integration plan:

1. Download and inspect schema locally. The card lists columns `id`,
   `Question`, `Answer`, and `Subject`.
2. Implement a DFM eval suite that prompts in Danish and scores exact-ish/F1
   overlap plus optional judge-based cultural relevance/accuracy if needed.
3. Keep it out of DFM8 training unless we deliberately mark the eval as
   contaminated/non-held-out.
4. Report it under Danish/culture, not general Danish language quality.
