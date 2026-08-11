---
type: Software Reference
title: '`scripts/synthesize_anonymized_sapient_exclusions.py`'
description: 'Part of Script Entities: `scripts/synthesize_anonymized_sapient_exclusions.py`.'
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
# `scripts/synthesize_anonymized_sapient_exclusions.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-12. Confidence: high for local syntax, initialization, and
active 8-shard launch; medium for final synthetic quality until the generated
rows are audited after completion.

Builds synthetic anonymized replacements for the 321 original Sapient source
files excluded from DFM5. It reads
`logs/data_audits/dfm5_excluded_original_sapient_sources.tsv`, creates one
folder per excluded source under `synth/`, and writes only judge-accepted rows.
For sharded runs it writes one gzip per shard, e.g.
`data/train.shard00000of00008.jsonl.gz`, to avoid concurrent gzip append
corruption.

For each input row the script asks a local OpenAI-compatible teacher to
generate a substantially different anonymized version of the
`condition`/`instruction`/`response` row, then uses the same model as judge. A
row is kept only if the judge accepts it and local heuristics do not find
unchanged PII-like strings or high 5-gram overlap. Rejected attempts are kept
under `rejected/`, also split by shard for sharded runs.

Resume fix, 2026-06-12: the first 8-worker run wrote every shard into the same
`data/train.jsonl.gz` and `rejected/rejected.jsonl.gz`, which corrupted the
gzip stream under concurrent appends. Those legacy files for
`synth/Platypus_reclor.jsonl` were quarantined under
`synth/Platypus_reclor.jsonl/corrupt_20260612T214749/`. The script now writes
per-shard accepted/rejected gzip files and per-shard summaries. It also skips
unreadable gzip files when loading resume IDs instead of crashing.

Quality-gate tightening, 2026-06-12: accepted rows now require all judge
booleans to be true (`keep`, `substantially_different`, `pii_changed`,
`low_textual_overlap`, `task_preserved`, and `quality_ok`) in addition to the
local heuristic requiring at most `0.08` candidate 5-gram overlap and no
unchanged PII-like strings. Before resuming, the existing 469 accepted ReClor
rows were audited locally and all 469 passed this stricter condition.

Priority/concurrency update, 2026-06-13: the script now supports
`--source-priority high40`, an explicit 40-file high-priority campaign that
excludes the huge WMT/translation and broad review/sentiment sources. It also
supports `--concurrency N` per worker. The first batched run used concurrency
`8` and verified `Running: 8 reqs` per GPU server. It was then restarted with
`CONCURRENCY_PER_SHARD=32`; vLLM sustained `31-32` running requests per GPU
with no waiting queue, KV cache usage below about `30%`, and a measured
high40 throughput sample of about `1,206` rows/min.

Concurrency-128 update, 2026-06-13: the first `MAX_NUM_SEQS=128` launch failed
on one GPU during vLLM/TorchInductor autotuning with `CUDA driver error: file
not found`, likely from shared compile/cache races during simultaneous
multi-server startup. The launcher now sets per-GPU `VLLM_CACHE_ROOT`,
`TORCHINDUCTOR_CACHE_DIR`, and `TRITON_CACHE_DIR` under the run log root. The
second 128 launch succeeded. vLLM showed about `99-128` running requests per
GPU, but some GPUs reached `96-99.9%` KV cache usage and small waiting queues.
The first measured high40 row-throughput sample under the then-active sources
was about `614` rows/min.

Smoke/init commands:

```bash
cd /work/dfm/HRM-Text
python scripts/synthesize_anonymized_sapient_exclusions.py --init-only
python scripts/synthesize_anonymized_sapient_exclusions.py \
  --base-url http://127.0.0.1:8900/v1 \
  --model posttrain-gemma-teacher \
  --limit-sources 1 \
  --limit-rows-per-source 10
```
