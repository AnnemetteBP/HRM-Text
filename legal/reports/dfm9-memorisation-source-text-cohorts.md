# DFM9 Minimal Source-Text Cohorts for Memorisation Testing

Status: engineering/legal test design for the current DFM9 corpus; not legal
advice or a determination that observed extraction is copyright infringement.
Prepared 2026-08-18.

## Construction rule

The test inventory should contain one canonical copy of each original work,
prompt, passage, schema, or conversation that survives into training. Normalize
and content-hash these references, then map all prompt templates, translations,
response regenerations, mixture copies, and repeated epoch selections back to
the canonical record. Do not count a transformed training row as a new source
text merely because its instruction or answer format changed.

Where the original source cannot be recovered, retain the earliest available
training-side expression as an explicitly labelled proxy. Keep exact/fuzzy
prefix extraction, rare-string extraction, membership/propensity testing, and
longest-common-substring results separate. Legal basis controls prioritization
and reporting; it does not by itself determine whether a model output is
memorized.

## A. Agreement-based source text

These cohorts have direct data-owner agreement coverage for training/model
release. Agreement scope does not remove the value of measuring extraction.

| ID | Canonical source-text cohort | Minimum canonical material | Training descendants / exposure | Local reference |
|---|---|---|---|---|
| A-01 | Lex.dk encyclopedia articles | Every original article, deduplicated by article ID and normalized body hash | `Lex.dk`, 313.397M tokens/epoch | `data/downloads/datasets/lexdk/lexdk_articles.jsonl.gz` |
| A-02 | DBC abstracts | Every original abstract, deduplicated by work/edition identifier and text hash | Part of DBC's 356.114M tokens/epoch | `data/downloads/datasets/dbc/dbc-abstracts_*.jsonl.gz` |
| A-03 | DBC reviews | Every original review, separately from abstracts of the same work | Part of DBC's 356.114M tokens/epoch | `data/downloads/datasets/dbc/dbc-reviews.jsonl.gz` |
| A-04 | Faktalink sections | Original title, section title, and section body; hash bodies across article versions | Part of DBC's 356.114M tokens/epoch | `data/downloads/datasets/dbc/dbc-faktalink.jsonl.gz` |
| A-05 | Forfatterweb sections | Original title, section title, and section body | Part of DBC's 356.114M tokens/epoch | `data/downloads/datasets/dbc/dbc-farfatterweb.jsonl.gz` |
| A-06 | Instruct-BT agreement passages | The response/source passage for `dkmedier` (486 rows), `odense` (337), and `danskerhverv` (281), kept as three cohorts | Agreement-backed fraction of `oliverkinch/instruct-bt`; aggregate exposure 13.461M tokens/epoch | `data/downloads/datasets/oliverkinch_instruct_bt/data/train-00000-of-00001.parquet`, selected by `subset` |

## B. Article-3-based source text

These are the narrow source-expression cohorts for which current scientific-
research use retains Article 3 / Danish section 11 c. Test source text rather
than counting the much larger containing mixtures.

| ID | Canonical source-text cohort | Minimum canonical material | Training descendants / exposure | Local reference or gap |
|---|---|---|---|---|
| B-01 | RLVE source problem statements | All 250 audited prompt variants linked to their source statement; exhaustively report the 45 close/constrained, 15 expressive, one unavailable-source, and four unmatched variants | Two direct RLVE datasets, 684.900M aggregate tokens/epoch; estimated narrow boundary 160.438M | `legal/registers/dfm9-rlve-prompt-expression-audit.csv`; preserve source URL/snapshot evidence and mark unavailable text |
| B-02 | LongAlign documents | All 9,888 original documents. Preserve the eleven content groups and all 1,621 copyright-marker rows as mandatory strata | Through SmolTalk/Apertus/DFM Dyna; 167.380M Gemma-template tokens before Apertus sampling | `/work/dfm/.cache/legal-audit/zai-org__LongAlign-10k/long.jsonl` and `legal/registers/dfm9-longalign-content-groups.csv` |
| B-03 | EuroBlocks embedded annealing documents | All 2,607 unique document hashes underlying the 5,169 source-retaining rows | Through EuroBlocks/Apertus/DFM Dyna; included in the 183.860M sampled LongAlign+EuroBlocks estimate | Official EuroBlocks parquet plus `legal/registers/dfm9-euroblocks-embedded-seed-documents.csv` |
| B-04 | EuroBlocks unavailable annealing seeds | Recover the canonical seeds for 134,819 seed-derived rows. Until then, retain generated prompt/answer rows only as proxies and do not describe them as original source text | Through EuroBlocks/Apertus/DFM Dyna | Provenance gap recorded in `legal/registers/dfm9-euroblocks-seed-risk.csv` |
| B-05 | Sapient Tasksource residual | Canonical upstream source records for all 84 residual files, grouped by upstream repository and normalized source text. Preserve social/user text, long passages, legal/medical text, and rare formulations as mandatory strata | Exact 69.759M tokens/epoch | `legal/registers/dfm9-sapient-instruction-family-inventory.csv`; current Sapient files are proxies where upstream originals are unavailable |

