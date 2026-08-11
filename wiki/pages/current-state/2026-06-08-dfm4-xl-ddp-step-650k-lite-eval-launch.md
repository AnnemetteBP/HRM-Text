---
type: Operational Record
title: 2026-06-08 DFM4 XL-DDP Step 650K Lite Eval Launch
description: 'Part of Current State: 2026-06-08 DFM4 XL-DDP Step 650K Lite Eval Launch.'
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
# 2026-06-08 DFM4 XL-DDP Step 650K Lite Eval Launch

Part of [Current State](/pages/current-state.md).

Confidence: high for local code changes and launch logs.

Before launching the `step_650000` lite eval while all GPUs were free, two eval
scheduler safeguards were added:

- `scripts/merge_dfm_eval_shards.py` now raises on zero DFM samples instead of
  writing/logging zero-sample metrics. This prevents the final merge path from
  overwriting correct incremental metrics when expected `.eval` artifacts are
  missing or incomplete.
- `scripts/schedule_checkpoint_evals.sh` now supports per-task batch-size
  overrides via environment variables such as `STANDARD_BATCH_SIZE_MATH=32` or
  `DFM_BATCH_SIZE_GOVREPORT=8`. The existing retry behavior still halves the
  selected per-task batch size after failures/OOMs.

Validation:

```bash
cd /work/dfm/HRM-Text
python -m py_compile scripts/merge_dfm_eval_shards.py
bash -n scripts/schedule_checkpoint_evals.sh
bash -n scripts/schedule_multiple_checkpoint_evals.sh
bash -n scripts/run_talemaader_split_gpu_eval.sh
```

The `step_650000` no-EMA lite eval was launched in tmux session
`dfm4_lite_eval_650k` with all eight GPUs free. Exact epoch x-coordinate:
`1.7747585795360006`.

```bash
cd /work/dfm/HRM-Text
env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_650k_20260608_freegpus \
  DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_650k_20260608_freegpus \
  CKPT_TAGS=step_650000 \
  EVAL_EPOCHS=1.7747585795360006 \
  CKPT_PATH=checkpoints/dfm4/XL-ddp \
  GPUS=0,1,2,3,4,5,6,7 \
  JUDGE_GPU=0 \
  LITE_EVAL=1 \
  LITE_SHARD_INDEX=0 \
  QUEUE_ORDER=heavy_first \
  MAX_RETRIES=5 \
  NO_EMA=1 \
  WANDB_SYNC=1 \
  WANDB_PROJECT='Original Plus Mixed Danish Instruction Rich L' \
  WANDB_RUN_ID=dfm4xlddpclean \
  WANDB_RUN_NAME='dfm4-XL-ddp clean lite history' \
  EVAL_PREFIX=lite_eval_noema \
  DFM_EVAL_PREFIX=lite_dfm_eval_noema \
  MODEL_PREFIX=hrm-dfm4-XL-ddp-noema \
  STANDARD_BATCH_SIZE=64 \
  DFM_BATCH_SIZE=32 \
  IFEVAL_BATCH_SIZE=16 \
  STANDARD_BATCH_SIZE_MATH=32 \
  STANDARD_BATCH_SIZE_DROP=16 \
  DFM_BATCH_SIZE_GOVREPORT=8 \
  DFM_BATCH_SIZE_NORDJYLLANDNEWS=16 \
  DFM_BATCH_SIZE_WMT24PP_EN_DA=16 \
  DFM_BATCH_SIZE_HUMANEVAL=8 \
  DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=8 \
  bash scripts/schedule_multiple_checkpoint_evals.sh
```

Early status: the scheduler started eight workers and assigned the first eight
jobs across GPUs 0-7. `GSM8k` completed successfully at batch size `64` with no
OOM and synced incrementally.

Headroom observation during the same launch, 2026-06-08. Confidence: high for
the live `nvidia-smi` snapshot; medium for future batch-size recommendations.

While the first wave of `step_650000` lite evals was running, observed GPU
memory left substantial headroom:

```text
IFEval-DA:        batch 16, ~52.4 GiB used, ~130.2 GiB free
MATH:             batch 32, ~77.1 GiB used, ~105.6 GiB free
DROP:             batch 16, ~40.4 GiB used, ~142.2 GiB free
MMLU:             batch 64, ~6.5 GiB used, ~176.1 GiB free
HellaSwag:        batch 64, ~6.4 GiB used, ~176.2 GiB free
WMT24++ en-da:    batch 16, ~52.4 GiB used, ~130.2 GiB free
```

