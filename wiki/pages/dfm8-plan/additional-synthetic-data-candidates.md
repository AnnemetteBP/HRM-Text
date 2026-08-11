---
type: Plan Record
title: Additional Synthetic Data Candidates
description: 'Part of DFM8 Plan: Additional Synthetic Data Candidates.'
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
# Additional Synthetic Data Candidates

Part of [DFM8 Plan](/pages/dfm8-plan.md).

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
