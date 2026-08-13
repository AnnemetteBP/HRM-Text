---
type: Plan Record
title: Broad Synthetic Common Pile and DynaWord Scaling
description: 'Part of DFM8 Plan: Broad Synthetic Common Pile and DynaWord Scaling.'
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
# Broad Synthetic Common Pile and DynaWord Scaling

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-09. Confidence: medium from local wiki/script notes and prior
partial audit runs.

DFM8 should revive the broader synthetic/transformation-data ambition rather
than only use the few files that happened to be accepted/tokenized in earlier
mixes.

Relevant existing work:

- DFM2 generated Danish DynaWord self-supervised task sources:
  prefix-continuation variants, denoising variants, and six span-fill variants
  from rechunked DynaWord continuation rows.
- DFM3 generated English Common Pile self-supervised task sources:
  direct continuation, prefix continuation, denoising, and three span-fill
  variants from rechunked Common Pile rows.
- DFM4 added paragraph reordering from DynaWord/Common Pile and summarization
  from Common Pile-derived/document-summary sources.
- Later export datasets covered eight audited transformation families:
  `common-pile-denoising`, `common-pile-paragraph-reordering`,
  `common-pile-prefix-continuation`, `common-pile-span-filling`,
  `danish-dynaword-denoising`, `danish-dynaword-paragraph-reordering`,
  `danish-dynaword-prefix-continuation`, and
  `danish-dynaword-span-filling`.
- The audit/rebalance infrastructure targeted about 100M accepted tokens per
  dataset, with paragraph-reordering capped at 50M accepted tokens. The broader
  run was paused/rebalanced several times, so prior DFM mixes used only a
  partial subset of the intended accepted export data.
- Post-training transformation/refinement work also prepared 10 synthetic
  request files of 50k requests each, with English and Danish variants for
  exact-sentence summary, past-tense rewrite, child-friendly simplification,
  numbered fact extraction, and non-copy rewrite.

DFM8 data plan for these sources:

1. Inventory all `export/*` and `expert/*` transformation datasets and their
   audit/filter state. Distinguish accepted rows, unaudited rows, rejected rows,
   and generated-but-not-tokenized rows.
2. Complete or resume audits to balanced token targets instead of taking a
   filesystem-accidental subset:
   - default 100M accepted tokens per transformation family;
   - 50M for paragraph reordering unless smoke tests show it is especially
     useful;
   - separate Danish DynaWord and English Common Pile targets.
3. Convert only accepted rows into DFM8 Gemma4-chat sources. Do not include
   unaudited rows by default.
4. Preserve source-family tags in analytics:
   `dynaword_denoising`, `dynaword_prefix_continuation`,
   `dynaword_span_filling`, `dynaword_paragraph_reordering`,
   `common_pile_denoising`, `common_pile_prefix_continuation`,
   `common_pile_span_filling`, `common_pile_paragraph_reordering`, and
   `posttrain_transform_refine`.
5. Cap continuation-like tasks so they support robustness and reconstruction
   skills without crowding out instruction following, math-contract, and
   tool-calling fixes.
6. Use the Gemma4 31B/26B teacher workflow only for transformation/refinement
   families where teacher generation adds value. For pure denoising/span/prefix
   tasks, deterministic conversion plus judge audit may be sufficient.
7. Add smoke/eval coverage for the transformation skills: denoising,
   span-filling, prefix continuation, paragraph reordering, exact sentence
   summary, simplification, tense rewrite, fact extraction, and non-copy
   rewrite in both Danish and English.

Operational DFM8 implementation plan for broad synthetic/transformation data:

1. Source inventory and manifests.
   - Build a manifest over:
     `export/common-pile-*`, `export/danish-dynaword-*`,
     `expert/common-pile-*`, `expert/danish-dynaword-*`, and any
     `posttrain_transform_refine*` outputs.
   - For every file, record source family, language, task type, row count,
     byte size, audit status, accepted row count, accepted-token estimate,
     teacher model if any, and whether it was already used in DFM5/DFM6/DFM7.
   - Produce a "missing broad coverage" report listing source families where
     only a few files were accepted/tokenized previously.
