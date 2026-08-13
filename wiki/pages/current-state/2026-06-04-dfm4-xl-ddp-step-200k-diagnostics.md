---
type: Operational Record
title: 2026-06-04 DFM4 XL-DDP Step 200K Diagnostics
description: 'Part of Current State: 2026-06-04 DFM4 XL-DDP Step 200K Diagnostics.'
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
# 2026-06-04 DFM4 XL-DDP Step 200K Diagnostics

Part of [Current State](/pages/current-state.md).

- Binary-choice option-order diagnostics were run for `checkpoints/dfm4/XL-ddp`
  `step_200000` using both raw non-EMA and EMA weights. Confidence: high. The
  command was:

```bash
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python scripts/diagnose_binary_choice_priors.py
```

  The report was written to
  `logs/eval/dfm4_XL_ddp_binary_choice_order_200k.json`. The diagnostic shows
  that BoolQ and PIQA scores at this checkpoint are strongly affected by answer
  letter/order priors rather than content understanding. For PIQA, flipping the
  options changes EMA accuracy from `0.1481` to `0.7963`; randomizing options
  brings it back near chance at `0.4167`. For BoolQ, non-EMA moves from a
  strong `A` prior on the original prompt to a strong `B` prior when the fixed
  option order is flipped, while EMA is dominated by a `B` prior in the flipped
  and randomized variants.
- IFEval-DA generation examples for `step_200000` were extracted from local
  Inspect `.eval` archives and summarized in
  `logs/eval/dfm4_XL_ddp_ifeval_da_generations_200k.md`. Confidence: high.
  In shard `0`, non-EMA has `2/17` strict passes, `1/17` loose-only pass, and
  `14/17` loose failures; EMA has `4/17` strict passes and `13/17` loose
  failures. The completions are usually readable Danish/English but often fail
  exact instruction constraints through repetition, missing length/format
  requirements, or shallow keyword/end-string compliance.
- Original+Mixed L CP4 was compared against DFM4 XL-DDP `step_200000` using the
  same BoolQ/PIQA original/flipped/randomized option-order diagnostic. Confidence:
  high. The CP4 command was:

```bash
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python scripts/diagnose_binary_choice_priors.py \
  --ckpt-path checkpoints/original_plus_mixed_danish_instruction_rich/L \
  --ckpt-tag epoch_4 \
  --output logs/eval/original_plus_mixed_L_cp4_binary_choice_order.json
```

  The combined comparison report is
  `logs/eval/original_plus_mixed_cp4_vs_dfm4_200k_choice_ifeval_comparison.md`.
  Original+Mixed CP4 EMA is much more stable under option-order changes than
  DFM4 200K EMA: BoolQ is `0.8164/0.8125/0.8164` for
  original/flipped/randomized, and PIQA is `0.4907/0.5185/0.5370` with only
  `0.0093` invalid rate. DFM4 200K EMA has a strong `B` prior: BoolQ is
  `0.4062/0.6133/0.5117`, and PIQA swings from `0.1481` original to `0.7963`
  flipped. CP4 non-EMA BoolQ is stable, but CP4 non-EMA PIQA is not a clean
  comparison because about `60%` of PIQA outputs are invalid.
  Original+Mixed CP4 full IFEval-DA has `final_acc=0.3664` over `541` samples;
  its 17-sample lite shard has `final_acc=0.2588`, while DFM4 200K lite is
  `0.2069` no-EMA and `0.3176` EMA on the corresponding lite setup.
- Original+Mixed L CP1 was compared against DFM4 XL-DDP `step_200000` using
  only EMA weights for CP1, per the user request. Confidence: high. The CP1
  command was:

```bash
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python scripts/diagnose_binary_choice_priors.py \
  --ckpt-path checkpoints/original_plus_mixed_danish_instruction_rich/L \
  --ckpt-tag epoch_1 \
  --models ema \
  --output logs/eval/original_plus_mixed_L_cp1_ema_binary_choice_order.json
```

  The comparison report is
  `logs/eval/original_plus_mixed_cp1_ema_vs_dfm4_200k_choice_ifeval_comparison.md`.
  Original+Mixed CP1 EMA already has stable BoolQ behavior across
  original/flipped/randomized options (`0.7344/0.7422/0.7383`) with balanced
  randomized predictions. PIQA is not yet stable at CP1: it mostly predicts
  `B`, giving `0.1667` original, `0.7685` flipped, and `0.4259` randomized.
  This resembles DFM4 200K EMA for PIQA. The full CP1 IFEval-DA score is
  `final_acc=0.3186` over `541` samples, rising to `0.3664` by CP4; the
  17-sample lite CP1 shard is noisy and reports only `0.1833`.
