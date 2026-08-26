# DFM9 Copyright Audit Status - 2026-08-18

Status: engineering/legal triage for the current academic/non-commercial
scientific-research purpose; not legal advice or commercial-use clearance.

## Effective-Dataset Status

The declarative DAG contains all 161 effective DFM9 datasets and reconciles to
79,938,703,077.8 tokens per epoch, or 399,693,515,389 tokens over five epochs.

| Computed status | Effective datasets | Tokens/epoch | Share | Five-epoch tokens |
|---|---:|---:|---:|---:|
| Cleared | 161 | 79,938,703,077.8 | 100.00% | 399,693,515,389.0 |
| Partial | 0 | 0 | 0.00% | 0 |
| Unresolved | 0 | 0 | 0.00% | 0 |

Of the cleared datasets, 150 datasets/74,967,702,117.8 tokens per epoch have
complete dependency declarations. Another 11 datasets/4,971,000,960 tokens per
epoch are cleared on their recorded top-level basis but still need provenance
expansion. “Cleared” is purpose-specific and does not mean open licensed.

Of all effective sources, **157 sources / 54,329,897,336.6 tokens per epoch
(67.96%)** are both DAG-cleared and do not rely on Article 3. This count
includes project-owner Article 4, low-risk, and participant-publication
decisions, including MAN-021 and MAN-022. The other four cleared sources /
25,608,805,741.2 tokens per epoch use Article 3 for at least one component.

The prior six-source count was superseded after reconciling the completed DOLCI
component DAG with the source-level rights algebra. `Dolci-Instruct-SFT` and
`Dolci-Instruct-SFT-No-Tools` resolve through direct terms, MAN-001 through
MAN-004, express permission, and MAN-013/MAN-014 Article 4 decisions; neither
retains a required Article 3 component.

MAN-017 and MAN-018 close the remaining LongAlign and EuroBlocks human
boundary review for current Article 3 scientific-research use. They do not
change the effective counts because the DAG already represented these leaves
as cleared under Article 3; the decisions change their review state from
unapproved fallback to expressly approved fallback.

## Remaining Exposure

MAN-021 manually approves all 70 `schneiderkamplab/sapient-synth-*`
derivatives. Their named upstream-task links remain in the DAG as provenance
and memorisation-test evidence, but no longer propagate blocking status into
the synthetic effective datasets. The Sapient aggregate is complete:
non-factual FLAN uses direct terms plus MAN-019 Article 4, Platypus uses direct
component terms, and only 69.759M tokens/epoch in Tasksource retain Article 3
under MAN-020.

The four former aggregate-level unresolved sources have now been decomposed.
IF SFT Verified is cleared through exact Tulu-3 ID lineage. MAN-022 accepts
deliberate ShareGPT publication as permission for current academic/non-commercial
research training, clearing Tulu v2 SFT, Tulu v2 SFT Long, and SciRIFF Train
Mix for that purpose. Privacy, raw redistribution, and nonresearch scope remain
separate.

## Next High-Impact Targets

1. **Cleared but top-level-only provenance:** permissive OPUS DA-EN (2.903B)
   and Big Reasoning Traces (1.657B) are the largest documentation-completeness
   targets. They do not currently block approval but should be decomposed for
   a stronger reproducibility dossier.

## Top-Level-Only Decomposition Triage

Eleven effective datasets, totalling 4,971,000,960 tokens per epoch, currently
have only a top-level provenance declaration. They do not all need the same
additional work. Decomposition is warranted where one aggregate contains
materially different source bases, licences, or obligations:

