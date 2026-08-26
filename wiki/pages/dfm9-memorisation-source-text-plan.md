---
type: Plan
title: DFM9 Memorisation Source-Text Plan
description: Canonical source-text cohorts for extraction and memorisation testing, grouped by operative rights basis.
tags: [dfm9, legal, memorisation, datasets, evaluation]
status: draft
last_updated: 2026-08-20
confidence: high
---
# DFM9 Memorisation Source-Text Plan

The legal audit now has a deduplicated source-text test design in
`legal/reports/dfm9-memorisation-source-text-cohorts.md`. The design stores one
canonical copy of each original work or prompt and maps every translated,
reformatted, regenerated, mixed, and repeated training row back to it.

The four top-level groups are:

- **Agreement:** Lex.dk, four DBC text families, and three agreement-backed
  Instruct-BT subsets.
- **Article 3:** RLVE source problems, all LongAlign documents, EuroBlocks
  annealing seeds, and the 84-file Sapient Tasksource residual.
- **Article 4:** RACE, DREAM, WebQuestions, uncovered CoQA, four non-factual
  Sapient FLAN submixtures, shared FLAN-v2/SciRIFF material, and four uncovered
  OpenHermes families.
- **Other bases:** participant permission/publication, manual low-risk
  acceptances, direct/noncommercial licences, and direct code/math dataset
  terms. Each cohort records its condition.

Superseding scope decision (2026-08-18): this source-text exercise excludes
Common Pile, DynaWord, OPUS pairs, Wikipedia/Wikimedia, EUR-Lex, GovReport,
permissively filtered arXiv, Giannor/Oliverkinch/Synquid contributor-created
material, and genuinely from-scratch DFM8 material. Agreement-backed
Instruct-BT subsets remain under the agreement cohort.

Locally available originals, retained proxies, audit registers, and explicit
gaps are assembled without copying bulk data by
`scripts/assemble_dfm9_memorisation_sources.py` into
`data/legal/dfm9_memorisation_sources/`. The verified 2026-08-18 build has
4,017 artifact links (`A=26`, `B=95`, `C=3,784`, `D=112`), no broken links,
and 17 explicitly recorded source gaps. Deduplicated referenced-source sizes
are `A=2.343 GB`, `B=2.905 GB`, `C=90.357 GB`, and `D=148.667 GB` (244.272 GB
total); the symlink bundle itself does not duplicate these bytes.

## A/B Extraction Result

On 2026-08-18, the DFM8 XL 1.65M EMA export was tested with 64 source-prefix
tokens and 64 greedy continuation tokens in raw and Gemma-chat assistant-prefill
modes. The deterministic stratified run covered 32,765 Category-A and 32,739
Category-B unique eligible texts. Category A had no exact-64 or >=50-token
match. Category B had seven unique exact-64 sources in both modes, all manually
classified as whitespace, sequential tables of contents/legal identifiers,
repeated digits, or an all-ones synthetic grid rather than expressive prose.

The row-level evidence is in
`logs/analysis/dfm9_memorisation_categories_ab_step1650000/`; the review is in
`legal/reports/dfm9-memorisation-extraction-probe-ab.md`. Stable request keys,
atomic shards, `prepare-exhaustive`, and `--skip-results` make all 131,008
sample generations reusable in a later exhaustive run.

Original source text is preferred. Where it is unavailable, the earliest
retained prompt is marked as a proxy rather than being represented as the
original. A source hash and canonical source ID must deduplicate copies across
Sapient, Tulu, DOLCI, Apertus, OpenHermes, and DFM transformations.

The implementation manifest must record source path, normalized hash, legal
basis, licence/decision, descendant datasets, sampled exposure, test strata,
and original-versus-proxy status. Exact/fuzzy extraction, rare-string tests,
membership/propensity tests, and longest-match reporting remain separate.

## C/D Extraction Result

On 2026-08-19, the fixed 64-prefix/64-target greedy memorisation probe also
completed for exhaustive runs in A/B/D:

- **Category A exhaustive:** 7 assistant-prefill exact-64 matches and 8 raw exact-64 matches
  (`1,366,040` requests per mode, `exact_64_rate`: 0.0006% and 0.0006%).
- **Category B exhaustive:** 4 assistant-prefill exact-64 matches and 3 raw exact-64 matches
  (`205,754` requests per mode, `exact_64_rate`: 0.0019% and 0.0015%).
- **Category D exhaustive:** 385 assistant-prefill exact-64 matches and 281 raw exact-64 matches
  (`4,611,054` requests per mode, `exact_64_rate`: 0.0083% and 0.0061%).

Across those three completed exhaustive runs, the high-traffic exact-64 sources were
DBC abstracts in A, RLVE-tasksource in B, and D-05/D-10/D-01 in D. The hits remain
dominated by repetitive token patterns (numbers, delimiters, boilerplate formatting), with
no reviewed high-risk expressive prose memorisation in these protocol views.

The matching C/D run completed on 2026-08-18 with 137,620 eligible examples
per mode for Category C and 76,386 per mode for Category D. Category C had
11 raw and 10 chat exact-64 matches; Category D had 11 raw and 12 chat
exact-64 matches. Median longest-common-prefix length was zero in every
category/mode. P99 was 9 tokens for C and 10 for D; matches of at least 50
tokens occurred in 13--14 C rows and 14--15 D rows per mode. D-04 yielded
9,867 eligible rows because shorter tool prompts cannot support the fixed
64+64 protocol. D-06 Sudoku prompts were too short and contributed no rows.

