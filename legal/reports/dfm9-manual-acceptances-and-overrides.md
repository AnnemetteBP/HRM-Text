# DFM9 Manual Acceptances and Rights-Basis Overrides

Status: project decision register for engineering/legal triage, not legal
advice or institutional approval. Decisions recorded 2026-08-17 and
2026-08-18 by Professor Peter Schneider-Kamp as project owner unless stated
otherwise.

## Scope

This file collects discretionary project decisions that changed whether a
DFM9 source or subsource blocked training. It deliberately excludes ordinary
facts such as a captured open licence, public-domain status, or a data-owner
agreement. Those remain in the source-rights DAG and legal-basis registers.

The decisions are purpose-limited to the current academic/non-commercial
scientific-research model training unless a row says otherwise. They do not
authorize redistribution of source records, erase attribution or privacy
obligations, or convert a source into open-licensed material.

Agreement-backed sources are not manual overrides and therefore do not appear
in the decision register. A supplemental cohort table below keeps selected
agreement-backed material in the same future memorisation/propensity audit
plan without changing its legal classification.

## Decision Register

| ID | Dataset or subdataset | Decision and reason | Residual issue | Future memorisation/propensity test target |
|---|---|---|---|---|
| MAN-001 | `allenai/Dolci-Instruct-SFT-Tool-Use`: SimFC unmatched/adapted API schemas | Accepted as low risk. Most schemas match xLAM or ToolACE; the unmatched 92,800-row upper bound may include adapted public MCP APIs. No material reason to invoke Article 3 was identified. | Exact API provenance is incomplete; preserve notices where known. | Probe uncommon API names, descriptions, argument schemas, and exact schema continuations in the unmatched subset. |
| MAN-002 | Same DOLCI Tool Use family: Semantic Scholar titles, abstracts, and occasional paper content in M3/M4v2/M5v2 | Accepted as low risk. The generated trajectory layer and non-commercial Semantic Scholar API use are direct; retained paper content has heterogeneous terms. No material reason to invoke Article 3 was identified. | Per-paper licence coverage is incomplete. | Prefix extraction against retained abstracts/titles, stratified by recorded paper licence and missing-licence rows. |
| MAN-003 | Same DOLCI Tool Use family: DRv4 Serper search-result snippets | Accepted as low risk. Fetched pages were summarized, while short search snippets remain in environment messages. No material reason to invoke Article 3 was identified. | Source-site terms and snippet provenance are incomplete. | Exact and approximate extraction from distinctive retained snippets. |
| MAN-004 | Same DOLCI Tool Use family: five residual OpenScholar-labelled rows/four unique prompts | Accepted as low risk because the residual set is extremely small and the generated trajectory layer is direct. No material reason to invoke Article 3 was identified. | Prompt release was not located. | Exhaustive prompt/response extraction test for all four unique prompts. |
| MAN-005 | `allenai/verifiable-reasoning-filtered-gpt-41` and `allenai/verifiable-reasoning-filtered-o4-mini`: complete RLVE prompt family | Accepted for current research after a 250-variant prompt audit. This includes 45 close/constrained, 15 expressive/source-specific, one unavailable, and four unmatched variants; Article 3 remains the fallback where protected expression is retained. | Fifteen variants retain the strongest source-specific expression; four are unmatched and one source was unavailable. | Test all 15 carryover variants, prioritising `blockimage`, `powernest`, `fbi_binarytree`, and `abprogramsimulation`; also test unavailable/unmatched variants. |
| MAN-006 | Sapient Sudoku Extreme, especially Enjoy Sudoku/community puzzle collections | Accepted as low risk without Article 3. Individual grids and solutions are functional records; only possible selection/arrangement or database rights in unlicensed community collections remained. | Compilation/database-right evidence remains incomplete. | Puzzle-prefix/solution extraction and membership inference, grouped by named community collection. |
| MAN-007 | Sapient factual-FLAN RACE | Article 4 / Danish section 11 b chosen based on lawful long-running public research/HF distribution, no identified reservation, and no known rightsholder challenge. | No explicit open content licence; acquisition-time reservation evidence is incomplete. | Prefix extraction from exam passages and exact question/choice reproduction, stratified by source exam. |
| MAN-008 | Sapient factual-FLAN DREAM | Same Article 4 determination as RACE. | Human-authored examination dialogues have no captured open content licence; acquisition-time evidence is incomplete. | Dialogue-prefix extraction and exact question/choice reproduction. |
| MAN-009 | Sapient factual-FLAN WebQuestions | Same Article 4 determination; public crowd-authored questions and Freebase answers were long distributed without a known reservation/challenge. | No explicit licence for the crowd-authored question collection was found. | Exact prompt extraction and rare-name/entity completion. |
| MAN-010 | Sapient factual-FLAN uncovered CoQA portions, principally RACE-derived examination material | Article 4 chosen for layers not already covered by source-specific direct terms. | CoQA is a mixed-source corpus; the decision does not alter CC-BY-SA, MSR-LA, or Apache obligations on covered components. | Test only source-uncovered/RACE-derived rows separately from directly licensed CoQA sources. |
| MAN-011 | Sampled TriviaQA question/short-answer rows across all 14 question-source groups | Accepted the official repository statement that Apache-2.0 applies to code and data as the operative basis. This supersedes the earlier Article 3/4 split, including JetPunk and TriviaCountry. | UW separately disclaims ownership of included questions/documents; current robots findings remain evidence. The decision excludes evidence documents. | Exact question/answer extraction by `question_source`, with dedicated JetPunk and TriviaCountry strata. |
| MAN-012 | WildChat retained human prompts/conversations and descendants including `synquid/ifbench-train` and `synquid/wildchat-100k-qwen-messages` | Accepted affirmative user consent for research/product-development use and third-party publication/sharing as express permission for current research training. | Privacy/GDPR safeguards remain independent; permission does not eliminate personal-data controls. | Canaries, rare-string extraction, and user-prompt memorisation tests, stratified by original versus generated continuation rows and privacy-risk flags. |
| MAN-013 | `ai2-adapt-dev/flan_v2_converted`, including copies inherited by Tulu 3, DOLCI, and Apertus | Article 4 / Danish section 11 b selected for uncovered retained upstream task expression; direct terms continue to govern identified components. This supersedes the initial Article 3 fallback. | The 89,982-row release lacks task-level licence metadata; task provenance and acquisition-time reservation evidence remain partial. | Stratified prefix extraction and membership/propensity testing by recoverable FLAN/OpenOrca task family, prioritising long passages and distinctive questions. |
| MAN-014 | `allenai/SciRIFF`, including retained rows in Tulu 3, DOLCI, Apertus, and related mixtures | Article 4 / Danish section 11 b selected for uncovered scholarly expression; ODC-By covers the task/schema layer and direct source terms apply where captured. This supersedes the initial Article 3 fallback. | Approximately 39 task families can retain portions of scientific papers; document lineage and acquisition-time reservation evidence remain partial. | Prefix extraction and approximate-match testing against retained paper text, stratified by task family, source licence, and document availability. |
| MAN-015 | `open-r1/Mixture-of-Thoughts` math, code, science, and generated-trace components | Residual source-expression and editorial risk accepted for the current project based on immediate package/per-sample terms and the recorded prompt-level assessment. No material reason to invoke Article 3 was identified; this is a project-owner risk acceptance, not a blanket upstream relicensing. | Competition/editorial and forum provenance remains incomplete; the `codeforces-cots` card and README use inconsistent CC-BY-4.0/ODC-By labels. | Prioritise AoPS, AMC/AIME, long science questions, complete editorials, and exact/fuzzy trace-to-editorial overlap. |
| MAN-016 | Uncovered OpenHermes 2.5 components: Airoboros 2.2, Caseus custom, CoT Alpaca GPT-4, and residual Open-Platypus material | Article 4 / Danish section 11 b selected for retained source expression not covered by captured component terms. This supersedes the initial Article 3 fallback; direct terms continue to govern covered components. | Work-level provenance, acquisition-time reservation evidence, and the lost CoT-Alpaca source page remain incomplete. | Stratify extraction testing by `openhermes_source`, with separate Airoboros, Caseus, CoT-Alpaca, and Platypus cohorts in both repaired English and translated Danish derivatives. |
| MAN-017 | `zai-org/LongAlign-10k`: all eleven content groups, including the 1,621 full-document copyright-marker rows | Approved on 2026-08-18 for the current academic/non-commercial scientific-research training under Article 3 / Danish section 11 c. The approval expressly includes 760 restrictive, 56 mixed, 640 generic, 89 public-domain-marker, 70 open-licence-marker, and six government-notice rows found by full-document scanning. | This accepts the current research-TDM boundary; it does not establish document-level licences, negate restrictive notices, authorize raw redistribution, or clear Article 4/commercial use. | Exhaustive marker cohort plus stratified samples from the 8,267 no-marker rows; prioritize books/publisher material, long prompts, restrictive notices, late markers, and rare domains. |
| MAN-018 | `utter-project/EuroBlocks-SFT-Synthetic-1124`: 5,169 source-retaining rows/2,607 unique embedded documents and 134,819 seed-derived rows | Approved on 2026-08-18 for the current academic/non-commercial scientific-research training under Article 3 / Danish section 11 c, with direct terms retained for generated layers. | The annealing corpus and many source URLs/licences remain unidentified; eight unique documents have restrictive notices and 2,474 have no explicit marker. Approval does not authorize raw redistribution or general/non-research use. | Test all 2,607 unique document hashes with occurrence-weighted reporting, plus derived-row overlap tests by language and content group; prioritize restrictive, long, rare-domain, and no-marker documents. |
| MAN-019 | Sapient retained non-factual FLAN: CoT, FLAN-2021, NIv2, and T0/P3 materializations | Applied the prior MAN-013 Article 4 / Danish section 11 b determination consistently to uncovered FLAN-v2 source expression in the Sapient materialization. Direct source terms remain controlling where identified. | NIv2 explicitly says instance licences follow original datasets; P3 and Google repository licences do not necessarily relicense all source expression. Acquisition-time reservation evidence remains incomplete. | Stratify extraction by the four submixtures and canonical source task; prioritize long passages, unusual instructions, and source families lacking specific terms. |
| MAN-020 | Sapient Tasksource residual: 84 files / 69,758,538.8 tokens per epoch with blank, `unknown`, `other`, or generic `cc` source-repository metadata | Approved for the current academic/non-commercial scientific-research training under Article 3 / Danish section 11 c. The 77 files with specific recognized licences remain on their direct terms. | Tasksource is a harmonizer rather than a blanket source-rights grant. This decision does not resolve privacy, raw redistribution, nonresearch use, or missing provenance inside derived repositories. | Stratify by upstream repository and metadata class; prioritize CoNLL/Reuters-derived corpora, social/user text, long passages, legal/medical text, and rare labels or formulations. |
| MAN-021 | All 70 `schneiderkamplab/sapient-synth-*` effective datasets | Manually approved by the project owner on 2026-08-18 for the current academic/non-commercial scientific-research training. The generated and audited replacement datasets are accepted as the operative training works; named upstream-task links remain provenance evidence but no longer block clearance of these synthetic derivatives. | This does not relicense or independently clear the named upstream datasets, authorize redistribution of their source records, or erase privacy and memorisation-testing obligations. | Preserve task-family strata and test exact/fuzzy overlap against named source tasks, prioritising long, distinctive, review, dialogue, and benchmark-derived prompts. |
| MAN-022 | ShareGPT participant expression retained in `allenai/tulu-v2-sft-mixture`, `allenai/tulu-v2-sft-long-mixture`, and the Tulu-v2 half of `allenai/SciRIFF-train-mix` | The project owner accepts users' deliberate one-click publication to a service designed for public sharing, browsing, and public-API access as participant permission for the current academic/non-commercial research training. This gives the source the same operative cleared status as WildChat for this project. | The evidence is not equivalent to WildChat's explicit research/product-development consent: no ShareGPT term expressly authorizing model training was found. This decision is not a blanket Apache-2.0 licence, raw-redistribution permission, or nonresearch authorization; privacy/GDPR and credential controls remain independent. | Test source-ID-stratified rare strings, credentials/PII flags, and prefix extraction; report the split and Long variants separately and deduplicate by original ShareGPT ID where both are retained. |

