---
type: Experiment Record
title: LexDK Prefix-Extraction Probe
description: Verbatim continuation extraction test against original LexDK source prefixes using the DFM8 XL 1.65M EMA HF export.
tags: [data, privacy, memorization, lexdk, evaluation]
status: stable
last_updated: 2026-08-15
confidence: high
part_of: /pages/data-mix-policy.md
---
# LexDK Prefix-Extraction Probe

## Scope

On 2026-08-15, `exports/dfm8_XL_step1650000_ema_hf` was tested for
extractable verbatim continuation of LexDK articles. The probe reads only the
original archive:

```text
data/downloads/datasets/lexdk/lexdk_articles.jsonl.gz
```

It does not read `data/converted_sources/lexdk/lexdk_articles.parquet`, use the
converted title/source instruction, or depend on converted row order. Prefixes
and 64-token reference continuations are tokenized directly from each original
row's `text` field with the checkpoint's exported tokenizer.

Two greedy decoding modes were measured:

- `raw`: `<bos>` followed directly by the original source prefix.
- `assistant_prefill`: the same source prefix is prefilled as the beginning of
  the assistant response after a neutral Gemma 4 chat request to continue the
  text verbatim. This respects the model's chat contract without revealing the
  converted LexDK instruction.

The final exhaustive run tested every non-empty original row that had enough
tokens for the selected prefix plus the 64-token reference. Prefix lengths were
`4`, `8`, `16`, `32`, `64`, `128`, and `256`. There are `108,718` archive rows,
of which `108,711` contain text. Eligibility decreases from `90,409` rows at
prefix 4 to `41,333` at prefix 256. Both modes together produced `1,058,010`
greedy generations, with normal EOS stopping and a maximum of 64 generated
tokens.

## Exhaustive Result

| Mode | Prefix | Eligible | Exact 64 | Mean LCP | P95 | P99 | P99.9 | Max | At least 20 | At least 50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chat prefill | 4 | 90,409 | 0 | 0.39 | 2 | 4 | 7 | 18 | 0 | 0 |
| chat prefill | 8 | 89,594 | 0 | 0.81 | 4 | 5 | 8 | 17 | 0 | 0 |
| chat prefill | 16 | 87,873 | 0 | 1.00 | 4 | 6 | 10 | 18 | 0 | 0 |
| chat prefill | 32 | 84,155 | 0 | 1.19 | 4 | 7 | 11 | 28 | 6 | 0 |
| chat prefill | 64 | 76,092 | 0 | 1.24 | 5 | 7 | 14 | 39 | 42 | 0 |
| chat prefill | 128 | 59,549 | 0 | 1.32 | 5 | 8 | 16 | 35 | 18 | 0 |
| chat prefill | 256 | 41,333 | 0 | 1.38 | 5 | 8.7 | 25 | 40 | 61 | 0 |
| raw | 4 | 90,409 | 0 | 0.22 | 1 | 3 | 5 | 11 | 0 | 0 |
| raw | 8 | 89,594 | 0 | 0.47 | 2 | 4 | 7 | 14 | 0 | 0 |
| raw | 16 | 87,873 | 0 | 0.59 | 3 | 5 | 9 | 16 | 0 | 0 |
| raw | 32 | 84,155 | 0 | 0.97 | 4 | 7 | 13 | 30 | 6 | 0 |
| raw | 64 | 76,092 | 0 | 1.20 | 4 | 7 | 16 | 39 | 57 | 0 |
| raw | 128 | 59,549 | 0 | 1.33 | 5 | 8 | 16 | 55 | 37 | 1 |
| raw | 256 | 41,333 | 0 | 1.37 | 5 | 9 | 22 | 40 | 50 | 0 |

No 64-token target was extracted. One generation matched 55 tokens: a raw
128-token prefix of `Napiers formler`, where the reference and generation
continued the same displayed trigonometric formula before selecting different
terms in the next formula. Across both modes, 277 generations matched at least
20 tokens, but these represent only 158 source rows and 90 distinct 20-token
reference prefixes. `175/277` have `København` in their title and predominantly
reuse listed-building boilerplate. The high-tail counts are therefore not 277
independent memorization events. The exhaustive result supports limited partial
recall of formulaic, duplicated, or mathematically constrained text, but finds
no complete 64-token extraction under this protocol.

## Superseded Pilot

The earlier 1,000-row-per-prefix pilot reported a maximum LCP of 31 and no
50-token match. That conclusion is superseded by the exhaustive run above,
which found the single 55-token mathematical-formula continuation.

## Reproduction

```bash
cd /work/dfm/HRM-Text
export PATH=/home/ucloud/miniforge3/envs/hrm-cu132/bin:$PATH
export CUDA_HOME=/home/ucloud/miniforge3/envs/hrm-cu132
bash scripts/run_lexdk_prefix_extraction_exhaustive.sh
```

The reusable implementation is
[`scripts/eval_lexdk_prefix_extraction.py`](/../scripts/eval_lexdk_prefix_extraction.py).
The merger is
[`scripts/merge_lexdk_prefix_extraction.py`](/../scripts/merge_lexdk_prefix_extraction.py).
Detailed outputs are local under
`logs/analysis/lexdk_prefix_extraction_step1650000_exhaustive/`, with final
statistics and outliers under `merged/`.
The script explicitly uses vLLM's native greedy sampler because the optional
FlashInfer sampler attempted to JIT against unavailable `curand.h`; model
attention remains on FlashAttention.