2. DynaWord deterministic task families.
   - Include broadly sampled Danish DynaWord-derived:
     `denoising`, `prefix_continuation`, `span_filling`, and
     `paragraph_reordering`.
   - Convert to instruction rows, not raw continuation rows:
     - denoising: "Ret støjfejlene i teksten";
     - prefix continuation: "Fortsæt teksten naturligt";
     - span filling: "Udfyld de manglende passager";
     - paragraph reordering: "Sæt afsnittene i den mest naturlige rækkefølge".
   - Keep targets as clean final answers only; no teacher reasoning.
3. Common Pile deterministic task families.
   - Include broadly sampled English Common Pile-derived:
     `denoising`, `prefix_continuation`, `span_filling`, and
     `paragraph_reordering`.
   - Use the same task contracts as DynaWord, but in English.
   - Cap raw continuation-like rows tightly; DFM8 is primarily an
     instruction/chat rebuild, not a return to raw pretraining.
4. Teacher-generated transformation/refinement families.
   - Use Gemma4 31B/26B teacher generation for tasks where deterministic
     conversion is insufficient:
     exact-sentence summary, two-sentence summary, child-friendly
     simplification, past-tense rewrite, numbered fact extraction,
     non-copy rewrite, style-neutral rewrite, and concise answer extraction.
   - Generate Danish and English variants for every task family.
   - Use broad random sampling from Common Pile and DynaWord source shards,
     not only the first or easiest few files.
   - Keep request/response prompts short and explicit; targets should be clean
     final answers without hidden reasoning traces.
5. Audit and acceptance.
   - Deterministic tasks can be accepted by structural checks plus lightweight
     judge/audit sampling.
   - Teacher-generated tasks require judge audit for:
     follows instruction, preserves meaning, language correctness, no
     hallucinated facts, no copying when non-copy rewrite is requested, and
     safe refusal only when truly needed.
   - Use balanced audit targets: default 100M accepted tokens per family and
     50M for paragraph reordering, unless a pilot shows a different family is
     unusually high or low value.
6. Sampling policy.
   - Report these as separate top-level categories, not as generic Danish or
     English instruction data.
   - Suggested category caps for the first DFM8 build:
     - DynaWord transformation tasks: useful but bounded;
     - Common Pile transformation tasks: useful but bounded;
     - teacher refinement tasks: prioritize over continuation-like tasks;
     - paragraph reordering: cap lower unless eval/smoke shows strong benefit.
   - Do not let continuation/prefix tasks crowd out strict math, native
     tool-calling, Danish school/instruction, OpenHermes format-following, or
     TV2R-GEC.
7. Validation before training.
   - For each family, sample 25 rendered Gemma4-chat rows and inspect manually.
   - Run a small bilingual smoke suite for denoising, span filling, paragraph
     ordering, summary length control, tense rewrite, fact extraction, and
     non-copy rewrite.
   - Fail the build if rendered rows contain raw template artifacts, missing
     assistant targets, wrong language, teacher meta-commentary, or repeated
     instructions in the answer.

Build note, 2026-07-09. Confidence: high from local file/audit-summary
inspection.

The first DFM8 implementation pass linked the existing `export-upload/*`
transformation datasets. These are compacted accepted-row uploads, not merely
the first `export/data` files, but they are still not the full broad
Common-Pile/DynaWord transformation ambition.

Current accepted/uploaded coverage:

| Family | Uploaded accepted rows | Uploaded shard files | Effective source families | Effective source files |
| --- | ---: | ---: | ---: | ---: |
| `common-pile-denoising` | 254,565 | 7 | 2 | not listed |
| `common-pile-paragraph-reordering` | 86,328 | 16 | 2 | 16 |
| `common-pile-prefix-continuation` | 619,911 | 19 | 3 | 19 |
| `common-pile-span-filling` | 253,715 | 7 | 2 | 7 |
| `danish-dynaword-denoising` | 65,518 | 4 | 1 | 4 |
| `danish-dynaword-paragraph-reordering` | 55,340 | 3 | 1 | 3 |
| `danish-dynaword-prefix-continuation` | 105,317 | 2 | 1 | 2 |
| `danish-dynaword-span-filling` | 54,968 | 2 | 1 | 2 |

