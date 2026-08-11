---
type: Operational Record
title: DFM8 L 50K/100K Evaluation Plan, 2026-07-25
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 L 50K/100K Evaluation Plan,
  2026-07-25.'
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
# DFM8 L 50K/100K Evaluation Plan, 2026-07-25

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high from local plan generation, process inspection, and tmux
launch verification.

A full standard + DFM + EuroEval plan for DFM8 L checkpoints `step_50000` and
`step_100000` is stored at:

```text
logs/scheduler/dfm8_L_steps50k_100k_vllm_hrmenv_20260725
```

It targets W&B project `DFM5`, run ID `g2oaotmc`, and logs the checkpoints at
DFM8 epoch coordinates `0.1859719823565767` and `0.3719439647131534`.
The plan contains checkpoint waits, EMA HF exports, 170 standard-eval shards,
102 DFM shards, 64 DFM IFEval-DA shards, 40 EuroEval jobs, per-task merges and
W&B syncs, and headline/suite averages.

The plan uses the established DFM8 Gemma settings: FA4/vLLM, Gemma native chat
template and BFCL tool conversion, EuroEval-first ordering, 5 retries,
standard batch 64, DFM/IFEval/EuroEval batch 32, and the local
`unsloth/gemma-4-E4B-it` judge with judged target-server utilization 0.18.

The active L training process currently leaves only about 5-19 GiB free per
GPU. To avoid disrupting training, tmux window `hrm-0:6` waits until no
`pretrain.py data=dfm8 arch/size@arch=L` process remains before starting the
scheduler on GPUs 0-7. The Rich monitor is in `hrm-0:7`.

Update, 2026-07-25. Confidence: high from atomic plan inspection, scheduler
status, and GPU/process inspection.

The conservative batch/utilization settings and training guard above are
superseded for this campaign. After the DFM8 L training workers were stopped
and all eight GPUs had about 173 GiB free, the plan was updated to use:

```text
general vLLM GPU memory utilization: 0.90
standard eval batch:                 128
DFM eval batch:                       64
DFM IFEval-DA batch:                  64
EuroEval batch/concurrency:           64
generative_talemaader batch:          32
generative_talemaader utilization:  0.65
```

The judged `generative_talemaader` task retains lower target-server
utilization so the Gemma judge can coexist on the same GPU. Eval jobs retain
adaptive retry behavior (`fixed_retry_batch=false`) and up to five retries,
halving the batch after resource failures. The pre-edit plan is backed up as
`plan.before_highmem_20260725.tsv` in the plan directory.

The scheduler now runs directly in `hrm-0:6` and the 30-second Rich monitor in
`hrm-0:7`. Both EMA HF exports completed successfully, after which all eight
GPUs began EuroEval jobs at batch 64. Initial scheduler state had no failures.
