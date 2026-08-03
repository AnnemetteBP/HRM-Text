# DFM8 Plan

Last updated: 2026-07-12
Confidence: medium
Scope: Forward-looking plan for a post-DFM7 rebuild. This page should collect
changes that are too invasive to apply to the active DFM7 run.

Operational update, 2026-07-13. Confidence: high from local tmux/process/log
inspection. Restarting `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`
with an existing `data/dfm8_openhermes_repaired` work root resumes safely, but
it re-enters the stages in order. Completed shard files are not regenerated
wholesale; however, row-level failures are archived and retried. This can make
the GPUs show short changing bursts of 100% utilization while the runner sweeps
through an already-completed stage such as `source_audit`, retrying only a few
failed rows per shard, before it returns to the unfinished stage. This behavior
is expected and should be monitored through worker logs and output row counts,
not only through `nvidia-smi` utilization.

## Objectives

DFM8 should keep the DFM7 gains from Gemma4 tokenization, native tool-calling
data, and broader Danish instruction data, but fix two remaining training-data
contract problems:

- Freeform math should consistently teach the contract used by MATH-style evals:
  reasoning if useful, then exactly one final `\boxed{...}` answer.
- Native tool-calling should keep one clean Gemma4/OpenAI-compatible tool-call
  interface and avoid mixed XML/Python-call/string-argument supervision.

DFM8 should also add Danish education/school instruction coverage through
`kobprof/skolegpt-instruct`, pending local row/schema/license inspection.

## Implementation Plan

Update, 2026-07-09. Confidence: medium. This is the concrete build plan for
turning DFM8 from planning notes into a sampleable dataset.

DFM8 should be built as a full Gemma4-template dataset, not as an incremental
patch over DFM7. The implementation should keep all DFM8 paths separate until
validation succeeds:

- raw/downloaded sources: `data/downloads/datasets/*`
- DFM8 converted chat sources: `data/dfm8_chat_sources`
- DFM8 tokenized sources: `data/tokenized_dfm8`
- DFM8 sampled epochs: `data/sampled_dfm8`
- DFM8 sampling config: `data_io/prefix_config_dfm8.yaml`
- training config: `config/data/dfm8.yaml`
- validation logs: `logs/dfm8_*`

High-level build order:

1. Freeze source policy.
   - Include all DFM7 sources that were accepted after the DFM7 fixes unless
     superseded by a DFM8 converter.
   - Include OpenHermes 2.5 as an allowed English SFT source.
   - Fully include `giannor/dala_tv2r_it` and
     `giannor/gec_dala_tv2r_it`.
   - Include `kobprof/skolegpt-instruct` if local row inspection confirms it
     is useful and not mostly redundant.
   - Include the DFM7 native tool-call sources, but regenerate/fix any source
     whose rendered assistant target is not one canonical Gemma4/native tool
     call representation.
2. Download/update raw sources.
   - Extend `scripts/download_training_datasets.py` with DFM8 groups for
     `openhermes`, `giannor_tv2r_instruction`, `skolegpt`, and any new
     synthetic/exported sources.
   - Keep HF dataset revisions in the manifest where practical.
   - Do not write credentials into scripts or wiki pages.
3. Build DFM8 source converters.
   - Add a DFM8 source-tree builder rather than overloading
     `scripts/build_dfm7_chat_source_tree.py`.
   - Every converted row should become a Gemma4-chat source row with explicit
     analytics tags: language, source family, task family, answer contract,
     tool-use contract, and synthetic/teacher/deterministic origin.
   - Render sample rows through `data_io/chat_templates/gemma4_native_chat.jinja`
     before tokenization and fail fast on malformed rows.
4. Run source audits before tokenization.
   - Math audit: boxed/freeform/MCQ/prose/mixed-format rates.
   - Tool audit: valid top-level tools, valid assistant `tool_calls`, no XML
     leftovers, no Python-call string targets, no repeated calls unless intended.
   - Format audit: exact JSON/table/bullet/sentence-count contracts.
   - Danish grammar audit: DaLA/GEC corruption types and expected responses.
   - OpenHermes audit: source/category counts and examples.
5. Tokenize.
   - Use the Gemma4 tokenizer, not the old Sapient BPE tokenizer.
   - Use the non-Rust/Gemma-compatible tokenizer path that handled DFM6/DFM7.
   - Restart partially tokenized files from scratch; do not trust incomplete
     outputs.
6. Sample.
   - Create `data_io/prefix_config_dfm8.yaml` with stable category weights.
   - Produce at least five sampled epochs initially, with the option to append
     more epochs later by copying epoch index files and updating metadata as in
     DFM7.
   - Report source/category token counts before training.
7. Validate sampled rows.
   - Inspect rendered examples from every major category and source.
   - Run a small tokenizer/template smoke to verify BOS/EOS/chat-template
     behavior.
   - Run a source-distribution report by Danish, English, math/code/tool,
     OpenHermes, TV2R-GEC, DynaWord/Common-Pile transforms, tool calling, and
     strict boxed math.
8. Train readiness.
   - Only after the audits pass, add `config/data/dfm8.yaml` pointing to
     `data/sampled_dfm8`.
   - Keep DFM8 W&B runs separate from DFM6/DFM7 unless deliberately resuming
     from a DFM7 checkpoint, in which case the run name should state the data
     switch.

Suggested implementation artifacts:

| File | Purpose |
| --- | --- |
| `scripts/build_dfm8_chat_source_tree.py` | Build symlink/source tree and run DFM8 converters. |
| `scripts/convert_dfm8_openhermes.py` | Convert OpenHermes ShareGPT rows into Gemma4 chat rows with source/category tags. |
| `scripts/convert_dfm8_giannor_tv2r.py` | Convert the two selected TV2R instruction datasets, preserving their `direction`, `content`, `response`, and corruption metadata. |
| `scripts/audit_dfm8_sources.py` | Unified source audit for math/tool/format/Danish-GEC/OpenHermes categories. |
| `scripts/report_dfm8_mix.py` | Token and sampled-count report by source and category. |
| `data_io/prefix_config_dfm8.yaml` | Sampling weights/caps. |
| `config/data/dfm8.yaml` | Training data path. |

Validation gates:

- `giannor/dala_tv2r_it` and `giannor/gec_dala_tv2r_it` full inclusion must be
  visible in the final token report. The current estimate is about 281.1M
  rendered tokens across all splits.
- If all TV2R splits are included, existing DaLA/GEC-DaLA eval metrics should
  be marked as train-contaminated for DFM8. Create a new held-out diagnostic
  from another source or a freshly generated small set if we need clean Danish
  grammar evals.
- OpenHermes full inclusion must be visible in the token report. Current
  estimate is about 430M rendered tokens.
- Strict boxed freeform math must have enough sampled weight to dominate
  mixed-format freeform math.
- Native tool-calling samples must pass rendered-template audits before
  tokenization.
- Broad Common Pile and DynaWord transformed data must be sampled by accepted
  rows and balanced targets, not by whichever files happened to finish earlier.

## Danish Education Data

`kobprof/skolegpt-instruct` is a DFM8 candidate. It is described as Danish
instruction SFT from a quality-filtered translated OpenOrca subset plus
SkoleGPT survey instructions.

Plan:

1. Download and inspect rows locally before integration.
2. Convert to the canonical Gemma4 chat-template message format.
3. Cap initially rather than letting OpenOrca-like rows dominate if the active
   mix already contains similar translated instruction data.
4. Tag it as Danish education/general instruction data in analytics so its
   contribution can be tracked separately from other Danish SFT.

Risk: expected marginal value is medium, not guaranteed high, if the dataset is
mostly redundant with existing translated OpenOrca-like content.

Status, 2026-07-09. Confidence: high from local commands and manifests.

Supersedes the earlier 2026-07-09 note that `kobprof/skolegpt-instruct` was
only a planned source. It is now integrated into the local DFM8 build:

- Downloader entry: `scripts/download_training_datasets.py` as
  `kobprof_skolegpt_instruct`, HF repo `kobprof/skolegpt-instruct`, group
  `dfm8`.
- Converter: `scripts/convert_dfm8_skolegpt.py`.
- Converted source:
  `data/dfm8_special_sources/kobprof_skolegpt_instruct/train-00000.jsonl`.
- Tokenized task:
  `data/tokenized_dfm8/kobprof_skolegpt_instruct__train-00000.jsonl`.
- Sampling policy: `data_io/prefix_config_dfm8.yaml` with `repeat: 8`.

Verified local counts:

| Source slice | Rows/examples | Rendered Gemma4 tokens |
| --- | ---: | ---: |
| `kobprof/skolegpt-instruct` total | 21,580 | 10,967,033 |
| upstream `cot` | 4,593 | not separately counted |
| upstream `flan` | 5,571 | not separately counted |
| upstream `niv` | 5,623 | not separately counted |
| upstream `skolegpt_survey` | 162 | not separately counted |
| upstream `t0` | 5,631 | not separately counted |

The source schema is `id`, `system_prompt`, `question`, `response`, `source`.
The converter preserves `system_prompt` as a system message, `question` as the
user turn, and `response` as the assistant target. This keeps the intended
prompt contract instead of relying on generic field guessing.

Operational commands that worked from `/work/dfm/HRM-Text`:

```bash
python scripts/download_training_datasets.py --groups dfm8 --download
python scripts/convert_dfm8_skolegpt.py --force
python scripts/build_dfm8_chat_source_tree.py --force --new-only
TOKENIZERS_PARALLELISM=false python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir data/tokenized_dfm8_jinja \
  --workers 16 \
  --skip-bad-json
python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
```

Current DFM8 special-source integration status:

| Planned DFM8 addition | Local status |
| --- | --- |
| `teknium/OpenHermes-2.5` | downloaded, converted, tokenized; 1,001,551 rows; about 391.5M rendered tokens in current tokenized report |
| `giannor/dala_tv2r_it` | downloaded, converted, tokenized; 984,126 rows; 68.5M rendered tokens |
| `giannor/gec_dala_tv2r_it` | downloaded, converted, tokenized; 930,565 rows; 192.9M rendered tokens |
| `kobprof/skolegpt-instruct` | downloaded, converted, tokenized; 21,580 rows; 11.0M rendered tokens |
| broad Common Pile and DynaWord transformed rows | generated and audit/filtering is in progress; do not treat the current DFM8 sample as final until accepted-row filtering is complete |

## Targeted Synthetic Generation Operations

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

## Token Delta Estimate Versus DFM7

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

## Danish Linguistic Acceptability And GEC Data

Update, 2026-07-09. Confidence: medium from Hugging Face API/card metadata and
sampled token estimates; high for the inspected schema fields.

Relevant `giannor/*` datasets should be considered for DFM8, but mostly as
Danish linguistic-acceptability, grammar-correction, and diagnostic-eval data,
not as large general instruction data.

Observed namespace shape:

- `giannor/dala`, `giannor/dala_medium`, `giannor/dala_large`,
  `giannor/dala_label_da`: Danish linguistic acceptability rows with `text`,
  `corruption_type`, and label fields. `giannor/dala` is CC-BY-4.0 and has
  train/validation/test/full-train style splits.
- `giannor/dala_gen_v2`, `giannor/dala_gen_v3`,
  `giannor/dala_gen_large_v3`, `giannor/dala_gen_large_v3_ci`,
  `giannor/dala_gen_tv2r`: paired `original`/`corrupted` rows with
  `corruption_type` and affected-token fields. These are candidates for
  Danish correction/rewrite SFT if license/provenance checks pass.
- `giannor/dala_tv2r_it` and `giannor/gec_dala_tv2r_it`: the selected TV2R
  instruction-formatted DaLA/GEC-DaLA datasets for DFM8. Local HF parquet
  metadata inspection on 2026-07-09 found train/validation/test splits and
  instruction-shaped rows with `direction` plus nested `samples.content` and
  `samples.response`.
- `giannor/dala_tv2r` and `giannor/dala_gen_tv2r`: non-instruction base
  variants. Keep as fallback sources for custom converters, but prefer the
  `*_it` instruction variants for DFM8.

Token estimates using the DFM6/DFM7 Gemma4 HF export tokenizer and rendered
Gemma4-chat rows:

| Dataset | Rows, all splits | Estimated tokens, all splits | Estimated train tokens |
| --- | ---: | ---: | ---: |
| `giannor/dala_tv2r_it` | 984,126 | 72.1M | 57.7M |
| `giannor/gec_dala_tv2r_it` | 930,565 | 209.1M | 167.3M |
| Combined selected TV2R instruction data | 1,914,691 | 281.1M | 225.0M |

DFM8 handling:

1. Fully include `giannor/dala_tv2r_it` and
   `giannor/gec_dala_tv2r_it` in DFM8 unless a row-level validation error is
   found. "Fully" here means all train/validation/test rows, so current
   DaLA/GEC-DaLA evals must be labeled train-contaminated for DFM8.
2. Preserve the instruction-tuned row structure:
   - user prompt = `direction` plus `samples.content`;
   - assistant target = `samples.response`;
   - metadata = `corruption_type`, affected-token fields when present, split,
     and source dataset.
3. Keep the non-instruction `dala_tv2r`/`dala_gen_tv2r` base variants as
   fallback only. Do not duplicate them in DFM8 unless we deliberately build a
   separate custom correction/acceptability converter.
4. Add DFM8 diagnostic eval slices by `corruption_type`, because recent smoke
   tests suggest Danish grammar/correction can improve even when aggregate
   Danish headline averages are nearly flat.
5. Cap these rows as a language-quality/GEC slice if the final DFM8 target size
   is small, but include every row at least once when possible. They should
   improve Danish grammar sensitivity, not dominate broad Danish instruction
   following.

## English General SFT And Format-Following Candidates

Update, 2026-07-09. Confidence: medium from dataset card, viewer metadata, and
sampled token estimate.

`teknium/OpenHermes-2.5` may help DFM8 format following, general instruction
following, code, multiple-choice answering, and English reasoning style, but it
should still be category/source audited before sampling heavily.

Observed facts:

- The dataset card says OpenHermes 2.5 has about 1M primarily synthetic
  instruction/chat samples and follows a ShareGPT-style `conversations`
  structure.
- The viewer/API exposes `conversations`, `category`, `source`, and
  `skip_prompt_formatting`, which makes source/category filtering feasible.
- The card lists mixed upstream sources such as Airoboros, CamelAI domain
  expert datasets, ChatBot Arena GPT-4-only, CoT Alpaca GPT4, Evol Instruct,
  Glaive Code Assistant, GPT4-LLM, GPTeacher, Medical Tasks, MetaMath,
  SlimOrca, Platypus, ShareGPT, and Unnatural Instructions.
- Project decision, 2026-07-09: treat OpenHermes as acceptable for DFM8 from a
  license perspective because it is essentially synthetic throughout. This
  supersedes the earlier "review required for licensing" concern. Source and
  category audits are still useful for quality, duplication, and format-policy
  control.
- A stratified local estimate over 12k rows sampled across 24 parquet row
  groups with the DFM6/DFM7 Gemma4 HF export tokenizer gives about 430M
  rendered Gemma4-chat tokens for the full 1,001,551-row dataset. A head-only
  20k-row sample estimated about 412M tokens but was source-order biased
  toward `airoboros2.2`.

DFM8 handling:

1. OpenHermes should be included in DFM8 as an English
   SFT/format-following/code/MCQ/direct-answer source, with an initial planning
   size of roughly 430M tokens if used whole once.
2. It should still not be used as a blind bulk replacement for our English SFT.
3. Build a source/category audit first:
   - count rows/tokens by `source` and `category`;
   - inspect examples from every source/category;
   - classify whether each source overlaps with data already present in
     DFM5/DFM6/DFM7.
4. Candidate rows to keep, subject to audit:
   - strict format-following examples;
   - concise answer-only MCQ rows;
   - code instruction rows, especially if they use clean final code blocks;
   - math/reasoning rows only if their final-answer contract can be rewritten
     or tagged consistently;
   - general assistant rows that demonstrate direct no-thinking answers.
5. Candidate rows to exclude or cap tightly:
   - roleplay/stylized celebrity/IP imitation rows;
   - medical advice rows unless explicitly wanted and separately risk-tagged;
   - mixed-format math rows that conflict with the DFM8 boxed-answer contract;
   - rows with `skip_prompt_formatting=true` until rendered output is audited.
6. Convert retained rows through the Gemma4 native chat template and tag them
   as `openhermes_format_following`, `openhermes_code`,
   `openhermes_mcq`, `openhermes_direct_answer`, or
   `openhermes_mixed_reviewed`.
7. Add a small OpenHermes-derived smoke/eval slice for exact-format following
   before giving this source meaningful sampling weight.

Implementation clarification, 2026-07-11. Confidence: high from
`scripts/convert_dfm8_openhermes.py` and local converted rows. The OpenHermes
converter normalizes ShareGPT roles (`human`/`gpt`/`system`) into canonical
Gemma4-style `user`/`assistant`/`system` message rows, and DFM8 tokenization
renders those rows with `data_io/chat_templates/gemma4_native_chat.jinja`.
It does not rewrite the assistant text itself into stricter DFM8 answer
contracts. Therefore OpenHermes is Gemma4-native at the chat-template/wrapper
level, while preserving OpenHermes response style/content.