## Affected Effective Sources

### Deduplicated effective-dataset exposure

The table below counts each effective DFM9 dataset once even when several
manual decisions apply to its internal components. It reports whole effective
dataset exposure, not the narrower number of tokens governed by the decision.

| Decisions | Effective datasets | Dataset count | Tokens/epoch |
|---|---|---:|---:|
| MAN-001 through MAN-004, plus inherited MAN-012 through MAN-014 decisions | `allenai/Dolci-Instruct-SFT`, `allenai/Dolci-Instruct-SFT-No-Tools`, `allenai/Dolci-Instruct-SFT-Tool-Use` | 3 | 7,337,564,443.0 |
| MAN-005 | `allenai/verifiable-reasoning-filtered-gpt-41`, `allenai/verifiable-reasoning-filtered-o4-mini` | 2 | 684,899,562.4 |
| MAN-006 through MAN-011, MAN-019, MAN-020 | `sapientinc/HRM-Text-data-io-cleaned-20260515` | 1 | 21,380,034,516.8 |
| MAN-012 | `synquid/ifbench-train`, `synquid/wildchat-100k-qwen-messages` | 2 | 202,557,582.0 |
| MAN-013 and MAN-014 | `allenai/tulu-3-sft-mixture`, `allenai/IF_sft_data_verified` | 2 | 1,590,502,438.0 |
| MAN-015 through MAN-018 | `danish-foundation-models/dfm-dyna-instruct` | 1 | 3,543,871,662.0 |
| MAN-016 | `schneiderkamplab/dfm8-openhermes-da`, `schneiderkamplab/dfm8-openhermes-en` | 2 | 1,594,164,824.0 |
| MAN-021 | All 70 `schneiderkamplab/sapient-synth-*` effective datasets | 70 | 74,880,552.0 |
| MAN-022 | `allenai/tulu-v2-sft-mixture`, `allenai/tulu-v2-sft-long-mixture`, `allenai/SciRIFF-train-mix` | 3 | 1,577,333,282.0 |
| **Deduplicated total** |  | **86** | **37,985,808,862.2** |