An additional exhaustive C run for 2026-08-19 (`.../dfm9_memorisation_category_c_exhaustive_step1650000`)
was started to scale from 10K-cap to full coverage. As of this update, it is still
incomplete (`.jsonl.gz.tmp` shards present) and final exact-64 totals are not yet
trusted until the full run is resumed and re-compressed shards are written.

**Superseded on 2026-08-20:** the exhaustive C run completed and its eight
compressed result shards are final. Across exhaustive A-D outputs, all 5,562
exact-64 occurrences (3,423 unique source-prefix/continuation pairs) were then
adjudicated with Gemma 4 31B and the highest prose-like cases manually checked.
Only 61 occurrences were coherent prose and one was expressive prose. The sole
expressive case was a predictable next verse of the traditional repetitive
song *Five Little Ducks*. No exact match was rated high copyright-expression or
high review priority. See
`legal/reports/dfm9-memorisation-exact-match-adjudication-abcd.md` and
`logs/analysis/dfm9_memorisation_exact_match_judge_step1650000/`.

The earlier lexical content classifier's approximately 33% `prose` result is
superseded for substantive interpretation. It measured surface form and
misclassified repeated captions, prices, and similar constrained strings. The
stricter adjudication yields coherent prose in 1.10% and expressive prose in
0.018% of exact occurrences. This remains protocol-bound evidence, not proof
against adaptive or near-exact extraction.

The C/D evidence is in
`logs/analysis/dfm9_memorisation_categories_cd_step1650000/`, with the
summary at `summary.json` and review at `report.md`. The preparation uses
atomic per-source candidate checkpoints so malformed records do not force a
complete rescan.

The 56 C/D rows with LCP >=50 represent 33 unique source texts (raw/chat are
duplicate protocol views). Severity review: 27 low-severity structural or
pathological continuations and 6 medium-review generic code/math cases (C#,
Java, route optimization, majority-element detection, die statistics, and
Fibonacci code). There were no high-severity expressive, personal, or
source-specific prose extractions. The long matches are dominated by numeric
sequences, JSON/XML/CSV/table scaffolds, repeated strings, date/index lists,
and synthetic code/math formatting.

## Planned Category-B Throughput Probe

The active Category-A exhaustive run remains unchanged at Python submission
batch 256. The planned exhaustive Category-B run uses submission batch 1024,
with vLLM explicitly configured for `max_num_seqs=1024` and
`max_num_batched_tokens=209216`, matching the observed per-server KV-cache
capacity. It enables vLLM periodic runtime statistics so `shard_*.log` records
live KV-cache occupancy as well as startup capacity. The launcher is
`scripts/run_memorisation_category_b_exhaustive.sh` and is intentionally not
started until Category A completes.

## Exhaustive A/B Remainder Results

The exhaustive A remainder completed on 2026-08-18 for the three large
agreement-backed cohorts: 1,366,040 unique eligible source texts, tested in
both modes (2,732,080 requests). DBC abstracts produced 7 exact-64 chat and 8
exact-64 raw continuations; Lex.dk and DBC reviews produced none. The longest
matches inspected were whitespace runs, repeated replacement characters,
table-of-contents or numbered structures, and repetitive bibliographic/list
material. No reviewed long match was expressive prose.

The exhaustive B remainder completed the same day for the remaining RLVE and
Tasksource texts: 205,754 unique texts, 411,508 requests. It produced 4
exact-64 chat and 3 exact-64 raw continuations. The longest examples were an
all-ones grid and repeated multilingual strings, both mechanically predictable
or degenerate rather than expressive prose. Together with the earlier B
stratified sample, the full locally available B coverage is 238,493 unique
texts; B-02--B-04 remain covered by their earlier exhaustive local subsets.

Across the earlier C/D stratified run (214,006 unique texts, both modes), 22
exact-64 matches occurred in each mode. Its 56 rows at 50 or more matching
tokens represented 33 unique source texts: 27 low-severity structural or
pathological cases and 6 medium-review generic code/math cases. No high-risk
expressive, personal, or source-specific prose extraction was observed.

For D specifically, an additional exhaustive pass (same 64-prefix/64 target)
completed on 2026-08-19 for 4,611,054 texts/mode from this protocol:

- Raw: exact-64=281 (0.006%), >=50=581, mean LCP=1.10, P99=10.0, max=64.
- Assistant-prefill: exact-64=385 (0.008%), >=50=715, mean LCP=1.18, P99=10.0, max=64.

Top-match inspection in that pass is still dominated by formulaic or duplicated
content (for example D-05/D-10/D-01 repetitions and structured token strings).
No new high-severity expressive/prose-style extraction has been flagged from this
fixed greedy protocol, but this is still a protocol-bound probe and does not
eliminate all extraction risk.

These findings are evidence about this fixed greedy 64-prefix/64-generation
protocol, not a proof of non-membership or non-extraction under adaptive
prompts, longer prefixes, sampling, or other decoding strategies.