Sampling decision, 2026-07-11. Confidence: medium. Keep OpenHermes at
`repeat: 1` in `data_io/prefix_config_dfm8.yaml`. Raising it to `repeat: 2`
would only add about 0.39B source tokens, but it would also double the weight
of OpenHermes response style. If more OpenHermes-like breadth is wanted, prefer
a Danish-native translated/rewrite derivative with category-specific audits
over simply repeating the English source.

Candidate Danish OpenHermes derivative. Confidence: low-to-medium estimate
from local row/token counts and observed Gemma 4 31B c128 pipeline throughput.
OpenHermes currently has 1,001,551 converted rows and about 391.5M rendered
Gemma4 tokens. A Danish derivative is feasible but should be treated as a
medium-complexity synthetic-data project, not a blind translation:

- Translate/rewrite `user`, `assistant`, and optional `system` turns into
  idiomatic Danish while preserving roles and conversation structure.
- Use category-specific prompts for MCQ, code, math/reasoning, direct-answer,
  and general chat rows.
- Preserve code, identifiers, formulas, option labels, JSON, and exact-format
  contracts unless the row explicitly asks for translation.
- For math rows, optionally rewrite the assistant target to the DFM8 boxed
  final-answer contract instead of preserving OpenHermes style.
- Validate JSON/schema, Danish-language coverage, MCQ option consistency,
  code-block preservation, and answer-contract compliance; regenerate failures.

On the current 8-GPU Gemma 4 31B setup, observed targeted-synthetic throughput
with c128 was roughly 14 shards/hour, with shards around 9k-10k requests. For
about 1M OpenHermes rows this implies about 8 hours per single generation-like
pass at optimistic throughput. A generation plus full judge/audit pass is more
realistically **15-25 hours**, and **1-2 days wall clock** after retries,
recovery, upload packaging, and tokenization. Implementation work for a clean
converter/generator/auditor is about **0.5-1 engineering day** if reusing the
DFM8 synthetic pipeline patterns.

Preparation status, 2026-07-11. Confidence: high from local commands. The
Danish OpenHermes derivative has been scaffolded separately from the active
`dfm8-synthetic-*` generation so it will not disturb the current run:

- package: `dfm8_openhermes_da/`
- CLI: `python -m dfm8_openhermes_da.cli`
- guarded runner: `dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh`
- working root: `data/dfm8_openhermes_da_synthetic`
- upload root: `export-upload-dfm8-openhermes-da`
- default runner ports: `8600-8607`, not the active `8500-8507`
- default safety guard: refuses to start if active
  `dfm8_synthetic.cli generate|audit` or
  `run_dfm8_targeted_synthetic_8gpu.sh` processes are detected.

Offline request preparation was completed without touching GPUs/vLLM:

```bash
PYTHONPATH=/work/dfm/HRM-Text/dfm8_openhermes_da \
python -m dfm8_openhermes_da.cli make-requests \
  --input-root data/dfm8_special_sources/openhermes_2_5 \
  --root data/dfm8_openhermes_da_synthetic \
  --force

PYTHONPATH=/work/dfm/HRM-Text/dfm8_openhermes_da \
python -m dfm8_openhermes_da.cli shard-requests \
  --root data/dfm8_openhermes_da_synthetic \
  --shards 512 \
  --force
```

Prepared request counts:

| Artifact | Count/size |
| --- | ---: |
| OpenHermes rows converted to Danish rewrite requests | 1,001,551 |
| Request shards | 512 |
| Rows per shard | min 1,827 / max 2,099 / avg 1,956 |
| Prepared request/shard tree size | about 9.4G |

The generation prompt asks Gemma 4 31B to rewrite/translate natural-language
content into idiomatic Danish while preserving roles, turn order, facts, MCQ
labels, code blocks, commands, paths, URLs, formulas, exact JSON/XML/table
syntax, and other structural constraints. Math/reasoning rows are instructed
to end with exactly one final `\boxed{...}` answer when there is a determinate
final answer. The audit prompt checks Danishness, structure preservation,
meaning preservation, answer correctness, and format preservation, plus
deterministic checks for roles, MCQ labels, code fences, and boxed math signal.

When the current `dfm8-synthetic-*` run is finished and GPUs are free, the
prepared command is:

```bash
CONCURRENCY=128 \
GPU_MEMORY_UTILIZATION=0.7 \
MAX_NUM_SEQS=128 \
bash dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh
```

Do not set `ALLOW_ACTIVE_DFM8_SYNTHETIC=1` unless intentionally overriding the
safety guard after stopping or completing the active DFM8 synthetic generation.

Pre-training gate, 2026-07-11. Confidence: high. Before any DFM8 training
restart, run this Danish OpenHermes generation/audit, inspect the accepted
rows, integrate the accepted upload folder into the DFM8 chat-source/tokenized
tree, and resample `data/sampled_dfm8`. The prepared request shards alone are
not enough; training should not resume from a DFM8 sample that lacks the
accepted Danish OpenHermes derivative.

Superseded W&B preparation for DFM8-XL continuation, 2026-07-11. Confidence: high from
local script output and W&B API verification. A new W&B run has been prepared
in project `DFM5`:

```text
run id: dfm8-xl-from-dfm6-dfm7-epoch5
name:   DFM8-XL from DFM6-DFM7 epoch5
url:    https://wandb.ai/peter-sk-sdu/DFM5/runs/dfm8-xl-from-dfm6-dfm7-epoch5
```

It was created by `scripts/backfill_dfm8_xl_from_dfm6_dfm7_wandb.py`, cloning
numeric history from `DFM5/dfm6-dfm7-xl-gas2`. The run config points future
training at `data/sampled_dfm8`, writes checkpoints under
`checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5`, and resumes from
`checkpoints/dfm7/XL-gas2-from-dfm6-epoch3` with `resume_checkpoint_tag=epoch_5`.
The local epoch-5 sidecar records `step=1229504`, but the cloned W&B history
currently has usable rows through step `1200000`; this is a display/history
caveat, not a checkpoint-resume caveat.

Superseded/repair, 2026-07-11. Confidence: high from W&B API verification. The
first clone missed sparse late training rows. A follow-up one-metric-at-a-time
tail repair appended 653 train rows covering steps `1200045..1229485`.
The prepared DFM8-XL run now verifies with `_step=1229485`,
`train/step=1229485`, and normal train metrics through the end of the source
training curve. The local `epoch_5` checkpoint sidecar remains the resume
authority at step `1229504`.

Failure note, 2026-07-11. Confidence: high. The prepared W&B run above was
deleted by the user after inspection because the history was misleading: the
initial backfill missed sparse late rows, and the incremental repair produced
a visually wrong final training segment. Do not recreate DFM8-XL W&B state
with `scripts/backfill_dfm8_xl_from_dfm6_dfm7_wandb.py`; the script is now
deprecated and guarded. Any future DFM8 W&B preparation should be rebuilt from
deterministic local scheduler/eval artifacts and separately validated before
syncing.

## Math Answer-Contract Fix

Current DFM7 state, verified 2026-07-02:

- Corrected `allenai_rlvr_gsm` and `allenai_rlvr_math` rows teach boxed answers,
  but they contribute only about 6.76M target tokens over 5 epochs.
- Large inherited math-ish sources dominate the target-token budget:
  `openmathinstruct2 + dmmath + ampsmathematica + flan` contribute about
  46.40B target tokens over 5 epochs, roughly 6,861x the boxed RLVR target
  weight.
- Source-row audit showed:
  - `openmathinstruct2__cot` often contains `\boxed{...}` but rarely ends with
    a boxed answer.
  - `openmathinstruct2__direct` and `dmmath` mostly teach bare direct answers.
  - `ampsmathematica` teaches `$...$` LaTeX answers.
  - FLAN GSM8K-style rows teach prose answers such as `The answer: 24.`

Therefore, simply training longer on the current DFM7 mix should not be
expected to reliably fix freeform math formatting.

DFM8 remediation plan:

1. Build DFM8-specific math converters instead of reusing inherited math rows
   verbatim.
2. For freeform direct math rows, convert targets to exactly
   `\boxed{answer}` whenever the answer can be parsed safely.
3. For freeform CoT rows, preserve reasoning but rewrite/append the final line
   to exactly one `\boxed{answer}` when the final answer can be extracted.
4. For sources where answer extraction is unreliable, either exclude them from
   the strict math-contract slice or keep them in a separately capped
   "math reasoning, mixed format" bucket.
5. Keep MCQ math separate. MCQ prompts should request exactly one option
   letter and should not be mixed with freeform boxed-answer rows.
6. Keep raw/prose answer formats only if deliberately sampled as auxiliary
   diversity, and cap them below the strict boxed-contract slice.

Suggested source-specific handling:

| Source | DFM8 action |
| --- | --- |
| `allenai_rlvr_gsm`, `allenai_rlvr_math` | Keep; increase weight substantially. Fix nested-LaTeX boxed detection in audits so matrix/vector answers are not miscounted. |
| `openmathinstruct2__direct` | Convert bare answers to exact boxed direct answers. |
| `openmathinstruct2__cot` | Extract final answer and enforce final line `\boxed{...}`; exclude or cap rows where extraction fails. |
| `dmmath` | Convert direct bare numeric/algebraic answers to boxed answers, or cap if too synthetic/direct-heavy. |
| `ampsmathematica` | Convert `$...$` targets to `\boxed{...}` where safe; keep `$...$` only inside boxed content. |
| FLAN GSM8K/math rows | Convert prose final-answer rows to boxed answers only when extraction is robust; otherwise cap tightly. |
| `kaenguruen` and other MCQ math | Keep as MCQ letter-answer data only. |

Sampling policy:

- The strict boxed-freeform math bucket should have enough target-token weight
  to dominate freeform math answer style. As a starting point, target at least
  low single-digit billions of boxed math target tokens per epoch, not millions.
- Mixed-format math rows should be capped below the strict boxed bucket until
  smoke tests show the model reliably ends freeform math with one boxed answer.
- Track `strict_boxed_math`, `mixed_math_reasoning`, and `math_mcq` as separate
  analytics categories.

Validation gates before sampling:

1. Run a source-row audit over every math source and report:
   `contains_boxed`, `ends_boxed`, `exact_boxed`, `bare_numeric`,
   `$...$-wrapped`, prose-final-answer, and extraction-failure rates.
2. Fail the build if strict boxed sources have less than a chosen threshold of
   exact or ends-boxed rows.
3. Sample rendered examples after Gemma4 chat-template tokenization and verify
   that the visible prompt contract and assistant target match.
4. Run smoke generations on early checkpoints for GSM-style, MATH-style, and
   MCQ math separately.

Refinement, 2026-07-09. Confidence: medium from local eval behavior and
epoch_5 smoke generations.

Tracking different math types should mean two things, not only new evals:

1. Training-data analytics: every math row should be tagged into at least
   `strict_boxed_freeform`, `mixed_format_freeform`, `gsm_style_numeric`,
   `mcq_letter`, `proof_or_explanation`, and `code_or_symbolic_math`.
   Sampling analytics should report target-token counts by these tags.
2. Diagnostic eval slices: keep the headline `MATH`, `GSM8K`, and MMLU results,
   but add small controlled eval suites that separately test:
   - GSM-style arithmetic with required bare numeric and boxed variants.
   - MATH-style freeform with required final `\boxed{...}`.
   - MCQ math with one-letter answer contract.
   - Format-only scoring: correct answer but wrong final format, no final
     answer, multiple boxed answers, and answer after token cap.

These diagnostic evals are not meant to replace the headline benchmark numbers.
They should explain why a checkpoint loses points: capability, answer contract,
reasoning-length cutoff, or extraction/scoring failure.

DFM6-DFM7 epoch_5 smoke evidence:

- The final `epoch_5` HF export solved two easy math prompts correctly in
  content, but ignored an explicit instruction to finish with exactly one
  `\boxed{...}` answer.
- This supports the hypothesis that the current mix has a format-contract
  problem. It does not by itself rule out reasoning-length limits on harder
  MATH items.

MATH regression investigation plan:

- Compare old Sapient/original and DFM5 generations against DFM7 on a shared
  fixed sample of MATH rows, storing full generations and classifying failures
  as `wrong reasoning`, `right answer wrong format`, `no boxed final`,
  `multiple boxed answers`, `truncated`, or `extractor mismatch`.
- Check prompt/template differences: original HRM condition-token evals versus
  Gemma4 chat-template evals can change whether the model starts a reasoning
  trace, a direct answer, or a final boxed line.
- Check generation limits: if DFM7 gives long unfinished traces while earlier
  models were shorter/directer, MATH can fall even when underlying reasoning is
  not worse.
- Check data mix: DFM7 inherited far more mixed-format math than strict boxed
  math, so answer-style drift is a plausible primary cause until the fixed
  sample says otherwise.

## Danish DAISY Eval Candidate

Update, 2026-07-09. Confidence: medium from the Hugging Face dataset card.

Add `schneiderkamplab/SDU-Daisy` as a DFM8 evaluation candidate, not a training
source by default. The dataset card describes SDU DAISY as a Danish cultural
benchmark over the official Danish Culture Canon, with QA/text-generation
tasks, parquet format, Danish language, MIT license, and 592 train examples.
It is small enough to run as a full diagnostic eval.

Integration plan:

1. Download and inspect schema locally. The card lists columns `id`,
   `Question`, `Answer`, and `Subject`.
2. Implement a DFM eval suite that prompts in Danish and scores exact-ish/F1
   overlap plus optional judge-based cultural relevance/accuracy if needed.
3. Keep it out of DFM8 training unless we deliberately mark the eval as
   contaminated/non-held-out.
4. Report it under Danish/culture, not general Danish language quality.

## Tool-Calling Carryover

Carry over the DFM7 native tool-use rebuild:

- Keep corrected `dolci_native_tool_use`.
- Keep `glaive_native_tool_use`, `toolace_native_tool_use`, and
  `xlam_native_tool_use`.
- Keep malformed original DOLCI tool-use rows capped to zero unless they have
  been converted.
- Keep `when2call` as auxiliary no-call/when-to-call data only unless converted
  to top-level `tools` plus assistant `tool_calls`.

DFM8 should add an explicit BFCL-shaped native tool-call SFT bucket with:

- exact function selection,
- exact argument formation,
- no-tool cases,
- multi-tool cases,
- and a failure-bucket smoke script for `no tool call`, `malformed`,
  `wrong function`, `wrong arguments`, and `correct`.

Refinement, 2026-07-09. Confidence: medium from DFM6-to-DFM7 eval trend and
epoch_5 smoke generations.

The DFM6-to-DFM7 switch improved tool calling temporarily but did not stabilize
it. The final epoch_5 smoke test shows partial native syntax learning:

- With a `get_weather` tool, the model emitted `call:get_weather{...}`, but
  repeated/malformed the call instead of emitting one clean call.
- With a `search_web` tool available for a greeting that needed no tool, the
  model avoided the tool but incorrectly refused the simple greeting because it
  over-focused on tool availability.

DFM8 tool-call fixes should therefore go beyond adding more rows:

1. Audit every tool-call source after rendering through the Gemma4 template.
   Check for exactly one assistant target per example, valid top-level `tools`,
   valid assistant `tool_calls`, no XML leftovers, no Python-call string
   targets, and no repeated calls unless the row genuinely requires multiple
   calls.
2. Build explicit no-tool examples where tools are present but the correct
   answer is ordinary text. These should be sampled strongly enough to prevent
   "tool availability means I must call or refuse" behavior.
3. Add malformed-output prevention rows: one clean function call, exact JSON-ish
   arguments, stop after the call, and no repeated call loops.
4. Add held-out smoke/eval buckets for `must_call`, `must_not_call`,
   `multi_call`, `wrong_tool_available`, and `tool_response_followup`.
5. Inspect whether Nemotron Agentic, Glaive, ToolACE, XLAM, and corrected DOLCI
   all use the same canonical final assistant representation after conversion.
   If not, normalize or split/cap the inconsistent buckets.

## Epoch 5 Qualitative Smoke

Update, 2026-07-09. Confidence: high for local prompt/output capture; medium
for qualitative interpretation.

Final DFM6-to-DFM7 `epoch_5` HF export:

```text
exports/dfm6_dfm7_XL_gas2_epoch_5_ema_hf_hrmenv_202253
```

was loaded through vLLM as `HrmTextForCausalLM` with the Gemma4 native chat
template, `enable_thinking=false`, temperature `0.0`, and FlashAttention 4.

Reusable script and report:

```text
scripts/smoke_dfm6_dfm7_epoch5_qualitative.py
docs/dfm6-dfm7-epoch5-smoke.md
logs/analysis/dfm6_dfm7_epoch5_smoke/generations.jsonl
docs/dfm6-dfm7-epoch5-extended-smoke.md
logs/analysis/dfm6_dfm7_epoch5_extended_smoke/generations.jsonl
```

Observed in the smoke set:

- Basic Danish explanatory chat worked.
- Simple Python code generation worked.
- Multi-turn memory worked for a short three-turn prompt.
- English and Danish summarization were grounded and followed one-/two-sentence
  requests in the tested examples; a requested 4-5 bullet summary instead came
  back as prose, so formatting compliance still needs work.
- Creative freeform generation was coherent but generic in English and better
  in Danish.