Interpretation:

- Common Pile prefix continuation has reasonable breadth over arXiv abstracts,
  arXiv papers, and Library of Congress. Other Common Pile families are still
  narrower than the full Common Pile source inventory.
- DynaWord transformation uploads are accepted rows from only a few DynaWord
  source files. They should not be treated as broad DynaWord coverage.
- Do not sample DFM8 until this is resolved. The interrupted initial sampling
  attempt was stopped and the partial `data/sampled_dfm8` output was removed.

Required fix before sampling:

1. Decide whether DFM8 should use the existing accepted/uploaded transformation
   subset as-is or expand it now.
2. If expanding, resume/rebuild accepted rows from broader `export/data` and
   `export/audited` coverage, especially for DynaWord.
3. Rebuild `export-upload` or a DFM8-specific accepted-transform root, then
   retokenize/rebuild `data/tokenized_dfm8` before sampling.

Update, 2026-07-09. Confidence: high from local commands and manifests.

The DFM8 transformation expansion now samples new candidate rows from broader
`export/*/data` coverage while keeping the existing accepted upload rows. The
target was changed to 2.5x the existing accepted row count per family, because
the intended policy is "slightly more than 2x additional rows before audit" so
that audit rejection still leaves about a 2x expansion.

Expansion manifest:

| Family | Existing accepted rows | Target new candidates | Actual new candidates |
| --- | ---: | ---: | ---: |
| `common-pile-denoising` | 254,565 | 636,413 | 636,413 |
| `common-pile-paragraph-reordering` | 86,328 | 215,820 | 85,029 |
| `common-pile-prefix-continuation` | 619,911 | 1,549,778 | 1,549,778 |
| `common-pile-span-filling` | 253,715 | 634,288 | 634,288 |
| `danish-dynaword-denoising` | 65,518 | 163,795 | 150,773 |
| `danish-dynaword-paragraph-reordering` | 55,340 | 138,350 | 69,707 |
| `danish-dynaword-prefix-continuation` | 105,317 | 263,293 | 234,008 |
| `danish-dynaword-span-filling` | 54,968 | 137,420 | 134,580 |
| **Total** | **1,495,662** | **3,739,157** | **3,494,576** |

Some families exhausted the available source rows before reaching the 2.5x
per-family target. Total new candidates are still more than 2x the existing
accepted rows.

Audit launch, 2026-07-09. Confidence: high from active process list, vLLM
readiness checks, and GPU telemetry.

The expansion candidates are being audited with
`scripts/run_dfm8_transform_expansion_audits_8gpu_vllm.sh`, launched from the
`hrm` conda environment in tmux window `hrm-0:dfm8-audit`.

Audit settings:

- one OpenAI-compatible vLLM Gemma4 31B judge server per GPU;
- ports `8400` through `8407`;
- `GPU_MEMORY_UTILIZATION=0.95`;
- audit client `CONCURRENCY=8` per family/GPU;
- model path:
  `data/models/google/gemma-4-31B-it-fresh-20260604`, with fallback to
  `/work/dfm/brainsurgery/models/google/gemma-4-31B-it`;
- log root:
  `logs/dfm8_transform_expansion_audits_20260709T101927`;
- audit outputs:
  `data/dfm8_transform_expansion/<family>/audit_full/audit.jsonl`.

Observed startup state: all eight `/v1/models` endpoints answered, all eight
audit clients started, and GPUs were at roughly 173-176 GiB allocated with
100% utilization. vLLM logged that Gemma4's Blackwell FA4 path is not used for
head sizes 256/512 and fell back to Triton attention; this does not block the
audit but is relevant for performance expectations.

Update, 2026-07-09. Confidence: high from local commands, manifest updates,
and vLLM metrics.

