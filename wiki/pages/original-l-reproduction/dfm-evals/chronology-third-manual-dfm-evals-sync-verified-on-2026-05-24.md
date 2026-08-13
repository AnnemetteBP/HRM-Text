---
type: Operational Record
title: Third manual dfm-evals sync, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Third manual dfm-evals sync, verified
  on (2026-05-24).'
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
# Third manual dfm-evals sync, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Third manual dfm-evals sync, verified on 2026-05-24: completed WMT24++ and MultiWikiQA logs were exported and logged to W&B run `origLclean`. The sync included epoch 1 WMT24++, epoch 3 WMT24++ and MultiWikiQA, and epoch 4 WMT24++ and MultiWikiQA. A follow-up sync in the same turn added epoch 1 MultiWikiQA and epoch 2 WMT24++ after those files completed. Confidence: high.

Third/follow-up manual sync results:

```text
epoch 1:
  dfm_eval/wmt24pp-en-da/chrf3pp/mean = 0.19774
  dfm_eval/multi_wiki_qa/exact_match/mean = 0.00000
  dfm_eval/multi_wiki_qa/f1/mean = 0.00970

epoch 2:
  dfm_eval/wmt24pp-en-da/chrf3pp/mean = 0.22980

epoch 3:
  dfm_eval/wmt24pp-en-da/chrf3pp/mean = 0.23627
  dfm_eval/multi_wiki_qa/exact_match/mean = 0.04688
  dfm_eval/multi_wiki_qa/f1/mean = 0.10095

epoch 4:
  dfm_eval/wmt24pp-en-da/chrf3pp/mean = 0.24968
  dfm_eval/multi_wiki_qa/exact_match/mean = 0.09424
  dfm_eval/multi_wiki_qa/f1/mean = 0.17277
```
