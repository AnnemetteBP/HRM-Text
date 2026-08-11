---
type: Operational Record
title: Parallel dfm-evals launch, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Parallel dfm-evals launch, verified
  on (2026-05-24).'
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
# Parallel dfm-evals launch, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Parallel dfm-evals launch, verified on 2026-05-24: epoch 1 remained active on GPU 0/port 8092. Epochs 2, 3, and 4 were launched independently with `setsid` on GPU 1/port 8093, GPU 2/port 8094, and GPU 3/port 8095. All four HRM shim processes passed health checks and began processing dfm-evals requests. The epoch 2-4 launcher logs are under `logs/dfm_evals/parallel_launch/epoch_{2,3,4}.setsid.log`. Confidence: high.
