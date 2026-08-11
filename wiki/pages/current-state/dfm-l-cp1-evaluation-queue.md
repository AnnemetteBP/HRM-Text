---
type: Operational Record
title: DFM L CP1 Evaluation Queue
description: 'Part of Current State: DFM L CP1 Evaluation Queue.'
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
# DFM L CP1 Evaluation Queue

Part of [Current State](/pages/current-state.md).

Updated on 2026-05-29. Confidence: high.

`scripts/schedule_checkpoint_evals.sh` is a generic 8-GPU checkpoint eval
scheduler derived from the original+mixed CP3/CP4 scheduler. For DFM L CP1 it
targets:

- `CKPT_PATH=checkpoints/dfm/L`
- `EPOCH=1`
- `WANDB_PROJECT="DFM L"`
- `WANDB_RUN_ID=kgnbdmwf`
- `WANDB_RUN_NAME=dfm-L`

Superseded on 2026-05-29: the initial dry-run used 16 MATH shards and 16
IFEval-DA shards.

Current sharding policy on 2026-05-29. Confidence: high for implemented
standard and DFM behavior.

Runtime buckets:

- `<10m`: 1 shard.
- `10-20m`: 2 shards.
- `20-40m`: 4 shards.
- `40-80m`: 8 shards.
- `80-160m`: 16 shards.
- `160-320m`: 32 shards.

Implemented in `scripts/schedule_checkpoint_evals.sh`:

- Standard evals are generically shardable through `evaluation/main.py`, which
  now accepts `num_shards` and `shard_index` in each benchmark config and slices
  prompts/targets after benchmark construction.
- Standard shard metrics are merged with `scripts/merge_standard_eval_shards.py`
  before W&B logging.
- IFEval-DA defaults to 32 shards via
  `config/dfm_evals_hrm_ifeval_da_32_shards.yaml`.
- DFM eval tasks now accept `num_shards` and `shard_index` through a shared
  `dfm-evals/dfm_evals/tasks/_sharding.py` helper.
- Sharded DFM task metrics are merged from Inspect `.eval` sample records with
  `scripts/merge_dfm_eval_shards.py` before W&B logging. Shards do not log
  partial metrics as full metrics.

Superseded on 2026-05-29: the DFM CP1 dry-run queue had `112` jobs with
`MATH` split into `8` shards. Observed CP1 MATH shard runtime was about an hour
or more for `625` samples, which violates the target of roughly ten minutes per
shard.

Current future-run queue policy on 2026-05-29. Confidence: high.

- `GSM8k`: 8 shards.
- `DROP`: 4 shards.
- `MMLU`: 4 shards.
- `ARC`: 1 shard.
- `HellaSwag`: 2 shards.
- `Winogrande`: 1 shard.
- `BoolQ`: 1 shard.
- `MATH`: 64 shards.
- `danish_citizen_tests`: 1 shard.
- `dala`: 1 shard.
- `gec_dala`: 2 shards.
- `wmt24pp_en_da`: 8 shards.
- `multi_wiki_qa`: 2 shards.
- `piqa`: 1 shard.
- `generative_talemaader`: 8 shards.
- `govreport`: 16 shards.
- `nordjyllandnews`: 8 shards.
- `humaneval`: 4 shards.
- `ifeval-da`: 32 shards.

Prior status logs show the longest tails were IFEval-DA, MATH, GSM8k,
WMT24++ en-da, generative-talemaader, and summarization tasks with BERTScore.

Validation:

- `python -m py_compile` passed for the scheduler helpers and patched eval
  task files.
- `bash -n scripts/schedule_checkpoint_evals.sh` passed.
- `DRY_RUN=1 ... scripts/schedule_checkpoint_evals.sh` produced the 112-job
  CP1 queue.
- A zero-sample Inspect probe for `hrm_danish_multi_wiki_qa` with
  `-T num_shards=2 -T shard_index=0` resolved to
  `dataset: MultiWikiQA-da-shard-0-of-2`.
- A zero-sample Inspect probe for `hrm_code_humaneval_local` with
  `-T num_shards=4 -T shard_index=0` resolved to
  `dataset: humaneval-shard-0-of-4`.
- A dry run after the MATH adjustment confirmed that
  `scripts/schedule_checkpoint_evals.sh` queues `64` standard `MATH` shards.

Launch state on 2026-05-29. Confidence: high.

Superseded: the DFM L CP1 112-job eval scheduler was initially queued behind a
watcher because the active DFM L training run still occupied all 8 GPUs with
high utilization.

Updated later on 2026-05-29: the user confirmed the GPUs had enough headroom,
so the watcher was stopped and the scheduler was launched immediately while the
DFM L training run was still active. Command:

