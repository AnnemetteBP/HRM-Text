# DFM9 Copyright and EU TDM Triage

Status: source-level legal triage for the effective final DFM9 sample; not legal advice or final institutional approval.

## Scope and method

The register covers **161 top-level effective sources** and reconciles to **399,693,515,389 sampled tokens across five epoch index sets** (average **79,938,703,077.8 tokens/epoch**). It starts from the exhaustive DFM8 inventory and replaces the affected source exposures with exact DFM9 analytics.

A Hugging Face card or repository licence is treated as metadata, not proof that the publisher owned every embedded work. Mixtures and transformation datasets therefore retain their upstream lineage classification.

## Legal interpretation used

- [DSM Directive Articles 3 and 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790) are implemented in Denmark by [Copyright Act sections 11 c and 11 b](https://www.retsinformation.dk/eli/lta/2023/1093). Section 11 c is the candidate basis for reproductions/extractions by a qualifying research organisation for scientific research, where the project has lawful access and stores copies with appropriate security. Rights holders cannot contract out of section 11 c.
- Section 11 b is the general TDM route. It also requires lawful access, but fails where rights were expressly reserved in an appropriate manner. The project did not preserve complete acquisition-time opt-out evidence. FLAN v2, SciRIFF, and four uncovered OpenHermes families are recorded as project-owner Article 4 determinations despite that evidentiary limitation; this is not a general clearance of other sources under Article 4.
- Direct licences/public-domain status and agreements are used first. Article 3 is a fallback only for uncovered copyright/database-right components; it does not cure lack of lawful access.
- CC-BY-NC and CC-BY-NC-SA are direct permission only for uses satisfying NonCommercial and the other licence conditions. They are not treated as permission for future commercial use.

## Summary

| Classification | Sources | Tokens/epoch | Share |
|---|---:|---:|---:|
| `agreement_or_contract` | 2 | 669,511,768.8 | 0.84% |
| `article3_research_tdm_candidate` | 2 | 684,899,562.4 | 0.86% |
| `article3_research_tdm_for_uncovered_components` | 1 | 21,380,034,516.8 | 26.75% |
| `direct_noncommercial_licence` | 7 | 510,733,392.0 | 0.64% |
| `direct_open_licence_or_public_terms` | 28 | 24,652,721,447.8 | 30.84% |
| `explicit_publisher_training_permission` | 3 | 1,805,832,029.0 | 2.26% |
| `mixed_direct_and_manual_low_risk_acceptance` | 63 | 1,652,845,178.0 | 2.07% |
| `mixed_direct_and_participant_publication_permission` | 3 | 1,577,333,282.0 | 1.97% |
| `mixed_direct_licences_and_agreements` | 4 | 1,853,942,692.0 | 2.32% |
| `mixed_licences_and_article3_fallback` | 1 | 3,543,871,662.0 | 4.43% |
| `mixed_licences_and_article4` | 6 | 8,907,418,817.0 | 11.14% |
| `mixed_open_and_noncommercial_licences` | 4 | 251,016,144.0 | 0.31% |
| `mixed_open_licences_and_training_release_agreements` | 1 | 13,460,570.0 | 0.02% |
| `mixed_open_or_public_domain_licences` | 27 | 10,288,812,302.0 | 12.87% |
| `project_generated_derivative_of_open_source` | 3 | 279,605,417.0 | 0.35% |
| `project_generated_direct` | 6 | 1,866,664,297.0 | 2.34% |

## Answer to the three-way question

1. **OK through other licensing/status:** 147 sources, 43,568,535,827.6 average tokens/epoch (54.50%), but only within the recorded scope and obligations.
2. **Require the research TDM exception for the current project:** 3 sources, 22,064,934,079.2 average tokens/epoch (27.60%), for all or some content. Another 1 mixed derivative sources, 3,543,871,662.0 average tokens/epoch (4.43%), may require Article 3 only for uncovered components.
3. **Use the regular/non-research TDM exception:** 6 mixed sources, 8,907,418,817.0 average tokens/epoch (11.14%), currently use section 11 b/Article 4 for uncovered FLAN v2, SciRIFF, and four OpenHermes source families by project-owner determination. Other Article-3-dependent sources/components would also need Article 4 for non-research retraining unless direct permission is obtained, but are not currently cleared under that route.

## Sources by classification

### `agreement_or_contract`

- `DBC`
- `Lex.dk`

### `article3_research_tdm_candidate`

- `allenai/verifiable-reasoning-filtered-gpt-41`
- `allenai/verifiable-reasoning-filtered-o4-mini`

### `article3_research_tdm_for_uncovered_components`

- `sapientinc/HRM-Text-data-io-cleaned-20260515`

### `direct_noncommercial_licence`

- `HuggingFaceH4/no_robots`
- `kobprof/skolegpt-instruct`
- `MegaScience/TextbookReasoning`
- `schneiderkamplab/sapient-synth-flan-flan-fsnoopt-data-aeslc-1.0.0`
- `schneiderkamplab/sapient-synth-flan-flan-fsopt-data-aeslc-1.0.0`
- `schneiderkamplab/sapient-synth-flan-flan-zsnoopt-data-aeslc-1.0.0`
- `schneiderkamplab/sapient-synth-flan-flan-zsopt-data-aeslc-1.0.0`

### `direct_open_licence_or_public_terms`

- `allenai/Dolci-Instruct-SFT-Tool-Use-SA`
- `allenai/open_math_2_50k_r1-original`
- `allenai/RLVR-GSM`
- `danish-foundation-models/kaenguruen`
- `danish-foundation-models/laerebogen`
- `GEM/wiki_cat_sum`
- `glaiveai/glaive-function-calling-v2`
- `laion/Scientific-Summaries`
- `nvidia/AceReason-1.1-SFT`
- `nvidia/Nemotron-SFT-Agentic-v2`
- `nvidia/Nemotron-SFT-Multilingual-v1`
- `nvidia/OpenMathInstruct-2`
- `oliverkinch/danish-qa`
- `oliverkinch/danmarks-statistik-bt`
- `oliverkinch/doab-da-bt`
- `oliverkinch/dst-table-prompts-bt`
- `oliverkinch/machine-translation-da-ar`
- `oliverkinch/machine-translation-da-en`
- `oliverkinch/machine-translation-da-uk`
- `oliverkinch/multi-wiki-qa-high-quality-subset`
- `oliverkinch/tidsskrift-dk-bt`
- `open-thoughts/OpenThoughts2-1M`
- `Salesforce/xlam-function-calling-60k`
- `schneiderkamplab/sapient-synth-flan-dialog-fsopt-data-qrecc`
- `schneiderkamplab/sapient-synth-flan-dialog-fsopt-data-qrecc-ii`
- `schneiderkamplab/sapient-synth-flan-dialog-zsopt-data-qrecc`
- `schneiderkamplab/sapient-synth-flan-dialog-zsopt-data-qrecc-ii`
- `Team-ACE/ToolACE`

### `explicit_publisher_training_permission`

- `nvidia/Nemotron-SFT-Instruction-Following-Chat-v2`
- `synquid/ifbench-train`
- `synquid/wildchat-100k-qwen-messages`

### `mixed_direct_and_manual_low_risk_acceptance`

- `allenai/Dolci-Instruct-SFT-Tool-Use`
- `schneiderkamplab/sapient-synth-flan-flan-fsnoopt-data-opinion-abstracts-idebate`
- `schneiderkamplab/sapient-synth-flan-flan-fsnoopt-data-opinion-abstracts-rotten-tomatoes`
- `schneiderkamplab/sapient-synth-flan-flan-fsopt-data-opinion-abstracts-idebate`
- `schneiderkamplab/sapient-synth-flan-flan-fsopt-data-opinion-abstracts-rotten-tomatoes`
- `schneiderkamplab/sapient-synth-flan-flan-zsnoopt-data-opinion-abstracts-idebate`
- `schneiderkamplab/sapient-synth-flan-flan-zsnoopt-data-opinion-abstracts-rotten-tomatoes`
- `schneiderkamplab/sapient-synth-flan-flan-zsopt-data-opinion-abstracts-idebate`
- `schneiderkamplab/sapient-synth-flan-flan-zsopt-data-opinion-abstracts-rotten-tomatoes`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1309-amazonreview-summary-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1370-newscomm-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1371-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1373-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1374-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1375-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1376-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task1377-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task264-paper-reviews-accept-reject`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task265-paper-reviews-language-identification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task266-paper-reviews-reviewer-perspective`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task589-amazonfood-summary-text-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task590-amazonfood-summary-correction-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task618-amazonreview-summary-text-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task634-allegro-reviews-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task635-allegro-reviews-answer-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task672-amazon-yelp-summarization`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task870-msmarco-answer-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task871-msmarco-question-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task902-deceptive-opinion-spam-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task903-deceptive-opinion-spam-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task906-dialogre-identify-names`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task907-dialogre-identify-relationships`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task908-dialogre-identify-familial-relationships`
- `schneiderkamplab/sapient-synth-flan-niv2-fsopt-data-task909-dialogre-prevalent-speakers`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1309-amazonreview-summary-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1370-newscomm-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1371-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1373-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1374-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1375-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1376-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task1377-newscomm-translation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task264-paper-reviews-accept-reject`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task265-paper-reviews-language-identification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task266-paper-reviews-reviewer-perspective`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task589-amazonfood-summary-text-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task590-amazonfood-summary-correction-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task618-amazonreview-summary-text-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task634-allegro-reviews-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task635-allegro-reviews-answer-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task672-amazon-yelp-summarization`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task870-msmarco-answer-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task871-msmarco-question-generation`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task902-deceptive-opinion-spam-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task903-deceptive-opinion-spam-classification`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task906-dialogre-identify-names`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task907-dialogre-identify-relationships`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task908-dialogre-identify-familial-relationships`
- `schneiderkamplab/sapient-synth-flan-niv2-zsopt-data-task909-dialogre-prevalent-speakers`
- `schneiderkamplab/sapient-synth-platypus-reclor`
- `schneiderkamplab/sapient-synth-platypus-scibench`
- `schneiderkamplab/sapient-synth-tasksource-pragmeval-sarcasm`
- `schneiderkamplab/sapient-synth-tasksource-reclor`

### `mixed_direct_and_participant_publication_permission`

- `allenai/SciRIFF-train-mix`
- `allenai/tulu-v2-sft-long-mixture`
- `allenai/tulu-v2-sft-mixture`

### `mixed_direct_licences_and_agreements`

- `schneiderkamplab/transformations-danish-danish`
- `schneiderkamplab/transformations-danish-english`
- `schneiderkamplab/transformations-english-danish`
- `schneiderkamplab/transformations-english-english`

### `mixed_licences_and_article3_fallback`

- `danish-foundation-models/dfm-dyna-instruct`

### `mixed_licences_and_article4`

- `allenai/Dolci-Instruct-SFT`
- `allenai/Dolci-Instruct-SFT-No-Tools`
- `allenai/IF_sft_data_verified`
- `allenai/tulu-3-sft-mixture`
- `schneiderkamplab/dfm8-openhermes-da`
- `schneiderkamplab/dfm8-openhermes-en`

### `mixed_open_and_noncommercial_licences`

- `allenai/tulu-3-sft-personas-algebra`
- `allenai/tulu-3-sft-personas-code`
- `allenai/tulu-3-sft-personas-instruction-following`
- `allenai/tulu-3-sft-personas-math`

### `mixed_open_licences_and_training_release_agreements`

- `oliverkinch/instruct-bt`

### `mixed_open_or_public_domain_licences`

- `allenai/big-reasoning-traces`
- `allenai/RLVR-MATH`
- `ccdv/govreport-summarization`
- `common-pile/arxiv_papers_filtered`
- `danish-foundation-models/ai_arena_udtraek`
- `oliverkinch/autodata-da-sft`
- `oliverkinch/da-instruct-dynaword`
- `oliverkinch/da-instruct-dynaword-contemporary`
- `oliverkinch/da-instruct-dynaword-contemporary-hq`
- `oliverkinch/da-instruct-dynaword-hq`
- `oliverkinch/danish-summarization`
- `oliverkinch/danish-university-portals-bt`
- `oliverkinch/dynaword-bt`
- `oliverkinch/eur-lex-bt`
- `oliverkinch/eur-lex-sum-instruct`
- `schneiderkamplab/common-pile-denoising`
- `schneiderkamplab/common-pile-paragraph-reordering`
- `schneiderkamplab/common-pile-prefix-continuation`
- `schneiderkamplab/common-pile-span-filling`
- `schneiderkamplab/danish-dynaword-denoising`
- `schneiderkamplab/danish-dynaword-paragraph-reordering`
- `schneiderkamplab/danish-dynaword-prefix-continuation`
- `schneiderkamplab/danish-dynaword-span-filling`
- `schneiderkamplab/opus-da-en-permissive`
- `synquid/mt-da-deepseek`
- `synquid/translation-100k`
- `synquid/wiki-instruct-da`

### `project_generated_derivative_of_open_source`

- `giannor/dala_tv2r_it`
- `giannor/gec_dala_tv2r_it`
- `synquid/danish-verifiable-reasoning`

### `project_generated_direct`

- `schneiderkamplab/dfm8-synthetic-code-debugging`
- `schneiderkamplab/dfm8-synthetic-constrained-format-following`
- `schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls`
- `schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat`
- `schneiderkamplab/dfm8-synthetic-native-tool-calling`
- `schneiderkamplab/dfm8-synthetic-strict-math-answer-contract`

## Blocking human/legal checks

- Confirm SDU/DFM and this training activity satisfy Article 3's research-organisation, scientific-research, lawful-access, beneficiary and secure-retention conditions.
- Classify the DBC and Lex.dk agreements for the Commission template and review any unconfirmed retention, source-redistribution, attribution, duration, security and downstream-use terms; training and model release are confirmed.
- Preserve the recorded component decisions for Sapient, DOLCI, and DFM Dyna; FLAN v2, SciRIFF, and four OpenHermes families use project-owner Article 4 determinations, MoT uses a residual-risk acceptance, and WildChat, TV2R, and four source-retaining transformation datasets have recorded direct bases, with privacy controls separate.
- Review third-party generator-output terms for the four Tulu persona sources.
- For any non-research retraining, perform a fresh Article 4 opt-out check at acquisition time; current HF tags are not enough.

Machine-readable detail: `legal/registers/dfm9-copyright-basis-register.csv`.
Component-level evidence: `legal/reports/dfm9-article3-component-audit.md`.
