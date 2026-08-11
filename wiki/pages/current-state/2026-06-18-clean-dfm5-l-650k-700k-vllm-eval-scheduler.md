---
type: Operational Record
title: 2026-06-18 Clean DFM5-L 650K/700K vLLM Eval Scheduler
description: 'Part of Current State: 2026-06-18 Clean DFM5-L 650K/700K vLLM Eval Scheduler.'
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
# 2026-06-18 Clean DFM5-L 650K/700K vLLM Eval Scheduler

Part of [Current State](/pages/current-state.md).

Confidence: high for local code inspection, `py_compile`, throwaway plan
probe, plan creation, and live scheduler monitor output.

The first DFM5-L `step_650000` vLLM scheduler run was invalid for standard
English evals. Standard `evaluation.main` vLLM rows attempted to force FA4 with
`VLLM_ATTENTION_BACKEND=FLASH_ATTN`, but this vLLM build logs that env var as
unknown and selected FlashInfer. The broken local artifacts were removed:

```text
logs/scheduler/dfm5_L_step650000_vllm_20260618
logs/eval/dfm5_L_step650000_vllm_20260618
logs/dfm_evals/dfm5_L_step650000_vllm_20260618
logs/euroeval/dfm5_L_step650000_vllm_20260618
```

The scheduler now passes `attention_backend=FLASH_ATTN` as an actual
`evaluation.main` override for standard vLLM rows. Plan metadata records this
as `vllm_attention_backend: FLASH_ATTN`. This matches the known-good DFM5-L
`step_550000` vLLM FA4 standard eval path, whose logs showed
`Using AttentionBackendEnum.FLASH_ATTN backend` and `Using FlashAttention
version 4`.

The scheduler also now has a first-class GPU-backed action:

```text
export_hf
```

For internal vLLM plans, `plan create` inserts `export_hf` after
`wait_checkpoint` by default. It runs `conversion/convert_to_hf.py` with
`--ckpt_use_ema true` unless `--no-ema` is set, writes into a temporary sibling
directory, and swaps it into the requested export path only after
`model.safetensors` is present. If the target export already has
`model.safetensors`, the job succeeds immediately without rewriting it. Disable
this only with `--no-include-hf-export` when the export is managed externally.

The clean combined plan is:

```text
plan_dir:      logs/scheduler/dfm5_L_clean_vllm_650k_700k_20260618
standard logs: logs/eval/dfm5_L_clean_vllm_650k_700k_20260618/step_{650000,700000}
dfm logs:      logs/dfm_evals/dfm5_L_clean_vllm_650k_700k_20260618/step_{650000,700000}
euro logs:     logs/euroeval/dfm5_L_clean_vllm_650k_700k_20260618
W&B run:       DFM5 / dfm5-l-vllm-clean-650k-700k-20260618
```

It contains full 650K and 700K eval graphs. The 700K wait row is explicitly
chained behind the 650K report row:

```text
wait-00212 step_700000 depends on report-00211 step_650000
export-00213 step_700000 depends on wait-00212
```

The run was launched in tmux session `hrm-0`:

```bash
cd /work/dfm/HRM-Text
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm5_L_clean_vllm_650k_700k_20260618 \
  --gpus 0,1,2,3,4,5,6,7

python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm5_L_clean_vllm_650k_700k_20260618 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 10
```

Initial monitor output showed `wait-00001` and `export-00002` done for 650K.
The export job skipped because
`exports/dfm5_L_step650000_ema_hf/model.safetensors` already existed. The first
EuroEval wave was running on all eight GPUs.

Follow-up, 2026-06-19. Confidence: high for local scheduler code inspection,
`py_compile`, plan edits under `PlanLock`, and live monitor output. The DFM
`generative_talemaader` task must not rely on a single shared judge URL. The
scheduler now supports managed per-task judge servers for this task via plan
metadata:

```text
judge_model: openai/gemma-4-e4b-judge
judge_server_model: unsloth/gemma-4-E4B-it
judge_server_dtype: bfloat16
judge_server_attn_implementation: sdpa
judge_server_max_new_tokens: 64
```

For `generative_talemaader`, each shard starts its own target HRM/vLLM server
and its own judge server on the same assigned GPU, passes the resulting
per-shard `--judge-base-url` to `dfm-evals`, and tears down the judge in the job
cleanup path. This replaced the broken single external judge assumption that
caused 650K Talemaader shards to stall.

There are two distinct batching controls for this path:

```text
initial_batch:   target HRM/vLLM server batch size shown as `batch` in monitor
max_connections: dfm-evals client concurrency to the target and judge APIs
```

The 650K Talemaader recovery rows were intentionally kept conservative at
`initial_batch=4` and `max_connections=4`; live monitor output showed all eight
shards moving with no failed judge calls.

Superseded: the still-pending 700K Talemaader rows were briefly updated under
scheduler lock to `initial_batch=16` and `max_connections=16`.

Superseded: Replacement, 2026-06-19. The 700K Talemaader rows were removed
from the active clean plan:

```text
removed eval-00385..eval-00392
removed merge-00393
updated average-00421 deps 37 -> 36
```

Replacement, 2026-06-19. Confidence: high for local process inspection,
locked plan edit, and scheduler monitor output. The intended change was to
stop and remove all 700K eval work, not just Talemaader. The scheduler stop
file was written, the active scheduler/eval process group `1106626` was
terminated, and every `step_700000` row was removed from the clean plan:

