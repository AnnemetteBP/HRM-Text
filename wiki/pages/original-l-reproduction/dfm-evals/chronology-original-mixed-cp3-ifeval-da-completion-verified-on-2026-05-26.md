---
type: Operational Record
title: Original+mixed CP3 IFEval-DA completion, verified on (2026-05-26)
description: 'Chronological record from dfm-evals: Original+mixed CP3 IFEval-DA completion,
  verified on (2026-05-26).'
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
# Original+mixed CP3 IFEval-DA completion, verified on (2026-05-26)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Original+mixed CP3 IFEval-DA completion, verified on 2026-05-26. Confidence:
high.

The four CP3 IFEval-DA shards completed, were merged, and were synced to W&B
run `es1od1in` at `dfm_eval/epoch=3`. Evidence:

```text
merged metrics: logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/merged_ifeval_da_metrics.json
sync log: logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/merge_ifeval_da_wandb.log
W&B log line: Synced 4 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
```

Merged epoch-3 IFEval-DA metrics:

```text
num_samples: 541
dfm_eval/ifeval-da/instruction_following/final_acc: 0.35809184618703394
dfm_eval/ifeval-da/instruction_following/final_stderr: 0.016830669337024047
dfm_eval/ifeval-da/instruction_following/inst_loose_acc: 0.4462242562929062
dfm_eval/ifeval-da/instruction_following/inst_loose_stderr: 0.015684688759299244
dfm_eval/ifeval-da/instruction_following/inst_strict_acc: 0.4279176201372998
dfm_eval/ifeval-da/instruction_following/inst_strict_stderr: 0.015609094571451737
dfm_eval/ifeval-da/instruction_following/prompt_loose_acc: 0.2846580406654344
dfm_eval/ifeval-da/instruction_following/prompt_loose_stderr: 0.0194187691064861
dfm_eval/ifeval-da/instruction_following/prompt_strict_acc: 0.2735674676524954
dfm_eval/ifeval-da/instruction_following/prompt_strict_stderr: 0.019183727107392846
```

For future checkpoints, prefer 8 IFEval-DA shards instead of 4 to reduce the
tail runtime. Confidence: medium.
