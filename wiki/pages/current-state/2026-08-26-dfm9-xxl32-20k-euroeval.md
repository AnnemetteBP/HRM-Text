---
type: Analysis
title: DFM9 XXL-32 20K EuroEval
description: Completion state and preliminary interpretation of EuroEval at the DFM9 XXL-32 20K EMA checkpoint.
tags: [dfm9, xxl, euroeval, evaluation]
status: draft
last_updated: 2026-08-26
confidence: high
---
# DFM9 XXL-32 20K EuroEval

The scheduler plan
`logs/scheduler/dfm9_XXL32_steps20k_100k_20260826` completed and individually
synced 18 EuroEval tasks for the 20K EMA export. `valeu-da` was intentionally
skipped. `valeu-en` failed after six attempts because none of its 53
predictions contained a permitted candidate label. The checkpoint-level
`suite_avg_v3/euroeval` row remains pending until the wider standard/DFM
checkpoint graph satisfies its average-job dependencies.

Headline results in percentage units:

| Language | Task | Result |
|---|---|---:|
| Danish | Angry Tweets macro F1 | 16.061 |
| Danish | ScaLA-da macro F1 | 33.736 |
| Danish | DaNSK NER micro F1 | 0.000 |
| Danish | MultiWikiQA-da F1 | 0.000 |
| Danish | Nordjylland News chrF3++ | 0.000 |
| Danish | Danish sayings accuracy | 21.406 |
| Danish | Danish citizen tests accuracy | 39.778 |
| Danish | HellaSwag-da accuracy | 24.883 |
| Danish | IFEval-da instruction accuracy | 28.644 |
| English | SST-5 macro F1 | 11.731 |
| English | ScaLA-en macro F1 | 32.865 |
| English | CoNLL NER micro F1 | 0.000 |
| English | SQuAD F1 | 0.000 |
| English | CNN/DailyMail chrF3++ | 0.000 |
| English | Life in the UK accuracy | 28.984 |
| English | HellaSwag accuracy | 21.523 |
| English | IFEval instruction accuracy | 26.007 |
| English/tool use | BFCL-v2 accuracy | 0.000 |

Excluding both VaLEU tasks, a manual invocation of the production normalization
and membership functions gives `suite_avg_v3/euroeval =
0.1586767288296339` with `count = 18` (15.86767288296339%). All 18 expected
keys were present. This value was computed locally on 2026-08-26 and was not
logged to W&B; it is not yet the scheduler's atomic suite-average artifact.

All reported MCC values are exactly zero. Combined with zero NER, reading
comprehension, summarization, and tool-calling scores and near-chance
HellaSwag, this indicates severe early-checkpoint output/label collapse rather
than broad task competence. The citizen test and instruction-following values
are the clearest nonzero signals, but the 20K checkpoint is not yet a useful
instruction model.

## Short-answer generation cap

The subsequent 20K TriviaQA evaluation exposed a latent task-definition issue:
the early checkpoint failed to emit EOS and generated repetitive text to the
4,096-token context limit. In the first completed batch, 223 of 224 responses
used at least 4,000 output tokens, with a mean of 4,048.9. By comparison, the
same task on the mature DFM9 XL 1.8M checkpoint averaged 16.9 output tokens;
2,233 of 2,243 responses used at most 64 tokens and only six reached 4,000.

As of 2026-08-26, `dfm_evals.tasks.gen5` explicitly caps TriviaQA and NQ-Open
at 64 generated tokens. These are short-answer exact/F1 tasks whose prompts
request the fewest possible words. CoQA retains its existing 128-token cap.
Long-form code, instruction-following, translation, correction, and
summarization tasks are unchanged. Already-running Inspect clients must be
restarted to load the new cap; persistent vLLM servers do not require a model
reload.
