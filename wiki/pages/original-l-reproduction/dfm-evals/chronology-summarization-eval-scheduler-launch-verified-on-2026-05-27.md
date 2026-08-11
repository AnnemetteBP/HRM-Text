---
type: Operational Record
title: Summarization eval scheduler launch, verified on (2026-05-27)
description: 'Chronological record from dfm-evals: Summarization eval scheduler launch,
  verified on (2026-05-27).'
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
# Summarization eval scheduler launch, verified on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Summarization eval scheduler launch, verified on 2026-05-27. Confidence: high.

`scripts/schedule_summarization_evals_all_checkpoints.sh` queues only the
English/Danish summarization benchmarks:

```text
GovReport
NordjyllandNews
```

Default checkpoint coverage:

```text
original_sapient: epochs 1,2,3,4 under checkpoints/original_sapient/L
original_plus_mixed_danish_instruction_rich: epochs 1,2,3 under checkpoints/original_plus_mixed_danish_instruction_rich/L
```

The scheduler uses eight GPU lanes by default (`GPUS=0,1,2,3,4,5,6,7`) and a
shared `jobs.tsv` protected by `flock`, so each lane takes one job at a time.
The 2026-05-27 launch queued `14` jobs and started all eight initial original
Sapient summarization jobs:

```text
log root: logs/eval/summarization_all_checkpoints_20260527T085348
scheduler PID: 480235
worker PIDs: 480243 480244 480245 480246 480247 480248 480249 480250
status: logs/eval/summarization_all_checkpoints_20260527T085348/status.tsv
```

Launch command:

```bash
cd /work/dfm/HRM-Text
LOG_ROOT="logs/eval/summarization_all_checkpoints_$(date +%Y%m%dT%H%M%S)"
mkdir -p "$LOG_ROOT"
setsid scripts/schedule_summarization_evals_all_checkpoints.sh \
  > "$LOG_ROOT/scheduler.log" 2>&1 < /dev/null &
echo $! > "$LOG_ROOT/scheduler.pid"
```
