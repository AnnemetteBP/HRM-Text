---
type: Operational Record
title: Extra-worker update (2026-06-08)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Extra-worker update
  (2026-06-08).'
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
# Extra-worker update (2026-06-08)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Extra-worker update, 2026-06-08. Confidence: high. GPU1 and GPU4 had enough
headroom to run additional batch-1 standard evals, so two workers were attached
to the existing shared queue with:

```text
RESUME_EXISTING_QUEUE=1
SKIP_FINAL_MERGE=1
GPUS=1,4
```

This preserved the existing `jobs.tsv` and left final merge to the original
scheduler. Initial extra-worker status:

```text
RESUME_QUEUED 15 jobs
START step_600000 standard MMLU shard_0_of_4 gpu_1
START step_600000 standard HellaSwag shard_0_of_2 gpu_4
```

Memory note: after loading these jobs, GPU1 had about `857 MiB` free and GPU4
only about `43 MiB` free. GPU4 is therefore useful but risky for large or
server-backed eval jobs while training is active.