Safe completed tasks from telemetry:

```text
GSM8k:      batch 64, status 0, no OOM
Winogrande: batch 64, status 0, no OOM
ARC:        batch 64, status 0, no OOM
GovReport:  batch 8,  status 0, no OOM
```

For the next all-GPU/no-training lite eval, reasonable starting candidates are
`STANDARD_BATCH_SIZE=128`, `STANDARD_BATCH_SIZE_MATH=64`,
`STANDARD_BATCH_SIZE_DROP=32`, `DFM_BATCH_SIZE=64`,
`DFM_BATCH_SIZE_GOVREPORT=16`, `DFM_BATCH_SIZE_WMT24PP_EN_DA=32`,
`DFM_BATCH_SIZE_NORDJYLLANDNEWS=32`, `DFM_BATCH_SIZE_HUMANEVAL=16`,
`DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16`, and `IFEVAL_BATCH_SIZE=32`, while
keeping `MAX_RETRIES>=5` so the scheduler halves on OOM/failure.

Future eval telemetry update, 2026-06-08. Confidence: high for local dry-run
validation. `scripts/schedule_checkpoint_evals.sh` now records
`peak_used_mib` in `eval_attempts.tsv` for each eval attempt. The value is
sampled with `nvidia-smi` around each worker job and stored beside task, shard,
GPU, batch size, status, OOM flag, before-memory, and after-memory. Existing
telemetry files without this column are migrated on scheduler startup; old rows
receive `peak_used_mib=NA`, while new rows receive measured values. Sampling
interval defaults to `GPU_MEM_PEAK_POLL_SECONDS=2`.

EMA high-batch follow-up for `step_650000`, 2026-06-08. Confidence: high for
local logs and telemetry. The EMA lite eval was run locally under:

```text
logs/eval/dfm4_XL_ddp_ema_lite_650k_20260608_highbs_retry/step_650000
logs/dfm_evals/dfm4_XL_ddp_ema_lite_650k_20260608_highbs_retry/step_650000
```

No W&B sync was performed for this run (`WANDB_SYNC=0`). Local final merge
completed successfully. During this run two scheduler issues were found and
fixed in `scripts/schedule_checkpoint_evals.sh`:

- the peak-memory sampler originally kept command substitution open when
  launched in the background; it now redirects stdout/stderr to `/dev/null`;
- failed standard eval jobs returned while `set -e` was still disabled, so a
  child scheduler could exit before retrying/logging telemetry; this path now
  preserves retry/telemetry behavior.

Batch-size findings from `peak_used_mib`:

```text
GSM8k batch 128: OOMed; batch 64 succeeded, peak ~151090 MiB
MATH batch 64: succeeded, peak ~151092 MiB
DROP batch 32: succeeded, peak ~77404 MiB
ARC/BoolQ/HellaSwag/MMLU/Winogrande batch 128: succeeded, peak only ~6-7 GiB
DFM server tasks batch 64: OOMed for gec_dala, multi_wiki_qa,
  danish_citizen_tests, dala, and piqa
DFM server tasks batch 32: succeeded, peak ~101748-101756 MiB
GovReport batch 16: succeeded, peak ~52886 MiB
HumanEval batch 16: succeeded, peak ~52394 MiB
Generative Talemaader batch 16: succeeded, peak ~68462 MiB
IFEval-DA batch 32: succeeded, peak ~101748 MiB
```

Recommended next no-training lite eval defaults from this run:

```text
STANDARD_BATCH_SIZE=128
STANDARD_BATCH_SIZE_GSM8K=64
STANDARD_BATCH_SIZE_MATH=64
STANDARD_BATCH_SIZE_DROP=32
DFM_BATCH_SIZE=32
DFM_BATCH_SIZE_GOVREPORT=16
DFM_BATCH_SIZE_HUMANEVAL=16
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16
IFEVAL_BATCH_SIZE=32
```

Do not use generic `STANDARD_BATCH_SIZE=128` without overriding `GSM8k` to 64;
do not use generic `DFM_BATCH_SIZE=64` for HRM server-backed DFM tasks on this
checkpoint/model because it leaves less than 1 GiB free and causes cache
allocation OOMs.

