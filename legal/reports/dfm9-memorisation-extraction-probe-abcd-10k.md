# DFM9 Memorisation Extraction Audit: 10K Cap

## Protocol

The DFM8 XL step-1,650,000 EMA HF export was tested on 2026-08-18 using
64-token source prefixes and up to 64 greedy continuation tokens. Each text
was tested as a raw causal continuation and with the Gemma-native assistant
prefill. Sampling was deterministic, content-hash based, and capped at
10,000 eligible unique texts per legal/source cohort. Texts shorter than 128
tokenizer tokens were excluded because they cannot provide both protocol
segments.

## Results

| Category | Mode | N | Exact 64 | >=10 | >=20 | >=50 | Mean LCP | P95 | P99 | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | raw | 32,765 | 0 | 69 | 15 | 0 | 0.91 | 4 | 6 | 38 |
| A | chat | 32,765 | 0 | 63 | 13 | 0 | 0.95 | 4 | 6 | 38 |
| B | raw | 32,739 | 7 | 301 | 52 | 12 | 1.04 | 4 | 9 | 64 |
| B | chat | 32,739 | 7 | 282 | 53 | 11 | 1.07 | 4 | 9 | 64 |
| C | raw | 137,620 | 11 | 1,370 | 148 | 13 | 1.08 | 4 | 9 | 64 |
| C | chat | 137,620 | 10 | 1,281 | 153 | 14 | 1.11 | 5 | 9 | 64 |
| D | raw | 76,386 | 11 | 812 | 140 | 14 | 1.13 | 5 | 10 | 64 |
| D | chat | 76,386 | 12 | 927 | 158 | 15 | 1.22 | 5 | 10 | 64 |

The 56 C/D rows with LCP >=50 represent 33 unique source texts because raw
and chat are duplicate protocol views. Twenty-seven unique texts are
low-severity structural/pathological matches: numeric sequences, repeated
strings, JSON/XML/CSV/table scaffolds, dates, indices, Sudoku layouts, and
repeated headlines. Six are medium-review generic code/math cases: C#/Java
code, route optimization, majority-element detection, die statistics, and
Fibonacci code. No high-severity expressive, personal, or source-specific
prose extraction was observed.

The raw evidence is retained in
`logs/analysis/dfm9_memorisation_categories_ab_step1650000/` and
`logs/analysis/dfm9_memorisation_categories_cd_step1650000/`.
