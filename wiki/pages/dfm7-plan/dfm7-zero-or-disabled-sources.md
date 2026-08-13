---
type: Plan Record
title: DFM7 Zero Or Disabled Sources
description: 'Part of DFM7 Plan: DFM7 Zero Or Disabled Sources.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# DFM7 Zero Or Disabled Sources

Part of [DFM7 Plan](/pages/dfm7-plan.md).

DFM7 source check for six questioned datasets, 2026-06-30. Confidence: high
from local inspection of `data_io/prefix_config_dfm7.yaml`, downloaded source
schemas, and tokenized `tokens.npy` / `inst_len.npy` arrays. Superseded
2026-06-30 by the corrected conversion and sampling run below.

Current status in `data/tokenized_dfm7`:

| Source | Tokenized examples | Tokenized tokens | Current sampled contribution | Reason |
| --- | ---: | ---: | --- | --- |
| `danish_wildchat4_8m` | 0 | 0 | 0 | Source rows contain `first_user_message` and `translated_first_user_message`, not assistant responses. The chat SFT tokenizer emits no supervised examples. |
| `ai_arena_udtraek` | 0 | 0 | 0 | Source rows contain `conversation_a` / `conversation_b` branches. The generic tokenizer does not yet adapt those branch columns into `messages`, so no examples are emitted. |
| `allenai_rlvr_gsm` | 0 | 0 | 0 | Source rows contain one user `messages` entry plus `ground_truth`; there is no assistant message. Needs a converter from final question + `ground_truth` to a supervised answer. |
| `allenai_rlvr_math` | 0 | 0 | 0 | Same one-message + `ground_truth` schema issue as RLVR GSM. Needs a boxed-final-answer converter. |
| `nemotron_swe` | 2,872,238 | 85,460,456,586 | 0 | Tokenized successfully, but `data_io/prefix_config_dfm7.yaml` sets `max_per_file: 0`. |
| `synquid_wildchat_100k_qwen_messages` | 129,688 | 204,013,378 | 0 | Tokenized successfully, but `data_io/prefix_config_dfm7.yaml` sets `max_per_file: 0`, likely because broader WildChat was intended to replace it. |

Superseded implication:

- The current DFM7 sample does not include any of these six sources.
- `nemotron_swe` and `synquid_wildchat_100k_qwen_messages` can be included by
  changing the sampling config and resampling, subject to caps.
- `danish_wildchat4_8m`, `ai_arena_udtraek`, and the two RLVR sources need
  source-specific conversion/adapters before resampling; simply changing repeat
  is not sufficient.

Corrected DFM7 source status, 2026-06-30. Confidence: high from local
conversion/tokenization/sample output.

- `danish_wildchat4_8m` remains excluded. It contains first-user-message style
  rows without assistant targets and is not useful as supervised SFT without
  additional generation.
- `nemotron_swe` remains excluded and is also excluded from the tokenized union
  builder so it cannot be inherited accidentally from `data/tokenized_dfm6`.
  The current reason is practical context/length risk and excessive source
  size for the intended DFM7 mix.
- `ai_arena_udtraek` is now adapted by
  `scripts/prepare_dfm7_special_sources.py`: it extracts branch conversations
  from `conversation_a` and `conversation_b`, preserving system/user/assistant
  chat turns. The corrected tokenized union contains 4,569 supervised examples
  and 6,370,820 tokens.
- `allenai_rlvr_gsm` and `allenai_rlvr_math` are now converted from one-message
  + `ground_truth` rows into supervised instruction/response rows with boxed
  final answers. The corrected tokenized union contains 7,473 / 7,498 examples
  and 682,485 / 806,707 tokens respectively.
- `synquid_wildchat_100k_qwen_messages` is now included in full rather than
  capped at 50K rows. The corrected tokenized union contains 129,688 examples
  and 204,013,378 tokens.
  or cap values will not add useful supervised tokens.

Recommended fixes:

1. Convert `allenai_rlvr_gsm` and `allenai_rlvr_math` into two-message math
   examples with explicit answer contracts. Prefer boxed final answers for the
   dominant freeform math style.
2. Convert `ai_arena_udtraek` by extracting assistant turns from both
   `conversation_a` and `conversation_b`, preserving preceding history and
   skipping prompt-only rows.
3. Treat `danish_wildchat4_8m` as translation / prompt-seed data, not direct
   chat SFT. It can become translation examples
   `first_user_message -> translated_first_user_message`, but it does not
   contain assistant answers to the translated user requests.
4. Re-enable `synquid_wildchat_100k_qwen_messages` if we want immediate
   WildChat-style contribution while the 4.8M Danish WildChat adapter is still
   unresolved.
5. Include `nemotron_swe` only with a deliberate cap; the available tokenized
   pool is very large and would dominate if uncapped.

Conversion update, 2026-06-30. Confidence: high from local script execution and
tokenized array inspection.

Applied decisions:

- `danish_wildchat4_8m` is excluded from DFM7. It is no longer linked by
  `scripts/build_dfm7_chat_source_tree.py`, is no longer selected by
  `scripts/build_tokenized_dfm7_tree.py`, and has `max_per_file: 0` in
  `data_io/prefix_config_dfm7.yaml` as a guard against stale tokenized outputs.
- `ai_arena_udtraek` is converted by
  `scripts/prepare_dfm7_special_sources.py` into normal `messages` JSONL,
  extracting both `conversation_a` and `conversation_b` branches and preserving
  assistant turns with their preceding history. The converter wrote `2,997`
  branch rows; tokenization yielded `4,569` supervised assistant-turn examples
  and `6,370,820` tokens in the DFM7 union.
- `allenai_rlvr_gsm` is converted from one-message prompt + `ground_truth` rows
  into direct boxed-answer math examples. The converter wrote and tokenized
  `7,473` examples, `682,485` tokens.
- `allenai_rlvr_math` is converted the same way, yielding `7,498` examples,
  `806,707` tokens.
- `nemotron_swe` remains excluded with `max_per_file: 0`. The DFM6 sampling
  notes found the huge SWE artifact unsuitable under the current 4k context
  PrefixLM truncation rule; revisit only through a dedicated windowing or
  conversion path.
- `synquid_wildchat_100k_qwen_messages` is restored to the DFM5/DFM6 policy of
  `max_per_file: 50000`, because the broader `danish_wildchat4_8m` replacement
  is now excluded.

Operational note:

- Superseded 2026-07-01: the DFM7 tokenized union was rebuilt after these
  changes, then fully resampled into the canonical `data/sampled_dfm7` path.
  Do not use `reuse_tokens=true` for future updates that change the tokenized
  union, because the concatenated `tokens.npy` backing file changes shape.

Verified safe resample pattern:

```bash
cd /work/dfm/HRM-Text/data_io
python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm7 \
  output_path=../data/sampled_dfm7_rebuild_tmp \
  epochs=5 \
  concat_workers=4 \
  prefix_config_path=prefix_config_dfm7.yaml \
  > ../data/show_analytics_dfm7_rebuild_tmp.md
```

After validating `../data/sampled_dfm7_rebuild_tmp/metadata.json`, the rebuild
was moved into `data/sampled_dfm7` and `config/data/dfm7.yaml` was kept pointed
at the canonical path.
