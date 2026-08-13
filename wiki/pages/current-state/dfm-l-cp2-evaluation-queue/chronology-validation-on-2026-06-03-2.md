---
type: Operational Record
title: Validation on (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Validation on
  (2026-06-03).'
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
# Validation on (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Validation on 2026-06-03 passed with `python -m py_compile evaluation/main.py`,
`bash -n scripts/schedule_checkpoint_evals.sh`, and a config-only OmegaConf
check showing `run_only ['DROP']`, preserved DROP generation config
`condition=direct`, `max_tokens=64`, `stop="\n\n"`, and shard override
`num_shards=4`, `shard_index=0`. Confidence: high.

MATH/GSM8k standard-eval limits, 2026-06-03. Confidence: high.
MATH is intentionally a CoT eval in the standard HRM config, using the global
`condition: synth,cot` and `max_context: 3072`. Full MATH has `5000` examples
and is sharded into `64` shards, so shard 0 has `79` prompts. Active lite
timing showed shard 0 taking roughly one hour; the runtime comes from long CoT
generation, not from a huge shard count like DROP. To make the intended limit
explicit rather than relying on `SimpleEngine.generate()` defaulting
`max_tokens` to `max_context`, `evaluation/config/hrm_benchmarking.yaml` now
sets `max_tokens: 3072` for both `GSM8k` and `MATH`. A config-only check showed
future MATH/GSM8k launches resolve to `condition=synth,cot`,
`max_context=3072`, `max_tokens=3072`, and `batch_size=8` with the correct
shard override. Confidence: high.

Original-code comparison for MATH/GSM8k, 2026-06-03. Confidence: high.
The upstream/original `evaluation/config/hrm_benchmarking.yaml` used global
generation settings `batch_size: 33`, `max_context: 3072`, `temperature: 0.0`,
and `condition: "synth,cot"` for both `GSM8k` and `MATH`, with no explicit
`max_tokens`. The original `SimpleEngine.generate()` set `max_tokens =
max_context` when `max_tokens` was omitted, so the effective original
MATH/GSM8k output cap was `3072`. The local `max_tokens: 3072` entries are
therefore behavior-preserving for output length. Differences from the original
single-process config are operational: the scheduler shards MATH/GSM8k and
forces `generation_config.batch_size=8` for memory/scheduling stability rather
than using the config default `batch_size: 33`. Confidence: high.
