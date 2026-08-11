---
type: Operational Record
title: 'Update 2026-06-13: The completed EuroEval groups initially failed during W&B
  merge with'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  The completed EuroEval groups initially failed during W&B merge with.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Update 2026-06-13: The completed EuroEval groups initially failed during W&B merge with

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high. The completed EuroEval groups initially
failed during W&B merge with:

```text
RuntimeError: No numeric EuroEval metrics found in .../euroeval_benchmark_results.jsonl
```

The result files were valid. EuroEval 17.3.0 writes the current benchmark
schema under `evaluation_results` with `score_details.score`, while
`scripts/log_euroeval_to_wandb.py` only parsed the older flat `results` field.
The logger was patched to support both schemas, parse languages/dataset/task
from `eval_library.additional_details`, skip blank JSONL lines, and log score,
confidence interval, sample count, and failed-instance count under
`euroeval/{lang}/{task}/{dataset}/{metric}`.

Manual sync after the patch succeeded for completed groups:

```bash
cd /work/dfm/HRM-Text
for g in 2 4 7; do
  /home/ucloud/miniforge3/envs/hrm/bin/python scripts/log_euroeval_to_wandb.py \
    --results logs/euroeval/dfm5_XXS_step50000_parallel_20260613/gpu${g}/euroeval_benchmark_results.jsonl \
    --epoch 0.276088 \
    --output logs/euroeval/dfm5_XXS_step50000_parallel_20260613/gpu${g}/merged_metrics.json \
    --prefix euroeval \
    --language da \
    --language en \
    --log-wandb \
    --project DFM5 \
    --run-id 2tv9u438 \
    --run-name dfm5-XXS
done
```

The still-running groups will use the patched logger when their wrapper exits.
