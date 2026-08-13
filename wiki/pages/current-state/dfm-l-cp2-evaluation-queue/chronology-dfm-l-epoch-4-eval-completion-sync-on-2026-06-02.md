---
type: Operational Record
title: DFM L epoch 4 eval completion/sync on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L epoch 4
  eval completion/sync on (2026-06-02).'
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
# DFM L epoch 4 eval completion/sync on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L epoch 4 eval completion/sync on 2026-06-02. Confidence: high.

All `168` CP4 eval jobs completed. One `generative_talemaader` shard initially
stalled after a port collision (`127.0.0.1:9602` already in use), was forced
through the scheduler retry path, and then completed successfully:

```text
2026-06-02T20:58:33+02:00 RETRY dfm generative_talemaader shard_4_of_8 gpu_1 status_2 next_attempt_2
2026-06-02T20:58:43+02:00 START dfm generative_talemaader shard_4_of_8 gpu_1 attempt_2_of_4
2026-06-02T21:05:38+02:00 END dfm generative_talemaader shard_4_of_8 gpu_1 status_0
```

The user asked to stop scheduler/monitor processes just as final merge started.
The eval computation itself was already complete. The final merge/W&B sync was
then rerun with `RESUME_EXISTING_QUEUE=1`, reaching:

```text
2026-06-02T21:09:37+02:00 FINAL_MERGE_START
2026-06-02T21:11:28+02:00 FINAL_MERGE_END
```

Local merged metrics were present for representative standard/DFM tasks,
including MATH, IFEval-DA, and generative-talemaader. W&B API verification for
`peter-sk-sdu/DFM L/kgnbdmwf` found representative CP4 metrics:

```text
eval/MATH/acc/epoch_4 = 0.48119616
eval/GSM8k/acc/epoch_4 = 0.7998448066717211
dfm_eval/ifeval-da/instruction_following/final_acc/epoch_4 = 0.46285377109091136
dfm_eval/generative-talemaader/model_graded_fact/accuracy/epoch_4 = 0.08168316831683169
dfm_eval/wmt24pp-en-da/chrf3pp/mean/epoch_4 = 0.5068738652893814
```

Superseded: the CP4 metrics above were synced to the wrong W&B target for the
comparison view. The intended target is
`peter-sk-sdu/Original Plus Mixed Danish Instruction Rich L/dfm-l-resume-epoch3`.
Confidence: high.