The no-override Article-3-fallback counterfactual is smaller: 74 additional
datasets / 12,340,154,859 tokens per epoch. It excludes the four effective
datasets that already contain an Article 3 dependency and eight MAN-021
synthetic datasets whose captured QReCC/AESLC terms independently provide a
direct basis. Those eight contribute 36,848,262 tokens per epoch; the other 62
MAN-021 datasets contribute 38,032,290.

Narrow component measurements are available for the Sapient decisions:
Sudoku Extreme under MAN-006 contributes 178,000,000 tokens/epoch; RACE under
MAN-007 contributes 5,928,810,490; DREAM under MAN-008 contributes
192,229,708; the full mixed CoQA family under MAN-010 contributes 82,494,160;
TriviaQA under MAN-011 contributes 61,108,488.2; WebQuestions under MAN-009
contributes 15,845,676; non-factual FLAN under MAN-019 contributes
4,327,889,931.6; and the exact Tasksource residual under MAN-020 contributes
69,758,538.8. Only part of CoQA is governed by MAN-010, so its 82.494M figure
is an upper bound for that decision.

- MAN-001 through MAN-004 affect the five DOLCI Tool Use components,
  `allenai/Dolci-Instruct-SFT-Tool-Use`, and mixtures inheriting those rows.
- MAN-005 affects both filtered verifiable-reasoning releases and all DOLCI,
  Tulu, and DFM mixtures that inherit RLVE prompts.
