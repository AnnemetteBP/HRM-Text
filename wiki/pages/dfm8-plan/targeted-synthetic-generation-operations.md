---
type: Plan Record
title: Targeted Synthetic Generation Operations
description: 'Part of DFM8 Plan: Targeted Synthetic Generation Operations.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# Targeted Synthetic Generation Operations

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-10. Confidence: high from local process/log inspection.

The targeted DFM8 synthetic generation runner currently writes each generated
request shard directly to `data/dfm8_targeted_synthetic/generated/shard_*.jsonl`
and only marks the corresponding queue job done after the Python generator exits
successfully. The Python generator itself can resume from an existing partial
file by request id, but the bash runner's `prepare_jobs` logic treats any
existing generated shard file as complete.

Operational consequence: if a generation client or vLLM server stalls after
writing a partial shard, do not leave the partial file at the final generated
path before restarting the whole runner. Either complete that exact shard with
the Python generator's request-id resume behavior, or move the partial file to a
separate quarantine path and regenerate the shard from scratch.

Observed stall on 2026-07-10:

- run root: `logs/dfm8_targeted_synthetic_fixed_20260709T223530`
- stuck job:
  `queue/generate_running/gpu0__shard_00116_of_00512.jsonl.job`
- partial output:
  `data/dfm8_targeted_synthetic/generated/shard_00116_of_00512.jsonl`
- progress stopped at 8,629 JSONL rows out of 9,417 requests, while the GPU0
  vLLM server still answered `/v1/models` but reported `Running: 64 reqs`,
  zero prompt throughput, and zero generation throughput.

Safe recovery pattern:

1. Stop the stuck generator client for that shard.
2. Prevent audit from racing ahead if the GPU0 server is still wedged.
3. Move or finish the partial generated shard explicitly.
4. Restart the affected vLLM server before using that GPU for audit or further
   generation.

Recovery implementation added on 2026-07-10:

- `scripts/run_dfm8_targeted_synthetic_audit_recovery.sh` starts fresh vLLM
  judge servers, releases jobs from `queue/audit_held_gpu0_recovery`, audits
  only already completed generated shards, and then runs `build-upload`.
- This script deliberately does not call `prepare_jobs` and therefore does not
  requeue held generation shards.
- The incomplete `shard_00116_of_00512.jsonl` from the stalled generation run
  was moved under `data/dfm8_targeted_synthetic/generated_partial/` before
  recovery auditing.

Recovery result, 2026-07-10. Confidence: high from
`export-upload-dfm8-synthetic/build_summary.json`.

The audit-only recovery completed for the 126 generated shards that existed
before the stop-after-active intervention. Upload-ready folders were written
under `export-upload-dfm8-synthetic`. Counts:

| Family | Accepted rows |
| --- | ---: |
| `native_tool_calling` | 207,103 |
| `constrained_format_following` | 206,484 |
| `danish_summarization_rewrite_controls` | 203,722 |
| `strict_math_answer_contract` | 136,594 |
