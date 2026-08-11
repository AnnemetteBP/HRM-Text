---
type: Operational Record
title: 2026-06-04 Post-Training Transformation Refine Dataset
description: 'Part of Current State: 2026-06-04 Post-Training Transformation Refine
  Dataset.'
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
# 2026-06-04 Post-Training Transformation Refine Dataset

Part of [Current State](/pages/current-state.md).

Confidence: high for local artifacts and command results; medium for downstream
effect until fine-tuning/eval.

A separate post-training dataset family was added for refining final
checkpoints on controlled transformations:

```text
config/data/posttrain_transform_refine.yaml
data_io/prefix_config_posttrain_transform_refine.yaml
scripts/prepare_posttrain_transform_refine.py
scripts/prepare_posttrain_transform_refine.sh
scripts/build_tokenized_posttrain_transform_refine_tree.py
```

Completed locally:

- Downloaded `grammarly/coedit`, `Muennighoff/natural-instructions`, and
  `facebook/asset` into `data/downloads/datasets/posttrain_*`.
- Converted `70,783` CoEdIT rows and `500,000` filtered Super-NI rows to
  `data/converted_sources_posttrain_transform_refine`.
- Created `500,000` synthetic request records under
  `data/synthetic_requests_posttrain_transform_refine`, split across five task
  families and Danish/English.
- Installed/configured Rust stable locally with `rustup default stable` because
  the shell had no Rust toolchain.
- Tokenized existing post-training rows to
  `data/tokenized_posttrain_transform_refine_existing`.
- Built `data/tokenized_posttrain_transform_refine`, linking `4,117` selected
  tokenized tasks.
- Sampled `data/sampled_posttrain_transform_refine` with `EPOCHS=1`; metadata
  reports `total_length=29,131,369,710` tokens.

Synthetic responses have not yet been generated. Later steps:

```bash
cd /work/dfm/HRM-Text
GEMMA_OPENAI_BASE_URL=http://127.0.0.1:8000/v1 \
GEMMA_TEACHER_MODEL=gemma-4-31b \
scripts/prepare_posttrain_transform_refine.sh generate-synthetic
scripts/prepare_posttrain_transform_refine.sh convert-synthetic
WORKERS=2 scripts/prepare_posttrain_transform_refine.sh tokenize-synthetic
scripts/prepare_posttrain_transform_refine.sh build-tokenized-tree
CONCAT_WORKERS=2 EPOCHS=1 scripts/prepare_posttrain_transform_refine.sh sample
```

While sampling, `data_io/sample_tokenized.py` was fixed to size its epoch buffer
by repeated sampled rows, not unique rows. This fixed the repeat-heavy
post-training config failure.

Teacher model selection, 2026-06-04. Confidence: high for local file
inspection.

The intended synthetic-data teacher is the local instruction-tuned Gemma 4 31B:

```text
GEMMA_MODEL_PATH=/work/dfm/brainsurgery/models/google/gemma-4-31B-it
```

Local inspection found both base and instruction-tuned 31B directories:

```text
/work/dfm/brainsurgery/models/gemma4_31b
/work/dfm/brainsurgery/models/google/gemma-4-31B
/work/dfm/brainsurgery/models/google/gemma-4-31B-it
```

`gemma4_31b` and `google/gemma-4-31B` have identical `config.json` files and
represent the base model. `google/gemma-4-31B-it` has a different config and
generation config, and is the better default for generating instruction-style
synthetic responses. Empty-looking alias dirs such as
`/work/dfm/brainsurgery/models/gemma4-31b` should not be used.

Synthetic generation launch update, 2026-06-04. Confidence: high for local
commands/logs; low-to-medium for output quality until prompts/validators are
fixed.

The 8x single-GPU vLLM generation run for `posttrain_transform_refine` required
several environment fixes:

- `deep-gemm==2.5.0+88965b0` was installed from a recursive local clone at
  `external/DeepGEMM` because the PyPI sdist lacked CUTLASS submodule files.
- A CUDA 13.2 shim was created at `external/cuda-13.2-shim` with `bin`,
  `include`, and `lib64` symlinks into the local CUDA toolkit layout. The build
  also needed CUDA 13 headers/libs from
  `/home/ucloud/miniforge3/envs/hrm/lib/python3.13/site-packages/nvidia/cu13`.
- vLLM 0.20.2 with FlashAttention 4 needed a local site-packages patch so
  `flash_attn.ops.triton.rotary` import failure falls back instead of crashing.
