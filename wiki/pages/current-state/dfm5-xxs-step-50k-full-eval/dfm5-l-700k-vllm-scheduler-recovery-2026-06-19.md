---
type: Operational Record
title: DFM5-L 700K vLLM Scheduler Recovery, 2026-06-19
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM5-L 700K vLLM Scheduler Recovery,
  2026-06-19.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM5-L 700K vLLM Scheduler Recovery, 2026-06-19

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high for local process inspection, scheduler monitor output, and
log inspection.

The 700K main-run vLLM scheduler plan is:

```text
logs/scheduler/dfm5_L_step700000_vllm_main_20260619
```

It logs to the main W&B run:

```text
entity/project/run: dfm/DFM5/oti1lisg
display name: dfm5-L
```

Two separate issues caused ready shards not to be picked up:

1. GPU5 had an orphaned `VLLM::EngineCore` process from an earlier failed
   scheduler attempt, consuming about 65 GiB in addition to the training
   process. Killing the orphan restored GPU5 to only the training process.
2. The active scheduler runner had exited after a managed Talemaader judge
   startup failure. The monitor still showed stale `running` rows in
   `plan.tsv`, but `ps` showed no live `eval_scheduler run` process, so ready
   rows could not be claimed.

GovReport context overflow was handled by setting a more aggressive DFM eval
task override:

```yaml
max_report_chars=9000
```

in `config/dfm_evals_hrm_single_tasks.yaml`. After this, 15/16 GovReport shards
completed; the remaining shard failed only because of the GPU5 orphan process,
not because of context length. After clearing the orphan, GovReport shard 5
finished and the GovReport merge became ready.

Talemaader requires three GPU residents at once during each shard: the training
process, the HRM vLLM server, and a local `unsloth/gemma-4-E4B-it` judge server.
With `vllm_gpu_memory_utilization=0.35`, judge startup OOMed. Talemaader eval
and merge rows in the 700K plan were adjusted to:

```text
vllm_gpu_memory_utilization=0.25
batch=16
managed judge: unsloth/gemma-4-E4B-it, bfloat16, sdpa
```

The seven stale Talemaader `running` rows were reset to `pending` with
`attempt=0`, and the scheduler was restarted in tmux window:

```text
hrm-0:eval700resume2
```

Code hardening: `eval_scheduler/eval_scheduler/runtime.py` now catches
`SchedulerError` from `run_job()` inside `Runner.run_one()` and converts it to a
retryable status `72`, logging an `ERROR` event instead of crashing the whole
scheduler. This is important for managed judge/vLLM startup failures: a single
bad shard should no longer leave the plan with stale `running` rows and no live
runner.
