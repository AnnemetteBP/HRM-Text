---
type: Operational Record
title: DROP standard-eval slowness diagnosis (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DROP standard-eval
  slowness diagnosis (2026-06-03).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# DROP standard-eval slowness diagnosis (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DROP standard-eval slowness diagnosis, 2026-06-03. Confidence: high.
The active lite DROP shard is large because the EleutherAI DROP validation set
contains about `9536` examples after `lm_eval.tasks.drop.utils.process_docs`;
with the current `DROP` shard count of `4`, shard 0 has `2384` prompts. It is
also slow because each prompt is few-shot reading comprehension with long
passages, and `SimpleEngine.generate()` defaults `max_tokens` to
`max_context` when no explicit `max_tokens` is set. The active DROP log shows
it is running with `max_context: 3072`, `batch_size: 8`, and no explicit
`max_tokens`, so each short-answer DROP item can decode up to `3072` new
tokens. Confidence: high.

There is also a scheduler/config interaction to fix for future standard evals.
`evaluation/config/hrm_benchmarking.yaml` intends DROP to use
`generation_config.condition: direct`, but `scripts/schedule_checkpoint_evals.sh`
launches single-task shards by overriding Hydra/OmegaConf with
`benchmarks=[{name: TASK, num_shards: ..., shard_index: ...}]`. That replaces
the YAML benchmark entry and loses per-benchmark generation overrides. The
active DROP log confirms it used the global `condition: synth,cot` rather than
the intended `direct`. Confidence: high.

At `08:00 CEST`, active DROP shard 0 had processed `120 / 2384` samples in
`3067s`, or about `141 samples/hour`. A linear estimate from that point was
about `16.1h` remaining for that single shard, not multiple days. This is still
too slow for a lite probe. Future lite probes should either omit DROP, use a
much smaller DROP shard/sample cap, or run DROP with a short-answer
`max_tokens` cap and preserved `direct` condition. Confidence: high for the
measured rate; medium for the recommended cap until validated.
