---
type: Policy Record
title: DFM2 Raw-Text Task Mix
description: 'Part of Data Mix Policy: DFM2 Raw-Text Task Mix.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# DFM2 Raw-Text Task Mix

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Decision recorded on 2026-05-30. Confidence: high for the target policy and
verified local DFM2 sample outputs.

Superseded clarification, 2026-05-30: `X` is not the entire current DFM
direct/instruction-style corpus. In this context, `X` is the existing
approximately `2.8B` DynaWord direct/continuation-token slice per epoch. Keep
that existing direct slice and add `5X` additional raw-text-derived task tokens.

DFM2 should keep the current DynaWord direct/continuation token budget as `X`,
then add raw-text-derived objectives with the following covered-token budgets:

- `X` existing direct/continuation tokens, preserving the current DynaWord
  plain-text signal.
- `X` continuation-task tokens where each example gives a non-trivial document
  prefix as instruction/context and trains the model to generate the suffix.
  The prefix should be randomly selected between `25%` and `75%` of the chunk.
- `X` denoising-task tokens where the instruction contains corrupted text and
  the response is the clean original text. Corruption should affect about
  `10%` of words, using a mix of word swaps, deletions, replacements, and
  random inserted words after selected words.
- `3X` autoregressive span-filling tokens. The instruction contains the full
  text with masked spans; the response rewrites the full clean text, filling in
  the masked spans.

Total DFM2 raw/plain-text-derived target size is therefore `6X` covered tokens
for the DynaWord-derived component if `X` is measured over sampled covered
tokens. With `X ~= 2.8B` per epoch, the new additions are about `14B` tokens per
epoch and the total DynaWord-derived component becomes about `16.8B` tokens per
epoch. The added `5X` part is split as `1X` prefix-continuation, `1X`
denoising, and `3X` span filling, with span filling intentionally dominating
the self-supervised additions.

Implemented and sampled locally on 2026-05-30:

- Generator: `scripts/generate_dfm2_dynaword_tasks.py`
- Sampling config: `data_io/prefix_config_dfm2.yaml`
- Training data config: `config/data/dfm2.yaml`
- Generated converted sources: `data/converted_sources_dfm2_dynaword_tasks`
- Generated tokenized sources: `data/tokenized_dfm2_dynaword_tasks`
- Tokenized union: `data/tokenized_dfm2`
- Sampled output: `data/sampled_dfm2`
- Analytics: `data/show_analytics_dfm2.md`

The final implementation avoids `repeat: 2` for generated DynaWord task
families because repeating can duplicate rows. Instead it creates two unique
prefix-continuation variants, two unique denoising variants, and six unique
span-fill variants. The generated tokenization was run with exactly one
tokenizer worker.

Verified DFM2 sampled totals:

- `metadata.total_length`: `42,317,252,803` tokens per epoch.
- Global unique tokens sampled: `71,801,166,164 / 95,130,241,400` across four
  epochs.
- Retained direct DynaWord slice: `11,255,771,693` covered tokens across four
  epochs, or `2,813,942,923` per epoch. This is `X`.
- Generated DynaWord task additions: `56,253,792,196` covered tokens across
  four epochs, or `14,063,448,049` per epoch. This is `4.998X`.

Measured generated additions by objective:

| Objective family | Covered tokens / epoch |
|---|---:|
| Prefix continuation v1 | `1,320,302,625` |
| Prefix continuation v2 | `1,320,302,124` |
| Denoising v1 | `1,456,506,751` |
| Denoising v2 | `1,456,578,755` |
| Span fill v1 | `1,418,307,269` |
| Span fill v2 | `1,418,288,911` |
| Span fill v3 | `1,418,277,059` |
| Span fill v4 | `1,418,307,269` |
| Span fill v5 | `1,418,305,179` |
| Span fill v6 | `1,418,272,107` |
