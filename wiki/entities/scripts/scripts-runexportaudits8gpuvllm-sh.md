---
type: Software Reference
title: '`scripts/run_export_audits_8gpu_vllm.sh`'
description: 'Part of Script Entities: `scripts/run_export_audits_8gpu_vllm.sh`.'
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
# `scripts/run_export_audits_8gpu_vllm.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-11. Confidence: high for shell syntax, local script wiring,
and successful 8-GPU audit startup; medium until the full 8-GPU audit
completes.

Runs the judge audit for the eight non-synthetic export datasets:

```text
common-pile-denoising
common-pile-paragraph-reordering
common-pile-prefix-continuation
common-pile-span-filling
danish-dynaword-denoising
danish-dynaword-paragraph-reordering
danish-dynaword-prefix-continuation
danish-dynaword-span-filling
```

It starts one single-GPU vLLM server per dataset/GPU using Gemma 4 31B IT and
then runs each folder's self-contained:

```bash
python recreate_dataset.py audit ...
```

Default model path is
`data/models/google/gemma-4-31B-it-fresh-20260604`, falling back to
`/work/dfm/brainsurgery/models/google/gemma-4-31B-it` if the fresh local copy is
not present. Default served model name is `posttrain-gemma-teacher`.

Example:

```bash
SAMPLE_RATE=1.0 CONCURRENCY=8 bash scripts/run_export_audits_8gpu_vllm.sh
```

Operational update on 2026-06-11: simultaneous startup of eight Gemma 4 31B IT
vLLM servers initially failed in two ways:

- normal vLLM compilation hit a `torch._inductor` autotune failure
  (`CUDA driver error: file not found`);
- eager startup then hit `deep_gemm` import/warmup failure because `CUDA_HOME`
  was not visible.

The runner now supports `VLLM_EXTRA_ARGS`, isolates
`TORCHINDUCTOR_CACHE_DIR`/`TRITON_CACHE_DIR` per GPU under the log root, and
defaults `VLLM_DEEP_GEMM_WARMUP=skip`. The successful launch used:

```bash
SAMPLE_RATE=1.0 \
CONCURRENCY=8 \
GPU_LIST='0 1 2 3 4 5 6 7' \
AUDIT_ROOT_NAME=audit_full \
VLLM_EXTRA_ARGS='--enforce-eager' \
DEEP_GEMM_WARMUP=skip \
bash scripts/run_export_audits_8gpu_vllm.sh
```

The first full-audit attempt also exposed that the exported
`recreate_dataset.py audit` implementation was not safe for large full
datasets: it built a full in-memory job list and submitted one future per row.
The eight folder-local recreate scripts were patched to stream audit jobs and
keep at most `--concurrency * --queue-factor` futures pending. The streamed
path also passes `path.name` rather than a `Path` object into audit rows, so
`json.dumps` succeeds.

Update later on 2026-06-11: the eight folder-local audit scripts also support
stable sharding and skip-existing behavior:

```bash
python recreate_dataset.py audit \
  --num-shards 4 \
  --shard-index 0 \
  --skip-audit audit_full/audit.jsonl \
  ...
```

The shard key is the stable `row_id` (`dataset/train-xxxxx.jsonl.gz:<line>`).
`--skip-audit` can be repeated and loads existing row ids before scanning, so a
rebalance worker can avoid rejudging rows already present in earlier audit
files. This is used by `scripts/rebalance_export_audits.py`.

Each dataset writes `audit_full/audit.jsonl` and `audit_full/summary.json`
inside its own export folder. To create filtered upload data, run inside each
dataset folder:

```bash
python recreate_dataset.py filter \
  --audit audit_full/audit.jsonl \
  --output-root audited \
  --force
```

Filtering keeps only `keep=true` rows. Negatively judged rows, judge errors,
and unaudited rows are excluded.