The first static audit showed that `common-pile-prefix-continuation` was
oversampled: it accounted for 1,549,778 of 3,494,576 new candidates, or 44.3%
of the expansion. Because this is continuation-like data and should not crowd
out instruction, math/code/tool, denoising, span-filling, and Danish data, DFM8
now removes half of the new `common-pile-prefix-continuation` shard files.

The cap was applied by moving 229 whole `.jsonl.gz` files from
`data/dfm8_transform_expansion/common-pile-prefix-continuation/data` to
`data/dfm8_transform_expansion/common-pile-prefix-continuation/removed_for_dfm8_cap_20260709`.
Whole-file removal preserves row IDs and line numbers for retained rows.

After the cap:

- retained `common-pile-prefix-continuation` new candidates: 774,936;
- removed `common-pile-prefix-continuation` new candidates: 774,842;
- total DFM8 transform-expansion new candidates: 2,719,734.

The static audit was stopped and replaced by
`scripts/run_dfm8_transform_expansion_audits_dynamic_8gpu_vllm.sh`, launched in
tmux window `hrm-0:dfm8-audit` with log root
`logs/dfm8_transform_expansion_dynamic_audits_20260709T104515`.

Dynamic audit behavior:

- one Gemma4 31B OpenAI-compatible vLLM server per GPU;
- `GPU_MEMORY_UTILIZATION=0.95`;
- `CONCURRENCY=32` per audit process;
- stable hash shards per family;
- workers claim the next pending shard when their current shard finishes;
- existing partial `audit_full/audit.jsonl` rows from the static run are passed
  with `--skip-audit` and are not repeated.

Although vLLM reported "Maximum concurrency for 8,192 tokens per request:
15.66x", live metrics with the real audit prompts at `CONCURRENCY=32` showed
29-32 running requests, 0 waiting requests, and only about 23-29% KV-cache use
per server. This suggests the audit prompts are much shorter than the 8,192
token worst-case estimate and concurrency 32 is acceptable for this audit.

Update, 2026-07-09. Confidence: high from local commands and vLLM metrics.

The dynamic audit was restarted with `CONCURRENCY=64` and
`AUDIT_SHARD_ROOT_NAME=audit_shards_c64`, log root
`logs/dfm8_transform_expansion_dynamic_audits_c64_20260709T105550`.
The launcher now skips all existing per-family `audit.jsonl` files, including
the static `audit_full` rows and the partial `audit_shards` rows from the
concurrency-32 run, so work completed before the restart is not repeated in
the final union of audit files.

Observed c64 state shortly after restart:

- 61-64 running requests per vLLM server;
- 0 waiting requests on all servers;
- about 46-51% KV-cache usage;
- 8 running shard jobs, 168 pending, 0 failed.

This makes `CONCURRENCY=64` acceptable for the current Gemma4 audit workload
with `MAX_NUM_SEQS=64`; do not raise above 64 without restarting vLLM with a
higher `--max-num-seqs` and rechecking waiting/KV metrics.

Update, 2026-07-09. Confidence: high from local commands and vLLM metrics.

The audit was restarted again with `GPU_MEMORY_UTILIZATION=0.7` while keeping
`CONCURRENCY=64`, log root
`logs/dfm8_transform_expansion_dynamic_audits_c64_u070_20260709T110453`, and
`AUDIT_SHARD_ROOT_NAME=audit_shards_c64_u070`.

Observed u0.7 state:

- GPU memory dropped to roughly 129 GiB used per GPU, leaving about 53 GiB free;
- 60-64 running requests per vLLM server;
- 0 waiting requests;
- about 80-88% KV-cache use;
- no errors in the startup/progress sample.

Measured throughput over one 60-second sample was about 3,162 rows/min
(7,264 to 10,426 rows). This is slower than the previous u0.95/c64 sample
(about 3,919 rows/min), but leaves much more free memory. Use u0.7 when memory
headroom matters; u0.95 appears faster for this audit if the GPUs are otherwise
dedicated.