- The local Gemma 4 31B IT checkpoint has weights/tokenizer/config but no
  processor files. For text-only synthetic generation, vLLM must be launched
  with `--hf-overrides '{"architectures":["Gemma4ForCausalLM"]}'`.
- That text-only override exposes no chat template, so
  `scripts/prepare_posttrain_transform_refine.py generate-synthetic` was changed
  to call `/v1/completions` with an explicit prompt wrapper rather than
  `/v1/chat/completions`.
- `scripts/run_posttrain_synthetic_generation_vllm.sh` now exports `CUDA_HOME`,
  `DG_JIT_NVCC_COMPILER`, and `LD_LIBRARY_PATH` for DeepGEMM/vLLM, and its
  shard-claim loop retries after `mv` races so all workers can claim shards.

The active launch command in tmux session `posttrain_gen:runner` is:

```bash
cd /work/dfm/HRM-Text
env VLLM_PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python \
  CLIENT_PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python \
  GEMMA_MODEL_PATH=/work/dfm/brainsurgery/models/google/gemma-4-31B-it \
  SERVED_MODEL_NAME=posttrain-gemma-teacher \
  GPU_LIST=0,1,2,3,4,5,6,7 \
  REQUESTS_PER_SHARD=1000 \
  CLIENT_CONCURRENCY=8 \
  scripts/run_posttrain_synthetic_generation_vllm.sh
```

Observed live behavior at 22:26-22:28 CEST:

```text
Memory:      ~165,870 MiB / 183,359 MiB per B200
Utilization: ~96-100%, usually 100%
Power:       ~722-754 W in one snapshot
Throughput:  359 rows in 74 s ~= 4.85 rows/s globally, ~=0.61 rows/s/GPU
ETA:         500,000 rows / 4.85 rows/s ~= 28.6 h if this speed holds
```

Important quality warning: the first sampled completion output after switching
to `/v1/completions` was non-empty but degenerate (`"l l l ..."`) and passed
the current weak validators. Do not treat synthetic output from the old
text-only/completions run as usable.

Superseding update, 2026-06-04. Confidence: high. A fresh copy of
`google/gemma-4-31B-it` was downloaded inside this checkout and must be used
instead of the older incomplete local copy:

```text
/work/dfm/HRM-Text/data/models/google/gemma-4-31B-it-fresh-20260604
```

This fresh snapshot includes `chat_template.jinja` and `processor_config.json`.
Both `AutoTokenizer` and `AutoProcessor` load the Gemma 4 chat template locally.
The older `/work/dfm/brainsurgery/models/google/gemma-4-31B-it` copy lacked the
processor/template files and should not be used for instruction serving.

`scripts/prepare_posttrain_transform_refine.py generate-synthetic` now supports
`--endpoint chat|completions` and defaults to the chat endpoint. The vLLM runner
`scripts/run_posttrain_synthetic_generation_vllm.sh` now defaults to:

```text
CLIENT_CONCURRENCY=32
GENERATION_ENDPOINT=chat
```

The text-only `--hf-overrides '{"architectures":["Gemma4ForCausalLM"]}'`
workaround is now only used if `VLLM_FORCE_TEXT_ONLY=1` is explicitly set.

Fresh-model smoke tests through `/v1/chat/completions` on port `8100` produced
coherent Danish factual answers, exact English tense rewriting, and clean
summarization. Real synthetic-request smoke tests produced a valid five-item
English fact list and a coherent Danish paraphrase. The old bad partial queue
was reset: `500` shards are pending, `0` running, and stale generated JSONL
files from the text-only run were removed.

Current generation launch, 2026-06-04. Confidence: high for local command and
early outputs. The full 8-GPU generation run was relaunched in tmux session
`posttrain_gen:runner` with:

```bash
cd /work/dfm/HRM-Text
env VLLM_PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python \
  CLIENT_PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python \
  GEMMA_MODEL_PATH=/work/dfm/HRM-Text/data/models/google/gemma-4-31B-it-fresh-20260604 \
  SERVED_MODEL_NAME=posttrain-gemma-teacher \
  GPU_LIST=0,1,2,3,4,5,6,7 \
  REQUESTS_PER_SHARD=1000 \
  CLIENT_CONCURRENCY=32 \
  GENERATION_ENDPOINT=chat \
  scripts/run_posttrain_synthetic_generation_vllm.sh
```

All eight servers reached readiness and workers started on eight shards. Early
GPU behavior is about `165,840 MiB` used per GPU with `100%` utilization. Early
disk samples are coherent Danish child-friendly simplifications; they often use
natural prefaces such as `Her er...`, so stricter style would require prompt or
validator tightening rather than another serving-path change.