- Freeform math gave correct easy answers but did not emit final boxed answers.
- Tool calling showed native-looking syntax but repeated/malformed a call and
  mishandled a no-tool-needed greeting.
- Commonsense was weak in two tested cases: one leaked into `<think>` and did
  not answer; one gave implausible explanations for a wet sidewalk.

Next smoke battery, 2026-07-09. Confidence: medium from the first qualitative
smoke results.

The first smoke was useful but too small. Before finalizing DFM8 sampling,
run a broader targeted smoke battery on `epoch_5`, DFM5/DFM6 reference
checkpoints, and early DFM8 checkpoints:

1. Math contract:
   - easy GSM-style arithmetic with bare-answer, boxed-answer, and "show work"
     prompts;
   - MATH-style algebra/geometry where the final answer must be one
     `\boxed{...}`;
   - long reasoning prompts near the token limit to detect truncation;
   - MCQ math with "answer only A/B/C/D".
2. Tool calling:
   - one required call, no tool needed, wrong tool available, multi-call,
     call-then-use-tool-response, Danish tool prompts, and malformed/repeated
     call detection.
3. Thinking leakage:
   - direct commonsense, direct QA, and direct MCQ prompts with
     `enable_thinking=false`; flag any visible `<think>` as a contract failure.
4. Format following:
   - exact one sentence, exactly two sentences, 4-5 bullet points, JSON-only,
     table-only, and "do not add explanation".
5. Danish practical competence:
   - everyday Danish instructions, rewriting tone/register, spelling/grammar
     correction, and Danish cultural QA including SDU-Daisy-style questions.
6. Coding:
   - one simple function, one debugging task, one small algorithm, one code
     explanation, and one "do not execute, only explain" task.
7. Conversation:
   - five-to-eight turn memory, user correction, refusal-to-tool when no tool
     is needed, and language-switching between Danish and English.
8. Commonsense:
   - short causal prompts where the expected answer is obvious, plus
     multi-cause prompts where the model must not collapse to one cause.

DFM8 implications from the first smoke:

- Add explicit direct-answer/no-thinking SFT rows. The model can leak `<think>`
  even when the Gemma4 template disables thinking, so DFM8 should include
  direct-mode examples that answer plainly without a hidden/reasoning trace.
- Add strong format-following SFT rows for summaries, bullets, JSON, tables,
  exact sentence counts, final-answer-only, and one-boxed-answer math.
- Treat no-tool-needed examples as first-class tool training, not as incidental
  negatives. The model should learn that tools being available does not make a
  simple text answer impossible.
- Add repeated-tool-call loop checks to conversion audits and evals. A row that
  teaches or permits repeated identical calls should be excluded or capped.
- Add Danish commonsense/practical QA rows, not only cultural or encyclopedic
  Danish rows. The wet-sidewalk failure suggests a gap in ordinary causal
  reasoning or direct commonsense answer style.

Extended bilingual smoke, 2026-07-09. Confidence: high for local prompt/output
capture; medium for qualitative scoring heuristics.

The extended smoke is a strict superset of the initial smoke and contains 40
cases: 19 English, 20 Danish, and one bilingual language-switch case. It covers
chat, math, code, conversation, summarization, creative writing, format
following, tool calling, commonsense, and practical rewriting/correction.

Summary from `docs/dfm6-dfm7-epoch5-extended-smoke.md`:

```text
English: 12 pass, 6 weak, 1 bad
Danish:  18 pass, 2 weak, 0 bad
Both:     1 pass
```

Category summary:

```text
chat          2 pass
code          4 pass
conversation  3 pass
creative      2 pass
summarization 5 pass
format        3 pass, 1 weak
math          4 pass, 2 weak
practical     3 pass, 1 weak
tool_calling  3 pass, 3 weak
commonsense   2 pass, 1 weak, 1 bad
```

Notable asymmetries:

- Danish math followed the explicit boxed-answer instruction on two easy
  freeform prompts; English solved the content but omitted the boxed final
  answer. This suggests the format issue is prompt/language/style sensitive,
  not a uniform inability.
- Danish commonsense passed both smoke prompts; English leaked `<think>` on one
  prompt and gave implausible wet-sidewalk causes on another. DFM8 should not
  assume English common-sense/direct-answer behavior is already fixed by
  general English data.
- Danish JSON-only output failed by returning only `{`; English JSON-only
  passed. Structured-output formatting needs bilingual coverage.
- Tool calling remains weak in both languages for required calls: the model
  emits native-looking calls but repeats or malforms them. Danish no-tool-needed
  passed, while English no-tool-needed refused a simple greeting because a web
  search tool was present.
- English spelling/grammar correction leaked into a reasoning trace and did not
  provide the clean corrected sentence. Danish correction passed after heuristic
  correction.

DFM8 implications from the extended smoke:

1. Add bilingual direct-mode/no-thinking data, with English emphasized because
   the English smoke failures show more visible thinking leakage.
2. Add bilingual strict-format data for JSON-only, tables-only, exact sentence
   counts, bullet-only summaries, answer-only MCQ, and boxed math. Do not rely
   on one language transferring these contracts to the other.
3. Add bilingual spelling/grammar correction and practical rewriting data with
   targets that are clean final answers only.
4. Treat tool calling as a separate stabilized curriculum:
   - clean one-call examples,
   - no-tool-needed examples,
   - wrong-tool-available examples,
   - tool-response follow-up,
   - repeated-call loop negatives,
   - Danish and English variants.
5. Build small diagnostic evals from the smoke templates so early DFM8
   checkpoints can be checked before full benchmark runs.

## Broad Synthetic Common Pile and DynaWord Scaling

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

## Build Requirements

- Use the Gemma4 tokenizer and `data_io/chat_templates/gemma4_native_chat.jinja`
  throughout.
- Keep DFM8 in separate paths, for example `data/tokenized_dfm8`,
  `data/sampled_dfm8`, and `config/data/dfm8.yaml`.
- Do not call trained-on benchmark splits held out. If a benchmark-like source
  is used for training, as planned for full TV2R instruction inclusion, mark
  corresponding eval scores as non-held-out/train-contaminated and add a clean
  replacement diagnostic if needed.
- Add analytics tables comparing DFM7 vs DFM8 by Danish, English,
  math/tool/code, strict boxed math, mixed math, MCQ math, and native tool-use
  buckets.

## Additional Synthetic Data Candidates

Update, 2026-07-09. Confidence: medium. These are candidate synthetic slices
to consider after the current DFM8 transform audit finishes. They should be
generated from broad source pools, audited by a strong judge, and tagged so we
can cap or ablate them. Do not seed them from evaluation rows or near-duplicate
benchmark examples.

Highest-priority synthetic additions:

1. Strict math answer-contract data.
   - Generate Danish and English freeform math solutions with a consistent
     contract: concise reasoning, then exactly one final `\boxed{...}` answer.
   - Include variants for arithmetic word problems, algebra, geometry,
     counting/probability, and unit conversions.
   - Add explicit direct-vs-CoT prompt variants so the model learns when to
     give only the final answer and when to show reasoning.
2. Native tool-calling data.
   - Generate and validate Gemma4/OpenAI-style tool-use conversations with
     `tools` definitions and assistant `tool_calls`, not XML or Python-call
     strings.
   - Cover single-call, multi-call, no-call/when-not-to-call, argument repair,
     tool-result summarization, and Danish user prompts with English tool
     schemas.
3. Format-following and constrained-output data.
   - Generate tasks requiring exact JSON, CSV/table rows, bullet counts,
     one-sentence/two-sentence answers, and strict answer labels.
   - Include adversarial prompts where the user asks for a format and provides
     distracting prose, because previous smoke tests showed format fragility.
4. Danish summarization and rewriting controls.
   - Generate Danish text-to-summary pairs with explicit requested lengths:
     headline, one sentence, two sentences, short abstract, longer executive
     summary.
   - Include rewrites for tense, tone, simplification, school level, and
     preservation of named entities.
5. Multi-turn Danish and English instruction/chat.
   - Generate 2-6 turn conversations with follow-up references, corrections,
     topic shifts, and "you misunderstood" recovery.
   - Include ordinary user-support style prompts and school/educational
     tutoring prompts.
6. Code generation and debugging.
   - Generate small Python/TypeScript tasks with tests, bug-fix prompts, code
     explanation, and Danish natural-language instructions.
   - Prefer executable/self-checkable tasks where we can run tests or at least
     static checks before inclusion.

Lower-priority or cap-tightly:

- More continuation-style data. DFM8 already has DynaWord/Common-Pile-derived
  transformation data and capped Common-Pile prefix continuation; add more only
  if the audit shows high quality and the final mix lacks raw-ish language
  modeling mass.
- Synthetic benchmark clones. Avoid examples that look like MMLU, GSM8K,
  MATH, HumanEval, EuroEval, or DFM eval held-out rows unless they are clearly
  from independent source distributions and tracked as train-contaminating
  diagnostics.

Recommended generation workflow:

1. Sample source documents/prompts broadly from DynaWord and allowed
   Common-Pile-derived sources, not just early files.
2. Use Gemma4 31B or a stronger available teacher to generate candidates with
   explicit task-family prompts.
3. Run deterministic validators where possible: JSON parsing, tool-call schema
   validation, exact boxed-answer checks, code tests.
4. Run a judge audit for semantic quality, especially for Danish fluency and
   whether the response satisfies the requested format.
5. Keep accepted rows in separate source-family directories and add them to
   `data_io/prefix_config_dfm8.yaml` with conservative caps/repeats.

Suggested accepted-row targets for a first DFM8 synthetic pass:

| Slice | Accepted rows | Approx raw rendered tokens | Notes |
| --- | ---: | ---: | --- |
| Strict math answer-contract | 1.0M-1.5M | 1.0B-2.0B | Split by arithmetic, algebra, geometry, probability/counting, units, direct vs CoT. |
| Native tool calling | 500k-800k | 0.7B-1.5B | Include no-call, single-call, multi-call, argument repair, tool-result summarization, Danish prompts. |
| Constrained format-following | 700k-1.0M | 0.4B-0.9B | JSON/table/bullets/labels/sentence-count tasks; deterministic validators should reject malformed targets. |
| Danish summarization/rewrite controls | 500k-800k | 0.8B-1.8B | Headline, one-sentence, two-sentence, brief, long, tone/tense/level rewrites. |
| Multi-turn Danish/English chat | 300k-600k conversations | 0.7B-1.6B | 2-6 turns, follow-ups, corrections, tutoring, reference resolution. |
| Code/debugging | 300k-600k | 0.5B-1.2B | Small executable tasks, bug fixes, explanations, Danish code prompts. |

Total first-pass target: roughly 3.3M-5.3M accepted rows and 4.1B-9.0B raw
rendered tokens. For a DFM8-size epoch, this should be treated as a focused
behavioral-contract slice, not the majority of training. A reasonable initial
sampling target is about 7B-12B sampled tokens per epoch across these six
slices, with higher repeat/cap priority for strict math and native tool calling
than for generic multi-turn chat.

Generate more candidates than the accepted target because the judge and
deterministic validators should reject malformed rows. A practical starting
oversampling factor is 1.3x for format/code/math rows with deterministic
validators, and 1.5x-2.0x for tool-calling and summarization/rewrite rows where
semantic quality and schema matching are more fragile.

Implementation update, 2026-07-09. Confidence: high for local syntax checks and
request-generation smoke test; medium until the full generation/audit campaign
finishes.

The DFM8 targeted synthetic generation scaffold lives under
`dfm8_synthetic/`. It implements six uploadable dataset families:

- `strict_math_answer_contract`
- `native_tool_calling`
- `constrained_format_following`
- `danish_summarization_rewrite_controls`
- `multiturn_danish_english_chat`
- `code_debugging`

Important implementation choices:

- Gemma 4 31B is the default generator and judge model
  (`posttrain-gemma-teacher`).
- Generation and audit use different prompts.
- Lower-bound declared targets generate candidates using the accepted-row
  lower bound multiplied by each slice's overgeneration factor.
- Sharded request, generation, and audit files are used; no concurrent gzip
  appends.
- Stable `request_id`s make generation and audit resumable.
- Audit keeps a row only when all main judge booleans are true and deterministic
  family checks pass.
- Upload folders contain gzip JSONL shards, `README.md`, `manifest.json`, and
  a self-contained `recreate_dataset.py`.
- Variation controls are explicit: every family cycles through a fixed set of
  task variants, and the runner can pass broad seed globs. Seed text is only
  injected into families where source grounding is useful
  (`danish_summarization_rewrite_controls`,
  `multiturn_danish_english_chat`, and `constrained_format_following`), not
  into math/tool/code prompts where arbitrary source snippets would reduce
  relevance.

Commands that passed locally:

```bash
PYTHONPATH=/work/dfm/HRM-Text/dfm8_synthetic \
  python -m py_compile dfm8_synthetic/dfm8_synthetic/*.py

PYTHONPATH=/work/dfm/HRM-Text/dfm8_synthetic \
  python -m dfm8_synthetic.cli make-requests \
    --root tmp/dfm8_synthetic_smoke_requests \
    --rows-per-family 6

PYTHONPATH=/work/dfm/HRM-Text/dfm8_synthetic \
  python -m dfm8_synthetic.cli shard-requests \
    --root tmp/dfm8_synthetic_smoke_requests \
    --shards 4 \
    --force
```

The watcher/runner is:

```bash
bash scripts/watch_dfm8_transform_audit_then_targeted_synthetic.sh
```

It waits for the active DFM8 transform audit queue to finish without failures,
then starts `dfm8_synthetic/scripts/run_dfm8_targeted_synthetic_8gpu.sh` with
`CONCURRENCY=64`, `MAX_NUM_SEQS=64`, and `TARGET_BOUND=min`. The runner starts
or reuses one Gemma 4 31B vLLM server per GPU on ports 8500-8507 and then runs
generation, audit, and upload-folder construction.

Upload note: the previous export upload did happen. `wiki/pages/data-mix-policy.md`
records that `export-upload/` mapped to 82 public HF dataset repositories under
`schneiderkamplab`, including 12 previously uploaded post-training/transform
datasets. Local log `logs/hf_export_upload_all_82_20260617.log` contains
successful `DONE` commit URLs for the four `transformations-*` datasets and
the other uploaded export datasets.

## Active Post-Audit Operational Plan

Update, 2026-07-09. Confidence: high for local script paths and active tmux
watcher; medium for exact runtime until the remaining audit and generation jobs
finish.

Status update, 2026-07-09 21:46 Europe/Berlin. Confidence: high from local
logs and process inspection. The transform-expansion audit completed cleanly:
`done=176`, `running=0`, `pending=0`, `failed=0` in
`logs/dfm8_transform_expansion_dynamic_audits_c64_u070_20260709T110453`. The
watcher then launched targeted synthetic generation/audit at
`logs/dfm8_targeted_synthetic_20260709T214629`. The runner starts one Gemma 4
31B vLLM server per GPU sequentially and waits for server health before moving
to the next GPU; GPU0 became healthy on port `8500`, and GPU1 started loading on
port `8501`.

Status update, 2026-07-09 after transform filtering. Confidence: high from
local command output. The transform-expansion filter must use the union of all
known audit roots (`audit_full`, `audit_shards`, `audit_shards_c64`,
`audit_shards_c64_u070`) because the final dynamic pass used earlier roots as
skip lists. Using only `audit_shards_c64_u070` under-keeps by about 79k accepted
rows. `scripts/filter_dfm8_transform_expansion_audits.py` was updated to pass
the full nonempty audit union to the per-dataset recreate scripts. The corrected
filtered output is:

| Family | Seen rows | Kept rows | Dropped rows | Audit files |
| --- | ---: | ---: | ---: | ---: |
| `common-pile-denoising` | 636,413 | 580,434 | 55,979 | 49 |
| `common-pile-paragraph-reordering` | 85,029 | 43,821 | 41,208 | 9 |
| `common-pile-prefix-continuation` | 774,936 | 703,658 | 71,278 | 65 |
| `common-pile-span-filling` | 634,288 | 572,098 | 62,190 | 33 |
| `danish-dynaword-denoising` | 150,773 | 137,520 | 13,253 | 9 |
| `danish-dynaword-paragraph-reordering` | 69,707 | 34,931 | 34,776 | 9 |
| `danish-dynaword-prefix-continuation` | 234,008 | 201,507 | 32,501 | 17 |
| `danish-dynaword-span-filling` | 134,580 | 124,414 | 10,166 | 9 |
| **Total** | **2,719,734** | **2,398,383** | **321,351** | **200** |

The transform expansion was then linked into `data/dfm8_chat_sources`,
tokenized with the Gemma4 tokenizer/template into `data/tokenized_dfm8_jinja`,
and included in `data/tokenized_dfm8`. Tokenization command used:

```bash
cd /work/dfm/HRM-Text
TOKENIZERS_PARALLELISM=false python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir data/tokenized_dfm8_jinja \
  --workers 16 \
  --skip-bad-json
```

The tokenizer scanned 3,975 files and produced 2,398,383 newly processed rows
with zero skipped bad rows in 173.6 seconds. `data/tokenized_dfm8` currently
contains 137,154,725,776 tokens across 10,669 task directories. The category
report is in `data/show_tokenized_dfm8.json` and `data/show_tokenized_dfm8.md`.
Do not treat this as final DFM8 sampling input until the targeted synthetic
generation/audit output has been repaired or intentionally excluded.

