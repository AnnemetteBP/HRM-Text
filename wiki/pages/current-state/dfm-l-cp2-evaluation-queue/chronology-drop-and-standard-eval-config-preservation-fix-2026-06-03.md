---
type: Operational Record
title: DROP and standard-eval config preservation fix (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DROP and standard-eval
  config preservation fix (2026-06-03).'
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
# DROP and standard-eval config preservation fix (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DROP and standard-eval config preservation fix, 2026-06-03. Confidence: high.
Full standard evals run DROP as four shards via `standard_shards_for_task()`,
so the full DROP validation set of about `9536` processed examples is split
into roughly `2384` prompts per shard. `scripts/schedule_checkpoint_evals.sh`
previously launched a single task by replacing the whole `benchmarks:` list with
a minimal one-entry list. That lost YAML per-benchmark generation config and
settings such as MMLU `special_shots`.

`evaluation/main.py` now supports `shard_overrides`, allowing the scheduler to
use `run_only=[TASK]` while preserving the original YAML benchmark entry. The
standard scheduler now launches standard shards with:

```bash
run_only=[DROP] \
shard_overrides.DROP.num_shards=4 \
shard_overrides.DROP.shard_index=0
```

`evaluation/config/hrm_benchmarking.yaml` now makes DROP short-answer behavior
explicit:

```yaml
- name: DROP
  generation_config:
    condition: "direct"
    max_tokens: 64
    stop: "\n\n"
```