- MAN-006 affects the Sapient Sudoku Extreme branch.
- MAN-007 through MAN-011 affect the retained Sapient factual-FLAN branch.
- MAN-012 affects WildChat itself and DFM/Synquid transformations retaining
  human prompts.
- MAN-013 and MAN-014 affect Tulu 3, DOLCI, Apertus/DFM Dyna, and any other
  mixtures inheriting FLAN v2 Converted or SciRIFF rows.
- MAN-015 affects Mixture-of-Thoughts and mixtures inheriting its math, code,
  science, or generated-trace rows.
- MAN-016 affects OpenHermes 2.5, the repaired English and Danish OpenHermes
  derivatives, SmolTalk imports, Apertus, and downstream DFM mixtures.
- MAN-017 affects LongAlign itself, SmolTalk/SmolTalk2 imports, Apertus, DFM
  Dyna, and downstream DFM mixtures.
- MAN-018 affects EuroBlocks' source-retaining and seed-derived components,
  Apertus, DFM Dyna, and downstream DFM mixtures.
- MAN-019 affects all four retained non-factual Sapient FLAN submixtures.
- MAN-020 affects the residual Tasksource source repositories and therefore the
  Sapient aggregate; it retains Article 3 as the working basis.
- MAN-021 affects all 70 `schneiderkamplab/sapient-synth-*` effective
  datasets. Their upstream-task edges remain in the DAG as informational
  provenance, while the synthetic derivatives themselves no longer inherit a
  blocking status from those edges.
