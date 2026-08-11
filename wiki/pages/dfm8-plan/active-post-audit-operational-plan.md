---
type: Plan Record
title: Active Post-Audit Operational Plan
description: 'Part of DFM8 Plan: Active Post-Audit Operational Plan.'
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
# Active Post-Audit Operational Plan

Part of [DFM8 Plan](/pages/dfm8-plan.md).

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