| Effective dataset | Tokens/epoch | Decomposition decision | Reason |
|---|---:|---|---|
| `allenai/big-reasoning-traces` | 1,656,898,949 | Recommended | GeneralThought, OpenThoughts, and OpenR1-Math are separately identifiable components. Their current result is permissive, but component licences/notices and provenance should remain separable. |
| `common-pile/arxiv_papers_filtered` | 129,586,132 | Required for complete obligations accounting | Rows span CC BY, CC BY-SA, and CC0; group by retained per-record licence. |
| `oliverkinch/danish-summarization` | 168,358,988 | Required | EUR-Lex and Nordjylland/DynaWord use different source bases. |
| `oliverkinch/instruct-bt` | 13,460,570 | Required | Six DynaWord/open-public subsets and three agreement-backed subsets have different bases; preserve each agreement subset separately. |
| `schneiderkamplab/opus-da-en-permissive` | 2,903,437,259 | Required | OPUS component corpora have different permissive/public-domain licences and notice obligations. |
| `allenai/RLVR-MATH` | 8,067,070 | Not needed | The effective rows are one homogeneous MATH/MIT family. |
| `ccdv/govreport-summarization` | 4,412,302 | Not needed for the present result | GAO and CRS are both treated as US-government/public-domain sources; retain the existing source field for attribution and later embedded-work checks. |
| `danish-foundation-models/ai_arena_udtraek` | 45,690,600 | Not needed for copyright | ComparIA conversation/reaction data has one operative Etalab Open Licence basis. Privacy stratification is a separate control. |
| `oliverkinch/danish-university-portals-bt` | 21,765,750 | Not needed | One CC BY source family. |
| `oliverkinch/eur-lex-bt` | 16,694,550 | Not needed | One EUR-Lex source family. |
| `oliverkinch/eur-lex-sum-instruct` | 2,628,790 | Not needed | One EUR-Lex source family. |

Thus four aggregates require decomposition to distinguish current legal bases,
and `big-reasoning-traces` should also be decomposed for licence/notice and
reproducibility accounting. The other six are homogeneous for this audit.

## Narrow Article 3 Boundary

The 25,608,805,741.2-token headline is deliberately conservative aggregate
accounting: if any component of an effective dataset uses Article 3, all
sampled tokens from that effective dataset are counted. It is not an estimate
of the amount of Article-3-dependent expression.

The current narrow component estimate is **414,056,526 tokens per epoch**, or
**0.518% of DFM9**:

| Boundary | Estimated sampled tokens/epoch | Method |
|---|---:|---|
| Sapient Tasksource residual | 69,758,538.8 | Exact sampled file accounting: 84 residual files under MAN-020. |
| RLVE prompt-expression boundary | 160,437,653 | Proportional application of each RLVE dataset's actual DFM9 sampling ratio to the close/constrained, expressive, unavailable-source, and unmatched prompt bins. |
| LongAlign and EuroBlocks inside DFM Dyna/Apertus | 183,860,334.5 | Gemma-4-template measurement found 167,379,533 LongAlign tokens and 55,864,889 Article-3-boundary EuroBlocks tokens before DFM9 sampling. Their 223,244,422-token total is scaled by the Apertus sampling ratio, 3,033,512,464 / 3,683,310,696. |

The Sapient number is exact. The RLVE and Apertus numbers are proportional
estimates because the saved aggregate epoch indices do not retain component
labels. An exact reconstruction would require mapping every sampled sequence
back to its pre-tokenization component row. The estimate is nevertheless much
closer to the legal boundary than whole-aggregate accounting.

## Counterfactual Without Manual Overrides

Removing a manual decision does not automatically make its source legally
usable under Article 3; strictly, it makes that source unresolved pending a
replacement basis. For risk-envelope planning only, if each affected source
were conservatively assigned Article 3 as the replacement fallback, **74
additional effective datasets / 12,340,154,859 tokens per epoch** would become
Article-3-dependent. Together with the current four, that is **78 effective
datasets / 37,948,960,600.2 aggregate tokens per epoch (47.47% of DFM9)**.

The 74 additions comprise 62 MAN-021 Sapient synthetic derivatives, three
DOLCI aggregates, three MAN-022 ShareGPT mixtures, two WildChat descendants,
two OpenHermes derivatives, and two FLAN-v2/SciRIFF descendants. Manual
decisions nested inside Sapient or DFM Dyna do not add another effective
dataset because those two aggregates already have Article 3 dependencies;
they would enlarge the narrow component boundary instead.

## Decision Boundary

The LongAlign and EuroBlocks approvals retain Article 3's lawful-access,
research-organisation, scientific-purpose, security, and purpose-bound
retention conditions. Restrictive notices, unidentified documents, source
hashes, and memorisation-test cohorts remain evidence rather than being
discarded by the approval.

ShareGPT instead uses MAN-022's purpose-limited participant-publication
permission acceptance. It does not establish an open licence, raw-data
redistribution permission, nonresearch authorization, or GDPR compliance.