Synthetic-run note, 2026-07-09. Confidence: medium from local process and queue
state. `logs/dfm8_targeted_synthetic_20260709T214629` reached the point where
all eight vLLM servers became healthy and 512 generate jobs were materialized,
but no worker logs were created and all 512 jobs remained in
`queue/generate_pending`. All vLLM servers shut down at 22:01:57, consistent
with the shell launcher exiting and triggering its cleanup trap before
`run_phase generate` successfully launched workers. The likely root cause was
`set -euo pipefail` combined with `find "$DATA_ROOT/generated" ...` before the
`generated` directory existed. The launcher now creates both
`$DATA_ROOT/generated` and `$DATA_ROOT/audits` before those `find` calls.
The fixed restart was launched in tmux window `hrm-0:dfm8-synth` with log root
`logs/dfm8_targeted_synthetic_fixed_20260709T223530`.

When the active DFM8 transform audit finishes, the operational sequence is:

1. Let the watcher observe transform-audit completion.
   - Active watcher: `hrm-0:dfm8-synth-watch`.
   - It waits for
     `logs/dfm8_transform_expansion_dynamic_audits_c64_u070_20260709T110453`
     to reach `pending=0`, `running=0`, `failed=0`.
   - If any audit jobs fail, it stops instead of launching downstream work.
2. Start targeted synthetic generation automatically.
   - Script:
     `dfm8_synthetic/scripts/run_dfm8_targeted_synthetic_8gpu.sh`.
   - Model: Gemma 4 31B served as `posttrain-gemma-teacher`.
   - Ports: `8500-8507`.
   - Settings: `CONCURRENCY=64`, `MAX_NUM_SEQS=64`, `TARGET_BOUND=min`.
   - Lower-bound generation target: 4.8M candidate rows across the six DFM8
     targeted synthetic families.
3. Filter accepted transform-expansion rows.

```bash
cd /work/dfm/HRM-Text
python scripts/filter_dfm8_transform_expansion_audits.py --force
```

4. Rebuild the DFM8 chat-source tree so it points at filtered transform rows.

```bash
python scripts/build_dfm8_chat_source_tree.py --force --new-only
```

5. Tokenize DFM8 additions with the Gemma4 tokenizer/template.

```bash
TOKENIZERS_PARALLELISM=false python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir data/tokenized_dfm8_jinja \
  --workers 16 \
  --skip-bad-json
```

6. Rebuild the DFM8 tokenized union, report token/category counts, and only
   then sample.

```bash
python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
python scripts/report_dfm8_mix.py
```

7. After targeted synthetic generation/audit finishes, build upload folders and
   integrate accepted synthetic rows into the same DFM8 tokenization/sampling
   flow.
   - Upload-ready root: `export-upload-dfm8-synthetic`.
   - Do not upload or sample synthetic rows until the audit/filter result has
     been inspected for row counts, rejection rates, and examples per family.
8. Resample `data/sampled_dfm8` only after the transform-expansion accepted
   rows and any accepted targeted synthetic rows are both represented in
   `data/tokenized_dfm8`.
9. Inspect final category/token counts before training. Required checks:
   - Danish vs English vs math/code/tool totals;
   - transform-expansion contribution after audit rejection;
   - SkoleGPT contribution;
   - OpenHermes and TV2R contribution;
   - targeted synthetic contribution by the six families;
   - no accidental dominance by continuation-like data.

## DFM8 Targeted Synthetic Upload

Update, 2026-07-11. Confidence: high from local upload command exit status,
`export-upload-dfm8-synthetic/build_summary.json`, and Hugging Face commit URLs
printed by the uploader.

The completed DFM8 targeted synthetic generation produced `4,800,000`
candidate rows. The audit wrote `4,580,233` decisions for generated rows that
passed the generator-side `ok` check. Of those audited decisions, `3,809,300`
had `keep=true` and `770,933` had `keep=false`. The upload builder emitted
only the `keep=true` rows across six standalone Hugging Face dataset repos
under `schneiderkamplab`.

The successful upload command was run from `/work/dfm/HRM-Text` with the token
provided only via the `HF_TOKEN` environment variable:

```bash
PYTHONPATH=/work/dfm/HRM-Text/dfm8_synthetic \
  python -m dfm8_synthetic.cli upload \
    --root export-upload-dfm8-synthetic \
    --org schneiderkamplab \
    --commit-message "Upload complete DFM8 targeted synthetic datasets"
```

Upload log:

```text
logs/hf_upload_dfm8_synthetic_20260711T191006.log
```

Uploaded repos and commits:

| Dataset | Accepted rows | Commit |
| --- | ---: | --- |
| `schneiderkamplab/dfm8-synthetic-code-debugging` | `340,711` | `87e99f9815c1c4b484fecb4485a24e5c18277b1b` |
| `schneiderkamplab/dfm8-synthetic-constrained-format-following` | `838,905` | `61850112550ef6631d04f89eb575b7bddc80cbd2` |
| `schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls` | `825,861` | `3b528aa7510d3a7a5fea22a2b33e89b1a1a0d09c` |
| `schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat` | `414,196` | `e345d051a5d8714975de3bb19b137e357d76d92c` |
| `schneiderkamplab/dfm8-synthetic-native-tool-calling` | `836,675` | `3c2d177835beb79749a45143fd250fcedad5a6c9` |
| `schneiderkamplab/dfm8-synthetic-strict-math-answer-contract` | `552,952` | `14ff86ffae606f6dee4e959d0a4fe2c5a3b5c1bd` |

Do not store Hugging Face tokens in repo files or wiki pages.

## Danish OpenHermes Synthetic Run

Update, 2026-07-11. Confidence: high from local process logs and vLLM server
logs.

The Danish OpenHermes derivative run was started automatically after the DFM8
targeted synthetic run completed:

- script: `dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh`
- data root: `data/dfm8_openhermes_da_synthetic`
- original log root: `logs/dfm8_openhermes_da_20260711T190448`
- ports: `8600-8607`
- model: Gemma 4 31B served as `posttrain-gemma-teacher`

The first launch used `CONCURRENCY=128` and `MAX_NUM_SEQS=128`. This caused
repeated shard-level `HTTP Error 400: Bad Request` failures during both
generation and audit. The vLLM logs showed `Running` near `128`, nonzero
`Waiting`, and KV cache usage around `99-100%` before the 400s, so the most
likely cause is overdriving each single-GPU vLLM server rather than bad source
rows. The client did not record the 400 response body, so the exact server-side
reason is not yet preserved.

Recovery action:

1. Stop only the DaOH launcher/workers and vLLM servers on ports `8600-8607`.
2. Remove incomplete generated shards and incomplete audit shards from
   `data/dfm8_openhermes_da_synthetic`.
3. Restart with lower concurrency:

```bash
CONCURRENCY=64 \
MAX_NUM_SEQS=64 \
GPU_MEMORY_UTILIZATION=0.7 \
LOG_ROOT=logs/dfm8_openhermes_da_c64_20260711T194953 \
DATA_ROOT=data/dfm8_openhermes_da_synthetic \
bash dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh
```

The c64 restart launched in tmux window `hrm-0:daoh-c64` and began processing
the recovered shards with 200 OK responses on all eight vLLM servers.

Superseded by later instrumentation: make `dfm8_openhermes_da.cli` record HTTP
error response bodies and treat per-row generation/audit HTTP failures as
row-level `ok=false` or `keep=false` records, instead of failing the whole
shard. This matches the more resilient behavior we want for large synthetic
runs.

Update, 2026-07-11. Confidence: high from local code inspection and live logs.
The DaOH CLI now records structured row-level chat-completion failures and
archives row-failure records on resume. `run_openhermes_da_8gpu.sh` now rebuilds
its generate/audit queue by checking shard completeness, line counts, and
`row_failure` markers. The current diagnostic restart is:

```bash
CONCURRENCY=32 \
MAX_NUM_SEQS=64 \
GPU_MEMORY_UTILIZATION=0.7 \
LOG_ROOT=logs/dfm8_openhermes_da_c32_rowfail_20260711T220450 \
DATA_ROOT=data/dfm8_openhermes_da_synthetic \
bash dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh
```

The live c32 run weakens the earlier "pure concurrency pressure" diagnosis.
Each vLLM server reports:

```text
Available KV cache memory: 63.29 GiB
GPU KV cache size: 75,278 tokens
Maximum concurrency for 8,192 tokens per request: 9.19x
max_model_len: 8192
max_num_seqs: 64
```

At c32 the servers typically show `Running: 31-32`, `Waiting: 0`, and only about
`23-45%` KV cache usage. Captured row-level HTTP 400 bodies show context-limit
errors, e.g. prompt `4097` input tokens plus requested `4096` output tokens
exceeds the `8192` token maximum. Therefore some DaOH failures are caused by
request length, not by KV-cache exhaustion. Future retries should either reduce
generation `max_tokens`, truncate/filter long OpenHermes prompts, or route long
rows through a separate lower-output-token path.

OpenHermes length distribution, 2026-07-11. Confidence: high from a full local
Gemma-tokenizer pass over all `1,001,551` DaOH request rows. The full summary is
stored in:

```text
logs/dfm8_openhermes_da_length_distribution_20260711.json
```

Prompt-token distribution after the Gemma chat template:

| Metric | Tokens |
| --- | ---: |
| mean | `674` |
| p50 | `613` |
| p75 | `790` |
| p90 | `992` |
| p95 | `1,196` |
| p99 | `1,874` |
| p99.5 | `2,334` |
| p99.9 | `3,427` |
| max | `8,315` |

Estimated generated Danish JSON size was approximated by tokenizing the
original message JSON plus the target metadata, which is reasonable for
English-to-Danish rewriting because English and Danish lengths are usually
similar. The estimated prompt plus output distribution:

| Metric | Tokens |
| --- | ---: |
| mean | `1,102` |
| p50 | `978` |
| p75 | `1,334` |
| p90 | `1,736` |
| p95 | `2,146` |
| p99 | `3,504` |
| p99.5 | `4,424` |
| p99.9 | `6,613` |
| max | `16,391` |

With the previous fixed `max_tokens=4096`, only `282` rows (`0.028%`) have
`prompt_tokens + 4096 > 8192`, but those rows deterministically trigger vLLM
HTTP 400 context errors. With a more realistic output-length estimate,
`218` rows (`0.022%`) exceed the context at 1.0x output length, `333`
(`0.033%`) at 1.1x, and `596` (`0.060%`) at 1.3x. Therefore DaOH should use
dynamic `max_tokens = min(default, 8192 - prompt_tokens - safety_margin)` or
skip/route the very long tail, rather than relying on a fixed 4096-token output
budget for every row.

Implemented dynamic token budgeting, 2026-07-11. Confidence: high from local
syntax checks, a local long-row budget test, and live restarted worker commands.
`dfm8_openhermes_da/dfm8_openhermes_da/cli.py` now supports
`--dynamic-max-tokens`, `--tokenizer-path`, `--max-model-len`,
`--context-safety-margin`, and `--min-dynamic-max-tokens` for both generation
and audit. It measures prompt tokens with the Gemma chat template, caps
`max_tokens` to fit inside context, records `generation_budget`/`audit_budget`
metadata, and emits row-level `*_context_budget` failures for rows that leave
too little usable output budget.

`dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh` now enables dynamic
budgeting by default with:

```text
DYNAMIC_MAX_TOKENS=1
CONTEXT_SAFETY_MARGIN=64
GENERATION_MAX_TOKENS=4096
GENERATION_MIN_DYNAMIC_MAX_TOKENS=512
AUDIT_MAX_TOKENS=768
AUDIT_MIN_DYNAMIC_MAX_TOKENS=128
```

The active DaOH restart after this change is:

```text
tmux window: hrm-0:daoh-dynamic
log root: logs/dfm8_openhermes_da_c32_dynamic_20260711T224032
```

Live worker commands include `--dynamic-max-tokens --max-model-len 8192
--context-safety-margin 64`. A checked long row with `4110` prompt tokens was
capped from `4096` to `4018` output tokens. During the first post-restart
verification window, the new server logs showed no fresh `400 Bad Request`
lines; remaining row failures were mostly teacher JSON parse failures.

DaOH retry diagnostics, 2026-07-12. Confidence: high from local queue and row
scans while the dynamic run was still in progress. The current dynamic run has
no shard-level failed jobs: `generate_failed=0` and `audit_failed=0`. Earlier
failed shards were converted into row-level failures, archived under
`data/dfm8_openhermes_da_synthetic/row_failures/`, and requeued/resumed. The
archive at inspection time contained `118` row failures: `83` generation parse
failures and `35` HTTP 400 context failures from the pre-dynamic run.

At the same inspection point the active generated/audited subset had:

| Bucket | Count |
| --- | ---: |
| generated OK rows | `563,030` |
| generated row failures | `1,954` |
| audited rows | `527,641` |
| accepted rows | `492,306` |
| judge-dropped rows | `35,319` |
| audit row failures | `16` |

The `35,319` judge-dropped rows are mostly quality rejections, not failed
shards. The largest failure-type buckets were answer correctness
(`answer_correct`, `answer_incorrect`, `incorrect_answer`), instruction
following, meaning preservation, translation/language quality, and judge JSON
errors. Therefore the safe retry policy is selective:

1. Always retry row-level generation/audit transport, context, and parse
   failures unless the row leaves too little context budget even after dynamic
   capping.
2. Retry `judge_json_error` by rerunning audit, not generation.
3. Consider one regeneration attempt for language/translation/format/structure
   failures.
4. Do not blindly retry all answer-correctness or meaning-preservation drops;
   many indicate bad OpenHermes source answers or candidate corrections that no
   longer preserve the source. These are usually better excluded unless a later
   policy decides to repair source answers rather than translate them.

Policy update, 2026-07-12. Confidence: high as a project decision after
inspecting rejected DaOH examples. Repaired OpenHermes rows should be allowed
when the source OpenHermes answer is wrong and the generated row fixes it. The
rejection example `openhermes_2_5:train:14396` showed exactly this pattern: the
English source incorrectly maximized zoo animals by adding both species D and E,
while the Danish generated row correctly used the remaining space only for the
smallest species E. The audit rejected it for `meaning_preserved`, but for DFM8
this should be treated as an acceptable `repaired_translation` row if the row is
otherwise Danish, structurally valid, instruction-following, and answer-correct.

Implementation direction:

1. Do not simply loosen `meaning_preserved` globally. Add explicit audit fields
   such as `source_answer_defective`, `candidate_repairs_source`,
   `repair_preserves_user_intent`, and `repair_ok`.
2. Accept rows when either:
   - normal translation criteria pass, or
   - `repair_ok=true`, `candidate_repairs_source=true`,
     `repair_preserves_user_intent=true`, `answer_correct=true`,
     `danish_ok=true`, `structure_ok=true`, and `format_ok=true`.
3. Mark accepted repair rows in metadata, e.g.
   `translation_strategy="repaired_translation"` and
   `source_answer_defective=true`, so downstream sampling can cap or audit them
   separately.
4. Build a parallel English repaired OpenHermes dataset. Preferred approach:
   audit English OpenHermes first, generate repaired English rows only for
   rows with fixable answer/content defects, audit the repaired English rows,
   then translate only those repaired English rows into Danish and add the
   accepted Danish repaired rows to the main `dfm8-openhermes-da` dataset.
   This gives a canonical English repaired OH while improving the existing
   Danish OH translation rather than creating a separate final Danish repaired
   dataset.
5. Keep unfixable source rows excluded: incoherent prompts, impossible
   constraints, broken code where no reliable repair is possible, unsafe content
   that would require policy rewriting, and rows that cannot be made structurally
   valid within context.

Superseded implementation note, 2026-07-12. Confidence: high from local file inspection,
syntax checks, and an offline smoke test. The existing Danish OpenHermes
dataset name is `dfm8-openhermes-da`. The repaired English equivalent should
use the matching language-code name `dfm8-openhermes-en-repaired`. The aligned
Danish repaired subset should be `dfm8-openhermes-da-repaired`.

Superseded scope decision: clean English OpenHermes rows were assumed to be
covered by regular OpenHermes. This is no longer true for DFM8 because raw
`openhermes_2_5` is intentionally excluded from the final DFM8 source tree.
The corrected policy is below.

Updated implementation note, 2026-07-12. Confidence: high from local file
inspection and syntax checks. The repaired Danish rows should not be uploaded
as a separate final dataset. They should be merged into the existing Danish OH
translation, `dfm8-openhermes-da`, while remaining identifiable via metadata:
`dfm8_synthetic_family="openhermes_da_repaired"` and
`source_answer_defective=true`.

Corrected English OpenHermes policy, 2026-07-12. Confidence: high from local
code edits and syntax checks. DFM8 must not sample raw `openhermes_2_5`
directly, but it must still include positively audited English OpenHermes rows.
The English upload dataset is therefore named `dfm8-openhermes-en`, not
`dfm8-openhermes-en-repaired`. It contains:

- source-audited clean English OpenHermes rows tagged
  `dfm8_synthetic_family="openhermes_en_clean"`;
- accepted repaired English rows tagged
  `dfm8_synthetic_family="openhermes_en_repaired"`.

