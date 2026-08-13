---
type: Operational Record
title: Corrected CP4 eval sync on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Corrected CP4
  eval sync on (2026-06-02).'
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
# Corrected CP4 eval sync on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Corrected CP4 eval sync on 2026-06-02. Confidence: high.

The same local merged CP4 artifacts under
`logs/eval/dfm_L_epoch4_queued_all` and
`logs/dfm_evals/dfm_L_epoch4_queued_all` were resynced with:

```bash
EPOCH=4 CKPT_TAG=epoch_4 CKPT_PATH=checkpoints/dfm/L \
GPUS=0,1,2,3,4,5,6,7 \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=dfm-l-resume-epoch3 \
WANDB_RUN_NAME=dfm-L-resume-epoch3 \
LOG_ROOT=logs/eval/dfm_L_epoch4_queued_all \
DFM_LOG_ROOT=logs/dfm_evals/dfm_L_epoch4_queued_all \
QUEUE_ORDER=heavy_first MAX_RETRIES=3 RESUME_EXISTING_QUEUE=1 \
scripts/schedule_checkpoint_evals.sh
```

This reached:

```text
2026-06-02T21:19:46+02:00 FINAL_MERGE_START
2026-06-02T21:24:52+02:00 FINAL_MERGE_END
```

W&B API verification for
`peter-sk-sdu/Original Plus Mixed Danish Instruction Rich L/dfm-l-resume-epoch3`
found representative CP4 metrics:

```text
eval/MATH/acc/epoch_4 = 0.48119616
eval/GSM8k/acc/epoch_4 = 0.7998448066717211
eval/MMLU/acc/epoch_4 = 0.28052499999999997
dfm_eval/ifeval-da/instruction_following/final_acc/epoch_4 = 0.46285377109091136
dfm_eval/generative-talemaader/model_graded_fact/accuracy/epoch_4 = 0.08168316831683169
dfm_eval/wmt24pp-en-da/chrf3pp/mean/epoch_4 = 0.5068738652893814
dfm_eval/humaneval/verify/accuracy/epoch_4 = 0.2195121951219512
```
