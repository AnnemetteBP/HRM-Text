---
type: Operational Record
title: Generation retention for summarization vs translation evals, verified on (2026-05-27)
description: 'Chronological record from dfm-evals: Generation retention for summarization
  vs translation evals, verified on (2026-05-27).'
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
# Generation retention for summarization vs translation evals, verified on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Generation retention for summarization vs translation evals, verified on
2026-05-27. Confidence: high.

The repo's standard `evaluation.main` path used for `eval/GovReport/*` and
`eval/NordjyllandNews/*` does not persist per-sample generations. It keeps
generated strings in memory, passes them into `benchmark.compute_metrics(...)`,
and prints only progress bars plus the final `EVALUATION SUMMARY` to stdout.
The summarization logs under
`logs/eval/summarization_all_checkpoints_20260527T085348/**/{GovReport,NordjyllandNews}.log`
therefore contain metrics but not prompt/prediction/reference triples.

The Danish translation evals run through `dfm-evals`/Inspect do persist
per-sample records. Each `wmt24pp-en-da` `.eval` zip contains `samples/*.json`
entries with `input`, `target`, `messages`, `output.completion`, `scores`, and
metadata. The Every Eval Ever exports also write `.json` and `.jsonl` copies
under each task's `eee/` directory.
