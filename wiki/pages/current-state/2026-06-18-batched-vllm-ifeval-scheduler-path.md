---
type: Operational Record
title: 2026-06-18 Batched vLLM IFEval Scheduler Path
description: 'Part of Current State: 2026-06-18 Batched vLLM IFEval Scheduler Path.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-18 Batched vLLM IFEval Scheduler Path

Part of [Current State](/pages/current-state.md).

Confidence: high for local code inspection, py_compile checks, scheduler plan
inspection, and live monitor/vLLM log output.

The slow EuroEval `ifeval`/`ifeval-da` vLLM path was not fixed by merely
raising EuroEval's concurrent-call setting because EuroEval feeds these tasks
sample-by-sample. A local batched IFEval runner now bypasses that bottleneck
while preserving the EuroEval cached prompts and IFEval scoring:

```text
scripts/run_ifeval_batched_openai.py
scripts/run_batched_ifeval_on_checkpoint.sh
```

`scripts/native_compatible_openai_proxy.py` was also changed to use async
`httpx` forwarding instead of blocking `urllib.request.urlopen()` inside the
FastAPI route. This is required for actual concurrent upstream requests. Live
vLLM logs verified `Running: 32 reqs, Waiting: 0 reqs`.

The durable scheduler integration uses a new action:

```text
eval_euroeval_batched_ifeval
```

When a plan uses `hrm_server_backend=vllm` with the native-compatible proxy,
`eval_scheduler/eval_scheduler/plan.py` routes only EuroEval `ifeval` and
`ifeval-da` to this action; all other EuroEval tasks continue to use the normal
`eval_euroeval` action. `eval_scheduler/eval_scheduler/monitor.py` parses the
batched runner's `batched_ifeval.log`, so the normal scheduler monitor is the
intended monitor for this path.

The initial batched IFEval proof run was launched by an ad hoc tmux script, so
its monitor looked different from the scheduler monitor. Superseded: use the
scheduler path below for resumed and future runs.

Current resumed 550K DFM5-L vLLM IFEval comparison plan:

```text
plan_dir: logs/scheduler/dfm5_L_step550000_batched_ifeval_resume_20260618_205047
output_root: logs/euroeval/dfm5_L_step550000_vllm_native_proxy_batched_ifeval_20260618_204610/step_550000
tmux run window: hrm-0:eval550batched
tmux monitor window: hrm-0:mon550batched
GPUs: 0,1
batch/concurrency: 32
```

The wrapper script must be executable:

```bash
cd /work/dfm/HRM-Text
chmod +x scripts/run_batched_ifeval_on_checkpoint.sh
```

If the scheduler crashes before starting the wrapper, reset stale running rows
without incrementing attempts and relaunch:

```bash
cd /work/dfm/HRM-Text
PLAN_DIR=logs/scheduler/dfm5_L_step550000_batched_ifeval_resume_20260618_205047
python -m eval_scheduler plan reset-running --plan-dir "$PLAN_DIR" --no-increment-attempt
python -m eval_scheduler clear-stop --plan-dir "$PLAN_DIR"
python -m eval_scheduler run --plan-dir "$PLAN_DIR" --gpus 0,1
```

Follow-up, 2026-06-18. Confidence: high for local traceback and completed
scheduler rerun. `ifeval-da` initially retried until failure even though
`predictions.jsonl` had all 541 generations. The failure was in local scoring:
one or more Danish IFEval cached targets had fewer `kwargs` entries than
`instruction_id_list` entries, and `scripts/run_ifeval_batched_openai.py` used
`zip(..., strict=True)`. The runner now pads missing kwargs with `{}` before
calling EuroEval's constraint functions. After resetting only `eval-00009` to
`pending`, the rerun skipped generation, wrote metrics, and the scheduler ended
with `done=2 failed=0`.

Completed local vLLM-native-proxy 550K IFEval metrics:

```text
ifeval instruction_accuracy:    69.65486279197968
ifeval-da instruction_accuracy: 53.2762661506822
```

Follow-up sync patch, 2026-06-18. Confidence: high for local code inspection,
`py_compile`/`bash -n`, and successful W&B backfill. The custom batched
EuroEval IFEval wrapper now logs its flat JSONL result records to W&B through
`scripts/log_euroeval_to_wandb.py` when `WANDB_SYNC=1` and `EVAL_EPOCH` is set.
The scheduler passes the W&B project/run metadata to
`scripts/run_batched_ifeval_on_checkpoint.sh` for
`eval_euroeval_batched_ifeval` rows. The logger now accepts flat records with
singular `language`, `dataset`, `task`, `metric`, `score`, and confidence
fields, which produces the same canonical key shape as the normal EuroEval
sync.

The already-finished 650K batched rows were backfilled to the real DFM5-L W&B
run at epoch `3.5891500036842335`:

```text
euroeval/da/instruction-following/ifeval-da/instruction_accuracy: 53.81851573616802
euroeval/en/instruction-following/ifeval/instruction_accuracy:    69.36556541198156
```

Note: a first manual backfill attempt before the `language` parser fix uploaded
extra `euroeval/unknown/instruction-following/...` metric series. The canonical
`da` and `en` series above are now present; hide or delete the stray W&B series
in the UI if they become confusing.