If a repaired English row exists for a `source_row_id`, it supersedes the clean
source row for that same ID. The raw converted OpenHermes source remains only an
input to the audit/repair/translation pipeline.

Sampling enforcement update, 2026-07-12. Confidence: high from local file
inspection and syntax checks. DFM8 should use the audited English OpenHermes
dataset instead of raw `openhermes_2_5`. The raw converted
`data/dfm8_special_sources/openhermes_2_5` remains available only as input to
the repair/translation pipeline. The final DFM8 training source tree excludes
`openhermes_2_5` and includes `export-upload-dfm8-openhermes-repaired` instead.
The DFM8 sampling config uses:

```yaml
- prefix: dfm8-openhermes-en__
  repeat: 1
- prefix: dfm8-openhermes-da__
  repeat: 1
```

The relevant implementation changes are:

- `scripts/build_dfm8_chat_source_tree.py`: skips
  `data/dfm8_special_sources/openhermes_2_5` for final DFM8 source trees and
  links `export-upload-dfm8-openhermes-repaired`.
- `scripts/build_tokenized_dfm8_tree.py`: selects
  `dfm8-openhermes-en` and merged `dfm8-openhermes-da` from the
  repaired upload root.
- `data_io/prefix_config_dfm8.yaml`: removes `openhermes_2_5__` and samples
  the audited English and merged Danish OpenHermes prefixes.

The scaffolded package is:

```text
dfm8_openhermes_repaired/
```

It provides:

- CLI: `python -m dfm8_openhermes_repaired.cli`
- guarded 8-GPU runner: `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`
- work root: `data/dfm8_openhermes_repaired`
- upload root: `export-upload-dfm8-openhermes-repaired`
- English audited upload folder: `dfm8-openhermes-en`
- merged Danish upload folder: `dfm8-openhermes-da`

Pipeline phases:

1. `make-audit-requests`
2. `shard-requests`
3. `audit-source`
4. `make-repair-requests`
5. `repair-english`
6. `audit-repair`
7. `make-danish-repair-requests`
8. `translate-danish`
9. `audit-danish`
10. `build-upload`, which writes `dfm8-openhermes-en` and a merged
    `dfm8-openhermes-da` consisting of accepted regular DaOH rows, with any
    accepted repaired Danish rows replacing their corresponding regular rows.

Reasoning-style repair update, 2026-07-12. Confidence: high from local prompt
and syntax checks. The English OpenHermes repair pipeline should also repair
obsolete reasoning style, not just incorrect answers. The source audit tracks
`reasoning_style_defective`; the repair prompt instructs Gemma 4 to modernize
stale verbose chain-of-thought style into Gemma-4-compatible visible
explanations: concise rationale when useful, no hidden-CoT markup, no boilerplate
"let's think step by step", and exactly one final LaTeX boxed answer for
determinate math/verifiable tasks. The repair audit tracks
`candidate_modernizes_reasoning_style` and requires `reasoning_style_ok=true`.

Danish replacement update, 2026-07-12. Confidence: high from local deterministic
ID test. Danish repaired rows are not just appended to the merged
`dfm8-openhermes-da`; they replace the corresponding regular DaOH row when
available. The repaired row records:

```json
{
  "replaces_row_id": "<original DaOH openhermes_da stable id>",
  "replaces_source": "dfm8_openhermes_da",
  "replacement_policy": "replace_regular_daoh_row_with_repaired_translation"
}
```

The replacement ID is deterministic from the shared `source_row_id` using the
same `stable_id("openhermes_da", source_row_id)` scheme as DaOH. For the
inspected zoo example `openhermes_2_5:train:14396`, this gives
`8605fa41fc229359b8bd7395`, matching the original DaOH row ID. During
`build-upload`, regular DaOH rows whose `row_id` or `source_row_id` is
superseded by an accepted repaired Danish row are omitted from the merged
`dfm8-openhermes-da`.

The runner refuses to start while the active DaOH package appears to be using
the same vLLM ports. Offline smoke test:

```bash
PYTHONPATH=/work/dfm/HRM-Text/dfm8_openhermes_repaired \
python -m dfm8_openhermes_repaired.cli make-audit-requests \
  --input-root data/dfm8_special_sources/openhermes_2_5 \
  --root /tmp/dfm8_openhermes_repaired_smoke \
  --max-rows 5

PYTHONPATH=/work/dfm/HRM-Text/dfm8_openhermes_repaired \
python -m dfm8_openhermes_repaired.cli shard-requests \
  --root /tmp/dfm8_openhermes_repaired_smoke \
  --shards 2 \
  --force
```

The smoke test produced five audit requests and two shard files. Syntax checks
passed for both `dfm8_openhermes_repaired/dfm8_openhermes_repaired/cli.py` and
`dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`.

OpenHermes audit model policy, 2026-07-12. Confidence: medium from local model
path inspection and prior observed 31B audit behavior. Gemma 4 31B remains the
default source of truth for OpenHermes English repair audits and Danish
translation audits because it is the model already used for the DFM8 synthetic
and DaOH audit policy. A Gemma 4 26B MoE judge may be considered for first-pass
triage only after a paired calibration against the 31B judge on a representative
5k-20k OpenHermes sample. The calibration should measure clean/repair/exclude
agreement, inspect disagreements in math/code/factual/reasoning-style rows, and
compare end-to-end throughput. If agreement is strong and speed is materially
better, use 26B MoE for clean-vs-suspicious triage and keep 31B confirmation
for all repair/exclude/ambiguous rows plus a random sample of rows marked clean.
Do not silently switch the final audit standard mid-DFM8 without recording the
calibration result.

Repaired OpenHermes follow-on scheduling, 2026-07-12. Confidence: high from
local code inspection, syntax checks, and a dry-run request build. The current
policy is to keep Gemma 4 31B as both generator and judge for the follow-on
OpenHermes work. The implemented order is:

1. Wait until the active `dfm8_openhermes_da` run has exited.
2. Audit English OpenHermes source rows for clean/repair/exclude decisions.
3. Generate repaired English rows only for repairable source-answer defects or
   obsolete reasoning style.
4. Audit repaired English rows.
5. Translate accepted repaired English rows to Danish.
6. Audit those Danish repaired translations against the repaired English row.
7. Build retry requests for ordinary DaOH failures that are likely fixable:
   HTTP/timeout/bad-response, generation parse/JSON failures, and structural,
   formatting, language, or metadata audit failures. Do not retry semantic
   `meaning_preserved`, `answer_correct`, factual, or semantic drops in this
   retry lane; those are handled by the English repair path.
8. Generate and audit the DaOH retry translations against the original English
   row.
9. Build upload-ready `dfm8-openhermes-en` and a merged
   `dfm8-openhermes-da` containing regular accepted DaOH rows, accepted Danish
   repairs, and accepted DaOH retry rows.

If both a repaired-source Danish row and a DaOH retry row exist for the same
`source_row_id`, the repaired-source row wins and the retry row is omitted from
the merged dataset. The build summary records accepted repaired rows, accepted
retry rows, and retry rows shadowed by repair.

The implementation lives in `dfm8_openhermes_repaired/`. New/important commands:

```bash
python -m dfm8_openhermes_repaired.cli make-daoh-retry-requests \
  --root data/dfm8_openhermes_repaired \
  --danish-base-root data/dfm8_openhermes_da_synthetic

bash dfm8_openhermes_repaired/scripts/watch_daoh_then_run_openhermes_repair.sh
```

A dry run against the current DaOH state built `5523` retry candidates from
likely-fixable failures without missing original requests.

OpenHermes repeat policy update, 2026-07-12. Confidence: medium until final
accepted/token counts are available. Do not blindly set both audited English
and translated Danish OpenHermes to `repeat: 2`. The merged Danish
`dfm8-openhermes-da` is the better candidate for `repeat: 2` because it adds
Danish instruction breadth and includes audited regular, repaired, and retry
rows. Keep `dfm8-openhermes-en` at `repeat: 1` by default until final
accepted-token counts are available; it now contains all positively audited
clean English rows plus accepted repairs, so repeating it may significantly
increase OpenHermes style weight. Revisit after the repaired pipeline writes
`export-upload-dfm8-openhermes-repaired/build_summary.json` and token counts.

Superseded by user decision later on 2026-07-12. Confidence: high from local
config edit. DFM8 should upweight both audited English and merged Danish
OpenHermes to `repeat: 2`:

```yaml
- prefix: dfm8-openhermes-en__
  repeat: 2
- prefix: dfm8-openhermes-da__
  repeat: 2
```

## DFM8 Post-Training / RL Subset

Post-training subset plan, 2026-07-12. Confidence: medium. Starting from the
DFM6-DFM7 XL gas2 epoch-5 checkpoint, a DFM8 subset for further
mid-training/post-training should be narrower than the full DFM8 mix and should
target behavior rather than broad capability. Prioritize:

1. Multi-turn chat and instruction-following:
   - `dfm8-synthetic-multiturn-danish-english-chat`
   - `dfm8-synthetic-constrained-format-following`
   - `dfm8-openhermes-en` and `dfm8-openhermes-da`, sampled after positive
     audit
   - `kobprof_skolegpt_instruct`
   - `no_robots`, `allenai_if_sft_verified`,
     `allenai_if_multi_constraints_upto5`, and `allenai_rlvr_ifeval`
2. Agentic/tool calling:
   - `dfm8-synthetic-native-tool-calling`
   - corrected native-tool sources: `dolci_native_tool_use`,
     `glaive_native_tool_use`, `toolace_native_tool_use`,
     `xlam_native_tool_use`
   - `nemotron_agentic` and `nemotron_instruction_reasoning_off`, capped and
     converted to the same Gemma4/native tool-call contract
3. Communication/control tasks:
   - `dfm8-synthetic-danish-summarization-rewrite-controls`
   - selected Danish instruction data such as `oliverkinch_*`,
     `synquid_ifbench_train`, `synquid_wiki_instruct_da`, and
     `synquid_danish_verifiable_reasoning`
4. Keep only small anchors for broad ability:
   - small slices of strict math/code and high-quality general SFT to prevent
     regression, but do not let math/code/pretraining-style data dominate this
     phase.

Suggested SFT/post-training proportions:

| Bucket | Approx share |
| --- | ---: |
| Tool/agentic trajectories | 30-40% |
| Multi-turn chat | 15-25% |
| Instruction/format following | 15-25% |
| Danish instruction and summarization controls | 15-25% |
| Broadly sampled math/code/general anchors | 20% |

Use Gemma4 chat template and the same native tool-call representation used in
evaluation. For this phase, avoid continuation-style and broad transform data
unless the goal is still broad capability training rather than alignment. The
20% anchor slice is deliberate regression control, not a return to broad
pretraining-style sampling.

Implementation status, 2026-07-12. Confidence: high from local file inspection
and syntax checks.

DFM8-post now has separate sampling artifacts:

- `scripts/build_tokenized_dfm8_post_tree.py`: builds
  `data/tokenized_dfm8_post` as a filtered symlink union from
  `data/tokenized_dfm8`. This is required because `data_io/sample_tokenized.py`
  samples unmatched tasks with default `repeat=1`; pointing the sampler at full
  DFM8 would leak broad sources into the post-training mix.
- `data_io/prefix_config_dfm8_post.yaml`: post-training sampler config. It
  prioritizes DFM8 synthetic tool/chat/format/summarization data, audited
  English/Danish OpenHermes derivatives, native tool-use sources, Danish
  instruction/control sources, and a deliberately restrained broad-anchor
  section intended to be about 20% of sampled tokens after report-driven tuning.
- `scripts/prepare_dfm8_post_data.sh`: builds the filtered tree and samples
  `data/sampled_dfm8_post`, writing analytics to
  `data/show_analytics_dfm8_post.md`.
- `config/data/dfm8_post.yaml`: training data config pointing at
  `data/sampled_dfm8_post`.

Run after the final DFM8 tokenized tree is ready:

```bash
cd /work/dfm/HRM-Text
bash scripts/prepare_dfm8_post_data.sh
```

After sampling, inspect `data/show_analytics_dfm8_post.md` and tune
`data_io/prefix_config_dfm8_post.yaml` if the broad-anchor tasks are not close
to 20% of sampled tokens. The current sampler controls mix weights through
per-source caps and repeats rather than hard token-budget buckets.

Lightweight validation on the current incomplete DFM8 tokenized tree:

```bash
cd /work/dfm/HRM-Text
python scripts/build_tokenized_dfm8_post_tree.py --force
```

This linked `4,146` current tasks into `data/tokenized_dfm8_post`: `4,096`
focus tasks and `50` broad-anchor tasks. DFM8-specific synthetic/OpenHermes
derivatives will only appear after they have been integrated into
`data/tokenized_dfm8`.

RL / preference plan, 2026-07-12. Confidence: medium. For the same goals, start
with DPO-style preference tuning before PPO/GRPO. Sources:

- build DPO pairs from DFM8 tool-call audits and smoke/eval failures:
  chosen = valid one-call/native-tool output or correct clarification/no-tool
  answer; rejected = malformed calls, repeated calls, wrong tool, missing tool,
  over-eager tool use, or answer-without-required-tool.
- build instruction-following pairs from IFEval/IFBench-style constraints:
  chosen follows all constraints; rejected violates one constraint while being
  fluent.
- use judge-generated preference pairs for Danish summaries and multi-turn chat:
  chosen preserves requested length/tone/format and handles follow-ups; rejected
  is verbose, ignores language, loses constraints, or resets conversation state.
- consider public function-calling preference datasets such as
  `roborovski/glaive-tool-usage-dpo`,
  `roborovski/synthetic-tool-calls-v2-dpo-pairs`, and
  `interstellarninja/tool-calls-dpo` after conversion/audit.

How to obtain DPO pair sources, 2026-07-12. Confidence: medium from Hugging
Face search metadata and local pipeline design.

There are three acquisition paths:

1. Public HF DPO datasets. Download and convert them like other HF sources:

```bash
cd /work/dfm/HRM-Text
huggingface-cli download roborovski/glaive-tool-usage-dpo \
  --repo-type dataset \
  --local-dir data/downloads/datasets/roborovski_glaive_tool_usage_dpo
huggingface-cli download roborovski/synthetic-tool-calls-v2-dpo-pairs \
  --repo-type dataset \
  --local-dir data/downloads/datasets/roborovski_synthetic_tool_calls_v2_dpo_pairs
huggingface-cli download interstellarninja/tool-calls-dpo \
  --repo-type dataset \
  --local-dir data/downloads/datasets/interstellarninja_tool_calls_dpo
```

Then add explicit downloader manifest entries and a DPO converter that emits
`prompt/messages`, `chosen`, `rejected`, task-family tags, tool schema metadata,
and conversion/audit diagnostics. Do not mix these into DFM8 SFT by default;
keep them in a DPO-specific export.

2. Project-generated pairs from DFM8 audits and eval failures. For tool calling,
format following, summaries, and multi-turn chat, the best project-specific
pairs come from artifacts we already produce: rejected audit rows, smoke-test
failures, eval generations, and corrected/regenerated rows. Convert these as:
chosen = audited/fixed response; rejected = malformed, over-eager, wrong-tool,
wrong-format, verbose, or constraint-violating response. These pairs are more
valuable than generic preference data because they target exactly the failure
modes seen in DFM5-DFM7.

3. Environment/verifier-generated pairs. For BFCL-shaped tool calling,
math-answer-contract, and exact-format tasks, generate multiple candidate
responses from checkpoints or teachers, score them with deterministic
validators, and build chosen/rejected pairs from pass/fail or higher/lower
scores. This should be the bridge between SFT DFM8-post and later GRPO/PPO.

All DPO sources should be rendered/audited against the same Gemma4 chat and
native tool-call contract as DFM8. Store them separately from
`data/sampled_dfm8_post` until the DPO training code and loss path are explicit.

DFM8-preference export status, 2026-07-12. Confidence: high from local
downloads, schema inspection, conversion, and marker audits.

The first public-HF DPO/preference batch has been downloaded under
`data/downloads/datasets/` and converted to a separate Gemma4-template-safe
preference export at `data/dfm8_preference_pairs`. This is intentionally not
mixed into SFT sampling. The converter is
`scripts/prepare_dfm8_preference_data.py`.

Command that worked:

```bash
cd /work/dfm/HRM-Text
python scripts/prepare_dfm8_preference_data.py --force
```

The converter writes one JSONL file per source plus
`data/dfm8_preference_pairs/manifest.json`. Each row contains
`prompt_messages`, `tools`, `chosen_completion_messages`, and
`rejected_completion_messages`. Tool-call rows are represented as native
Gemma/OpenAI-style message sequences, e.g. `assistant.tool_calls -> tool ->
assistant`, not as literal XML or ChatML strings.

Converted rows:

