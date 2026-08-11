---
type: Operational Record
title: BERTScore note, updated on (2026-05-27)
description: 'Chronological record from dfm-evals: BERTScore note, updated on (2026-05-27).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# BERTScore note, updated on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

BERTScore note, updated on 2026-05-27. Confidence: high for local dependency
state, inspected Inspect archives, and generation-retention caveat; medium for
metric usefulness by task. `bert-score` is installed in the main HRM environment
and in the nested `dfm-evals` environment, with `xlm-roberta-large` selected as
the shared multilingual scorer model.

BERTScore is appropriate as an auxiliary metric for tasks with natural-language
predictions and reference text: `wmt24pp-en-da`, `generative-talemaader`,
`gec_dala`, and the new dfm-evals summarization tasks `govreport` and
`nordjyllandnews`. It is less informative but possible for `multi_wiki_qa`
because many answers are only one to three words. It should not be used for
classification/constraint-only tasks such as `danish-citizen-tests`, `dala`,
`piqa`, or `ifeval-da`.

The already completed standard summarization evals cannot be rescored with
BERTScore unless they are rerun, because `evaluation.main` did not persist
prompt/prediction/reference triples. Translation and other dfm-evals tasks can
be rescored from stored Inspect samples because those archives contain
`output.completion` and references. IFEval-DA archives were inspected locally:
samples have an empty `target`, the output is the model's free-form constrained
response, and scoring records instruction-following booleans/counts
(`prompt_level_strict`, `inst_level_strict`, `prompt_level_loose`,
`inst_level_loose`, `num_instructions`) rather than reference similarity.