Superseding prompt update, 2026-06-04. Confidence: high. The synthetic request
generator was tightened before the final full run:

- Request variant is now `teacher_v2_strict_prompt_variants`.
- Each task/language record stores `prompt_template` and `task_prompt`.
- Four prompt-frame templates are used per language (`plain_text`,
  `instruction_passage`, `source_block`, `compact`) and are distributed roughly
  evenly across each task-language file.
- Task-specific strict output rules tell the teacher to return only the answer,
  avoid introductions, and respect exact sentence/list constraints.
- The chat system prompt now forbids meta-commentary, titles, markdown fences,
  and prefaces such as `Here is`, `Her er`, `Sure`, or `Of course`.
- The validator now rejects common preambles with `reject_reason=preamble`.

The strict v2 requests were rebuilt from scratch:

```bash
cd /work/dfm/HRM-Text
/home/ucloud/miniforge3/envs/hrm/bin/python scripts/prepare_posttrain_transform_refine.py make-synthetic-requests --force
/home/ucloud/miniforge3/envs/hrm/bin/python scripts/prepare_posttrain_transform_refine.py shard-synthetic-requests --force --requests-per-shard 1000
rm -f data/generated_posttrain_transform_refine/*.jsonl
```

The rebuilt queue contains `500` pending shards for `500,000` requests.

The full run was restarted in `posttrain_gen:runner` with the same fresh Gemma
4 31B IT model, chat endpoint, and `CLIENT_CONCURRENCY=32`. After startup, a
60-second active-generation window wrote `3,792` rows, or `63.2 rows/s`
globally. At that rate, the initial full-run ETA was about `2.18 h` for all
`500,000` rows. Early sampled strict-v2 outputs are cleaner: accepted rows no
longer include `Her er...` prefaces, and the observed rejected rows are rejected
for `preamble` as intended. Early acceptance snapshot: `6,211/6,503` rows
accepted (`95.5%`), with `292` preamble rejections.

Completion and quality probe, 2026-06-05. Confidence: high for local counts and
sample inspection. The strict-v2 synthetic generation completed all `500,000`
rows and all `500` shards. vLLM/generation processes were stopped afterward and
all GPUs were freed.

A deterministic three-example-per-dataset probe was written to:

```text
logs/posttrain_transform_refine_generation/quality_probe_20260605.md
```

Counts by task-language dataset:

```text
child_friendly_simplification_da: 47,771 accepted / 50,000
child_friendly_simplification_en: 49,997 accepted / 50,000
exact_sentence_summary_da:        49,384 accepted / 50,000
exact_sentence_summary_en:        49,389 accepted / 50,000
non_copy_rewrite_da:              49,988 accepted / 50,000
non_copy_rewrite_en:              49,994 accepted / 50,000
numbered_fact_extraction_da:      49,998 accepted / 50,000
numbered_fact_extraction_en:      50,000 accepted / 50,000
past_tense_rewrite_da:            49,924 accepted / 50,000
past_tense_rewrite_en:            49,924 accepted / 50,000
```

Quality decision from the probe:

- `include`: `child_friendly_simplification_da`,
  `child_friendly_simplification_en`, `exact_sentence_summary_da`,
  `exact_sentence_summary_en`, `non_copy_rewrite_da`, `non_copy_rewrite_en`,
  `numbered_fact_extraction_da`, `numbered_fact_extraction_en`,
  `past_tense_rewrite_en`.
- `exclude or regenerate`: `past_tense_rewrite_da`. The Danish instruction asks
  for Danish output, but many accepted rows preserve English source headers or
  English body text while only changing tense. Heuristics found
  `Executive Summary` in `46,949/49,924` accepted rows and English-heavy wording
  in `38,957/49,924` accepted rows. This is likely harmful for Danish
  instruction following unless regenerated with a clearer Danish translation
  objective or stronger language validation.

Root cause for `past_tense_rewrite_da`, 2026-06-05. Confidence: high from local
code inspection. `scripts/prepare_posttrain_transform_refine.py` builds one
shared `seed_texts` list from ASSET, `data/converted_sources/*`, and
`data/converted_sources_dfm4_summarization/*`, then passes the same source text
pool to both English and Danish request generation. The `language` field only
controls the prompt wording and requested answer language; it does not filter
source texts by language. This is acceptable for summarization/extraction and
for Danish simplification when the desired skill includes Danish explanation of
English content, but it is the wrong design for `past_tense_rewrite_da`: the
task should use Danish source texts if the intended skill is Danish tense
rewriting. Regenerate this dataset from Danish-only sources, or rename/change
the task to an explicit translate-and-rewrite operation and validate output
language.

