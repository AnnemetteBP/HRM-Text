---
type: Operational Record
title: 2026-06-06 Posttrain Synthetic Audit Plan
description: 'Part of Current State: 2026-06-06 Posttrain Synthetic Audit Plan.'
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
# 2026-06-06 Posttrain Synthetic Audit Plan

Part of [Current State](/pages/current-state.md).

Confidence: high for local code paths and seed export counts; medium for final
quality impact until the first judged audit has been inspected.

Decision: when generating the remaining `550,000`
`posttrain_transform_refine` synthetic samples, do not blindly regenerate the
already usable `450,000` old samples. Instead:

1. Generate the remaining `550,000` rows with `--judge-quality` enabled.
2. Run a standalone judge audit over the existing `450,000` generated rows.
3. Always drop and regenerate any row for which the judge is unhappy. A whole
   slice may still be regenerated for efficiency if the audit shows many
   failures, but no judge-failed row should be kept.

The code now supports this as separate commands in
`scripts/prepare_posttrain_transform_refine.py`:

```bash
cd /work/dfm/HRM-Text
python scripts/prepare_posttrain_transform_refine.py export-seed-texts --force
python scripts/prepare_posttrain_transform_refine.py audit-generated \
  --generated-root data/generated_posttrain_transform_refine \
  --audit-root logs/posttrain_transform_refine_generation/audits \
  --base-url http://127.0.0.1:8100/v1 \
  --model posttrain-gemma-teacher \
  --concurrency 32
```

`audit-generated` reads accepted generated JSONL rows, reruns the local
heuristic validator, asks the OpenAI-compatible judge model for quality
judgment, writes per-record audit JSONL files, and writes
`summary.json` grouped by generated file. It does not mutate generated training
rows; downstream conversion/regeneration must treat every `judge_ok=false` row
as excluded.

Seed pools for future request generation were materialized locally:

```text
data/posttrain_transform_refine_seed_texts/en.jsonl: 1,119,746 rows, 1.7G
data/posttrain_transform_refine_seed_texts/da.jsonl:    99,538 rows, 187M
data/posttrain_transform_refine_seed_texts/manifest.json
```

The manifest records the exact source roots, seed value, and source traversal
limits used for the export. The English pool comes from ASSET plus
`data/converted_sources_dfm4_summarization`; the Danish pool comes from
`lexdk`, `danish_dynaword`, `laerebogen_with_followups`,
`synquid_wiki_instruct_da`, and selected Oliver Kinch Danish/BT converted
sources.

Follow-up launch, 2026-06-08. Confidence: high for local commands and observed
process state.

Added orchestration script:

```text
scripts/run_posttrain_transform_refine_to_1m_vllm.sh
```

It runs toward the `1,000,000` synthetic instruction target on all eight GPUs:

1. start one vLLM Gemma 4 31B IT server per GPU;
2. generate the pending `550,000` rows with `JUDGE_QUALITY=1`;
3. audit English-source generated rows (`en_en`, `en_da`) with one judge per
   GPU;
4. build regeneration requests for every row where the judge is unhappy;
5. generate judged replacements for those failures.

The script uses the fresh local teacher model:

```text
data/models/google/gemma-4-31B-it-fresh-20260604
```

The run was launched in tmux:

```bash
cd /work/dfm/HRM-Text
tmux attach -t posttrain_to_1m
```

At launch, all eight vLLM servers became ready on ports `8100..8107`, each GPU
allocated about `165,840 MiB`, and eight shard workers started processing the
missing queue. Initial queue state after worker start:

```text
data/synthetic_request_shards_posttrain_transform_refine_v3_missing/pending: 542
data/synthetic_request_shards_posttrain_transform_refine_v3_missing/running:   8
```