```bash
EPOCH=1 CKPT_PATH=checkpoints/dfm/L GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm_L_epoch1_queued_all \
DFM_LOG_ROOT=logs/dfm_evals/dfm_L_epoch1_queued_all \
WANDB_PROJECT="DFM L" WANDB_RUN_ID=kgnbdmwf WANDB_RUN_NAME=dfm-L \
MODEL_PREFIX=hrm-dfm-L scripts/schedule_checkpoint_evals.sh
```

Files:

- Scheduler PID file: `logs/eval/dfm_L_epoch1_queued_all/scheduler.pid`
- Launcher log: `logs/eval/dfm_L_epoch1_queued_all.launcher.log`
- Status log: `logs/eval/dfm_L_epoch1_queued_all/status.tsv`
- Queue file: `logs/eval/dfm_L_epoch1_queued_all/jobs.tsv`

Verified immediately after launch:

- Scheduler PID: `2285914`.
- Queue: `112` jobs.
- Checkpoint readiness passed for `checkpoints/dfm/L` epoch 1.
- Workers started, with staggered first jobs beginning on `GSM8k` shards.

Completion inspection on 2026-05-29. Confidence: high.

The DFM L CP1 scheduler exited after all `112` queued jobs reached `END`
status, but final aggregation reported two failures:

```text
FINAL_MERGE_STANDARD_MATH_FAILED
FINAL_MERGE_DFM_generative_talemaader_FAILED
FINAL_MERGE_END
```

Successful synced aggregates include standard `ARC`, `BoolQ`, `DROP`,
`GSM8k`, `HellaSwag`, `MMLU`, and `Winogrande`, plus DFM `dala`,
`danish_citizen_tests`, `gec_dala`, `govreport`, `humaneval`,
`multi_wiki_qa`, `nordjyllandnews`, `piqa`, `wmt24pp_en_da`, and merged
`ifeval-da`. The merged IFEval-DA file is
`logs/dfm_evals/dfm_L_epoch1_queued_all/merged_ifeval_da_metrics.json` and
contains `541` samples with
`dfm_eval/ifeval-da/instruction_following/final_acc=0.393870787633715`.

`MATH` failed only for shard `4` of `8`. Its log is
`logs/eval/dfm_L_epoch1_queued_all/standard_shards/MATH/MATH_shard_4_of_8.log`
and shows an HF Hub `504 Gateway Time-out` while loading
`EleutherAI/hendrycks_math` `precalculus`; the scheduler correctly recorded
`END standard MATH shard_4_of_8 gpu_0 status_1`. The other seven MATH shards
have summaries and do not need to be rerun.

`generative_talemaader` failed at merge time because the wrapper task did not
forward `num_shards` and `shard_index`; each of the eight launched jobs ran the
full `808` samples and therefore produced duplicate sample IDs such as `dtm_0`.
`dfm-evals/dfm_evals/tasks/talemaader/task.py` was patched so
`generative_talemaader()` accepts and forwards `num_shards` and `shard_index`.
`python -m py_compile` passes, and a zero-sample probe now resolves to
`dataset: generative-talemaader-shard-0-of-8` without unused-parameter
warnings:

```bash
OPENAI_API_KEY=inspectai uv run --project dfm-evals evals suite hrm_danish_generative_talemaader \
  --file config/dfm_evals_hrm_single_tasks.yaml \
  --target-model openai/dummy \
  --target-base-url http://127.0.0.1:9/v1 \
  --judge-model openai/dummy \
  --judge-base-url http://127.0.0.1:9/v1 \
  --mode set -- -T num_shards=8 -T shard_index=0 --limit 0 \
  --log-dir /tmp/hrm_talemaader_shard_probe --log-dir-allow-dirty
```

The already completed `generative_talemaader` shard `0` is actually a full run
over all `808` samples, so it can be logged as the full CP1 talemaader result
without rerunning judge inference. Verified local merge from only that `.eval`
produces
`dfm_eval/generative-talemaader/model_graded_fact/accuracy=0.07920792079207921`,
`accuracy_stderr=0.008161235917216217`, and `n=808`.

Repair update on 2026-05-29. Confidence: high.

The complete `generative_talemaader` shard `0` `.eval` was merged and synced to
W&B run `kgnbdmwf` in project `DFM L` using:

```bash
python scripts/merge_dfm_eval_shards.py \
  logs/dfm_evals/dfm_L_epoch1_queued_all/generative_talemaader/shard_0_of_8/epoch_1/inspect/*.eval \
  --task generative_talemaader \
  --epoch 1 \
  --output logs/dfm_evals/dfm_L_epoch1_queued_all/generative_talemaader/merged_metrics.json \
  --log-wandb \
  --project "DFM L" \
  --run-id kgnbdmwf \
  --run-name dfm-L
```

