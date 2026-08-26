# DFM9 Exact-Match Adjudication Across Categories A-D

Date: 2026-08-20

This report classifies every exact-64 occurrence produced by the exhaustive
64-prefix/64-continuation greedy extraction probes for the DFM8 XL 1.65M EMA
checkpoint. It assesses the character of extracted text; it does not itself
establish legal memorisation, copyright infringement, or dataset membership.

## Method

All exact-target rows were extracted from the completed Category A-D result
shards. Identical source-prefix/continuation evidence was judged once while all
raw/chat and cohort occurrences were retained. Eight existing Gemma 4 31B
OpenAI-compatible servers classified each item by textual form, coherent prose,
expressive prose, formulaic constraint, copyright-expression level, and manual
review priority. The only medium-priority result and the leading prose-like
results were then inspected manually.

The run covered 5,562 exact-match occurrences representing 3,423 unique
source-prefix/continuation pairs. All judge calls completed successfully.

## Results

| Category | Exact occurrences | Coherent prose | Expressive prose | Main character |
|---|---:|---:|---:|---|
| A: agreement | 15 | 0 | 0 | repeated patterns and lists/tables |
| B: Article 3 | 7 | 0 | 0 | repeated patterns |
| C: Article 4 | 4,874 | 40 | 0 | 4,311 repeated patterns; 495 lists/tables |
| D: other bases | 666 | 21 | 1 | repeated patterns, math, code, and lists/tables |
| **Total** | **5,562** | **61** | **1** | overwhelmingly constrained or repetitive |

Across all occurrences, the primary-form labels were 4,561 repeated patterns,
619 lists/tables, 175 math, 166 code, 22 markup/metadata, 9 boilerplate, 5
factual prose, 4 other, and 1 expressive prose. The judge assigned 5,561 low
copyright-expression/review-priority labels and one medium label; none were
high.

The sole expressive item is a continuation of the traditional repetitive
children's song *Five Little Ducks*. Its exact continuation follows the
countdown verse already exposed in the prefix. It merits review because it is
creative-language surface text, but its traditional, repeated structure makes
this weak evidence of source-specific expressive memorisation.

## Strict Prose Examples

These short excerpts illustrate the strongest sentence-like matches. They are
quoted only briefly; each complete matched continuation is 64 model tokens.

| Category/source | Short excerpt | Adjudication | Why exact completion is weak evidence here |
|---|---|---|---|
| D-10, `train-00007-of-00038.parquet:1100` | “Four little ducks went out one day, over the hills and up away.” | expressive prose; medium review | The prefix already establishes a countdown song and the next verse repeats its template. |
| C-07, Newsroom row 454 | “The Concord Monitor broke with political tradition Sunday, telling readers ...” | coherent factual news prose; low review | The same byline and sentence recur in the source, and the model continues that loop. |
| C-07, Newsroom row 4006 | “Park officials cleaned up debris that washed ashore Sunday following the Macy's fireworks show.” | coherent factual sentence; low review | One caption-like sentence is repeated several times before and throughout the target. |
| C-07, Newsroom row 1796 | “A San Rafael couple have sued Marin County in Superior Court ...” | coherent factual news prose; low review | The target repeats the sentence already present immediately before generation. |
| C-07, Newsroom row 95 | “Recent heavy rains are being blamed for the collapse of this 50-foot section ...” | coherent factual sentence; low review | The continuation loops a sentence already supplied in the prefix. |

Thus there are prose-shaped exact matches, but manual inspection does not find
an example where the model freely reconstructs a new, distinctive prose passage
after a non-repeating lead-in. The exact matches are mostly predictable from
local repetition, constrained structure, or public/traditional patterns.

## Interpretation And Limitations

The earlier lexical classifier's approximately 33% `prose` bucket is
superseded for substantive review. It detected prose-like character sequences,
not expressive content, and included repeated captions, prices, and other
formulaic strings. The stricter adjudication finds coherent prose in 1.10% of
exact occurrences and expressive prose in 0.018%.

This remains a fixed greedy 64+64 extraction probe. It does not exclude
memorisation under longer prefixes, adaptive prompting, sampled decoding,
membership inference, near-exact paraphrase, or targeted attacks. The judge is
also a model-assisted triage mechanism rather than a legal decision-maker.

## Reproducibility Artifacts

- `scripts/judge_memorisation_exact_matches.py`
- `logs/analysis/dfm9_memorisation_exact_match_judge_step1650000/exact_matches.jsonl`
- `logs/analysis/dfm9_memorisation_exact_match_judge_step1650000/unique_evidence.jsonl`
- `logs/analysis/dfm9_memorisation_exact_match_judge_step1650000/judgments.jsonl`
- `logs/analysis/dfm9_memorisation_exact_match_judge_step1650000/adjudicated_occurrences.jsonl`
- `logs/analysis/dfm9_memorisation_exact_match_judge_step1650000/summary.json`