Source-target revamp, 2026-06-05. Confidence: high from local file operations
and script output. The synthetic dataset naming scheme was changed from
`task_en` / `task_da` to `task_source_target`, e.g. `task_en_en`,
`task_en_da`, `task_da_da`, `task_da_en`.

Completed usable generated JSONL files were renamed:

- old `*_en__shard_*.jsonl` -> `*_en_en__shard_*.jsonl`
- old `*_da__shard_*.jsonl` -> `*_en_da__shard_*.jsonl`

The bad old `past_tense_rewrite_da` output was removed after renaming, so
`past_tense_rewrite_en_da` can be regenerated with explicit instructions:
translate the English source to Danish and rewrite in past tense. Current local
state:

```text
data/synthetic_requests_posttrain_transform_refine: 20 request files
data/generated_posttrain_transform_refine:          450 completed shard files
data/synthetic_request_shards_posttrain_transform_refine_v3_missing: 550 pending shards
```

`scripts/prepare_posttrain_transform_refine.py` now:

- stores `source_language`, `target_language`, and `language_pair` on new
  request records;
- defaults to all four pairs: `en:en`, `en:da`, `da:da`, `da:en`;
- has separate default English and Danish source roots;
- supports repeatable `--language-pair`, `--task`, and shard
  `--request-glob`;
- adds special cross-lingual past-tense prompts for `en:da` and `da:en`;
- rejects Danish past-tense outputs with obvious English leakage as
  `reject_reason=language_leak`.

Danish-source request files were generated from already converted Danish
sources, including `lexdk`, `danish_dynaword`, `laerebogen_with_followups`,
`synquid_wiki_instruct_da`, and selected Oliver Kinch Danish/BT sources. The
prepared missing queue covers:

```text
*_da_da.jsonl:                    5 tasks x 50 shards = 250 shards
*_da_en.jsonl:                    5 tasks x 50 shards = 250 shards
past_tense_rewrite_en_da.jsonl:   1 task  x 50 shards =  50 shards
total:                                                 550 shards / 550,000 rows
```

The launch script for the later GPU run is:

```bash
cd /work/dfm/HRM-Text
scripts/run_posttrain_transform_refine_v3_missing_generation.sh
```

That script uses the fresh Gemma 4 31B IT model, the chat endpoint,
`CLIENT_CONCURRENCY=32`, the new v3-missing shard root, and
`data/generated_posttrain_transform_refine` as the output directory.

The underlying vLLM runner was also hardened: servers are launched under
`setsid`, and cleanup now terminates the process group and escalates to
`SIGKILL` if needed. With `STOP_SERVERS_ON_EXIT=1`, vLLM servers should be
taken down automatically when generation finishes.

Self-judged generation option, 2026-06-05. Confidence: high from local code and
syntax checks; low-to-medium for final quality impact until a smoke run is
inspected. The generator can now ask the same OpenAI-compatible Gemma endpoint
to judge candidate outputs before accepting them:

```text
scripts/prepare_posttrain_transform_refine.py generate-synthetic --judge-quality --judge-retries 2
```

The judge prompt requires compact JSON and checks:

- declared source language is plausible for the source text;
- response language matches the target language;
- the task was solved;
- exact formatting/count constraints were followed.

If the judge reports a serious issue, the generator retries the response. If
all attempts fail, the row is written with `accepted=false`,
`reject_reason=judge_quality`, and a `judge_quality` JSON object containing the
complaint. This does not mutate the request/instruction itself; it regenerates
a replacement response for the same request during the attempt budget. If the
instruction itself is flawed, it remains rejected and should be replaced by
future request generation.

The generic vLLM runner supports:

```text
JUDGE_QUALITY=1
JUDGE_RETRIES=2
```

The prepared v3-missing launch helper defaults to `JUDGE_QUALITY=1` and
`JUDGE_RETRIES=2`. This will reduce throughput because each accepted candidate
requires an additional judge call, plus extra generation calls for judge
failures. Run a small smoke shard first if walltime matters.

Minor caveats:

- Danish child-friendly simplification has useful pedagogical responses but a
  higher preamble rejection rate (`2,229`) than the other datasets; accepted
  examples looked clean.
- Danish non-copy rewrite and numbered fact extraction looked useful in sampled
  examples, but a handful of accepted rows triggered English-heavy heuristics;
  consider adding a stricter Danish-language validator before final conversion.
- Exact two-sentence summaries mostly satisfy the intended format; rejected rows
  were primarily sentence-count failures.
