---
type: Operational Record
title: CP2 standard MATH completion, verified on (2026-05-26)
description: 'Chronological record from dfm-evals: CP2 standard MATH completion, verified
  on (2026-05-26).'
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
# CP2 standard MATH completion, verified on (2026-05-26)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

CP2 standard MATH completion, verified on 2026-05-26. Confidence: high.

All eight epoch-2 MATH shards completed and no standard-eval processes remained.
The shards were merged and synced with:

```bash
cd /work/dfm/HRM-Text
python scripts/merge_standard_math_shards.py \
  logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_math_shards_v2/epoch_2/MATH_shard_*_of_8.log \
  --epoch 2 \
  --output logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_math_shards_v2/epoch_2/merged_math_metrics.json \
  --log-wandb \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  --run-id es1od1in \
  --run-name "original-plus-mixed-danish-instruction-rich-L"
```

Merged epoch-2 MATH metrics:

```text
eval/MATH/n: 5000
eval/MATH/acc: 0.4412
eval/MATH/invalid: 0.0928
```

The active training process continues to overwrite the remote W&B summary back
to a small training-only summary, so direct summary patching did not persist.
However, W&B history verification returned both standard MATH rows:

```text
epoch 1: eval/MATH/acc = 0.3658, eval/MATH/invalid = 0.1100, eval/MATH/n = 5000
epoch 2: eval/MATH/acc = 0.4412, eval/MATH/invalid = 0.0928, eval/MATH/n = 5000
```

Use `eval/epoch` as the x-axis for these plots. Confidence: high.
