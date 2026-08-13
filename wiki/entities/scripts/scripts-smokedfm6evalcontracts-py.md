---
type: Software Reference
title: '`scripts/smoke_dfm6_eval_contracts.py`'
description: 'Part of Script Entities: `scripts/smoke_dfm6_eval_contracts.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/smoke_dfm6_eval_contracts.py`

Part of [Script Entities](/entities/scripts.md).

Last updated: 2026-06-24
Confidence: high
Scope: DFM6 eval preflight/smoke test.

This script is a contract smoke test for DFM6 checkpoint evaluations. It does
not run model generations. Instead it checks the eval/export plumbing that can
silently invalidate metrics:

- DFM6 HF export tokenizer/config metadata: BOS `2`, EOS `<turn|>` id `106`,
  PAD `0`, `fix_mistral_regex=True`, and a present Gemma chat template.
- Evaluation and data-prep Gemma template files have identical SHA-256 hashes.
- A rendered Gemma prompt contains the user turn and ends at
  `<|turn>model`.
- `evaluation/config/dfm6_vllm_benchmarking.yaml` contains the expected
  standard benchmark set, per-task generation limits, and
  `stop_token_ids: [106]`.
- DFM single-task and 32-way IFEval configs contain the expected tasks,
  shard arguments, GovReport truncation, and max-generation settings.
- A generated in-memory scheduler plan routes standard, DFM, and EuroEval jobs
  through vLLM/native-proxy with Gemma BFCL parser mode, the intended
  utilization/batch settings, `suite_avg_v2`/`headline_avg_v2` average prefixes,
  and the correct average dependencies.

Run before launching a DFM6 full eval:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python scripts/smoke_dfm6_eval_contracts.py
```

Latest verified output on 2026-06-24:

```text
DFM6 eval smoke passed. Wrote /work/dfm/HRM-Text/logs/smoke/dfm6_eval_contracts_20260624_080712.json
Standard tasks: 10
DFM tasks: 10 + 32 IFEval shards
EuroEval groups: 20 (valeu-da skipped by plan)
```

## Segmented training/evaluation campaigns
Last updated: 2026-07-28
Confidence: high
Scope: exact-step training stops and non-blocking eval post-processing.

- `pretrain.py stop_after_step=N` forces a regular `step_N` checkpoint after
  optimizer/EMA step `N`, then exits through the normal distributed and W&B
  shutdown path. Null preserves ordinary uninterrupted training.
- `train_until_step` reserves every GPU passed to the scheduler atomically,
  closes persistent vLLM leases, runs an explicit training command, and accepts
  success only after the target checkpoint, carries, and sidecar verify.
- `deps_mode` is explicit in `plan.tsv`. Existing rows default to `success`;
  `terminal` is opt-in.
- `terminal_barrier` treats done, failed, skipped, and permanently unreachable
  eval rows as terminal, but waits for active or runnable retries.
- `teardown_eval` closes persistent evaluator leases. The next training segment
  depends on teardown rather than merge/sync/average, so failed eval
  post-processing does not leave training GPUs idle.
- `plan add-eval-release` adds the terminal barrier and teardown for one
  checkpoint. `plan add-training` adds the next all-GPU segment and can inject
  a verified prior checkpoint with `--resume-from-tag`.

## `scripts/follow_latest_training_log.sh`
Added on 2026-07-30. Confidence: high from a live tmux smoke test.

Follows the newest `train_until_step_*.log` below a training-log root and
automatically replaces its `tail -F` child when the scheduler starts a newer
segment. This avoids hard-coding one segment path in a long-running tmux
window. For the DFM8 XXL campaign, `hrm-0:8` runs:

```bash
scripts/follow_latest_training_log.sh logs/training/dfm8_XXL_1epoch 10
```

## `scripts/export_wandb_metrics_csv.py`
Added on 2026-07-31. Confidence: high from a complete remote-history export
and CSV integrity validation.

Streams unsampled W&B history into a tidy CSV with one numeric metric
observation per row. It includes training, standard eval, DFM eval, EuroEval,
headline-average, and suite-average namespaces plus W&B step/time metadata.
Use `--workers` to partition the W&B step range into non-overlapping parallel
API scans; the parts are merged in step order and removed afterward.

```bash
python scripts/export_wandb_metrics_csv.py \
  peter-sk-sdu/DFM5/dfm8-xl-from-dfm6-dfm7-epoch5-clean-full \
  exports/metrics/dfm8-xl-clean-full-from-dfm6-dfm7-epoch5_metrics.csv \
  --workers 8 \
  --progress-every 10000
```
