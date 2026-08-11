---
type: Operational Record
title: IFEval port-collision fix (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: IFEval port-collision
  fix (2026-06-03).'
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
# IFEval port-collision fix (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

IFEval port-collision fix, 2026-06-03. Confidence: high.
The shared multi-checkpoint scheduler launches one child
`scripts/schedule_checkpoint_evals.sh` per job/GPU. Inside those child
schedulers, `worker_id` is always `0`. The old IFEval port formula used
`PORT_BASE + 1000 + worker_id * 100 + shard`, so `step_50000` and
`step_100000` IFEval shard 0 both tried port `10500`. The `step_100000` server
failed to bind with `address already in use`, but the health check passed
against the already-running `step_50000` server. The `step_100000` client then
sent requests for model `hrm-dfm-L-ifeval-da-shard-0-step_100000` to the
`step_50000` server, producing HTTP 404 `Unknown model` entries that the
monitor counted as failed requests on the `step_50000` server.

`scripts/schedule_checkpoint_evals.sh` now derives DFM server ports from the
actual GPU id rather than the child worker id:

- normal DFM tasks: `PORT_BASE + gpu * 100 + random_offset`
- IFEval-DA: `PORT_BASE + 1000 + gpu * 100 + shard`
- judge server: `JUDGE_PORT + gpu`

The HRM `/health` wait now optionally checks that the health response reports
the expected model name, so a stale server on the requested port cannot satisfy
readiness for a different checkpoint/model. The doomed `step_100000` IFEval
child was stopped and relaunched manually on GPU6 with the patched script; the
replacement server used port `11100`. Confidence: high.