DFM4 XL-DDP eval backlog launch, 2026-06-08. Confidence: high for local launch
logs; medium for runtime estimates. A sequential tmux driver was launched in
session `dfm4_xl_ddp_eval_backlog_20260608`:

```text
logs/eval/dfm4_XL_ddp_eval_backlog_20260608/driver.log
```

The driver first runs missing EMA lite evals, then full epoch-1 no-EMA evals,
then full epoch-1 EMA evals. All sync to W&B run `dfm4xlddpclean` in project
`Original Plus Mixed Danish Instruction Rich L`.

Missing EMA lite checkpoints queued:

```text
step_50000, step_100000, step_150000, step_300000, step_350000,
epoch_1, step_400000, step_450000, step_500000, step_550000, step_600000
```

Corresponding x-axis epoch values:

```text
0.1365198907335385, 0.273039781467077, 0.4095596722006155,
0.819119344401231, 0.9556392351347696, 1,
1.092159125868308, 1.2286790166018464, 1.365198907335385,
1.5017187980689235, 1.638238688802462
```

Log roots and metric prefixes:

```text
EMA lite:
  logs/eval/dfm4_XL_ddp_ema_lite_missing_20260608
  logs/dfm_evals/dfm4_XL_ddp_ema_lite_missing_20260608
  lite_eval_ema/* and lite_dfm_eval_ema/*

Full epoch_1 no-EMA:
  logs/eval/dfm4_XL_ddp_noema_full_epoch1_20260608
  logs/dfm_evals/dfm4_XL_ddp_noema_full_epoch1_20260608
  eval_noema/* and dfm_eval_noema/*

Full epoch_1 EMA:
  logs/eval/dfm4_XL_ddp_ema_full_epoch1_20260608
  logs/dfm_evals/dfm4_XL_ddp_ema_full_epoch1_20260608
  eval_ema/* and dfm_eval_ema/*
```

Batch-size policy:

```text
STANDARD_BATCH_SIZE=128
STANDARD_BATCH_SIZE_GSM8K=64
STANDARD_BATCH_SIZE_MATH=64
STANDARD_BATCH_SIZE_DROP=32
DFM_BATCH_SIZE=32
DFM_BATCH_SIZE_GOVREPORT=16
DFM_BATCH_SIZE_HUMANEVAL=16
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16
IFEVAL_BATCH_SIZE=32
MAX_RETRIES=5
```

Observed start: the first EMA lite checkpoint (`step_50000`) spent about four
minutes in checkpoint/EMA load with eight concurrent workers before tasks began
to complete. This makes the missing-lite sweep likely slower than the warm
single-checkpoint `step_650000` run. Runtime estimate: missing EMA lite sweep
roughly `2.5-3.5h`; full epoch-1 no-EMA roughly `1.5-2.0h`; full epoch-1 EMA
roughly `1.5-2.5h`; full sequential backlog roughly `5.5-8h` depending on
checkpoint-load pressure and W&B sync latency.

DFM4 XL-DDP EMA vs no-EMA lite comparison through `step_500000`, 2026-06-08.
Confidence: high for local merged metric files; medium for interpretation
because lite evals use one shard per task and equal-weighting heterogeneous
metrics is only a rough summary. Comparing 98 higher-is-better score metrics at
each 50K checkpoint:

```text
checkpoint  EMA better  EMA worse  same  mean delta  median delta
50K         35          61         2     -0.4332     -0.0165
100K        22          73         3     -0.5193     -0.0438
150K        23          73         2     -0.4637     -0.0410
200K        60          28         10    +0.0387     +0.0230
250K        43          42         13    -0.0013     +0.0000
300K        64          30         4     +0.0249     +0.0261
350K        65          25         8     +0.0331     +0.0261
400K        57          31         10    +0.0244     +0.0025
450K        39          49         10    -0.0080     -0.0001
500K        42          47         9     -0.0044     +0.0000
```

Interpretation: before and through 150K, EMA is badly damaged, matching the
known EMA precision bug period. After the 150K reset, EMA is no longer
catastrophic and is broadly competitive: 200K, 300K, 350K, and 400K are net
positive on this equal-weighted lite comparison. By 450K-500K it becomes mixed
to slightly negative. Task-level pattern is also mixed: EMA often helps
MATH/DROP/IFEval-Da/DALA-like metrics, while no-EMA remains better on several
binary/classification or exact-choice tasks such as BoolQ, PIQA, ARC, and
Danish citizen tests.