```text
removed_step_700000_rows=202
total_rows=211
remaining_step_700000_rows=0
```

Post-edit monitor output showed the plan completed/stopped with
`done=211`, `running=0`, `ready=0`, `blocked_pending=0`, `failed=0`,
`total=211`. Process inspection found no remaining `step_700000` vLLM,
proxy, EuroEval, or scheduler-run processes; the remaining GPU processes were
the existing training workers.

Follow-up, 2026-06-19. Confidence: high for local plan creation, metadata
inspection, and live scheduler monitor output. A fresh 700K-only scheduler was
created so the 700K metrics log to the main DFM5-L W&B run rather than the
temporary clean 650K run:

```text
plan_dir:      logs/scheduler/dfm5_L_step700000_vllm_main_20260619
standard logs: logs/eval/dfm5_L_step700000_vllm_main_20260619
dfm logs:      logs/dfm_evals/dfm5_L_step700000_vllm_main_20260619
euro logs:     logs/euroeval/dfm5_L_step700000_vllm_main_20260619
W&B target:    DFM5 / oti1lisg / dfm5-L
eval_epoch:    3.865238465506098
```

The plan has 211 rows for `step_700000` only. It uses the agreed vLLM path:
standard evals through `evaluation/config/hrm_vllm_benchmarking.yaml`, HRM
EuroEval through the native-compatible proxy, explicit FA4 via
`--attention-backend FLASH_ATTN`, vLLM GPU memory utilization `0.35`, and
EuroEval max concurrent calls `32`. The managed Talemaader judge setup is
enabled with one per-shard `unsloth/gemma-4-E4B-it` judge server, and
Talemaader rows are explicitly set to `initial_batch=16` and
`max_connections=16`.

The run was launched in tmux session `hrm-0`:

```text
runner:  window eval700main
monitor: window mon700main
```

Initial monitor output showed `done=2`, `running=8`, `failed=0`, with the
EuroEval-first block running on GPUs 0-7.

Superseded/correction, 2026-06-19. Confidence: high for live process
inspection and local scheduler code inspection. The 700K plan above did use
vLLM for EuroEval, but it did **not** use vLLM for the DFM and DFM-IFEval
shards. Live DFM-IFEVal processes were:

```text
scripts/hrm_openai_server.py --ckpt-path checkpoints/dfm5/L --ckpt-tag step_700000 ...
```

not `vllm.entrypoints.openai.api_server`. Code inspection showed why:
`run_dfm()` and `run_dfm_ifeval()` only dispatch to their vLLM-backed
`*_external()` variants when `is_external_model(job)` is true. The
`hrm_server_backend=vllm` setting is currently honored by the EuroEval wrapper
path, not by scheduler DFM/DFM-IFEval rows for internal HRM checkpoints.

The run was stopped to avoid logging further non-vLLM 700K DFM results to the
main W&B run. Process group `1438800` was terminated. After stopping, process
inspection found no active `step_700000` scheduler, HRM server, vLLM server,
proxy, or EuroEval worker processes. At stop time the plan had completed:

```text
17 eval_euroeval rows
2 eval_euroeval_batched_ifeval rows
6 eval_dfm_ifeval rows using native HRM server
1 eval_euroeval row failed: valeu-da
```

Before a vLLM-only 700K DFM run, patch the scheduler so internal HRM
`eval_dfm` and `eval_dfm_ifeval` rows honor `hrm_server_backend=vllm` (or route
them through the existing vLLM server helper with the HF export path), then
create a fresh plan or reset only the intended rows.

Follow-up fix, 2026-06-19. Confidence: high for local code inspection,
`py_compile`, locked plan edit, live process inspection, and vLLM logs. The
scheduler was patched so internal HRM DFM and DFM-IFEval rows now honor
`hrm_server_backend=vllm`:

```text
eval_scheduler/eval_scheduler/runtime.py
```

The patch added helpers for internal vLLM routing:

```text
use_vllm_hrm_server(job)
vllm_model_path(job)
vllm_served_model_prefix(job)
```

`start_vllm_server()` now launches from `external_model` for external plans or
from `hrm_hf_export_dir` / `standard_hf_export_dir` for internal HRM plans.
`run_dfm()` and `run_dfm_ifeval()` dispatch to their vLLM-backed paths whenever
`hrm_server_backend=vllm`.

All 32 DFM-IFEval rows were reset to `pending` so the final DFM-IFEval metric
does not mix native HRM-server shards with vLLM shards. The failed EuroEval
`valeu-da` row was also reset. The scheduler was restarted in tmux window:

```text
runner: hrm-0:eval700vllmfix
monitor: hrm-0:mon700main
```

Live process inspection after restart showed DFM-IFEval rows running as:

```text
python -m vllm.entrypoints.openai.api_server \
  --model /work/dfm/HRM-Text/exports/dfm5_L_step700000_ema_hf \
  --served-model-name hrm-dfm5-L-vllm-native-proxy-ifeval-da-shard-... \
  --attention-backend FLASH_ATTN
```

and no `scripts/hrm_openai_server.py --ckpt-tag step_700000` processes. The
new DFM-IFEval vLLM logs confirmed:

```text
Using AttentionBackendEnum.FLASH_ATTN backend.
Using FlashAttention version 4
```
