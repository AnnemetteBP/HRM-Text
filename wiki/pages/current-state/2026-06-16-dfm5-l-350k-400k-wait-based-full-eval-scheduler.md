---
type: Operational Record
title: 2026-06-16 DFM5 L 350K/400K Wait-Based Full Eval Scheduler
description: 'Part of Current State: 2026-06-16 DFM5 L 350K/400K Wait-Based Full Eval
  Scheduler.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-16 DFM5 L 350K/400K Wait-Based Full Eval Scheduler

Part of [Current State](/pages/current-state.md).

Confidence: high for local commands, plan state, and tmux launch.

Created a new `eval_scheduler` plan for DFM5 L full evaluations at
`step_350000` and `step_400000`:

```text
plan_dir: logs/scheduler/dfm5_L_350k_400k_full_20260616
checkpoint path: checkpoints/dfm5/L
W&B project/run: DFM5 / oti1lisg / dfm5-L
model prefix: hrm-dfm5-L
```

The 350K subgraph uses:

```text
ckpt_tag: step_350000
eval_epoch: 1.932619232753049
standard log root: logs/eval/dfm5_L_step350000_full_20260616_new_scheduler
dfm log root: logs/dfm_evals/dfm5_L_step350000_full_20260616_new_scheduler
euroeval log root: logs/euroeval/dfm5_L_step350000_full_20260616_new_scheduler
```

The 400K subgraph was appended to the same plan and waits independently for:

```text
ckpt_tag: step_400000
eval_epoch: 2.208707694574913
standard log root: logs/eval/dfm5_L_step400000_full_20260616_new_scheduler
dfm log root: logs/dfm_evals/dfm5_L_step400000_full_20260616_new_scheduler
euroeval log root: logs/euroeval/dfm5_L_step400000_full_20260616_new_scheduler
```

Follow-up append, 2026-06-16. Confidence: high for locked local plan edit and
plan inspection. The same scheduler plan now also contains chained subgraphs
for `step_450000` and `step_500000`. These were appended in one locked write,
then dependency-gated so they run strictly after the prior checkpoint's report:

```text
step_400000 report-00420 -> step_450000 wait-00421
step_450000 report-00630 -> step_500000 wait-00631
```

The new x-axis values are:

```text
step_450000 eval_epoch: 2.4847961563967775
step_500000 eval_epoch: 2.7608846182186415
```

The new log roots are:

```text
logs/eval/dfm5_L_step450000_full_20260616_new_scheduler
logs/dfm_evals/dfm5_L_step450000_full_20260616_new_scheduler
logs/euroeval/dfm5_L_step450000_full_20260616_new_scheduler
logs/eval/dfm5_L_step500000_full_20260616_new_scheduler
logs/dfm_evals/dfm5_L_step500000_full_20260616_new_scheduler
logs/euroeval/dfm5_L_step500000_full_20260616_new_scheduler
```

All subgraphs include `wait_checkpoint` rows with 60-second polling. Batch
starts are standard `64`, dfm `32`, dfm IFEval-DA `32`, and EuroEval `16`; the
scheduler halves the batch size on retry after failures/OOMs.

Judged `generative_talemaader` rows are configured with the verified
Gemma judge endpoint:

```text
initial_batch: 16
metadata.max_connections: 4
metadata.judge_model: openai/gemma-4-e4b-judge
metadata.judge_base_url: http://127.0.0.1:8099/v1
```

The 350K subgraph is complete: standard, dfm-evals, EuroEval, Talemaader merge,
headline averages, and report generation finished. `docs/dfm5.md` has been
regenerated with a `DFM5-L 350K` column. The 400K `wait_checkpoint` row is the
only active scheduler row until the 400K checkpoint is fully written.

The scheduler was launched in tmux session `hrm-0`, window `8:eval350400`, with
monitor window `9:mon350400`:

```bash
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_350k_400k_full_20260616 \
  --gpus 0,1,2,3,4,5,6,7

python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_350k_400k_full_20260616 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 5
```

Startup status: `step_350000` checkpoint wait completed immediately because the
checkpoint was already fully present; the first eight 350K EuroEval jobs
started. The `step_400000` wait row is running as a non-GPU job and will unblock
the 400K eval DAG once that checkpoint is fully written.

Follow-up fix, 2026-06-16. Confidence: high. The first EuroEval launches failed
with status `127` because the new scheduler passed
`scripts/euroeval_api_no_flash_attn_guard.py` as a relative `EUROEVAL_BIN`, and
`scripts/run_euroeval_on_checkpoint.sh` changes directory into the EuroEval log
root before invoking that binary. `eval_scheduler/eval_scheduler/runtime.py`
now resolves relative `.py` EuroEval binaries to absolute paths. The eight
failed EuroEval rows were reset to `pending` with attempt `0`, `stop.request`
was cleared, and the scheduler was relaunched in tmux window `eval350400b`.
Process inspection confirmed active EuroEval clients using absolute
`/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py` paths.

Superseding scheduler update, 2026-06-16. Confidence: high for process
inspection, locked plan generation, dependency inspection, and launch status.
After `step_400000` became ready, the original plan above had started EuroEval
jobs on GPUs 0 and 1 while a separate Qwen external scheduler also existed.
Because separate `eval_scheduler run` instances do not share a global GPU
lease, the original DFM5 scheduler was stopped completely: the scheduler
process group, two active EuroEval client/server pairs, and monitor were
terminated, and the two running rows were reset to pending.

A fresh single ordered plan now owns the combined work:

```text
logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616
```

It contains three subgraphs in this order:

1. `qwen35_2b`: external Qwen3.5-2B full standard + DFM + EuroEval evals,
   using the local snapshot
   `/home/ucloud/.cache/huggingface/hub/models--Qwen--Qwen3.5-2B/snapshots/15852e8c16360a2fea060d615a32b45270f8a8fc`,
   one vLLM server per GPU worker/task, and `--enforce-eager`.
2. `step_400000`: full DFM5 L evals synced to W&B run `oti1lisg`.
3. `step_450000`: full DFM5 L evals synced to W&B run `oti1lisg`, with a
   checkpoint wait row.

The dependency chain was manually enforced in `plan.tsv`:

```text
wait-00209 step_400000 deps: average-00208
wait-00418 step_450000 deps: average-00417
```

The ordered scheduler was launched on all 8 GPUs in tmux session `hrm-0`,
windows `qwen400450` and `monq400450`:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler run \
  --plan-dir logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616 \
  --gpus 0,1,2,3,4,5,6,7

python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/qwen_then_dfm5_L_400k_450k_20260616 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30
```

Initial dependency inspection showed Qwen with 8 running jobs and 200 pending;
all `step_400000` and `step_450000` jobs were pending behind the explicit
dependencies.
