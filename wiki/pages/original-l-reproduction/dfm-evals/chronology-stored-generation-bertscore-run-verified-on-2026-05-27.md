---
type: Operational Record
title: Stored-generation BERTScore run, verified on (2026-05-27)
description: 'Chronological record from dfm-evals: Stored-generation BERTScore run,
  verified on (2026-05-27).'
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
# Stored-generation BERTScore run, verified on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Stored-generation BERTScore run, verified on 2026-05-27. Confidence: high.

`scripts/score_stored_dfm_eval_bertscore.py` computes offline BERTScore from
stored Inspect `.eval` archives without rerunning model inference. It uses
`bert-score` with `xlm-roberta-large`, chooses the best reference by F1 when a
sample has multiple references, and deduplicates repeated archives by
`family/epoch/task`, keeping the complete archive with the largest sample
count/newest mtime. The full command was:

```bash
cd /work/dfm/HRM-Text
python scripts/score_stored_dfm_eval_bertscore.py \
  --batch-size 32 \
  --output logs/dfm_evals/bertscore_xlm_roberta_large/stored_metrics.json \
  2>&1 | tee logs/dfm_evals/bertscore_xlm_roberta_large/stored_metrics.log
```

The run completed for 28 stored checkpoint/eval combinations:

```text
original_sapient epoch 1: gec-dala 0.898468, generative-talemaader 0.839199, multi-wiki-qa 0.794420, wmt24pp-en-da 0.857832
original_sapient epoch 2: gec-dala 0.965995, generative-talemaader 0.841373, multi-wiki-qa 0.801824, wmt24pp-en-da 0.866615
original_sapient epoch 3: gec-dala 0.968691, generative-talemaader 0.844272, multi-wiki-qa 0.815243, wmt24pp-en-da 0.873644
original_sapient epoch 4: gec-dala 0.982645, generative-talemaader 0.839617, multi-wiki-qa 0.831438, wmt24pp-en-da 0.876078
original_plus_mixed_danish_instruction_rich epoch 1: gec-dala 0.971922, generative-talemaader 0.857760, multi-wiki-qa 0.988429, wmt24pp-en-da 0.934503
original_plus_mixed_danish_instruction_rich epoch 2: gec-dala 0.807852, generative-talemaader 0.858760, multi-wiki-qa 0.982432, wmt24pp-en-da 0.937346
original_plus_mixed_danish_instruction_rich epoch 3: gec-dala 0.862708, generative-talemaader 0.859533, multi-wiki-qa 0.978532, wmt24pp-en-da 0.939909
```
