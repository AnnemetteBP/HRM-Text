---
type: Operational Record
title: Epoch-2 completion, verified locally and through W&B sync logs on (2026-05-25)
description: 'Chronological record from dfm-evals: Epoch-2 completion, verified locally
  and through W&B sync logs on (2026-05-25).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Epoch-2 completion, verified locally and through W&B sync logs on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Epoch-2 completion, verified locally and through W&B sync logs on 2026-05-25.
Confidence: high.

All seven non-IFEval tasks completed and were re-synced as one consolidated
CP2 W&B history row at `dfm_eval/epoch=2`. The eight IFEval-DA shards also
completed, were merged into `merged_ifeval_da_metrics.json`, and were re-synced
as part of the same consolidated CP2 row after the initial per-task summaries
did not reliably remain visible through the W&B API while the training run was
active.

```text
dfm_eval/danish-citizen-tests/knowledge/accuracy: 0.5229357798165137
dfm_eval/danish-citizen-tests/knowledge/dfm_evals_mcc: 0.32175001283952764
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1: 0.024884792626728113
dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc: -0.012718920251333386
dfm_eval/gec_dala/exact_match/mean: 0.005859375
dfm_eval/wmt24pp-en-da/chrf3pp/mean: 0.4914474618118289
dfm_eval/multi_wiki_qa/exact_match/mean: 0.82763671875
dfm_eval/multi_wiki_qa/f1/mean: 0.9187239022284758
dfm_eval/piqa/piqa_scorer/accuracy: 0.46296296296296297
dfm_eval/generative-talemaader/model_graded_fact/accuracy: 0.050742574257425746
dfm_eval/ifeval-da/instruction_following/final_acc: 0.35019213931316273
dfm_eval/ifeval-da/instruction_following/final_stderr: 0.016554524344104274
dfm_eval/ifeval-da/instruction_following/inst_loose_acc: 0.4405034324942792
dfm_eval/ifeval-da/instruction_following/inst_loose_stderr: 0.015728631269252082
dfm_eval/ifeval-da/instruction_following/inst_strict_acc: 0.4279176201372998
dfm_eval/ifeval-da/instruction_following/inst_strict_stderr: 0.015753402406761055
dfm_eval/ifeval-da/instruction_following/prompt_loose_acc: 0.2698706099815157
dfm_eval/ifeval-da/instruction_following/prompt_loose_stderr: 0.019102087526494387
dfm_eval/ifeval-da/instruction_following/prompt_strict_acc: 0.26247689463955637
dfm_eval/ifeval-da/instruction_following/prompt_strict_stderr: 0.0189337428760446
```

Launched mapping:

```text
shard 0: GPU 0, port 8601
shard 1: GPU 1, port 8611
shard 2: GPU 2, port 8621
shard 3: GPU 3, port 8631
shard 4: GPU 4, port 8641
shard 5: GPU 5, port 8651
shard 6: GPU 6, port 8661
shard 7: GPU 7, port 8671
```

Merge command after all eight shards complete:

```bash
cd /work/dfm/HRM-Text
python scripts/merge_ifeval_da_shards.py \
  logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_ifeval_da_sharded_b1/shard_{0,1,2,3,4,5,6,7}/epoch_1/inspect/*.eval \
  --epoch 1 \
  --output logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_ifeval_da_sharded_b1/merged_ifeval_da_metrics.json \
  --log-wandb \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  --run-id es1od1in \
  --run-name "original-plus-mixed-danish-instruction-rich-L"
```
