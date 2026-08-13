---
type: Operational Record
title: Later refinement on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Later refinement
  on (2026-06-02).'
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
# Later refinement on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Later refinement on 2026-06-02. Confidence: high. The monitor now parses
`START`/`END` scheduler status lines to infer the active job per GPU and prints
a GPU-ordered table such as `GPU0: ifeval-da shard 0 13/17 ETA 4.6m`. ETA is
estimated from elapsed wall time since the job's scheduler `START` and the
current completed/total request count when a denominator is known.