| Source | Local folder | Rows | Notes |
| --- | --- | ---: | --- |
| `roborovski/glaive-tool-usage-dpo` | `roborovski_glaive_tool_usage_dpo` | 42,014 | Tool-use preference rows; tool schemas extracted from old system text and rendered as native `tools`. |
| `roborovski/synthetic-tool-calls-v2-dpo-pairs` | `roborovski_synthetic_tool_calls_v2_dpo_pairs` | 8,005 | Structured accepted/rejected tool call/result/final-answer trajectories converted to native tool-call sequences. |
| `roborovski/synthetic-toolformer-dpo-pairs` | `roborovski_synthetic_toolformer_dpo_pairs` | 289 | Small structured tool preference set. |
| `interstellarninja/tool-calls-dpo` | `interstellarninja_tool_calls_dpo` | 235 | Small XML-style function-call DPO set; XML targets normalized or skipped. |
| `Hodfa71/saga-da-delta-dpo-r1` | `hodfa71_saga_da_delta_dpo_r1` | 7,410 | Danish grammar/completion preference pairs, wrapped as an instruction to continue Danish text naturally. |
| `Hodfa71/saga-da-delta-dpo-r2` | `hodfa71_saga_da_delta_dpo_r2` | 7,307 | Danish grammar/completion preference pairs, round 2. |
| `allenai/Dolci-Think-DPO-7B` | `allenai_dolci_think_dpo_7b` | 149,882 | General/reasoning preference data; rows with old template markers or excessive length skipped. |
| `argilla/distilabel-math-preference-dpo` | `argilla_distilabel_math_preference_dpo` | 2,418 | Math preference pairs. |
| `tzwilliam0/instruction_following_dpo_filtered` | `tzwilliam0_instruction_following_dpo_filtered` | 10,262 | Instruction-following preference pairs. |
| `tzwilliam0/instruction_following_dpo_filtered_add` | `tzwilliam0_instruction_following_dpo_filtered_add` | 18,813 | Additional instruction-following preference pairs. |
| `mlabonne/chatml-OpenHermes2.5-dpo-binarized-alpha` | `mlabonne_chatml_openhermes25_dpo_binarized_alpha` | 9,197 | OpenHermes-derived DPO; ChatML wrappers are not preserved. |
| `Capx/Agentic-DPO-V0.1` | `capx_agentic_dpo_v01` | 4,744 | General agentic DPO; converted from `data.json`. |

Total exported rows: `260,576`. Family counts:

| Family | Rows |
| --- | ---: |
| `general_reasoning` | 149,882 |
| `tool_calling` | 42,249 |
| `instruction_following` | 29,075 |
| `danish_grammar_completion` | 14,717 |
| `format_following_openhermes` | 9,197 |
| `tool_calling_structured` | 8,294 |
| `agentic_general` | 4,744 |
| `math_preference` | 2,418 |

Language counts: `245,859` English rows and `14,717` Danish rows.

Template-safety audit:

```bash
cd /work/dfm/HRM-Text
python - <<'PY'
from pathlib import Path
import json
bad=[]
markers=['<|im_start|>','<|im_end|>','<tool_call>','</tool_call>','<tools>','</tools>','[/INST]','<s>[INST]','<|endoftext|','<|endoftext|>']
for p in Path('data/dfm8_preference_pairs').glob('*.jsonl'):
    if p.name == 'render_failures.jsonl':
        continue
    with p.open() as f:
        for i,line in enumerate(f):
            row=json.loads(line)
            text=json.dumps(row.get('chosen_completion_messages'), ensure_ascii=False)+json.dumps(row.get('rejected_completion_messages'), ensure_ascii=False)+json.dumps(row.get('prompt_messages'), ensure_ascii=False)
            hit=[m for m in markers if m in text]
            if hit:
                bad.append((p.name,i,hit))
                break
print('bad_files', len(bad))
for item in bad[:20]: print(item)
PY
```

Result: `bad_files 0`. The export size is currently about `3.1G`.

Adjacent sources not yet part of `DFM8-preference`:

- `qnguyen3/dpo-r1`: local schema is SFT-shaped `messages` plus `source`, not
  direct `chosen`/`rejected` pairs.
- `zake7749/Qwen3.6-35B-A3B-Tool-Calling`: useful tool-call SFT source, but
  the local file is final SFT rows (`tools`, `messages`), not the preference
  pairs described in the card.
- `KKACHI-HUB/Tool-DPO-LLaMA-Factory`: metadata is visible with the provided
  token, but file download still returns "awaiting review from repo authors".
  Do not count this source until actual parquet download succeeds.

DFM8-preference next-step plan, 2026-07-12. Confidence: medium.

Keep `DFM8-preference` as a separate preference-training artifact, not part of
`DFM8-post` SFT sampling. The purpose is to support DPO-style tuning after
DFM8/DFM8-post SFT, especially for tool calling, instruction following,
Danish grammaticality, and answer-format control.

Planned stages:

1. Source QA and stratification.
   - Inspect examples by `task_family`, source, language, and length bucket.
   - Verify chosen/rejected semantics for each source; especially review
     `general_reasoning` and `agentic_general` for noisy or stylistically odd
     preferences.
   - Decide caps by family before training. Initial default should not let
     `allenai_dolci_think_dpo_7b` dominate just because it is large.
   - Keep `danish_grammar_completion` as a small targeted Danish slice, not as
     the main Danish alignment signal.
2. Converter hardening.
   - Add an explicit unit/smoke test that renders one row per source through
     `data_io/chat_templates/gemma4_native_chat.jinja`.
   - Add a stricter tool-schema audit: every `tools` item must have
     `type=function`, a valid function name, object parameters, and no old XML
     wrappers in prompt/chosen/rejected messages.
   - Preserve the current marker audit (`bad_files 0`) as a required gate.
3. Include pending/review sources only when safe.
   - Retry `KKACHI-HUB/Tool-DPO-LLaMA-Factory` after HF approval is complete;
     include only if actual parquet download succeeds and rows pass the same
     Gemma4 marker/tool audit.
   - Treat `zake7749/Qwen3.6-35B-A3B-Tool-Calling` and `qnguyen3/dpo-r1` as
     SFT/tool-call sources unless we derive negatives or recover true
     chosen/rejected pairs.
4. Project-specific pair generation.
   - Mine our eval/smoke/audit artifacts for pairs:
     chosen = fixed/audited response; rejected = observed failure.
   - Priority failure modes: wrong or missing tool call, over-eager tool use,
     repeated tool-call loops, malformed JSON/tool args, ignored output format,
     missing final boxed math answer, verbose summaries when brief was asked,
     and Danish language/grammar failures.
   - This path is cheap when using existing artifacts; it should be done before
     launching large new teacher-generation campaigns.
5. Verifier-generated pairs.
   - For tool calling, create BFCL-shaped prompts with deterministic validators
     for function name, JSON/schema, argument values, no repeated calls, and
     correct final answer after tool results.
   - For math, score final-answer extraction/boxed-answer compliance separately
     from reasoning quality.
   - For format following, use deterministic validators for JSON, tables,
     bullet counts, sentence counts, language, and exact labels.
   - Generate multiple candidates from target checkpoints or teachers, then
     build chosen/rejected pairs from validator scores.
6. Training integration.
   - Do not start DPO until there is an explicit DPO training entry point and
     config path. Required knobs: beta, learning rate, reference model path,
     max prompt/response length, family caps, and whether EMA/reference weights
     are used.
   - First run should be a small ablation on a copied checkpoint, not the main
     continuation run.
   - Evaluate before/after with the lite/full eval suites plus focused tool
     and format smoke tests.

Open design question: whether DPO should follow `DFM8-post` SFT or be run as a
short parallel branch from the same DFM8 checkpoint. Default recommendation is
SFT first, then DPO, because DPO assumes the model can already produce the
desired behavior often enough for preference tuning to sharpen it rather than
teach it from scratch.

## DFM8 Synthetic/OpenHermes Pipeline Status

Snapshot, 2026-07-12 20:46 CEST. Confidence: high from local process, queue,
manifest inspection, HF upload commit URLs, and HF-side file-count verification.

Completed stages:

- Broad transform expansion/audit finished:
  `logs/dfm8_transform_expansion_dynamic_audits_c64_u070_20260709T110453`
  has `176` done, `0` failed, `0` pending/running. Source manifest reports
  `1,495,662` accepted transformed rows after the Common Pile prefix cap.
  Superseded 2026-07-12 20:46 CEST: the earlier 2026-07-12 19:01 note said
  this stage was local-only. The additional accepted rows have now been uploaded
  additively to the eight existing `schneiderkamplab/*` transform dataset repos
  as `data/dfm8-extra-train-*.jsonl.gz`, with each repo also receiving its
  local `filter_summary.json`. The accidental HRM-Text README files in
  `data/dfm8_transform_expansion_filtered/*/README.md` were deliberately not
  uploaded. Upload log:
  `logs/hf_upload_dfm8_transform_expansion_20260712T204643.json`.

  New uploaded DFM8 transform-expansion rows:

  | HF dataset repo | New rows | New files | Commit |
  |---|---:|---:|---|
  | `schneiderkamplab/common-pile-denoising` | `580,434` | `470` | `692ba5faebd4a64247dac93c4ada8c9f858e9508` |
  | `schneiderkamplab/common-pile-paragraph-reordering` | `43,821` | `14` | `4e9a98cb4b5694cbe52839b28ae920ebde0a29f7` |
  | `schneiderkamplab/common-pile-prefix-continuation` | `703,658` | `229` | `e69fb584d078a9a44ae586985c2c98eb98e73e45` |
  | `schneiderkamplab/common-pile-span-filling` | `572,098` | `1,423` | `95878b6da460dd61e2bc17df2c450889bdf628c7` |
  | `schneiderkamplab/danish-dynaword-denoising` | `137,520` | `86` | `fedf451723440a365253b508810702259ed16fb1` |
  | `schneiderkamplab/danish-dynaword-paragraph-reordering` | `34,931` | `22` | `bcd114189098e5f88cb4ef5530b1eee00a484603` |
  | `schneiderkamplab/danish-dynaword-prefix-continuation` | `201,507` | `88` | `0bd798071d400d280fed4b766f77b04f777bd516` |
  | `schneiderkamplab/danish-dynaword-span-filling` | `124,414` | `268` | `88219d9d022d24897df646e4491f938bc038e5e8` |
  | **Total** | **`2,398,383`** | **`2,600`** | |

  HF-side verification after upload showed the expected extra file counts:
  `470`, `14`, `229`, `1423`, `86`, `22`, `88`, and `268`, respectively, and
  `filter_summary.json` present in each repo.

  The older accepted transform datasets remain uploaded under `schneiderkamplab`:
  - `common-pile-denoising`
    (`f911cf777c891c454d571cbfbf0b04670f4c81a4`, `7` JSONL.GZ files)
  - `common-pile-paragraph-reordering`
    (`e227c5f1e5f2b64231c6a56fd0eb2f42651fcc95`, `16` JSONL.GZ files)
  - `common-pile-prefix-continuation`
    (`819dc27acb1f8debfcc7b5ab63ad4ee0e4c89156`, `19` JSONL.GZ files)
  - `common-pile-span-filling`
    (`58160ebc1320488dbc2e8c50d8284cc94cb09f99`, `7` JSONL.GZ files)
  - `danish-dynaword-denoising`
    (`6860137828a44c0785490f35923a720882a906d1`, `4` JSONL.GZ files)
  - `danish-dynaword-paragraph-reordering`
    (`52a85233f1e8d4c887ab6bcd435d875ca79b4db2`, `3` JSONL.GZ files)
  - `danish-dynaword-prefix-continuation`
    (`d0902a56428d8fb2493fb313482bf6bf5ac15c21`, `2` JSONL.GZ files)
  - `danish-dynaword-span-filling`
    (`d237f85be7b90963e405ea9a968525e41f1d1abc`, `2` JSONL.GZ files)
  - `transformations-danish-danish`
    (`178b5009f3f8a03af5a14e469204d60c90fb03c0`, `251` JSONL.GZ files)
  - `transformations-danish-english`
    (`b935c7770b5233dd6b03fce101968ec3804c75bd`, `251` JSONL.GZ files)
  - `transformations-english-danish`
    (`eec08f3429f6d5060fd2bfab5952f5361408181a`, `410` JSONL.GZ files)
  - `transformations-english-english`
    (`b5599187244c037e68e18076a0c4e7411d6cb5cc`, `389` JSONL.GZ files)
- Targeted DFM8 synthetic generation/audit/upload is complete in
  `export-upload-dfm8-synthetic`. It generated `4,800,000` rows, audited
  `4,580,233`, and accepted:
  - `dfm8-synthetic-code-debugging`: `340,711`
  - `dfm8-synthetic-constrained-format-following`: `838,905`
  - `dfm8-synthetic-danish-summarization-rewrite-controls`: `825,861`
  - `dfm8-synthetic-multiturn-danish-english-chat`: `414,196`
  - `dfm8-synthetic-native-tool-calling`: `836,675`
  - `dfm8-synthetic-strict-math-answer-contract`: `552,952`
  Upload status: verified on 2026-07-12. The local completed export was pushed
  or confirmed unchanged on Hugging Face under:
  - `schneiderkamplab/dfm8-synthetic-code-debugging`
    (`87e99f9815c1c4b484fecb4485a24e5c18277b1b`)
  - `schneiderkamplab/dfm8-synthetic-constrained-format-following`
    (`61850112550ef6631d04f89eb575b7bddc80cbd2`)
  - `schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls`
    (`3b528aa7510d3a7a5fea22a2b33e89b1a1a0d09c`)
  - `schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat`
    (`e345d051a5d8714975de3bb19b137e357d76d92c`)
  - `schneiderkamplab/dfm8-synthetic-native-tool-calling`
    (`3c2d177835beb79749a45143fd250fcedad5a6c9`)
  - `schneiderkamplab/dfm8-synthetic-strict-math-answer-contract`
    (`14ff86ffae606f6dee4e959d0a4fe2c5a3b5c1bd`)
- Base Danish OpenHermes translation/audit/upload is complete in
  `export-upload-dfm8-openhermes-da`: `1,001,551` generated rows, `991,114`
  audited rows, and `924,816` accepted rows.
  Upload policy update: do not upload/use this base DaOH as final DFM8 input.
  Wait for the repaired/retranslated merge from
  `export-upload-dfm8-openhermes-repaired`, which will include repaired English
  OpenHermes, Danish translations of repaired rows, and retry rows for
  fixable DaOH failures.

Active stage:

- `dfm8_openhermes_repaired/scripts/watch_daoh_then_run_openhermes_repair.sh`
  detected DaOH completion and launched
  `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`.
- Active log root: `logs/dfm8_openhermes_repaired_20260712T085219`.
- Eight Gemma 4 31B vLLM servers are active on ports `8600-8607` with
  `gpu-memory-utilization=0.7`, `max-num-seqs=64`, and GPUs at about 100%
  utilization.
- Current substage: English OpenHermes source audit before English repair,
  Danish retranslation of repaired rows, DaOH retry translation, and final
  merged `dfm8-openhermes-en`/`dfm8-openhermes-da` upload build.
- Progress at snapshot: `248,164 / 1,001,551` source-audit rows written
  (`24.8%`). The script has not yet reached English repair, Danish
  retranslation, DaOH retry, or final repaired upload build.

Runner order after source audit:

1. `make-repair-requests`
2. `repair-english`
3. `audit-repair`
4. `make-danish-repair-requests`
5. `translate-danish` repaired rows
6. `audit-danish` repaired rows
7. `make-daoh-retry-requests`
8. `translate-danish` retry rows
9. `audit-danish` retry rows
10. `build-upload` to `export-upload-dfm8-openhermes-repaired`

GRPO/PPO should be reserved for executable or simulated environments with
verifiable rewards:

- BFCL-shaped single/multi-turn tool-call tasks for AST/executable/irrelevance
  rewards.
- τ-bench / τ²-bench style customer-service simulations for multi-turn
  tool-use and state tracking.
- small internal tool-call environments where rewards check valid JSON,
  exactly one tool call where required, no repeated-call loops, correct
  arguments, and correct final answer after tool results.

Avoid RL on noisy fluency-only preferences. For DFM8, the most useful reward
signals are structural validity, functional correctness, constraint satisfaction,
and task success, not generic helpfulness.

## Hugging Face Availability

Update, 2026-07-13. Confidence: high for DFM8-specific source status from local
config/wiki inspection; medium for inherited DFM7 full-manifest status.

Aside from the still-running OpenHermes repair/translation outputs, the
DFM8-specific additions are available from Hugging Face:

- `giannor/dala_tv2r_it`, `giannor/gec_dala_tv2r_it`, and
  `kobprof/skolegpt-instruct` are upstream HF datasets downloaded by
  `scripts/download_training_datasets.py --groups dfm8 --download`.
- The eight broad transform-expansion datasets are uploaded under
  `schneiderkamplab/{common-pile,danish-dynaword}-*`.
- The four older `transformations-*` datasets are uploaded under
  `schneiderkamplab/transformations-*`.
- The six targeted synthetic DFM8 datasets are uploaded under
  `schneiderkamplab/dfm8-synthetic-*`.

The final DFM8 OpenHermes inputs are intentionally not the raw
`teknium/OpenHermes-2.5` conversion. `data_io/prefix_config_dfm8.yaml` expects
`dfm8-openhermes-en` and `dfm8-openhermes-da`, which will be produced by the
active repaired OpenHermes pipeline and uploaded from
`export-upload-dfm8-openhermes-repaired`.

Caveat: the local DFM8 build currently reuses inherited DFM7 tokenized/source
trees (`data/tokenized_dfm7` and related converted/export artifacts). Many of
those inherited sources are HF upstream datasets or previously uploaded
`schneiderkamplab` exports, but the whole inherited corpus is not yet expressed
as one clean HF-only DFM8 download manifest. If DFM8 must be rebuildable from
scratch on another machine, add a manifest/audit step that maps every inherited
DFM7 prefix in `data_io/prefix_config_dfm8.yaml` to either an upstream HF repo
or a `schneiderkamplab` export repo.