## C. Article-4-based source text

Article 4 / Danish section 11 b applies only to uncovered retained expression;
direct source licences remain controlling where known. Source-level tests must
therefore preserve the subdataset label.

| ID | Canonical source-text cohort | Minimum canonical material | Training descendants / exposure | Local reference or gap |
|---|---|---|---|---|
| C-01 | RACE examination material | Canonical unique passages, questions, choices, and answers, deduplicated across all templates | 72 FLAN files, 6.065M sampled rows and 5.929B tokens/epoch | Original RACE release when obtained; current proxy under `data/downloads/datasets/sapient_cleaned/data_clustered/flan/` |
| C-02 | DREAM examination dialogues | Canonical dialogues, questions, choices, and answers | 28 files, 192.230M tokens/epoch | Original DREAM release; current factual-FLAN materialization as proxy |
| C-03 | WebQuestions | Canonical crowd-authored question text and answer/entity, deduplicated across templates | 22 files, 15.846M tokens/epoch | Original WebQuestions release; current factual-FLAN materialization as proxy |
| C-04 | Uncovered CoQA source text | RACE-derived examination passages and any other source-uncovered records only; exclude separately licensed Wikipedia, MCTest, and CNN strata from this Article-4 cohort | At most the full eight-file/82.494M-token CoQA family | Original CoQA `source` strata; factual-FLAN rows are fallback proxies |
| C-05 | Sapient non-factual FLAN: NIv2 | Canonical source instances for 1,430 tasks; deduplicate the same source record across few/zero-shot and template variants | 2,860 files, 2.400B tokens/epoch | Source mapping in `legal/registers/dfm9-sapient-instruction-family-inventory.csv`; transformed files under `sapient_cleaned/data_clustered/flan/` |
| C-06 | Sapient non-factual FLAN: T0/P3 | Canonical source-dataset records, retaining the P3 template ID only as transformation metadata | 548 files, 1.536B tokens/epoch | Same inventory and transformed source tree; recover canonical upstream rows by task |
| C-07 | Sapient non-factual FLAN: FLAN 2021 | Canonical source-dataset records, deduplicated across FLAN templates | 200 files, 291.356M tokens/epoch | Same inventory and transformed source tree |
| C-08 | Sapient non-factual FLAN: CoT | Canonical questions/problems and any human source solutions; treat generated chain-of-thought separately | 36 files, 101.174M tokens/epoch | Same inventory and transformed source tree |
| C-09 | FLAN v2 Converted shared component | Canonical source-task expression for 89,982 rows, content-hash joined to C-05 through C-08 to avoid duplicate testing | Inherited by Tulu 3, IF-SFT, DOLCI, Apertus, and DFM Dyna | Recover from `ai2-adapt-dev/flan_v2_converted`; local descendants identify the component |
| C-10 | SciRIFF retained paper expression | Original paper passages/sections per approximately 39 task families, keyed by paper/document ID and source licence | Inherited by Tulu 3, DOLCI, SciRIFF Train Mix, Apertus, and DFM Dyna | Local SciRIFF/Tulu artifacts plus paper identifiers; fetch canonical papers where lawful access permits |
| C-11 | OpenHermes Airoboros 2.2 | Original prompts/source records for 35,380 rows; separate public-dataset summaries from generated-only rows | Repaired English and translated Danish OpenHermes plus SmolTalk/Apertus descendants | Raw OpenHermes was intentionally removed; use retained prompts in `dfm8-openhermes-en` as proxies and recover Airoboros originals |
| C-12 | OpenHermes Caseus custom | All 2,688 retained prompts | Same OpenHermes descendants | Source page is unidentified; retained English prompts are the current proxy |
| C-13 | OpenHermes CoT Alpaca GPT-4 | All 42,026 retained prompts and any recoverable pre-generation source instances | Same OpenHermes descendants | Original source page was lost; retained English prompts are the current proxy |
| C-14 | OpenHermes residual Open-Platypus | Residual LeetCode/Airoboros and otherwise uncovered prompts only, not directly licensed Platypus components | Subset of 22,280 Platypus-labelled OpenHermes rows | Use `openhermes_source` and component metadata in the repaired English dataset |

For C-05 through C-10, the same canonical source instance can occur in several
mixtures. A normalized source hash plus task/repository identity must collapse
those copies before selecting prompts for extraction testing.

## D. Other bases and conditions

These source texts do not rely on an agreement, Article 3, or Article 4 for
the current use. The operative condition is stated explicitly.

