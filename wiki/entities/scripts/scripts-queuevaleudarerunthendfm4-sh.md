---
type: Software Reference
title: '`scripts/queue_valeu_da_rerun_then_dfm4.sh`'
description: 'Part of Script Entities: `scripts/queue_valeu_da_rerun_then_dfm4.sh`.'
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
# `scripts/queue_valeu_da_rerun_then_dfm4.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-12. Confidence: high for local syntax check and launch.

Priority EuroEval queue used after original Sapient L `epoch_2` completed only
19/20 EuroEval tasks. Local inspection showed the missing result row was
`valeu-da`; `euroeval.log` ended with `Completed 19 benchmarks, and errored 1
benchmarks`. The script watches GPUs 4-7 and runs:

```text
1. original_sapient/L epoch_2, dataset valeu-da only, separate log dir
2. dfm4/XL-ddp epoch_1
3. dfm4/XL-ddp epoch_2
```

The `valeu-da` rerun writes to:

```text
logs/euroeval/original_sapient_L/epoch_2_valeu_da_rerun
```

It intentionally sets `WANDB_SYNC=0` for the one-dataset rerun and does not
modify `logs/euroeval/original_sapient_L/epoch_2/euroeval_benchmark_results.jsonl`.
The row should be inspected and merged separately after success. DFM4 XL jobs
use the same W&B target as the normal queue.

Launch command:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s priority_valeu_da_then_dfm4 \
  'cd /work/dfm/HRM-Text && scripts/queue_valeu_da_rerun_then_dfm4.sh'
```

`scripts/run_original_sapient_l_euroeval_epochs.sh` launches the four original
Sapient L epoch checkpoints on GPUs 4-7:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s orig_sapient_l_euroeval \
  'cd /work/dfm/HRM-Text && scripts/run_original_sapient_l_euroeval_epochs.sh'
```

Defaults:

```text
CKPT_PATH=checkpoints/original_sapient/L
epochs: epoch_1, epoch_2, epoch_3, epoch_4
GPUs:   4, 5, 6, 7
EUROEVAL_LANGUAGES=da,en
WANDB_PROJECT=Original Plus Mixed Danish Instruction Rich L
WANDB_RUN_ID=origLclean
WANDB_RUN_NAME=original-sapient-L-clean-history
```

The launch does not set `EUROEVAL_FEW_SHOT`, `EUROEVAL_NUM_ITERATIONS`, or
`EUROEVAL_GENERATIVE_TYPE`, so EuroEval uses its standard defaults. Initial
logs showed EuroEval running few-shot and reporting `1/20 benchmarks`, with
all four HRM servers healthy on ports `9741`-`9744`.

`scripts/schedule_checkpoint_evals.sh` and
`scripts/schedule_multiple_checkpoint_evals.sh` support opt-in EuroEval jobs:

```bash
cd /work/dfm/HRM-Text
RUN_EUROEVAL=1 scripts/schedule_checkpoint_evals.sh
```

If EuroEval is not installed in the active environment, either install the repo
extra or use an explicit command:

```bash
uv pip install -e '.[euroeval]'
EUROEVAL_BIN='uv run --no-project --with euroeval euroeval' RUN_EUROEVAL=1 scripts/schedule_checkpoint_evals.sh
```
