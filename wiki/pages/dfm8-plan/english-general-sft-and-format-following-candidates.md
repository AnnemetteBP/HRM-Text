---
type: Plan Record
title: English General SFT And Format-Following Candidates
description: 'Part of DFM8 Plan: English General SFT And Format-Following Candidates.'
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
# English General SFT And Format-Following Candidates

Part of [DFM8 Plan](/pages/dfm8-plan.md).

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