Follow-up, 2026-07-13. Confidence: high from local manifest inspection and
`huggingface_hub` repo checks. For a full DFM8 rebuild from scratch, the answer
was not yet "all sources are available from HF" until we upload or otherwise
publish the locally staged Danish sources:

- `dbc` (`dbc-abstracts_*.jsonl.gz`, `dbc-reviews.jsonl.gz`,
  `dbc-faktalink.jsonl.gz`, `dbc-farfatterweb.jsonl.gz`)
- `lexdk` (`lexdk_articles.jsonl.gz`)
- `opus` (`opus_da_en.jsonl.gz`) - superseded by upload note below

These are present under `data/downloads/datasets/{dbc,lexdk,opus}` and are
sampled via the inherited DFM8 prefixes `dbc__*`, `lexdk__`, and `opus__`.
They are not in `scripts/download_training_datasets.py` as HF datasets, and
obvious public `schneiderkamplab/{dbc,lexdk,opus,dbc-danish,lexdk-articles,opus-da-en}`
repos did not resolve during the check. All obvious large inherited families
otherwise map to upstream HF datasets in the downloader or to previously
uploaded `schneiderkamplab` exports (`sapient-synth-*`, broad transforms, and
DFM8 synthetic outputs). A strict HF-only rebuild therefore needs at least these
three local Danish source groups uploaded or deliberately excluded/replaced.

Upload update, 2026-07-13. Confidence: high from successful uploader exit and
Hub-side repo inspection. The `opus` rebuild gap is closed:

- HF dataset: `schneiderkamplab/opus-da-en-permissive`
- Commit: `67d62cf28a6bbe5e17d208776e49b95d808cc9df`
- Public: yes
- Files: `README.md`, `data/opus_da_en.jsonl.gz`
- Local package: `export-upload-local/opus-da-en-permissive`
- Upload log:
  `logs/hf_upload_opus_da_en_permissive_20260713T062000.log`
- Downloader manifest: `scripts/download_training_datasets.py` now contains
  an HF entry named `opus`, so `python scripts/download_training_datasets.py
  --only opus --download` restores the expected local root
  `data/downloads/datasets/opus`.

After this upload, the remaining known local-only DFM8 rebuild gaps are `dbc`
and `lexdk`, pending separate upload or an explicit replacement/exclusion
decision.

Dataset inventory update, 2026-07-31. Confidence: high from the sampled epoch
indices, `data/show_analytics_dfm8.md`, and the local download manifest. A
human-readable inventory of every nonzero DFM8 source, its HF repository (where
applicable), and its sampled per-epoch token contribution is maintained in
[`docs/dfm8-datasets.md`](../../docs/dfm8-datasets.md). DBC and LexDK are listed
separately there as non-HF datasets supplied through Danish Foundation Model
agreements. The six-epoch analytics sum to 70.479B tokens per epoch and agree
with direct epoch-index length sums to normal sampling variation.

Inventory refinement, 2026-07-31. Confidence: high from the DFM8 prefix
specification, category/task analytics, tokenized source links, and converter
source code. The inventory is exhaustive at HF-repository granularity: 159
distinct HF dataset IDs have one row each, while DBC and LexDK occupy two
separate agreement-supplied rows. Combined analytics categories for Giannor
TV2R and corrected Dolci tool use are split using task-level coverage rather
than estimated proportions. `acereason` is correctly attributed to
`nvidia/AceReason-1.1-SFT`.

Repair runner scheduling fix, 2026-07-13. Confidence: high from script
inspection and `bash -n`. `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`
previously used a FIFO wait pattern in `run_shards`: after launching one shard
per GPU, it waited for the oldest PID before launching any later shard. This
caused head-of-line blocking in tail phases: if one shard was slow or wedged,
free GPUs were not assigned later shards. The loop now uses `wait -n` with an
active-worker counter, so each completed child immediately frees one scheduler
slot and the next shard starts without waiting for older still-running shards.
This affects future stages/runs, not already-running child processes from a
script instance that was started before the patch.

DaOH retry shadowing fix, 2026-07-13. Confidence: high from local code
inspection and `py_compile`. The DaOH retry phase should not spend GPU time
retrying old Danish OpenHermes translation failures when the same `source_row_id`
already has an accepted repaired Danish translation from the English
OpenHermes-repair path. `cmd_make_daoh_retry_requests` now loads
`danish_repaired` plus `danish_repair_audits`, computes accepted repaired
source IDs, and skips DaOH retry candidates shadowed by those accepted repairs.
The final `build-upload` path already removed shadowed retry/base rows, but this
change avoids unnecessary retry translation/audit work up front and reports
`skipped_shadowed_by_accepted_repair`.

Importance estimate, 2026-07-13. Confidence: high for counts from
`data/show_analytics_dfm7.md`, `data/show_tokenized_dfm8.md`, and local `du`.
The three local-only source groups are not just bookkeeping noise, but their
importance differs:

| Source group | DFM8 tokenized source tokens | DFM7 sampled tokens, five epochs | Local raw size | Importance |
| --- | ---: | ---: | ---: | --- |
| `opus` | about 5.665B | about 14.518B | 2.4G | Largest of the three; mostly Danish-English translation. Useful, but partly replaceable by other Danish translation sources. |
| `dbc` | about 1.607B | about 1.781B | 2.2G | Medium-sized and more unique Danish cultural/library/book/article instruction material. |
| `lexdk` | about 66M | about 1.567B | 70M | Small source inventory but heavily repeated; high-quality Danish encyclopedic style. |

Together these accounted for about 17.87B sampled tokens over the five-epoch
DFM7 sample, or about 3.57B tokens/epoch. In DFM8 their percentage will likely
be somewhat lower after the OpenHermes and DFM8 synthetic additions, but the
absolute sampling policy still makes them meaningful. For a faithful DFM8
rebuild, upload all three rather than silently dropping them. If one must be
removed, `opus` is the most replaceable by content type; `dbc` and `lexdk` are
more distinctive Danish-domain sources.

Repaired OpenHermes completion, 2026-07-14. Confidence: high from local
pipeline counters and the final tmux build summary. The repaired OpenHermes
pipeline completed all GPU stages and built upload-ready folders under
`export-upload-dfm8-openhermes-repaired`:

- English output: `export-upload-dfm8-openhermes-repaired/dfm8-openhermes-en`
  with `918,095` rows.
- Merged Danish output:
  `export-upload-dfm8-openhermes-repaired/dfm8-openhermes-da` with `967,334`
  rows.
- English audit summary: `1,001,551` source-audit rows, `460,695` accepted
  clean rows, `457,400` accepted repaired rows, and `457,400` clean rows
  shadowed by repair.
- Base Danish OpenHermes summary: `1,001,551` generated rows, `991,114` audit
  rows, `924,816` accepted rows.
- Danish repaired additions: `429,353` accepted repaired rows, `3,220`
  accepted retry rows, `432,573` accepted added rows, and `390,055` regular
  DaOH rows replaced by repaired rows.
- Retry materialization counters: `7,032` DaOH retry translation rows and
  `5,729` DaOH retry audit rows were written.

This supersedes the earlier instruction to wait for the repaired OpenHermes
pipeline before final DFM8 sampling. The remaining step is uploading these two
upload-ready HF dataset folders and then integrating/tokenizing them in the
DFM8 source tree.

Upload update, 2026-07-14. Confidence: high from successful upload command and
Hub API verification. The repaired OpenHermes datasets are now public on
Hugging Face:

- `schneiderkamplab/dfm8-openhermes-en`, commit
  `157a1488d453aef9e827bddabc77d78c0bfd57ef`, 10 `data/*.jsonl.gz` shards plus
  `manifest.json` and `README.md`.
- `schneiderkamplab/dfm8-openhermes-da`, commit
  `a9458057e49c84561b5c75495a3d0400614df1ba`, 10 `data/*.jsonl.gz` shards plus
  `manifest.json` and `README.md`.

The token used for upload was supplied interactively and must not be recorded
in the repo or wiki. Future DFM8 rebuilds can fetch these as normal HF
datasets; the next local step is to ensure the DFM8 download/source-tree config
uses these HF repos instead of relying only on
`export-upload-dfm8-openhermes-repaired`.

Continuation epoch-index rule for DFM8-post / DFM8-preference, 2026-07-14.
Confidence: high from `pretrain.py`, `dataset_new.py`, and
`data_io/sample_tokenized.py` inspection. Checkpoint epoch tags and sampled
dataset directories use different indexing conventions:

- Training/checkpoint epochs are 1-based. A checkpoint named `epoch_5` means
  five training epochs have completed.
- Sampled data directories are 0-based. `data_io/sample_tokenized.py` writes
  `epoch_0`, `epoch_1`, ...
- On resume, `pretrain.py` maps a completed `epoch_N` checkpoint to
  `start_epoch=N+1`, then calls `dataset.set_epoch(start_epoch - 1)`.
  Therefore resuming from `epoch_5` loads sampled directory `epoch_5` for the
  next epoch of data.

For a continuation from the DFM6/DFM7 `epoch_5` checkpoint into DFM8,
DFM8-post, or DFM8-preference SFT with the existing `pretrain.py`, the target
sampled dataset must contain `epoch_5` for the first continuation epoch. There
is no separate epoch-offset config in the current trainer. Safe options:

1. Sample at least six epochs and use the generated `epoch_5` onward. This is
   the most semantically direct path, but wastes time if only one continuation
   epoch is needed.
2. Sample one post-training epoch, then explicitly copy or symlink `epoch_0`
   to `epoch_5` in a continuation-specific sampled directory. This is acceptable
   because the directory number is only the trainer's epoch cursor, not an
   intrinsic data property. Record the mapping in the run config/wiki.
3. Add a small trainer/dataset option such as `data_epoch_offset` if we want to
   keep sampled directories compact while resuming at arbitrary global epochs.
   Until implemented, do not assume such an offset exists.

For W&B/eval continuity, keep the resumed run's global epoch numbering at 6+
when resuming from `epoch_5`; do not reset the training checkpoint epoch to 1
unless intentionally starting a new, separate post-training run.

DFM8 / DFM8-post sampled token distribution snapshot, 2026-07-14.
Confidence: high for local counts from `data/sampled_dfm7/metadata.json`,
`data/sampled_dfm8/metadata.json`, `data/sampled_dfm8_post/metadata.json`, and
their `data/show_analytics_*.md` reports; medium for coarse category grouping.
The analytics `Cov Toks` column is total over sampled epochs, so divide by the
sample count to get per-epoch values. Current per-epoch totals:

| Sample | Sampled epochs | Tokens per epoch |
| --- | ---: | ---: |
| DFM7 | 5 | 66.657B |
| DFM8 | 6 | 67.410B |
| DFM8-post | 9 | 27.048B |

Approximate per-epoch coarse buckets from `Cov Toks / epochs`:

| Bucket | DFM7 | DFM8 | DFM8-post |
| --- | ---: | ---: | ---: |
| Danish | 16.812B | 17.159B | 6.960B |
| English/general instruction | 14.400B | 14.791B | 2.888B |
| Math/code/reasoning | 16.944B | 16.958B | 4.201B |
| Tool/agentic | 9.624B | 9.624B | 11.648B |
| Synthetic/transforms | 3.498B | 3.498B | 0B by the coarse grouping used in the quick report |
| Other/legacy | 5.380B | 5.380B | 1.351B |

Superseded critical DFM8 union issue discovered while inspecting the
distribution, 2026-07-14. Confidence: high from
`scripts/build_tokenized_dfm8_tree.py`, `data/tokenized_dfm8`, and
`data/show_analytics_dfm8.md` inspection. The earlier
`data/tokenized_dfm8` / `data/sampled_dfm8` build should be treated as a
discarded snapshot, not the intended final DFM8 mix:

- `scripts/build_dfm8_chat_source_tree.py` excludes raw
  `data/dfm8_special_sources/openhermes_2_5`, but
  `scripts/build_tokenized_dfm8_tree.py` independently accepts any raw
  tokenized task prefixed by `dfm8_special_sources__`.
- As a result, `data/tokenized_dfm8` contains raw
  `openhermes_2_5__train-*.jsonl` tasks.
- The repaired HF-upload-shaped shards under
  `export-upload-dfm8-openhermes-repaired__dfm8-openhermes-en__data__*.jsonl.gz`
  and `...dfm8-openhermes-da...` were tokenized, but not selected into
  `data/tokenized_dfm8`; the selector only matched the exact directory name
  `dfm8-openhermes-en` / `dfm8-openhermes-da`, not nested shard paths.

Before DFM8 training, fix `scripts/build_tokenized_dfm8_tree.py` so it:

1. rejects `dfm8_special_sources__openhermes_2_5__*`;
2. maps repaired OpenHermes nested shard paths to stable selected task names
   such as `dfm8-openhermes-en__data__train-00000.jsonl.gz`;
3. rebuilds `data/tokenized_dfm8`, `data/sampled_dfm8`, and
   `data/sampled_dfm8_post`; and
4. reruns the distribution report.

Raw OpenHermes removal and repaired-only DFM8 rebuild, 2026-07-14.
Confidence: high from local script inspection, path scans, and successful
resampling. Raw `teknium/OpenHermes-2.5` / `openhermes_2_5` was removed from
the DFM8 pipeline entirely:

- `scripts/download_training_datasets.py` no longer contains a
  `teknium/OpenHermes-2.5` / `openhermes_2_5` dataset entry.
- `scripts/prepare_dfm8_data.sh` no longer calls the raw OpenHermes converter.
- `scripts/convert_dfm8_openhermes.py` was deleted.
- Raw local artifacts under `data/downloads/datasets/openhermes_2_5`,
  `data/dfm8_special_sources/openhermes_2_5`, and raw tokenized
  `dfm8_special_sources__openhermes_2_5__*` paths were removed.
- `scripts/build_dfm8_chat_source_tree.py` and
  `scripts/build_tokenized_dfm8_tree.py` no longer need raw-OpenHermes-specific
  exclusion rules.
- The corrected `data/tokenized_dfm8` contains only repaired OpenHermes shards
  named `dfm8-openhermes-en__data__train-*.jsonl.gz` and
  `dfm8-openhermes-da__data__train-*.jsonl.gz`.

The corrected DFM8 and DFM8-post samples were rebuilt after this cleanup:

```bash
python scripts/build_dfm8_chat_source_tree.py --force --new-only
python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
python scripts/report_dfm8_mix.py
rm -rf data/sampled_dfm8 data/sampled_dfm8_post data/tokenized_dfm8_post
(cd data_io && python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm8 \
  output_path=../data/sampled_dfm8 \
  epochs=6 \
  concat_workers=4 \
  prefix_config_path=prefix_config_dfm8.yaml \
  > ../data/show_analytics_dfm8.md)
DFM8_POST_EPOCHS=9 bash scripts/prepare_dfm8_post_data.sh
```

Corrected per-epoch totals from `metadata.json` and `show_analytics` reports:

| Sample | Sampled epochs | Tokens per epoch |
| --- | ---: | ---: |
| DFM7 | 5 | 66.657B |
| DFM8 | 6 | 68.613B |
| DFM8-post | 9 | 28.642B |

Approximate coarse per-epoch buckets:

| Bucket | DFM7 | DFM8 | DFM8-post |
| --- | ---: | ---: | ---: |
| Danish | 16.812B | 18.081B | 7.883B |
| English/general instruction | 14.400B | 15.072B | 3.560B |
| Math/code/reasoning | 16.944B | 16.958B | 4.201B |
| Tool/agentic | 9.624B | 9.624B | 11.648B |
| Synthetic/transforms | 3.498B | 3.498B | 0B by this coarse grouping |
| Other/legacy | 5.380B | 5.380B | 1.351B |

DFM8-specific additions and DFM8-post representation:

| Addition | DFM8 tokens/epoch | In DFM8-post? | DFM8-post tokens/epoch |
| --- | ---: | --- | ---: |
| `dfm8-openhermes-en` | 0.672B | yes | 0.672B |
| `dfm8-openhermes-da` | 0.922B | yes | 0.922B |
| `giannor_tv2r_instruction` (`dala_tv2r_it` + `gec_dala_tv2r_it`) | 0.261B | no | 0B |
| `kobprof_skolegpt_instruct` | 0.086B | yes, upweighted | 0.108B |

DFM8-post uses `data/tokenized_dfm8_post`, a filtered tokenized tree with
`4,166` linked tasks: `4,116` focus tasks and `50` broad-anchor tasks. Focus
families include repaired OpenHermes EN/DA, DFM8 behavior synthetic datasets,
native tool-use/agentic datasets, instruction-following datasets, Danish chat
and instruction datasets, and summarization/control datasets. Broad anchors
include math/code/general capability-preservation sources such as
`openmathinstruct2`, `allenai_rlvr_gsm`, `allenai_rlvr_math`, Tulu math/code,
Dolci no-tools/general SFT, Platypus, GSM8K, MATH, and WebInstruct.