Future scheduler runs are guarded against the same talemaader failure mode:
`scripts/schedule_checkpoint_evals.sh` now checks each dfm-evals shard log for
Inspect warnings that `num_shards` or `shard_index` were not used and fails that
job instead of treating it as valid shard output. The scheduler also defaults to
`MAX_RETRIES=3`, meaning each failed job can be attempted four total times, and
DFM/IFEval shard output directories are cleared before each attempt so partial
failed `.eval` files do not contaminate the final merge.

`MATH` shard `4` of `8` was restarted manually on GPU `0` with:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 python -u -m evaluation.main \
  config=evaluation/config/hrm_benchmarking.yaml \
  ckpt_path=checkpoints/dfm/L \
  ckpt_epoch=1 \
  "benchmarks=[{name: MATH, num_shards: 8, shard_index: 4}]" \
  generation_config.batch_size=8 \
  > logs/eval/dfm_L_epoch1_queued_all/standard_shards/MATH/MATH_shard_4_of_8.log 2>&1
```

For this already-started CP1 repair, keep the running `shard_4_of_8` and merge
it with the seven completed `of_8` shard logs. Switching CP1 repair to `64`
shards would require either rerunning all MATH under the new layout or adding a
one-off range slicer for only the missing eighth.

Final CP1 eval repair result on 2026-05-29. Confidence: high.

The restarted `MATH` shard `4` finished successfully with `n=625`,
`acc=0.3952`, and `invalid=0.1200`. All eight `MATH` shards were then merged
and synced to W&B run `kgnbdmwf` in project `DFM L`:

```text
eval/MATH/acc: 0.3854
eval/MATH/invalid: 0.1106
eval/MATH/n: 5000
```

The final local aggregate is
`logs/eval/dfm_L_epoch1_queued_all/standard_shards/MATH/merged_metrics.json`.
The sync log is
`logs/eval/dfm_L_epoch1_queued_all/standard_shards/MATH/merge_and_wandb_sync.log`.

A final scan of CP1 merge logs showed `OK` for all standard merge/sync logs,
all DFM task merge/sync logs, and `merge_ifeval_da_wandb.log`; no remaining
failed aggregate logs were found.

Cross-project W&B sync note, 2026-05-29. Confidence: high.

Syncing only the original active training directory does not include all later
manual eval metrics:

```bash
wandb sync --include-online --no-mark-synced \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  wandb/run-20260528_234406-kgnbdmwf
```

The eval merge scripts resumed run id `kgnbdmwf` and created separate local
W&B directories such as `wandb/run-20260529_221506-kgnbdmwf` and
`wandb/run-20260529_233116-kgnbdmwf`. A multi-directory `wandb sync` reported
success, but the target project summary still lacked the new keys when checked
through the W&B API. The reliable repair was to backfill the merged aggregate
JSON/logs directly into the target project run with `wandb.init(project=...,
id="kgnbdmwf", resume="allow")` by rerunning the local merge scripts with:

```bash
--project "Original Plus Mixed Danish Instruction Rich L" \
--run-id kgnbdmwf \
--run-name dfm-L \
--log-wandb
```

The backfill log is
`logs/wandb_backfill_kgnbdmwf_to_original_plus_mixed_20260529T234727.log`.
W&B API verification after the backfill showed the target project run contains
representative new metrics:

```text
eval/MATH/acc: 0.3854
eval/MATH/invalid: 0.1106
eval/MATH/n: 5000
dfm_eval/generative-talemaader/model_graded_fact/accuracy: 0.07920792079207921
dfm_eval/generative-talemaader/model_graded_fact/n: 808
dfm_eval/nordjyllandnews/rougeL/mean: 0.22148837256342324
dfm_eval/ifeval-da/instruction_following/final_acc: 0.393870787633715
```

DALA metric-name compatibility note, 2026-05-30. Confidence: high.

Earlier DALA runs logged the linguistic-acceptability macro-F1 and MCC metrics
with flattened scorer names:

```text
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1
dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc
```

The first DFM L CP1 merge emitted slash-form keys
`dfm_eval/dala/linguistic-acceptability/dfm_evals/macro_f1` and
`dfm_eval/dala/linguistic-acceptability/dfm_evals/mcc`, which did not line up
with older W&B panels. The target run `kgnbdmwf` in project
`Original Plus Mixed Danish Instruction Rich L` was backfilled with the
flattened aliases:

```text
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1: 0.4906548270682793
dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc: 0.03368421246821112
dfm_eval/dala/linguistic-acceptability/n: 2048
```

`scripts/merge_dfm_eval_shards.py` now emits the flattened DALA key names for
future runs. A local probe against the CP1 DALA `.eval` confirmed the updated
merge output.
