---
type: Plan Record
title: Token Delta Estimate Versus DFM7
description: 'Part of DFM8 Plan: Token Delta Estimate Versus DFM7.'
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
# Token Delta Estimate Versus DFM7

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-11. Confidence: medium. The current tokenized source inventory
was compared with `scripts/report_dfm8_mix.py` on `data/tokenized_dfm7` and
`data/tokenized_dfm8`. This is a source-token inventory estimate, not the final
sampled-per-epoch token count.

Verified current local source-token totals:

| Dataset tree | Rendered/source tokens |
| --- | ---: |
| `data/tokenized_dfm7` | 136,490,762,775 |
| `data/tokenized_dfm8` before full targeted synthetic integration | 137,154,725,776 |
| Current DFM8 delta before full targeted synthetic | 663,963,001 |

The current delta is mostly from the DFM8 additions that are already tokenized:
OpenHermes, TV2R DaLA/GEC-DaLA, and SkoleGPT. The full six
`dfm8-synthetic-*` datasets are not yet represented in `data/tokenized_dfm8`.

Estimated full targeted synthetic contribution:

| Family | Estimated full rows | Estimated rendered tokens |
| --- | ---: | ---: |
| `native_tool_calling` | 841,561 | 517,012,908 |
| `danish_summarization_rewrite_controls` | 827,823 | 396,812,231 |
| `multiturn_danish_english_chat` | 415,468 | 367,443,856 |
| `code_debugging` | 339,838 | 246,603,846 |
| `strict_math_answer_contract` | 555,049 | 173,084,063 |
| `constrained_format_following` | 839,046 | 170,447,474 |
| **Total targeted synthetic** | **3,818,785** | **1,871,404,378** |

Method: sample-tokenized 20,000 accepted uploaded rows per family with
`/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json` and
`data_io/chat_templates/gemma4_native_chat.jinja`, then scaled the accepted
126-shard upload slice to the planned 512 shards. This assumes later shards
have similar acceptance rates and length distributions.

Expected DFM8 source-token inventory if the full targeted synthetic datasets
are integrated at this acceptance/length profile:

| Quantity | Tokens |
| --- | ---: |
| DFM8 current total | 137,154,725,776 |
| Estimated full targeted synthetic | 1,871,404,378 |
| Estimated DFM8 full total | 139,026,130,154 |
| Estimated DFM8 full delta over DFM7 | 2,535,367,379 |

So, judged from current additions plus the full targeted synthetic plan, DFM8 is
expected to add about **2.54B source tokens** over DFM7, before applying final
sampling weights/caps.
| `multiturn_danish_english_chat` | 102,244 |
| `code_debugging` | 83,632 |
| Total accepted | 939,779 |

The build summary reports `generated_rows: 1183425` and `audit_rows: 1128522`.

Upload result, 2026-07-10. Confidence: high from local upload log and public
`repo_info` checks.

The six DFM8 targeted synthetic upload folders were uploaded as public Hugging
Face dataset repositories under `schneiderkamplab`:

| Repo | Commit |
| --- | --- |
| `schneiderkamplab/dfm8-synthetic-code-debugging` | `d38f0b9792a245d6cb5850828ec3dc3d09af8514` |
| `schneiderkamplab/dfm8-synthetic-constrained-format-following` | `adc7e9127e8f98b6a83f24b4b01fad403bcd4395` |
| `schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls` | `5632536f12b11d909a700efcb90cfe9f17dcd00f` |
| `schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat` | `40ea24848d4bf045a9e11d72ee6c62d51c4c93d9` |
| `schneiderkamplab/dfm8-synthetic-native-tool-calling` | `fddbf5c03a9ec82763ee816ca9508bf4ddb98512` |
| `schneiderkamplab/dfm8-synthetic-strict-math-answer-contract` | `9ce476a9104482befe7d1137b5fde6ab0c7cd378` |

The upload log is `logs/hf_upload_dfm8_synthetic_20260710T125623.log`.

Pipelined generation/audit update, 2026-07-10. Confidence: high from script
inspection and launch command.

`dfm8_synthetic/scripts/run_dfm8_targeted_synthetic_8gpu.sh` now supports
`PIPELINE_AUDIT_AS_GENERATED=1`. In this mode, each GPU worker generates a
request shard and immediately audits that generated shard before claiming the
next generation shard. It also drains any pre-existing `audit_pending` jobs at
the end. This avoids waiting for the whole generation campaign before audit
begins.

The remaining-shard run was started with:

```bash
cd /work/dfm/HRM-Text
LOG_ROOT=logs/dfm8_targeted_synthetic_pipeline_remaining_$(date +%Y%m%dT%H%M%S) \
DATA_ROOT=data/dfm8_targeted_synthetic \
UPLOAD_ROOT=export-upload-dfm8-synthetic \
PIPELINE_AUDIT_AS_GENERATED=1 \
CONCURRENCY=64 \
GPU_MEMORY_UTILIZATION=0.7 \
MAX_NUM_SEQS=64 \
bash dfm8_synthetic/scripts/run_dfm8_targeted_synthetic_8gpu.sh
```

Before launch, local counts were `512` request shards, `126` generated shards,
`126` audited shards, `386` missing generated shards, and `0` generated shards
missing audit.

Concurrency experiment, 2026-07-10. Confidence: high for the local process
state; medium for performance interpretation until a full wave finishes.

After the pipelined run reached `166` generated/audited shards, the pending
generation queue was drained safely for a `CONCURRENCY=128` /
`MAX_NUM_SEQS=128` trial:

1. Move `generate_pending` jobs in
   `logs/dfm8_targeted_synthetic_pipeline_remaining_20260710T125840/queue/`
   to `generate_held_for_concurrency128`.
2. Wait for `generate_running=0` and `audit_running=0`.
3. Kill the old tmux window so its vLLM servers are cleaned up.
4. Restart a pipelined run:

```bash
cd /work/dfm/HRM-Text
LOG_ROOT=logs/dfm8_targeted_synthetic_pipeline_c128_$(date +%Y%m%dT%H%M%S) \
DATA_ROOT=data/dfm8_targeted_synthetic \
UPLOAD_ROOT=export-upload-dfm8-synthetic \
PIPELINE_AUDIT_AS_GENERATED=1 \
CONCURRENCY=128 \
GPU_MEMORY_UTILIZATION=0.7 \
MAX_NUM_SEQS=128 \
bash dfm8_synthetic/scripts/run_dfm8_targeted_synthetic_8gpu.sh
```

Early observation for `logs/dfm8_targeted_synthetic_pipeline_c128_20260710T164733`:
the first 128-concurrency generation wave reached `700-800` rows per shard
after startup. vLLM reported generation throughput roughly similar to the
64-concurrency run, but KV cache usage rose to `97-99.8%` and several GPUs had
waiting requests. Keep 128 only if the first full generate+audit wave improves
wall time; otherwise revert to 64 because the extra concurrency leaves little
KV headroom.
