# DFM9 Agreement and Article-3 Memorisation Probe

Status: completed engineering evidence for legal/human review; not a legal
determination that any output is or is not copyright infringement. Run date:
2026-08-18.

## Protocol

The probe used the DFM8 XL 1.65M EMA Hugging Face export, a 64-token prefix
from the original or earliest retained source-side text, and at most 64 greedily
decoded tokens. Every text was tested twice:

- `raw`: bare causal continuation after BOS;
- `assistant_prefill`: the same prefix placed after a neutral Gemma 4 chat
  instruction to continue the text verbatim in its original language.

Texts shorter than 128 exported-tokenizer tokens were counted as ineligible.
Selection used deterministic content hashes, deduplicated globally across the
two categories. Large cohorts contribute 10,000 eligible unique texts; smaller
cohorts are exhaustive over all locally available eligible unique texts. The
prepared sample contains 65,504 texts and 131,008 model requests.

The complete local evidence is under
`logs/analysis/dfm9_memorisation_categories_ab_step1650000/`, including the
preparation inventory, compressed row-level results, JSON summary, 100 longest
matches, and generated Markdown report.

## Coverage

| Category/cohort | Eligible texts tested | Coverage |
|---|---:|---|
| A-01 Lex.dk | 10,000 | Deterministic sample |
| A-02 DBC abstracts | 10,000 | Deterministic sample from 11,663,987 source rows |
| A-03 DBC reviews | 10,000 | Deterministic sample |
| A-04 Faktalink | 514 | All eligible locally available articles |
| A-05 Forfatterweb | 1,180 | All eligible locally available articles |
| A-06 Danskerhverv | 281 | All eligible agreement rows |
| A-06 DK Medier | 465 | All eligible agreement rows |
| A-06 Odense | 325 | All eligible agreement rows |
| **Category A total** | **32,765** | Stratified |
| B-01 RLVE source-problem proxies | 10,000 | Deterministic sample |
| B-02 LongAlign documents | 9,888 | All locally available documents |
| B-03 EuroBlocks embedded documents | 2,602 | All eligible unique embedded documents |
| B-04 EuroBlocks unavailable-seed proxies | 249 | All eligible retained proxies; canonical seeds remain unavailable |
| B-05 Tasksource residual | 10,000 | Deterministic sample across the 84 retained files |
| **Category B total** | **32,739** | Stratified |

## Results

| Category | Mode | N | Exact 64 | Unique sources >=20 | Unique sources >=50 | P99 LCP | Max LCP |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Chat prefill | 32,765 | 0 | jointly 15 across modes | jointly 0 | 6 | 38 |
| A | Raw | 32,765 | 0 | jointly 15 across modes | jointly 0 | 6 | 38 |
| B | Chat prefill | 32,739 | 7 | jointly 65 across modes | jointly 13 | 9 | 64 |
| B | Raw | 32,739 | 7 | jointly 65 across modes | jointly 13 | 9 | 64 |

Category A produced no exact 64-token continuation and no 50-token match. Its
15 unique 20-token-or-longer tails are dominated by duplicated Lex.dk building
descriptions: the same Copenhagen development/fire passages occur in multiple
listed-building articles. One DBC abstract reached exactly 20 matching tokens.
This is limited partial recall of repeated source prose, not full extraction
under the chosen threshold. With zero successes in 32,765 trials per mode, the
simple rule-of-three upper bound within this stratified sample is approximately
0.0092% per mode; it is not a population-weighted corpus estimate.

Category B produced seven unique exact continuations, each reproduced in both
modes. Manual inspection classified them as:

| Pattern | Unique exact sources | Assessment |
|---|---:|---|
| Runs of blank/whitespace tokens | 2 | Formatting artefact; no expressive text |
| Sequential table-of-contents chapter labels | 2 | Mechanically predictable structure |
| Repeated digit sequence | 1 | Degenerate low-entropy continuation |
| Sequential legal-section identifiers | 1 | Mechanically predictable numbering |
| RLVE all-ones grid | 1 | Degenerate synthetic/functional structure |

Thus the operational exact-extraction rate is 7/32,739 = 0.0214% per mode,
but no reviewed exact match contains a 64-token expressive-prose continuation.
The other >=50-token tails are likewise dominated by whitespace, tables of
contents, repeated characters, grids, and numbered structures. Raw and chat
results are very similar, which argues against the observed tail being caused
by one prompt wrapper.

## Reuse in an exhaustive run

Every result carries a stable request key over protocol, model path, content
hash, and mode. Shard files are published atomically. An exhaustive preparation
can retain only the remaining texts:

```bash
python scripts/eval_memorisation_categories.py prepare-exhaustive \
  --categories A,B \
  --output-dir logs/analysis/dfm9_memorisation_categories_ab_step1650000 \
  --exclude-prepared logs/analysis/dfm9_memorisation_categories_ab_step1650000/prepared.jsonl.gz
```

Run its shards with
`--prepared-file prepared_exhaustive_remaining.jsonl.gz`,
`--skip-results logs/analysis/dfm9_memorisation_categories_ab_step1650000`, and
`--result-prefix results_exhaustive`. The existing 131,008 generations will be
excluded rather than recomputed; the normal `merge` command then combines the
sample and exhaustive shard files.

## Limitations

- This is a held-in prefix attack, not a membership-inference control study.
- Greedy 64-token continuation tests one extraction surface and does not rule
  out extraction under longer prefixes, sampling, prompt search, or repeated
  adaptive attempts.
- Large A-01/A-02/A-03, B-01, and B-05 cohorts are samples, not exhaustive.
- B-04 tests retained generated proxies because the original EuroBlocks seeds
  are unavailable; it cannot answer extraction from those missing seeds.
- Long matches require source-level adjudication because predictability and
  duplicated text can mimic memorisation.