- MAN-022 affects Tulu v2 SFT, Tulu v2 SFT Long, and SciRIFF Train Mix. It
  clears their shared ShareGPT dependency for the current research purpose
  without representing the anonymous mirror's Apache-2.0 label as a licence
  from conversation authors.

## Supplemental Agreement-Backed Audit Cohorts

These cohorts are cleared through data-owner agreements, not through the
manual decisions above. Their inclusion here is a testing-priority decision
only.

| Cohort | Training material to test | Proposed memorisation/propensity test |
|---|---|---|
| `Lex.dk` | Original `lexdk_articles.jsonl.gz` articles and their converted instruction targets | Extend the existing original-source prefix-extraction probe with exact/fuzzy continuation, rare-string, title-conditioned, and membership/propensity strata. |
| `DBC` | Original abstracts, reviews, Faktalink, and Forfatterweb JSONL sources and their converted instruction targets | Stratify by the four content families; test original-source prefixes, distinctive titles/names, exact/fuzzy continuation, and membership/propensity. |
| `oliverkinch/instruct-bt:dkmedier` | 486 agreement-covered news response passages plus synthetic prompts | Test both original passage prefixes and synthetic-prompt elicitation; report exact/fuzzy continuation and rare-string behavior separately. |
| `oliverkinch/instruct-bt:odense` | 337 agreement-covered news response passages plus synthetic prompts | Same source-prefix and prompt-conditioned tests, with an independent subset-level result. |
| `oliverkinch/instruct-bt:danskerhverv` | 281 agreement-covered news response passages plus synthetic prompts | Same source-prefix and prompt-conditioned tests, with an independent subset-level result. |

## Evidence

- `legal/reports/dfm9-dolci-toolu-component-audit.md`
- `legal/reports/dfm9-rlve-prompt-expression-audit.md`
- `legal/registers/dfm9-rlve-prompt-expression-audit.csv`
- `legal/reports/dfm9-sapient-synthetic-math-family-audit.md`
- `legal/reports/dfm9-sapient-factual-flan-family-audit.md`
- `legal/registers/dfm9-triviaqa-source-rights.csv`
- WildChat ICLR 2024 paper consent appendix and the source-rights DAG
- `legal/reports/dfm9-mot-copyright-risk.md`
- `legal/reports/dfm9-openhermes-component-audit.md`
- `legal/reports/dfm9-longalign-copyright-marker-audit.md`
- `legal/reports/dfm9-euroblocks-embedded-seed-audit.md`
- `legal/reports/dfm9-sapient-flan-tasksource-platypus-audit.md`
