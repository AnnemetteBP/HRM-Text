---
type: Operational Record
title: 2026-06-04 DFM4 XL-DDP Step 250K Lite Eval
description: 'Part of Current State: 2026-06-04 DFM4 XL-DDP Step 250K Lite Eval.'
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
# 2026-06-04 DFM4 XL-DDP Step 250K Lite Eval

Part of [Current State](/pages/current-state.md).

Confidence: high for launch command and checkpoint presence; completion pending.

The `checkpoints/dfm4/XL-ddp` `step_250000` checkpoint is present as an
unsharded DDP checkpoint:

```text
unsharded_step_250000.pt
checkpoint_state_step_250000.json
carry_step_250000.{0..7}.pt
```

The checkpoint state reports `step=250000`, `batch_in_epoch=250000`,
`epoch=1`, `global_batch_size=196608`, and `data_path=data/sampled_dfm4`.

A no-EMA lite eval was launched on 2026-06-04 in tmux window
`hrm-1:lite250k`, using all 8 GPUs and W&B run `4chqwd3w` in project
`Original Plus Mixed Danish Instruction Rich L`. It logs to the same Lite
section metric prefixes as the previous no-EMA lite runs:

```text
lite_eval_noema/*
lite_dfm_eval_noema/*
```

Command:

```bash
cd /work/dfm/HRM-Text
CKPT_TAGS=step_250000 \
EVAL_EPOCHS=0.6826013116866806 \
CKPT_PATH=checkpoints/dfm4/XL-ddp \
GPUS=0,1,2,3,4,5,6,7 \
LITE_EVAL=1 \
LITE_SHARD_INDEX=0 \
QUEUE_ORDER=heavy_first \
NO_EMA=1 \
WANDB_SYNC=1 \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=4chqwd3w \
WANDB_RUN_NAME=dfm4-XL-ddp \
EVAL_PREFIX=lite_eval_noema \
DFM_EVAL_PREFIX=lite_dfm_eval_noema \
STANDARD_CONFIG=evaluation/config/hrm_benchmarking_lite.yaml \
STANDARD_BATCH_SIZE=16 \
DFM_BATCH_SIZE=16 \
IFEVAL_BATCH_SIZE=16 \
MAX_RETRIES=3 \
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_probe_20260604_250k \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260604_250k \
scripts/schedule_multiple_checkpoint_evals.sh
```

Initial status:

Update, 2026-06-13. Confidence: high for telemetry from
`logs/eval/dfm5_XXS_100k_150k_full_20260613_100k_150k/step_100000/eval_attempts.tsv`;
medium for next-run recommendations. The `step_100000`/`step_150000` DFM5 XXS
full eval campaign was launched conservatively with
`STANDARD_BATCH_SIZE=16`, `DFM_BATCH_SIZE=16`, `IFEVAL_BATCH_SIZE=16`, and
`EUROEVAL_BATCH_SIZE=8`. Completed `step_100000` telemetry showed these batch
sizes are too small for the available B200 headroom: standard tasks at batch 16
peaked around 12-18 GiB, IFEval-DA batch 16 peaked around 13-16 GiB, GovReport
batch 16 peaked around 14-17 GiB, and EuroEval batch 8 peaked around 13-19 GiB.
For the next DFM5 XXS eval round, start closer to the known DFM4 high-batch
recipe and keep retry-halving enabled:

```text
STANDARD_BATCH_SIZE=128
STANDARD_BATCH_SIZE_GSM8K=64
STANDARD_BATCH_SIZE_MATH=64
STANDARD_BATCH_SIZE_DROP=32
DFM_BATCH_SIZE=32
DFM_BATCH_SIZE_GOVREPORT=32
DFM_BATCH_SIZE_NORDJYLLANDNEWS=32
DFM_BATCH_SIZE_WMT24PP_EN_DA=32
DFM_BATCH_SIZE_HUMANEVAL=16
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16
IFEVAL_BATCH_SIZE=32
EUROEVAL_BATCH_SIZE=16
MAX_RETRIES=5
```

EuroEval may benefit more from one-dataset grouping than from very high batch
size, because the current eight grouped jobs had two long-tail groups.

```text
QUEUED 19 jobs for 1 checkpoints
START step_250000 dfm_ifeval shard 0/32 on GPU0
START step_250000 MATH shard 0/64 on GPU1
START step_250000 GSM8k shard 0/8 on GPU2
START step_250000 DROP shard 0/4 on GPU3
START step_250000 MMLU shard 0/4 on GPU4
START step_250000 HellaSwag shard 0/2 on GPU5
START step_250000 ARC shard 0/1 on GPU6
START step_250000 Winogrande shard 0/1 on GPU7
```

Update, 2026-06-04. Confidence: high. The first `step_250000` lite run with
batch size `16` was stopped because dfm-evals servers repeatedly OOMed while
the DFM4 XL-DDP training run was still occupying about `140-150G` per GPU.
Only the eval scheduler/server process tree was killed; the training PIDs
remained active.

The retry is running in tmux window `hrm-1:7` (`lite250b8`) with monitor
window `hrm-1:8` (`mon250b8`). It uses fresh log roots and halves the eval
batch sizes:

