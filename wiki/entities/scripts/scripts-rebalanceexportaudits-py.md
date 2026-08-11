---
type: Software Reference
title: '`scripts/rebalance_export_audits.py`'
description: 'Part of Script Entities: `scripts/rebalance_export_audits.py`.'
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
# `scripts/rebalance_export_audits.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-11. Confidence: high for syntax, status output, and manual
rebalance launches; medium until all target-token audit runs finish.

Conservative process-level controller for token-targeted export audits. It can:

- report per-dataset accepted-token estimates with `status`;
- watch for the first dataset to cross a token target;
- stop the current monolithic `export_audits_8gpu` tmux session;
- relaunch only unfinished datasets as stable hash shards across the available
  GPUs, with each shard using `--skip-audit` to avoid already-audited rows.

The active watch session was launched as:

```bash
python scripts/rebalance_export_audits.py watch \
  --target-tokens 100000000 \
  --interval-seconds 300 \
  --gpus 0,1,2,3,4,5,6,7
```

This avoids killing a single child audit worker under
`scripts/run_export_audits_8gpu_vllm.sh`, because that parent script owns all
vLLM servers and its cleanup trap would otherwise tear down the full run.

Operational update later on 2026-06-11: rebalance-launched vLLM servers and
audit workers must be started with `start_new_session=True`. Without that,
children from a short-lived controller process can disappear after the
controller exits. The script now detaches both vLLM and audit worker children.

Verified 100M-token rebalance command:

```bash
python scripts/rebalance_export_audits.py rebalance \
  --target-tokens 100000000 \
  --gpus 0,1,2,3,4,5,6,7 \
  --port-base 8600 \
  --stop-current
```

The 2026-06-11 rebalance log root
`logs/export_dataset_audits_rebalance_20260611T193116` launched all eight GPUs
against the six datasets still below the 100M accepted-token target:

```text
GPU4: common-pile-denoising
GPU0/GPU6: common-pile-paragraph-reordering shards 0/2 and 1/2
GPU3: common-pile-prefix-continuation
GPU5: common-pile-span-filling
GPU1/GPU7: danish-dynaword-paragraph-reordering shards 0/2 and 1/2
GPU2: danish-dynaword-prefix-continuation
```

`danish-dynaword-denoising` and `danish-dynaword-span-filling` were already
above 100M estimated accepted tokens and were excluded from that rebalance.

Update later on 2026-06-11: paragraph-reordering exports are capped at 50M
accepted tokens rather than 100M. This is encoded in
`TARGET_TOKENS_BY_DATASET`:

```text
common-pile-paragraph-reordering: 50M
danish-dynaword-paragraph-reordering: 50M
all other export audit datasets: 100M default
```

The `status`, `rebalance`, and `watch` commands use these per-dataset targets.
The watcher also records the initially complete set and only triggers a
rebalance when a newly complete dataset appears, so already-complete datasets
do not cause an immediate rebalance loop. Active cap watcher:

```bash
python scripts/rebalance_export_audits.py watch \
  --target-tokens 100000000 \
  --interval-seconds 300 \
  --gpus 0,1,2,3,4,5,6,7 \
  --port-base 8600
```

tmux session: `export_audit_cap_watch`
log: `logs/export_audit_cap_watch_20260611T214524.log`

Update on 2026-06-12: `scripts/rebalance_export_audits.py` also supports a
manual `--allocation` override in the form
`dataset:gpu,gpu;dataset:gpu`. This was added after
`common-pile-paragraph-reordering` exceeded its 50M cap while still occupying
two GPUs. The ETA-aware rebalance launched at
`logs/export_dataset_audits_rebalance_20260612T064232` with:

```bash
python scripts/rebalance_export_audits.py rebalance \
  --target-tokens 100000000 \
  --gpus 0,1,2,3,4,5,6,7 \
  --port-base 8700 \
  --stop-current \
  --allocation 'common-pile-denoising:0,1;common-pile-prefix-continuation:2,3,4;common-pile-span-filling:5;danish-dynaword-paragraph-reordering:6,7'
```

Resulting allocation:

```text
GPU0/GPU1: common-pile-denoising shards 0/2 and 1/2
GPU2/GPU3/GPU4: common-pile-prefix-continuation shards 0/3, 1/3, 2/3
GPU5: common-pile-span-filling shard 0/1
GPU6/GPU7: danish-dynaword-paragraph-reordering shards 0/2 and 1/2
```

The 2026-06-12 audit generation was stopped manually after the user asked to
pause it. The run is resumable because each dataset-local `audit.jsonl` contains
durable judged `row_id`s and future rebalance launches include all previous
audit files via repeated `--skip-audit`. The stopped log root is:

```text
logs/export_dataset_audits_rebalance_20260612T064232
```

To resume the same ETA-aware allocation later, rerun the same `rebalance`
command above with `--stop-current`; it will skip already-audited rows from
all earlier audit roots.

Debug update on 2026-06-12. Confidence: high for local single-GPU smoke test.
`--enforce-eager` is not required for single-GPU vLLM startup on this machine.
A non-eager Gemma 4 31B IT server on GPU0 successfully loaded, compiled, became
ready, and answered a chat-completions request when launched without
`CUDA_MODULE_LOADING=EAGER`.

The failed/stuck debug launches showed:

- setting `CUDA_MODULE_LOADING=EAGER` caused the EngineCore to spend minutes in
  `torch.cuda._lazy_init()` before model load;
- removing `CUDA_MODULE_LOADING=EAGER` allowed CUDA init, model load,
  `torch.compile`, CUDA graph capture, and API warmup to complete;
- the smoke response to a Danish one-sentence prompt was
  `København er en smuk by.`

Successful debug log root:

```text
logs/vllm_debug_single_gpu_20260612T091958_no_cuda_module_eager
```

Successful launch used GPU0 only, no `--enforce-eager`, and no
`VLLM_DEEP_GEMM_WARMUP=skip`. If scaling back up, use GPUs 0-3 first; GPUs 4-7
were occupied by unrelated HRM OpenAI eval servers during this debug session.

Operational restart on 2026-06-12. Confidence: high for local launch and
process/GPU verification. `scripts/rebalance_export_audits.py` now has a
Boolean `--enforce-eager/--no-enforce-eager` option; default remains
`--enforce-eager` for compatibility with previous runs. After the successful
single-GPU non-eager smoke test, the remaining export audits were restarted on
GPUs 0-3 only, leaving GPUs 4-7 to unrelated HRM eval servers:

```bash
python scripts/rebalance_export_audits.py rebalance \
  --target-tokens 100000000 \
  --gpus 0,1,2,3 \
  --port-base 8900 \
  --allocation 'danish-dynaword-paragraph-reordering:0;common-pile-denoising:1;common-pile-span-filling:2;common-pile-prefix-continuation:3' \
  --no-enforce-eager
```

Launch root:

```text
logs/export_dataset_audits_rebalance_20260612T093058
```

Verified active allocation:

```text
GPU0: danish-dynaword-paragraph-reordering shard 0/1
GPU1: common-pile-denoising shard 0/1
GPU2: common-pile-span-filling shard 0/1
GPU3: common-pile-prefix-continuation shard 0/1
```
