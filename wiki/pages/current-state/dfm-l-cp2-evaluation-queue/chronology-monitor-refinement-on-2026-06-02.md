---
type: Operational Record
title: Monitor refinement on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Monitor refinement
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
# Monitor refinement on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Monitor refinement on 2026-06-02. Confidence: high. The first monitor version
showed misleading IFEval lines such as `generation: 0% ... 0/1` because the HRM
OpenAI shim emits a fresh one-request tqdm bar for each request. The monitor now
suppresses reset-only `generation: 0/1` lines and, for `server.log`, reports
compact completion counters by counting chat-completion HTTP responses. For
IFEval-DA it verifies the HF train split length as `541` and combines that with
the shard args in `inspect/eval-set.json`, so 32-way shards show counters like
`completion=11/17 failed=0` instead of raw tqdm output.