```text
STANDARD_BATCH_SIZE=8
DFM_BATCH_SIZE=8
IFEVAL_BATCH_SIZE=8
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_probe_20260604_250k_bs8
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260604_250k_bs8
```

Initial monitor output after model load showed active progress on all eight
GPUs rather than immediate OOM, but memory remains tight because training is
still active.

Trend snapshot, 2026-06-04. Confidence: high for local merged metrics. The
DFM4 XL-DDP lite metrics at `step_250000` are **non-EMA** metrics because the
run was launched with `NO_EMA=1` and logs under `lite_eval_noema/*` and
`lite_dfm_eval_noema/*`. After IFEval-DA finished and exact metric keys were
checked, 14 metrics improved from 200K to 250K and 4 real metrics regressed.
Improvements include ARC, DROP, GSM8k, HellaSwag, MMLU, DALA, GEC-DALA,
Danish Citizen Tests, HumanEval, WMT chrF++, MultiWikiQA, PIQA-da,
NordjyllandNews R2, and IFEval-DA. Regressions include BoolQ, MATH,
Winogrande, and GovReport R2. Treat BoolQ and MATH cautiously because the lite
setup uses small shards and prior probes showed binary-choice option-prior
instability. Generative-talemaader produced a merged metric with `n=0` and
accuracy `0.0`, so treat that checkpoint/task as failed or missing rather than
as a meaningful regression. The corresponding server log shows a CUDA OOM while
loading the HRM checkpoint on GPU0; no Inspect `.eval` file was produced, and
the merge input was the unmatched glob `inspect/*.eval`.

Follow-up, 2026-06-04. Confidence: high. Retrying Talemaader with
`DFM_BATCH_SIZE=1` on one GPU still OOMed while training was active, because
the memory pressure comes primarily from co-locating the HRM server and the
Gemma judge on the same GPU, not from eval batch size. A split-GPU helper was
added at `scripts/run_talemaader_split_gpu_eval.sh`; it waits for enough free
memory on both GPUs, starts the judge and HRM server on separate GPUs, runs
`hrm_danish_generative_talemaader`, exports EEE logs, and merges/syncs only
the Talemaader metrics. A 250K no-EMA split retry is queued in tmux window
`hrm-1:tal250split` with HRM on GPU4 and judge waiting for GPU1.

A local-only 250K EMA lite eval was launched in tmux window `hrm-1:ema250lite`
with `WANDB_SYNC=0`, `NO_EMA=0`, prefixes `lite_eval_ema/*` and
`lite_dfm_eval_ema/*`, batch size `4`, and logs under
`logs/eval/dfm4_XL_ddp_ema_lite_probe_20260604_250k` plus
`logs/dfm_evals/dfm4_XL_ddp_ema_lite_probe_20260604_250k`.

Follow-up results, 2026-06-04. Confidence: high for local merged metrics. The
corrected 250K no-EMA Talemaader split run completed and synced
`lite_dfm_eval_noema/generative-talemaader/model_graded_fact/accuracy =
0.054455445544554455` with `n=101`. The local-only 250K EMA split Talemaader
run completed with `lite_dfm_eval_ema/generative-talemaader/model_graded_fact/
accuracy = 0.034653465346534656` with `n=101`.

At the comparison snapshot after EMA Talemaader completed, 250K EMA was better
than 250K no-EMA on 9 available lite metrics, worse on 8, equal on 1, with
NordjyllandNews still missing. EMA improved ARC, DROP, GSM8k, MATH, DALA,
GEC-DALA, Danish Citizen Tests, WMT chrF++, and GovReport R2; it regressed
BoolQ, HellaSwag, MMLU, Winogrande, MultiWikiQA F1, PIQA-da, IFEval-DA, and
Talemaader. HumanEval was unchanged.

EMA-vs-noEMA trend update, 2026-06-04. Confidence: high for local merged
metrics. After NordjyllandNews became available in the 250K EMA comparison,
EMA's relative advantage had shrunk from 200K to 250K: EMA-minus-noEMA was
positive on 15/19 metrics at 200K but only 10/19 at 250K, equal on 1, and
negative on 8. The mean EMA-minus-noEMA delta across these lite metrics moved
from about `+0.0148` at 200K to about `-0.0019` at 250K. The largest
deteriorations were MultiWikiQA F1, IFEval-DA, GEC-DALA, HumanEval, and PIQA-da;
the biggest relative improvement was BoolQ, but BoolQ remains known to be
option-prior unstable.

Interpretation note. Confidence: medium. The DFM4 XL-DDP EMA was reset at
`step_150000`, so the 200K and 250K comparisons are both post-reset EMA
comparisons, not contaminated by the earlier EMA state. With `ema=0.9999`, the
EMA half-life is roughly `6.9k` optimizer steps and the effective averaging
window is roughly `10k` steps; the reset snapshot contributes only about
`0.67%` at 200K and about `0.005%` at 250K. Thus the shrinking EMA advantage
from 200K to 250K is best read as the current/raw weights catching or surpassing
the post-reset smoothed weights on several lite tasks, rather than as old EMA
state lingering.
