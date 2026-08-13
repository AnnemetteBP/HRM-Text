---
type: Software Reference
title: '`scripts/run_dfm_evals_on_checkpoints.sh`'
description: 'Part of Script Entities: `scripts/run_dfm_evals_on_checkpoints.sh`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/run_dfm_evals_on_checkpoints.sh`

Part of [Script Entities](/entities/scripts.md).

DFM eval runner for HRM checkpoints.

Current task note, 2026-05-28:

- `hrm_code_humaneval` is available in `config/dfm_evals_hrm_single_tasks.yaml`.
- It routes to `dfm_evals/humaneval`, which uses `inspect-evals` HumanEval and
  executes generated Python in a Docker sandbox by default.

Example command shape:

```bash
cd /work/dfm/HRM-Text
CKPT_PATH=checkpoints/original_plus_mixed_danish_instruction_rich/L \
EPOCHS="4" \
GPU=0 \
MODEL_PREFIX=hrm-original-plus-mixed-L \
SUITE_FILE=config/dfm_evals_hrm_single_tasks.yaml \
SUITE=hrm_code_humaneval \
LOG_ROOT=logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_humaneval \
WANDB_RUN_ID=es1od1in \
WANDB_RUN_NAME=original-plus-mixed-danish-instruction-rich-L \
FINAL_WANDB_SYNC=1 \
scripts/run_dfm_evals_on_checkpoints.sh
```

Confidence: high for registration and command shape; medium for full execution
until Docker/sandbox availability is verified on the target node.

End-to-end wrapper for dfm-evals on HRM checkpoints.

Responsibilities:

- use or clone `dfm-evals`
- start `scripts/hrm_openai_server.py` for each requested checkpoint epoch
- run a dfm-evals suite against the shim as an `openai/<model>` endpoint
- pass `--max-connections` to Inspect so concurrent sample requests can be micro-batched by the shim
- export Inspect logs to Every Eval Ever JSON
- start `scripts/sync_completed_dfm_evals.py` by default so each completed test is exported and logged to W&B under `dfm_eval/...`
- export full Inspect logs to Every Eval Ever JSON at the end for archival use

Default suite:

```text
config/dfm_evals_hrm.yaml: hrm_danish
```

This suite intentionally avoids judge-only and long-context dfm-evals tasks. The original HRM L checkpoints expose a 4096-token context, while the upstream `fundamentals` suite includes RULER 8192/32768 tasks and judge-dependent tasks. Confidence: high for script behavior; medium until a full dfm-evals run completes.

Runtime note, 2026-05-24: the dfm-evals registry in the cloned checkout exposed task ids as `dfm_evals/...`, so `config/dfm_evals_hrm.yaml` uses names like `dfm_evals/danish-citizen-tests`. The local dfm-evals checkout was patched for the public Danish citizen tests dataset schema (`option_a`, `option_b`, `option_c`) and for anonymous HF fallback when no token is present. Confidence: high.

Superseded batching note, 2026-05-24: Danish citizen tests was initially capped to `250` samples by a suite-level `--limit 250`.

Current batching and sync note, 2026-05-24: the suite-level limit was removed so task defaults are used. The wrapper default is `BATCH_SIZE=8`, `INSPECT_MAX_CONNECTIONS=8`, and `BATCH_TIMEOUT_MS=25`, allowing the server to coalesce concurrent Inspect requests into HRM generation batches. The wrapper also defaults to `INCREMENTAL_WANDB_SYNC=1`, `SYNC_INTERVAL_SECONDS=30`, and `FINAL_WANDB_SYNC=0`; this logs each completed test during the run and avoids re-logging the whole epoch at the end. Confidence: high.

Judge note, 2026-05-24: `config/dfm_evals_hrm.yaml:hrm_danish` includes `dfm_evals/generative-talemaader`, which requires a judge model. The wrapper accepts `JUDGE_MODEL` and `JUDGE_BASE_URL` and forwards them as dfm-evals suite placeholders. If `JUDGE_MODEL` is omitted, the suite should fail early instead of silently using an implicit judge. Confidence: high.

Example smoke command:

```bash
cd /work/dfm/HRM-Text
INSTALL=1 EPOCHS="4" scripts/run_dfm_evals_on_checkpoints.sh -- --limit 10
```

Full default command:

```bash
cd /work/dfm/HRM-Text
scripts/run_dfm_evals_on_checkpoints.sh
```