DFM8 missed-dataset check, 2026-07-14. Confidence: high from local
`data/tokenized_dfm8`, `data/dfm8_chat_sources`, and
`export-upload-dfm8-synthetic` inspection. The repaired OpenHermes EN/DA,
giannor TV2R DaLA/GEC-DaLA, SkoleGPT, broad Common-Pile/DynaWord transform
expansion, and older `transformations-*` uploads are present in the current
DFM8 tokenized tree. Raw OpenHermes is not present, which is intentional.

The six targeted DFM8 synthetic datasets are still missing from the current
DFM8 tokenized/sample tree even though the plan says they should be included
and the upload-ready folders exist under `export-upload-dfm8-synthetic`:

| Missing planned family | Current `data/tokenized_dfm8` tasks | Current source tokens |
| --- | ---: | ---: |
| `dfm8-synthetic-code-debugging` | 0 | 0 |
| `dfm8-synthetic-constrained-format-following` | 0 | 0 |
| `dfm8-synthetic-danish-summarization-rewrite-controls` | 0 | 0 |
| `dfm8-synthetic-multiturn-danish-english-chat` | 0 | 0 |
| `dfm8-synthetic-native-tool-calling` | 0 | 0 |
| `dfm8-synthetic-strict-math-answer-contract` | 0 | 0 |

Likely cause: `scripts/build_dfm8_chat_source_tree.py` links
`export-upload-dfm8-openhermes-repaired`, `dfm8_transform_expansion_filtered`,
`dfm8_special_sources`, and `export-upload`, but not
`export-upload-dfm8-synthetic`. As a result the six synthetic families are not
tokenized or sampled, and their `data_io/prefix_config_dfm8_post.yaml` focus
prefixes cannot contribute to DFM8-post yet.

Next fix before using DFM8/DFM8-post for training: link
`export-upload-dfm8-synthetic` into `data/dfm8_chat_sources`, ensure
`scripts/build_tokenized_dfm8_tree.py` maps nested synthetic shard paths to
stable task names matching the existing `dfm8-synthetic-*__` sampler prefixes,
then rebuild `data/tokenized_dfm8`, `data/sampled_dfm8`,
`data/tokenized_dfm8_post`, and `data/sampled_dfm8_post`.

Supersedes the missed-dataset check above. DFM8 targeted synthetic integration
completed, 2026-07-14. Confidence: high from local rebuild, manifests,
symlink-aware task scans, and sampled metadata. The six
`dfm8-synthetic-*` upload folders are now fully integrated:

- `scripts/build_dfm8_chat_source_tree.py` links
  `export-upload-dfm8-synthetic`.
- `scripts/build_tokenized_dfm8_tree.py` maps nested
  `export-upload-dfm8-synthetic__dfm8-synthetic-*__data__train-*.jsonl.gz`
  tokenized paths to stable `dfm8-synthetic-*__data__train-*.jsonl.gz`
  task names.
- `scripts/tokenize_chat_template.py` now normalizes legacy synthetic tool-call
  rows of the shape `{"function": "search", "parameters": {...}}` into the
  Gemma4 template-compatible
  `{"function": {"name": "search", "arguments": {...}}}` shape. This was needed
  for one row in
  `dfm8-synthetic-multiturn-danish-english-chat/data/train-00002.jsonl.gz`.

Rebuild commands used from the repo root:

```bash
rm -rf data/dfm8_chat_sources data/tokenized_dfm8_jinja data/tokenized_dfm8 \
  data/sampled_dfm8 data/tokenized_dfm8_post data/sampled_dfm8_post
TOKENIZER_WORKERS=16 DFM8_EPOCHS=6 DFM8_CONCAT_WORKERS=4 \
  bash scripts/prepare_dfm8_data.sh

# After the first tokenization pass exposed the legacy tool-call row shape:
python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir data/tokenized_dfm8_jinja \
  --workers 16 \
  --skip-bad-json

python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
python scripts/report_dfm8_mix.py
rm -rf data/sampled_dfm8 data/tokenized_dfm8_post data/sampled_dfm8_post
(cd data_io && python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm8 \
  output_path=../data/sampled_dfm8 \
  epochs=6 \
  concat_workers=4 \
  prefix_config_path=prefix_config_dfm8.yaml \
  > ../data/show_analytics_dfm8.md)
DFM8_POST_EPOCHS=9 DFM8_POST_CONCAT_WORKERS=4 bash scripts/prepare_dfm8_post_data.sh
```

Final manifests:

- `data/tokenized_dfm8/union_manifest.json`: `10,651` inherited DFM7 tasks and
  `69` DFM8-selected task shards. The DFM8-selected count includes the `42`
  targeted synthetic shards.
- `data/tokenized_dfm8_post/union_manifest.json`: `4,208` linked tasks:
  `4,148` focus tasks and `60` broad-anchor tasks.
- Symlink-aware scans confirm all six `dfm8-synthetic-*` shard families are
  present in both `data/tokenized_dfm8` and `data/tokenized_dfm8_post`.
- A symlink-aware scan confirms raw `openhermes_2_5` remains absent from
  `data/tokenized_dfm8`.

Corrected per-epoch totals after targeted synthetic integration:

| Sample | Sampled epochs | Tokens per epoch |
| --- | ---: | ---: |
| DFM7 | 5 | 66.657B |
| DFM8 | 6 | 70.479B |
| DFM8-post | 9 | 34.336B |

Approximate coarse per-epoch buckets, using the same bucket policy as the
previous snapshot and placing the six targeted synthetic datasets under
`Synthetic/transforms`:

| Bucket | DFM7 | DFM8 | DFM8-post |
| --- | ---: | ---: | ---: |
| Danish | 16.812B | 18.081B | 7.883B |
| English/general instruction | 14.400B | 15.072B | 3.560B |
| Math/code/reasoning | 16.944B | 16.958B | 4.201B |
| Tool/agentic | 9.624B | 9.624B | 11.648B |
| Synthetic/transforms | 3.498B | 5.364B | 5.694B |
| Other/legacy | 5.380B | 5.380B | 1.351B |

DFM8-specific additions and DFM8-post representation:

| Addition | DFM8 tokens/epoch | In DFM8-post? | DFM8-post tokens/epoch |
| --- | ---: | --- | ---: |
| `dfm8-openhermes-en` | 0.672B | yes | 0.672B |
| `dfm8-openhermes-da` | 0.922B | yes | 0.922B |
| `giannor_tv2r_instruction` | 0.261B | no | 0B |
| `kobprof_skolegpt_instruct` | 0.086B | yes | 0.108B |
| `dfm8-synthetic-code-debugging` | 0.247B | yes | 0.493B |
| `dfm8-synthetic-constrained-format-following` | 0.171B | yes | 0.513B |
| `dfm8-synthetic-danish-summarization-rewrite-controls` | 0.396B | yes | 1.188B |
| `dfm8-synthetic-multiturn-danish-english-chat` | 0.366B | yes | 1.099B |
| `dfm8-synthetic-native-tool-calling` | 0.513B | yes | 2.052B |
| `dfm8-synthetic-strict-math-answer-contract` | 0.173B | yes | 0.347B |

## DFM8 One-Epoch Continuation From DFM6/DFM7 XL

Update, 2026-07-14. Confidence: high from local checkpoint metadata and
sampled-data metadata inspection.

The finished DFM6/DFM7 XL checkpoint to continue from is:

```text
checkpoints/dfm7/XL-gas2-from-dfm6-epoch3/checkpoint_state_epoch_5.json
```

Its exact resume state is:

```json
{
  "tag": "epoch_5",
  "step": 1229504,
  "epoch": 5,
  "batch_in_epoch": 0,
  "batch_in_epoch_exact": true
}
```

DFM8 has `70,479,308,606` sampled tokens per epoch. With
`global_batch_size=262144`, this is `268,857` optimizer steps per epoch by the
training loop's floor division. Training one DFM8 epoch on top of the finished
DFM6/DFM7 checkpoint should therefore start at step `1,229,504` and finish at
about step `1,498,361`.

Use `resume_checkpoint_tag=epoch_5` and `epochs=6`. The epoch-tag resume path
starts at `tag_epoch + 1`, so this trains only the sixth configured epoch, which
corresponds to DFM8 sampled epoch index `5`, and then writes `epoch_6` under the
DFM8 checkpoint path.

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm8 \
  arch/size@arch=XL \
  lr=3e-4 \
  lr_min_ratio=1 \
  lr_warmup_steps=2000 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=0.9999 \
  global_batch_size=262144 \
  gradient_accumulation_steps=2 \
  epochs=6 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  checkpoint_format=sharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=true \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=500 \
  checkpoint_path=checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5 \
  resume_checkpoint_path=checkpoints/dfm7/XL-gas2-from-dfm6-epoch3 \
  resume_checkpoint_tag=epoch_5 \
  resume_step=1229504 \
  resume_epoch=5 \
  reset_ema_on_resume=false \
  upcast_optimizer_state_on_resume=false \
  project_name=DFM5 \
  run_name="DFM8-XL clean full from DFM6-DFM7 epoch5" \
  wandb_run_id=dfm8-xl-from-dfm6-dfm7-epoch5-clean-full \
  wandb_resume=allow
```

## DFM8 L Resume On 2026-08-01

Update, 2026-08-01. Confidence: high from inspected checkpoint sidecars,
process state, and live training output.

The DFM8 XXL one-epoch scheduler campaign was stopped before switching models.
Its latest fully written checkpoint at the time of the stop was
`checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_151000`. The scheduler plan
`logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725` retains
its stop request and must not be resumed unintentionally.

The DFM8 L run was resumed from the complete sharded checkpoint
`checkpoints/dfm8/L-gbs131072/fsdp2_step_100000` in W&B run `g2oaotmc`
(`DFM5` / `DFM8-L-gbs131072`). Despite the historical `L-gbs131072` name,
both `all_config.yaml` and `checkpoint_state_step_100000.json` specify
`global_batch_size=262144` and `gradient_accumulation_steps=1`; these
authoritative values must be preserved on resume. The checkpoint sidecar gives
`step=100000`, `epoch=1`, and exact `batch_in_epoch=100000`.

The verified resume command is:

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm8 \
  arch/size@arch=L \
  lr=3e-4 \
  lr_min_ratio=1 \
  lr_warmup_steps=2000 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=0.9999 \
  global_batch_size=262144 \
  gradient_accumulation_steps=1 \
  epochs=1 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  checkpoint_format=sharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=true \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=1000 \
  checkpoint_path=checkpoints/dfm8/L-gbs131072 \
  resume_checkpoint_path=checkpoints/dfm8/L-gbs131072 \
  resume_checkpoint_tag=step_100000 \
  reset_ema_on_resume=false \
  upcast_optimizer_state_on_resume=false \
  project_name=DFM5 \
  run_name=DFM8-L-gbs131072 \
  wandb_run_id=g2oaotmc \
  wandb_resume=allow
```

The process was launched in tmux pane `%146` (currently window `hrm-0:4`) and
was verified advancing beyond step 100079 with all eight GPUs active. W&B had
already received history through step 100079 from an earlier attempt, so resumed
points at or below that tail were rejected as out of order; normal logging
resumed after the process passed that point.

Superseded later on 2026-08-01: the uninterrupted manual resume was stopped
after the complete `ephemeral_step_101000` checkpoint so that training and
evaluation could be orchestrated by one scheduler campaign. Its W&B history had
advanced to step 101366, so the scheduler-managed resume intentionally replays
steps 101001-101366 without logging duplicate W&B points.

## DFM8 L Alternating Training/Evaluation Campaign

Update, 2026-08-01. Confidence: high from the atomically generated plan,
dependency audit, live scheduler state, and GPU telemetry.

The active campaign is:

```text
logs/scheduler/dfm8_L_campaign_150k_epoch1_20260801
```

It resumes from `ephemeral_step_101000`, forces regular checkpoints and full
evaluations every 50K steps at 150K, 200K, and 250K, and then trains the final
short segment to the one-epoch endpoint at step 268857. Each evaluation graph
has 188 GPU rows spanning standard, DFM, 32-shard DFM IFEval-DA, and EuroEval
tasks. A terminal eval barrier and evaluator teardown precede each next training
segment, while merges, W&B synchronization, averages, and reports can finish
independently and therefore cannot unnecessarily hold the training GPUs.

Training segments and exact sources are:

| Segment | Resume source | Forced target |
| --- | --- | ---: |
| `101000 -> 150000` | `ephemeral_step_101000` | `step_150000` |
| `150000 -> 200000` | `step_150000` | `step_200000` |
| `200000 -> 250000` | `step_200000` | `step_250000` |
| `250000 -> 268857` | `step_250000` | `step_268857` |

The production eval configuration uses the previous successful DFM8 L vLLM
path: EuroEval-first ordering, standard/DFM/IFEval/EuroEval initial batches of
128/64/64/64, six total attempts, Gemma 4 native chat template, vLLM utilization
0.9, and 178000 MiB effective-free-memory gates. Judged tasks use
`unsloth/gemma-4-E4B-it`, batch/concurrency 32, and vLLM utilization 0.65.
Persistent vLLM leases are enabled.

The campaign can be recreated by
`scripts/setup_dfm8_l_campaign.sh`. Its live tmux layout is:

| Window | Name | Purpose |
| ---: | --- | --- |
| 4 | `training` | follows the current scheduler-managed training log |
| 5 | `scheduler` | campaign scheduler with persistent vLLM |
| 6 | `monitor` | Rich scheduler monitor at 30-second refresh |

The `training` window uses `scripts/follow_dfm8_l_training.sh`, which
automatically switches to the newest segment log. At campaign launch,
`campaign-train-150000` successfully claimed GPUs 0-7 and resumed the complete
101000 checkpoint.

Monitor update, 2026-08-01. Confidence: high from focused tests and the live
150K training segment. The scheduler monitor now parses `train_until_step`
tqdm output, displays `current_step/forced_target` and segment-relative percent,
and computes ETA from the latest reported `it/s` or `s/it` rate. This avoids the
previous `ETA unknown` and avoids incorrectly extrapolating from the full-epoch
tqdm denominator. The Rich monitor in `hrm-0:6` was restarted on the updated
code without interrupting scheduler or training processes.

Managed-judge stall and fix, 2026-08-02. Confidence: high from process/socket
inspection, server logs, and successful live retries. Two step-200000
`generative_talemaader` shards assigned to GPUs 6 and 7 stalled for about 3.6
hours because the old judge formula generated ports 65606 and 65700. Uvicorn
silently listened on wrapped ports 70 and 164, while the OpenAI client rejected
the advertised out-of-range URLs; both jobs therefore remained at zero samples
with idle GPUs. `eval_scheduler.runtime.managed_judge_port` now folds all
deterministic GPU/shard offsets into ports 20000-59999. A regression test checks
validity and uniqueness across eight GPUs and eight shards. The scheduler was
stopped cleanly, the two malformed attempts were terminated, all persistent
servers were released, and only those two rows retried at valid ports 45606 and
45700. The retries immediately produced judge requests and active GPU load.

Tmux recovery note, 2026-08-02. Confidence: high from live tmux/process
inspection. When the old scheduler window exited during the managed-judge
restart, tmux renumbered window 6 to 5; respawning target 5 then replaced the
monitor while leaving the scheduler alive under the stale `monitor` name. The
layout was restored without interrupting training: `hrm-0:5` is the active
`scheduler`, and a fresh Rich `monitor` runs in `hrm-0:6`.

## DFM8 L Second-Epoch Campaign

Update, 2026-08-03. Confidence: high from the completed `epoch_1` checkpoint,
its sidecar, the prior campaign log, and the live second-epoch scheduler.

The earlier predicted first-epoch endpoint of step 268857 is superseded. The
data loader actually exhausted `epoch_0` after step 268650 and wrote the
complete regular checkpoint `fsdp2_epoch_1` at global step **268651**. Its
sidecar records `epoch=1`, exact `batch_in_epoch=0`, global batch 262144, and
all eight carry shards are present. The old campaign's sole failed row,
`campaign-train-268857`, was therefore a checkpoint-name verification failure
after successful completion, not a training failure.

The second epoch is managed by:

```text
logs/scheduler/dfm8_L_campaign_epoch2_20260803
```

It resumes `checkpoints/dfm8/L-gbs131072/fsdp2_epoch_1`, keeps the existing
W&B run `DFM5/g2oaotmc`, and evaluates complete EMA checkpoints at 300K, 350K,
400K, 450K, and 500K. The final scheduler target is the conservative
metadata-derived upper estimate 537714. This does not assert that epoch 2 has
exactly that many steps: the training loop naturally stops and writes
`fsdp2_epoch_2` when sampled `epoch_1` is exhausted. The actual second-epoch
boundary must be taken from that checkpoint sidecar after completion.
Evaluation epochs currently use `global_step / 268651`, anchored to the
observed first-epoch boundary. The full evaluation
configuration remains the one documented above: standard, DFM, 32-shard
IFEval-DA, and EuroEval; EuroEval-first ordering; persistent vLLM; Gemma 4
native chat template; and the established separate judge configuration.

The reproducible plan builder is
`scripts/setup_dfm8_l_epoch2_campaign.sh`. Live tmux windows are
`hrm-0:4` (`training`), `hrm-0:5` (`scheduler`), and `hrm-0:6` (`monitor`).
The training-log follower now searches both the first- and second-epoch log
roots.