| ID | Condition | Canonical source-text cohort | Minimum canonical material / test rule |
|---|---|---|---|
| D-01 | Express participant permission accepted for research training | WildChat human prompts and conversations, including IFBench and Qwen-response descendants | Canonical WildChat conversation ID; test rare strings, canaries, long prompts, and privacy-risk strata once across all descendants |
| D-02 | Deliberate participant publication accepted for current research | ShareGPT conversations in Tulu-v2, Tulu-v2 Long, and SciRIFF Train Mix | Canonical original ShareGPT ID; deduplicate split/Long copies and test credential/PII indicators separately |
| D-03 | Etalab Open Licence plus participant-text/privacy controls | ComparIA/AI Arena conversations and reactions | Canonical conversation ID; preserve language, model, and privacy strata |
| D-04 | Manual low-risk acceptance; direct generated/package layers otherwise | DOLCI Tool Use residual API schemas, Semantic Scholar abstracts/paper snippets, Serper snippets, and four unique residual DRv4 prompts | Test uncommon schemas, all four residual prompts, distinctive snippets, and paper text stratified by recorded licence |
| D-05 | Manual residual-risk acceptance plus package/per-sample terms | Mixture-of-Thoughts source prompts: NuminaMath/AoPS/AMC/AIME, Codeforces/ICPC/IOI statements, complete editorials, and NVIDIA science questions | Canonical problem/editorial ID; prioritize all editorial-conditioned rows, 8,345 AoPS prompts, competition wording, and long science questions |
| D-06 | Manual low-risk acceptance of functional records/database selection | Sudoku Extreme puzzle collections | Canonical grid+solution keyed by collection; test exact puzzle/solution extraction and membership, not prose continuation |
| D-07 | Manual reliance on publisher's Apache-2.0 representation | TriviaQA question/short-answer records | Canonical normalized question grouped by all 14 `question_source` values; include dedicated JetPunk and TriviaCountry strata; evidence documents were not trained |
| D-08 | Project-generated/audited derivative acceptance | All 70 `sapient-synth-*` datasets | Pair each generated row with its named upstream task where available; test source-prompt overlap and generated-row extraction separately |
| D-09 | Direct/noncommercial source terms | TextbookReasoning, SkoleGPT, `no_robots`, Tulu Persona families, and other CC-BY-NC/CC-BY-NC-SA material | Keep each source corpus separate because attribution, NC, and SA obligations differ; select canonical source passages rather than generated responses |
| D-10 | Direct code/math dataset terms with retained third-party notices | OpenMathInstruct, OpenThoughts/Big Reasoning Traces, Nemotron code/SWE, AceReason, and related math/code corpora | Canonical problem, repository file, or source prompt ID; prioritize contest prose, code files, long reasoning prompts, and notice-bearing records |

As a project-scope decision dated 2026-08-18, this memorisation-source review
does **not** require cohorts for Common Pile, DynaWord, OPUS pairs,
Wikipedia/Wikimedia, EUR-Lex, GovReport, permissively filtered arXiv papers,
Giannor/Oliverkinch/Synquid contributor-created material, or genuinely
from-scratch DFM8 material. This exclusion does not alter A-06: the three
agreement-backed Instruct-BT source subsets remain in A because their source
texts are covered by the requested agreement-based cohort.

## Minimal implementation order

1. Build canonical source stores for A-01 through A-06 and B-01 through B-05.
2. Recover and hash the original RACE/DREAM/WebQuestions/CoQA records, then
   join every factual-FLAN row to them.
3. Resolve C-05 through C-10 by canonical task and source-row ID, sharing one
   source store across Sapient, Tulu, DOLCI, and Apertus descendants.
4. Build the OpenHermes source-prompt store from repaired English prompts,
   replacing proxies when original Airoboros/Platypus material is recovered.
5. Add D-01 through D-08 as mandatory manual-decision test cohorts.
6. Add D-09 and D-10 as licence- and source-stratified controls. These are
   needed to distinguish legally sensitive extraction from the model's general
   propensity to reproduce any highly repeated or distinctive training text.

The test manifest should record `canonical_source_id`, normalized hash,
source-text path, legal-basis cohort, upstream licence/decision, all descendant
dataset IDs, DFM9 sampled exposure where known, and whether the reference is an
original or proxy.

## Local source-material assembly

The reproducible local assembly is generated with:

```bash
python scripts/assemble_dfm9_memorisation_sources.py --force
```

It writes `data/legal/dfm9_memorisation_sources/`, using symlinks rather than
copying bulk data. `manifest.tsv` records cohort, basis, material role, row/file
selector, source path, and local link. `gaps.tsv` records originals that remain
unavailable and the retained proxy that can be tested meanwhile. The generated
bundle currently contains 4,017 artifact links (`A=26`, `B=95`, `C=3,784`,
`D=112`) and 17 explicit source gaps. It contains all source material currently
available for A, B, C, and the revised D; its README records artifact-link
counts. Directory links intentionally leave their recursive byte counts unset.
The deduplicated referenced-source sizes measured on 2026-08-18 are `A=2.343
GB`, `B=2.905 GB`, `C=90.357 GB`, and `D=148.667 GB` (244.272 GB total).
These are logical source sizes, not physical space consumed by the symlink
assembly.

The standalone Danish-English OPUS-pair cohort is excluded from D. Some
Article-4 NIv2 task filenames still contain `opus` because they are inseparable
members of the independently in-scope non-factual FLAN cohort; this does not
reintroduce the excluded standalone OPUS dataset as a D cohort.