- Lite-vs-full eval comparison was generated on 2026-06-04 for checkpoints
  where local merged JSONs contain both versions. Confidence: high for the
  file inventory and metric pairing, medium for interpreting sparse overlaps.
  The score-only report is
  `logs/eval/lite_vs_full_eval_comparison_scores_only.md`, with raw paired data
  in `logs/eval/lite_vs_full_eval_comparison_scores_only.json`; the unfiltered
  raw comparison is `logs/eval/lite_vs_full_eval_comparison.md/json`. The
  overlap is broad for `dfm_L` epochs `1..4` (`96` score metrics each), but
  sparse for `original_plus_mixed` (`3` IFEval-DA metrics for epochs `1..2`;
  plus MATH for epochs `3..4`). Score-only median absolute lite-full deltas:
  DFM L `epoch_1=0.0451`, `epoch_2=0.0750`, `epoch_3=0.1652`,
  `epoch_4=0.1679`; original+mixed `epoch_1=0.1352`, `epoch_2=0.1541`,
  `epoch_3=0.0679`, `epoch_4=0.0990`. Large systematic differences include
  DFM L lite underestimating GSM8K and MATH, overestimating many MMLU
  per-domain scores, and noisy IFEval-DA lite estimates from single 17-sample
  shards.
- English smoke generations were run on 2026-06-04 for original Sapient L
  reproduction CP4 at `checkpoints/original_sapient/L`, `epoch_4`, EMA weights.
  Confidence: high. The local JSON output is
  `logs/eval/original_sapient_L_epoch4_english_smoke_generations.json`. Command
  used `SimpleEngine`, `condition=direct`, `temperature=0.0`,
  `max_context=2048`, and `max_tokens=220`. The model produced coherent but
  often very terse completions for simple English prompts; a polite-email prompt
  degenerated into repeated meeting-request sentences when allowed a longer
  decode.
- A second English smoke run for the same original Sapient L CP4 checkpoint used
  longer prompts around a roughly 1000-character photosynthesis text. Confidence:
  high. Output is
  `logs/eval/original_sapient_L_epoch4_english_long_smoke_generations.json`.
  With `max_context=4096`, `max_tokens=360`, `temperature=0.0`, and
  `condition=direct`, the model mostly copied or extracted input sentences
  rather than performing requested transformations. It gave a one-sentence
  continuation and a useful facts extraction, but failed exact two-sentence
  summarization, past-tense rewriting, and child-friendly rewriting.
- The same 10 English smoke prompts were run on DFM4 XL-DDP `step_200000` with
  EMA weights. Confidence: high. Output is
  `logs/eval/dfm4_XL_ddp_step200k_ema_english_smoke_generations.json`.
  Compared with original Sapient L CP4, DFM4 200K EMA is more responsive on
  simple English summarization/explanation prompts and gives a more informative
  low-light continuation, but still fails exact transformation constraints:
  the two-sentence summary is too long, past-tense and child-friendly rewrites
  mostly copy the source text, and the five-facts extraction collapses to one
  unnumbered sentence.
- The five-prompt long English smoke probe was rerun on 2026-06-06 for DFM4
  XL-DDP `step_400000` no-EMA, DFM4 XL-DDP `step_400000` EMA, and DFM L CP4
  EMA, using the same prompt file, `SimpleEngine`, `condition=direct`,
  `temperature=0.0`, `max_context=4096`, `max_tokens=360`, and `batch_size=1`.
  Confidence: high. Outputs:
  - `logs/eval/dfm4_XL_ddp_step400k_noema_english_long_smoke_generations.json`
  - `logs/eval/dfm4_XL_ddp_step400k_ema_english_long_smoke_generations.json`
  - `logs/eval/dfm_L_epoch4_ema_english_long_smoke_generations.json`

  Qualitative result: DFM4 400K no-EMA and EMA both give short, relevant
  low-light continuations and pass the numbered-list format better than the
  original Sapient long smoke, but they still mostly copy the source text for
  past-tense and child-friendly rewrite prompts. DFM4 no-EMA partially changes
  tense in the past-tense prompt (`happened`, etc.) but leaves much of the
  source unchanged. DFM4 EMA is cleaner on the low-light continuation and
  numbered facts but is still mostly extractive/copying. DFM L CP4 EMA is the
  strongest of these long-smoke probes: it gives a correct exact two-sentence
  summary and a substantially better past-tense rewrite, but it still mostly
  copies the child-friendly rewrite prompt rather than simplifying it.
- A few-shot version of the same long English probe was added at
  `scripts/run_english_long_fewshot_probe.py` and run on 2026-06-06. The script
  prepends three task-matched prompt/response examples before each final target
  prompt, then calls `SimpleEngine` with the same generation settings as the
  zero-shot long probe. Confidence: high. Outputs:
  - `logs/eval/dfm4_XL_ddp_step400k_noema_english_long_fewshot_smoke_generations.json`
  - `logs/eval/dfm4_XL_ddp_step400k_ema_english_long_fewshot_smoke_generations.json`
  - `logs/eval/dfm_L_epoch4_ema_english_long_fewshot_smoke_generations.json`

  Qualitative result: the few-shot examples did not reliably fix the controlled
  transformation behavior. DFM4 400K no-EMA kept the low-light continuation
  short and made the numbered-list format explicit, but the summary/past-tense
  outputs introduced irrelevant herbicide/pesticide content and the
  child-friendly rewrite still mostly copied the source. DFM4 400K EMA became
  worse under this few-shot wrapper, mostly copying the source for the first
  four prompts. DFM L CP4 EMA remained the strongest on past-tense rewriting
  and low-light continuation, but the few-shot summary became too long and the
  child-friendly rewrite still mostly copied. Few-shot prompting alone is not a
  substitute for targeted post-training data on these transformations.
