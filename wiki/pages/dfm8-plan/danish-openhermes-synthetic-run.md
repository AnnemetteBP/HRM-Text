---
type: Plan Record
title: Danish OpenHermes Synthetic Run
description: 'Part of DFM8 Plan: Danish OpenHermes Synthetic Run.'
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
# Danish OpenHermes Synthetic Run

Part of [DFM8 Plan](/pages/dfm8-plan.md).

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
