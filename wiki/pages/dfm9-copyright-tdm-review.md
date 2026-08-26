---
type: Analysis
title: DFM9 Copyright and EU TDM Review
description: Token-reconciled source-level copyright and EU TDM triage for every effective DFM9 repository or agreement source.
tags: [dfm9, copyright, legal, tdm, datasets]
status: draft
last_updated: 2026-08-22
confidence: medium
sources:
  - id: dsm-directive
    resource: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790
    title: Directive (EU) 2019/790
    author: org:European Union
  - id: danish-copyright-act
    resource: https://www.retsinformation.dk/eli/lta/2023/1093
    title: Danish Copyright Act
    author: org:Danish Ministry of Culture
  - id: aeslc-repository
    resource: https://github.com/ryanzhumich/AESLC
    title: Annotated Enron Subject Line Corpus
    author: person:Rui Zhang
  - id: flan-repository
    resource: https://github.com/google-research/FLAN
    title: The FLAN Collection
    author: org:Google Research
  - id: qrecc-repository
    resource: https://github.com/apple/ml-qrecc
    title: Open-Domain Question Answering Goes Conversational via Question Rewriting
    author: org:Apple
  - id: opinion-abstracts-tfds
    resource: https://www.tensorflow.org/datasets/catalog/opinion_abstracts
    title: Opinion Abstracts
    author: org:TensorFlow Datasets
---
# DFM9 Copyright and EU TDM Review

**Superseded correction, 2026-08-17:** the 2026-08-16 statement that DFM9 had
168 effective sources and 93,929,976,190 sampled tokens per epoch was wrong.
That token figure is the concatenated token-store size, not index-set exposure.
Seven prospective/tokenized additions were not referenced by the effective
DFM9 sample.

The corrected review covers **161 effective top-level DFM9 sources** and
reconciles exactly to **399,693,515,389 covered tokens across five epoch index
sets**, averaging **79,938,703,077.8 tokens/epoch**. The source of truth is
`data/show_analytics_dfm9.md`, checked against the sampled index coverage.

## Current Reconciled Result

This table supersedes the initial triage; dated decisions retain the history.

| Working basis | Sources | Average tokens/epoch | Share |
|---|---:|---:|---:|
| Cleared without Article 3 reliance | 157 | 54,329,897,336.6 | 67.96% |
| Cleared for current research with an Article 3 component | 4 | 25,608,805,741.2 | 32.04% |

For a non-research retraining, the Article-3-dependent sources or components
would instead require direct permission or the general TDM route in DSM
Article 4 / Danish Copyright Act section 11 b. They are **not currently
cleared under that route** because complete acquisition-time rights-reservation
evidence was not preserved. Section 11 b also requires lawful access and is
unavailable where rights were appropriately reserved.

## Interpretation Boundaries

- Direct licence is primary where its scope covers the actual work. A
  repository or database-container licence does not prove that every embedded
  third-party work is covered.
- CC-BY-NC and CC-BY-NC-SA are direct permission only while the use satisfies
  the NonCommercial condition and all attribution/share-alike requirements.
- ODC-By addresses database rights but does not alone clear copyright in every
  content item.
- Article 3 / section 11 c is conditional on SDU/DFM qualifying as the
  beneficiary, scientific-research purpose, lawful access, and appropriately
  secure storage. It does not authorize redistribution of the source corpus.
- The TDM exceptions address reproduction and extraction during TDM. They do
  not by themselves settle the copyright status of model weights, memorized
  output, public dataset redistribution, or downstream deployment.

Update, 2026-08-16: the project owner confirmed that the DynaWord and Common
Pile source passages selected for the project-generated DFM8 synthetic data are
public domain or open licensed. Those generated datasets and the corresponding
source-retaining DynaWord/Common Pile derivatives therefore use direct
project-held/per-source rights, not Article 3, provided source-level attribution
and ShareAlike obligations remain traceable. This confirmation does not extend
to Sapient, OpenHermes, DBC, Lex.dk, or other seed families.

Update, 2026-08-17: the project owner confirmed that all components of
`oliverkinch/instruct-bt` are covered for model training and release. DynaWord
is governed by its retained source terms; `dkmedier`, `odense`, and
`danskerhverv` are covered by agreements between Danish Foundation Models and
the respective data owners. The register therefore no longer assigns this
dataset to the Article 3 candidate category.

The local `oliverkinch/danish-summarization` files contain two explicitly
identified seed datasets:

- `oliverkinch/eur-lex-sum`: 831 downloaded rows, of which 36 fit the active
  4096-token sampling constraints; 490,328 sampled tokens per DFM9 epoch.
- `alexandrainst/nordjylland-news-summarization`: 63,855 downloaded rows, of
  which 63,847 fit; 167,868,660 sampled tokens per DFM9 epoch. Its local card
  identifies the texts as TV2 Nord news articles collected through the TV2
  Nord API and declares CC0-1.0.

Thus `danish-summarization` contributes 168,358,988 tokens per DFM9 epoch and
is 99.71% Nordjylland by sampled tokens. On 2026-08-17 the project owner
confirmed that EUR-Lex Sum is public-domain/CC-BY derived and that Nordjylland
is part of the accepted DynaWord source family. The register therefore uses
the applicable direct per-source terms rather than Article 3 for this
aggregate.

Update, 2026-08-17: component/row-level audits resolved five additional
copyright fallbacks to direct source status:

- `danish-foundation-models/ai_arena_udtraek` follows the Etalab Open Licence
  2.0 declared for its ComparIA conversation/reaction sources; privacy remains
  a separate review.
- `synquid/translation-100k` identifies the covered Oliver/OPUS source and
  source corpus in every row.
- `synquid/mt-da-deepseek`, `allenai/RLVR-MATH`, and
  `ccdv/govreport-summarization` follow, respectively, the confirmed
  DynaWord/project basis, MIT-licensed MATH lineage, and GAO/CRS government
  publication status.

At that point the pass retained Article 3 for WildChat messages, AllenAI
verifiable-reasoning and Open Math releases, and retained component fallback
for SciRIFF, IF SFT, Danish verifiable reasoning, and IFBench. This result is
partly superseded: the later WildChat permission decision cleared WildChat and
IFBench, while Ai2's authorship statement for the DOLCI logic-puzzle prompts
cleared Danish verifiable reasoning. AllenAI verifiable reasoning, Open Math,
Open Math and IF SFT remain unresolved. FLAN v2 and SciRIFF were subsequently
moved to Article 4 by project-owner decision. The earlier Giannor fallback is also
superseded by the TV2R provenance and DFM-contributor confirmations recorded on
2026-08-17.

Update, 2026-08-17: the project owner confirmed that Oliver Kinch and Synquid
work as part of DFM. Their authored transformations, generated content, labels,
metadata, and wrappers are authorized project contributions. This clears only
their contribution layer: retained DOLCI/WildChat or other upstream expression
continues to follow its source-specific classification.

Update, 2026-08-17: the project owner confirmed that the confidential DBC and
Lex.dk agreements both permit model training and model release. They therefore
remain direct agreement sources and do not need Article 3 for those acts. The
remaining `LEG-008`/`LEG-009` review is limited to Commission-template
agreement classification and any unconfirmed retention, source-redistribution,
attribution, duration, security, or broader downstream-use terms.

Update, 2026-08-18: agreement clearance does not remove the need for empirical
memorisation testing. The future memorisation/propensity audit cohort now
includes Lex.dk; DBC stratified into abstracts, reviews, Faktalink, and
Forfatterweb; and the agreement-covered `dkmedier`, `odense`, and
`danskerhverv` subsets of `oliverkinch/instruct-bt`. These are supplemental
test cohorts, not manual legal overrides. See
`legal/reports/dfm9-manual-acceptances-and-overrides.md`.

## DOLCI SFT Decomposition

Update, 2026-08-17: local parquet counts and the Ai2 cards decompose the DOLCI
family rather than treating its ODC-By container as one source.

| Effective dataset | Rows | Decomposition |
|---|---:|---|
| `allenai/Dolci-Instruct-SFT` | 2,152,112 | 22 exact source labels: 21 non-tool families plus Tool Use |
| `allenai/Dolci-Instruct-SFT-No-Tools` | 1,924,533 | Exactly the same 21 non-tool families; all 227,579 Tool Use rows are absent |
| `allenai/Dolci-Instruct-SFT-Tool-Use` | 227,579 | Five exact `dataset_source` labels |
| `allenai/Dolci-Instruct-SFT-Tool-Use-SA` | 1,604 | Separately licensed CC-BY-SA subset; already direct |

The non-tool families are OpenThoughts3, CoCoNot, FLAN v2, OASST1, four Tulu
persona sets, WildGuardMix, WildJailbreak, Aya, TableGPT, SciRIFF, Evol
CodeAlpaca, OpenMathInstruct-2, WildChat, logic puzzles, Precise IF, Python
Algorithms, Verifiable Reasoning, and hardcoded data. Ai2 calls the last five
families new prompts from Ai2. This clears the Ai2-authored contribution and
the twelve named logic-puzzle leaves for current research use under the DOLCI
ODC-By/research release, but it does not replace terms for retained upstream
prompts.

The Tool Use rows reconcile exactly to five internal mixtures: BFCLv3
decontaminated (`200,000`), S2 M4v2 (`9,085`), S2 M3 (`8,074`), S2 M5v2
(`5,417`), and DeepResearch DRv4 (`5,003`). A subsequent 2026-08-17 audit
traced these through the OLMo 3 paper and local rows. The BFCL-labelled data is
SimFC: 93,593 rows touch xLAM schemas, at least 45,577 touch ToolACE schemas,
and 92,800 have no local match to either source. The S2 sets are Science QA;
1,580 M3, 8,838 M4v2, and 5,304 M5v2 rows contain scholarly abstract fields.
All 5,003 DRv4 prompts were mapped: 2,572 SearchArena, 1,685 OpenSciLM, 692
TaskCraft, 49 WebWalkerQA, and five residual rows.

The Ai2-generated trajectories and named directly licensed prompt/API sources
are cleared as layers. **Superseded status, 2026-08-17:** full DOLCI Tool Use
was partial through the unassigned/adapted SimFC schema pool, third-party
scholarly content, five residual prompts, and source-specific web-search
snippets. Professor Peter Schneider-Kamp, as project owner, subsequently
accepted those four documented residual layers as low risk for current
academic/non-commercial scientific-research training and downstream-mixture
consideration, with no identified material reason to invoke Article 3. The DAG
now clears the Tool Use branch. Article 4 is only a conditional alternative
where lawful access and absence of an effective reservation are evidenced; the
audit does not establish those conditions for every residual item. Findings,
provenance gaps, and source-specific obligations remain recorded. See
`legal/reports/dfm9-dolci-toolu-component-audit.md`. The Tulu Persona branch
was cleared by the subsequent family audit below. FLAN v2 and SciRIFF were
subsequently assigned Article 4 for uncovered expression; other mixed-source
dependencies retain their separately recorded status.

### Tulu 3 Persona family

Update, 2026-08-17: the four directly sampled Persona datasets contribute
234,939 rows and 251,016,144 tokens per DFM9 epoch. Older aliases plus filtered
MATH and grade-school variants are shared by DOLCI, Tulu/OLMo, and DFM Dyna.
The Tulu report traces these to PersonaHub conditioning, GPT-4o generation,
Claude 3.5 Sonnet Python solutions, Ai2-authored IF examples, and the IFEval
constraint taxonomy. The apparent `GSM` label means generated grade-school
math; no retained GSM8K seed is identified.

The family is cleared for current academic/non-commercial scientific-research
training without Article 3 reliance. Apply ODC-By attribution and PersonaHub
CC-BY-NC-SA attribution, ShareAlike, and NonCommercial scope; retain the open
IFEval notices. Provider terms assign model outputs to the generating customer,
but Ai2's account-specific compliance is not independently archived. Detailed
lineage and aliases are in
`legal/reports/dfm9-tulu3-persona-family-audit.md`.

## AllenAI And Salesforce Findings

The unresolved AllenAI issue is generally **missing release/provenance
evidence**, not evidence of a known prohibition. The following earlier
schema-only assessment is superseded by the 2026-08-17 lineage audit:

- `verifiable-reasoning-filtered-gpt-41` (`284,820` rows) and
  `verifiable-reasoning-filtered-o4-mini` (`241,265` rows) expose 238 mostly
  programmatic reasoning categories. Their IDs map to 250 RLVE-Gym environment
  variants. RLVE-Gym is MIT and procedurally generates/verifies instances, but
  its source comments cite external problem sources for 122 variants: 115
  Luogu, three Codeforces, and one each from HDU, SPOJ, X, and Wikipedia.
  **Superseded count correction, 2026-08-17:** `127,865/284,820` GPT-4.1
  rows and `106,059/241,265` o4-mini rows map to the 122 externally cited
  variants. Another `4,921` and `4,107` rows, respectively, belong to four
  currently unmatched variants. The earlier combined figures of 128,466 and
  106,166 were incorrect. The MIT generator licence does not automatically
  license protected expression adapted from cited statements, but the
  prompt-level audit below materially narrows the layer for which that concern
  is plausible; there is no evidence that these releases scrape general web,
  personal, or user-conversation data.
- `open_math_2_50k_r1-original` has `49,829` rows: `40,841` augmented GSM8K and
  `8,988` GSM8K problems with regenerated R1-family answers. **Superseded:** it
  is not retained as Article 3 merely because it derives from GSM8K. The fields
  and examples trace to NVIDIA OpenMathInstruct-2 (CC-BY-4.0); GSM8K is MIT;
  and DeepSeek-R1's MIT terms expressly permit distillation and training other
  models. Treat it as direct open-licence lineage, preserving attribution and
  notices.
- `IF_sft_data_verified` has `31,751` rows, all marked
  `tulu-3-sft-mixture+IF-constraints`. It therefore inherits the mixed Tulu 3
  prompt dependencies; the card does not separately establish the generated
  constraint/completion layer.
- DOLCI's Ai2-authored prompt layer is now recorded as direct, but its retained
  upstream families and five ToolU mixtures remain source-dependent as above.

`Salesforce/xlam-function-calling-60k` is different. Its current card declares
CC-BY-4.0 and describes 60,000 synthetic, execution/format/semantic-verified
APIGen rows from 3,673 executable APIs. Salesforce also states in the official
HF discussion that DeepSeek confirmed redistribution of its generated outputs
under CC-BY-4.0; the other generator, Mixtral-8x22B, is Apache-2.0. The earlier
unresolved status is superseded: xLAM is direct for the current use, subject to
CC attribution, gated-access terms, and retention of any supplied API/source
notices. API-schema provenance remains a notice/compliance check rather than a
current Article 3 blocker.

## RLVE Prompt-Level Expression Bins

Update, 2026-08-17: all 250 retained ID-prefix variants were reviewed against
their mapped RLVE prompt templates and, where cited, the identified source
problem. This supersedes treating every source-commented environment as if it
necessarily retained protected source expression.

| Bin | Variants | GPT-4.1 rows | o4-mini rows | Working treatment |
|---|---:|---:|---:|---|
| Native RLVE generator; no external source comment | 124 | 152,034 | 131,099 | MIT generator layer; no external expression identified |
| Functional abstraction or material rewrite | 61 | 66,247 | 55,226 | No material source expression identified in comparison |
| Close but constrained restatement | 45 | 45,074 | 37,563 | Prompt-specific human review; conservative Article 3 fallback if retained |
| Expressive or source-specific carryover | 15 | 14,311 | 11,484 | Direct permission or Article 3 prudent |
| Cited source unavailable | 1 | 2,233 | 1,786 | Unresolved |
| Dataset variant unmatched to RLVE | 4 | 4,921 | 4,107 | Unresolved |

The strongest carryover cases retain ASCII diagrams, distinctive worked
examples, coined B/I/F and FBI terminology, the A::B token-rewrite system, or
other bespoke rule systems. The carryover bin is about 5% of rows in either
release; the close-restatement bin is about 16%. Current Luogu English pages
are comparison proxies and often machine translations, so these bins are
triage findings rather than final originality/infringement conclusions. The
full 250-row evidence is in
`legal/registers/dfm9-rlve-prompt-expression-audit.csv`; the method and
interpretation are documented in
`legal/reports/dfm9-rlve-prompt-expression-audit.md`.

Within the 15 carryover variants, the audit assigns the clearest copyright
concern to `blockimage`, `powernest`, `fbi_binarytree`, and
`abprogramsimulation`. Six are medium concern because they retain a
source-specific example, coined term, scenario, or ordered rule presentation;
five are lower concern because the retained substance is predominantly
functionality expressed in new language. Keep this severity distinction when
deciding exclusions or obtaining counsel rather than treating all 15 alike.

Manual policy override, 2026-08-17: the project owner accepts the complete RLVE
prompt family, including close, carryover, unavailable, and unmatched bins, for
the current academic/research model-training scope. Downstream datasets and
mixtures are not blocked merely because they inherit these RLVE prompts. The
underlying findings remain documented. This does not relabel the sources as
open licensed and does not remove the Article 3 fallback where protected
expression is retained; it is an explicit project risk-acceptance/inclusion
decision.

## Transformation Family Decomposition

Update, 2026-08-17: all four `schneiderkamplab/transformations-*` datasets were
added to the DAG worklist and fully decomposed using their accepted-row audit
summaries. The project-generated Gemma 4 transformation/audit layer is
Apache-2.0 and every exported row matched accepted generation metadata.

- Danish-to-Danish (`208,117` rows) and Danish-to-English (`211,401`) use
  DynaWord, Laerebogen, Danish Wikipedia instructions, Lex.dk, and four named
  Oliver Kinch sources. Those source families are covered by open terms,
  project authorization, or confirmed DFM/data-owner agreements.
- English-to-Danish (`246,288` rows) and English-to-English (`248,474`) use
  LAION scientific summaries, Common-Pile arXiv summaries, GovReport, DBC,
  Lex.dk, and 369/366 ASSET seed rows. These follow their recorded open/public,
  CC-BY-SA, or agreement bases.

The four roots contribute `1,853,942,692` sampled tokens per DFM9 epoch. They
now compute as cleared direct mixed-source derivatives; the former generic
Article 3 fallback is superseded.

## AESLC Synthetic Variants

Update, 2026-08-17: four effective DFM9 repositories share one AESLC task
dependency because the FLAN collection materialized a Cartesian product of
prompt regimes: `fs`/`zs` means few-shot/zero-shot, while `opt`/`noopt` means
multiple-choice answer options included/omitted. AESLC itself is generative,
so the options distinction is largely a FLAN mixture/rendering distinction,
not four underlying corpora. The project regenerated each source partition
independently to preserve provenance and source-level sampling identity.

The upstream AESLC corpus contains English Enron email bodies paired with
subject lines. The official repository declares CC BY-NC-SA 4.0; CMU states
that the underlying Enron mail was made public by FERC and distributes its
redacted corpus for research while warning about privacy. For the current
academic/non-commercial use, this supplies a direct licence route rather than
requiring Article 3. Commercial use is not cleared, and attribution,
ShareAlike/adaptation scope, and privacy remain review points.

The four DFM repositories are Apache-2.0 synthetic chat datasets generated and
judged with Gemma 4 31B. Across 56,165 accepted rows, the retained audit
metadata reports no unchanged PII-like strings, maximum candidate/original
5-gram overlap below 8%, and no exact row duplicates across variants. The DAG
therefore records task provenance through low-overlap synthetic recreation,
not a blanket claim that original AESLC email expression is retained.

## QReCC Synthetic Variants

Update, 2026-08-17: four effective DFM9 repositories similarly share one QReCC
task dependency. FLAN materialized few-shot and zero-shot dialogue prediction
for both the normal task and `-ii` input inversion; the latter reconstructs
dialogue context from a supplied answer or later turn. They are prompt/task
regimes, not four independent upstream corpora.

Apple's official QReCC repository declares the dataset CC BY-SA 3.0. QReCC is
an English conversational open-domain QA dataset with roughly 14,000
conversations and 81,000 question-answer pairs. It builds conversations from
TREC CAsT, QuAC, and Natural Questions, adds context-independent question
rewrites and answers, and records source web-page links. The component and web
lineage matters for raw QReCC, but the DFM variants do not redistribute its
retrieval collection or raw rows.

The four DFM repositories contain 40,180 accepted synthetic rows and contribute
18,259,893 sampled tokens per DFM9 epoch. Their audit metadata reports no
unchanged PII-like strings, maximum candidate/original 5-gram overlap of 8%,
and no exact duplicates across variants. They are therefore classified as a
project-generated Apache-2.0 layer with CC BY-SA 3.0 task provenance, not as
Article-3-dependent retained QReCC expression. Attribution, ShareAlike, notice,
and adaptation-scope review remain.

## Opinion Abstracts Synthetic Variants

Update, 2026-08-17: eight effective DFM9 repositories use two historical
Opinion Abstracts tasks across the same four FLAN prompt regimes. The Rotten
Tomatoes task originates from crawled professional critic reviews and editorial
consensus text. The iDebate task originates from crawled debate claims and
supporting argument sentences. TensorFlow Datasets describes and packages the
corpora but expressly does not grant permission for third-party dataset
contents; no direct source-content licence was found in the reviewed upstream
materials.

Wang and Ling collected the original corpora for their NAACL 2016 work on
abstractive opinion and argument summarization. Rotten Tomatoes contains
246,164 professional-critic review snippets grouped by 3,731 movies (about 66
per movie), paired with the site's editor-written one-sentence critic consensus
as the target summary. It is not principally a collection of audience star
ratings or user reviews. iDebate contains 676 controversial-topic debates split
into pro and con points. Each of its 2,259 points has an editor-written central
claim paired with supporting argument sentences; sentence splitting produces
17,359 source arguments. The learning task is to generate the claim from its
supporting arguments.

The DFM repositories contain 12,867 accepted Rotten Tomatoes rows and 4,657
accepted iDebate rows. Their audit metadata reports no unchanged PII-like
strings and maximum candidate/original 5-gram overlap of 8%. There are no exact
cross-variant duplicates for Rotten Tomatoes and one duplicate between the two
iDebate zero-shot variants. Together they contribute 9,009,039 sampled tokens
per DFM9 epoch.

The DAG therefore records the original text as a historical seed for
low-overlap synthetic recreation, rather than as redistributed source text.
The provenance investigation is marked complete, but the source-work nodes
remain unresolved: the current working route is Article 3 scientific-research
TDM, conditional on institutional approval, lawful access, research purpose,
and secure retention. The synthetic layer's Apache-2.0 label does not itself
clear the historical seed use or settle adaptation/output status.

Article 4 / Danish section 11 b is also a plausible alternative for the
project's later TDM use: it is not limited to research organisations or
non-commercial research. It would require evidence that the particular corpus
copy was lawfully accessible and that the relevant rightholders had not
expressly reserved TDM rights in an appropriate manner at the time of access;
for publicly available online content, the reservation should be
machine-readable, including relevant metadata or service terms. The current
evidence package does not preserve a reliable acquisition-time snapshot of the
corpus, host terms, metadata, and any applicable source-site reservations.
Consequently Article 4 remains conditional rather than rejected or cleared.
It would cover qualifying reproductions and extractions, not automatically the
earlier 2016 crawl, source-dataset redistribution, or copyright status of model
weights and generated outputs.

Current opt-out audit, 2026-08-17:

- **Rotten Tomatoes:** its terms, last updated 2026-01-06, expressly prohibit
  data mining and using site content directly or indirectly to train, develop,
  or improve AI models or systems. This is a clear current Article 4 reservation
  through online service terms even though no TDMRep file, HTTP TDM header, or
  TDM-specific HTML metadata was found and the relevant movie/review paths are
  not blocked by `robots.txt`. Article 4 should therefore be treated as
  unavailable for fresh access under the current terms. Counsel must still
  determine whether that reservation applied to the separately hosted corpus
  copy and the historical project access.
- **iDebate:** no express TDM/AI reservation, TDMRep file, HTTP TDM header, or
  TDM-specific HTML metadata was found on the current successor site. Its terms
  nevertheless allow only limited, unchanged, attributed, noncommercial
  educational/public-policy reproduction and require permission for other
  copying, modification, and reuse. Because Article 4 requires an express
  reservation, this is not recorded as a definite TDM opt-out; whether those
  general terms constitute an appropriate reservation or independently bind
  the project remains a counsel question.
- **Academic distribution:** the University of Michigan ZIP/README used by the
  TFDS builder exposes no TDM reservation or corpus licence, and the dataset
  path is not disallowed by the host's current `robots.txt`. TFDS similarly
  exposes no TDM reservation for its packaging layer. Silence at either host
  cannot waive rights or reservations held by the underlying source owners.

The structured observation record is
[`legal/registers/dfm9-opinion-abstracts-current-optout-audit.csv`](../../legal/registers/dfm9-opinion-abstracts-current-optout-audit.csv).

Working decision, 2026-08-17: the project will continue to rely on Article 3 /
Danish section 11 c for both Opinion Abstracts source works and will not rely on
Article 4. The DAG therefore treats these two provenance leaves as resolved for
the current scientific-research purpose. This is a purpose-specific working
classification, not a waiver of the Article 3 conditions or a clearance for
commercial/non-research retraining, source-corpus redistribution, or another
project.

## Evidence and Reproduction

- Detailed report: [`legal/reports/dfm9-copyright-tdm-review.md`](../../legal/reports/dfm9-copyright-tdm-review.md)
- Component audit: [`legal/reports/dfm9-article3-component-audit.md`](../../legal/reports/dfm9-article3-component-audit.md)
- Per-source register: [`legal/registers/dfm9-copyright-basis-register.csv`](../../legal/registers/dfm9-copyright-basis-register.csv)
- Component decision register: [`legal/registers/dfm9-article3-audit-register.csv`](../../legal/registers/dfm9-article3-audit-register.csv)
- Current HF metadata snapshot: [`legal/registers/dfm9-hf-current-metadata-register.csv`](../../legal/registers/dfm9-hf-current-metadata-register.csv)
- Acquisition evidence: [`legal/registers/hf-snapshot-register.csv`](../../legal/registers/hf-snapshot-register.csv)
- Builder: [`legal/tools/build_dfm9_copyright_review.py`](../../legal/tools/build_dfm9_copyright_review.py)
- Source-rights DAG report: [`legal/reports/dfm9-source-rights-dependency-dag.md`](../../legal/reports/dfm9-source-rights-dependency-dag.md)
- DAG nodes: [`legal/registers/dfm9-source-dag-nodes.csv`](../../legal/registers/dfm9-source-dag-nodes.csv)
- DAG edges: [`legal/registers/dfm9-source-dag-edges.csv`](../../legal/registers/dfm9-source-dag-edges.csv)
- Authoritative DAG node specification: [`legal/specs/dfm9-source-dag/nodes.csv`](../../legal/specs/dfm9-source-dag/nodes.csv)
- Authoritative DAG edge specification: [`legal/specs/dfm9-source-dag/edges.csv`](../../legal/specs/dfm9-source-dag/edges.csv)
- DAG expansion queue: [`legal/registers/dfm9-source-dag-expansion-queue.csv`](../../legal/registers/dfm9-source-dag-expansion-queue.csv)
- DAG resolver: [`legal/tools/manage_dfm9_source_dag.py`](../../legal/tools/manage_dfm9_source_dag.py)
- Rights-basis algebra: [`legal/reports/dfm9-rights-basis-algebra.md`](../../legal/reports/dfm9-rights-basis-algebra.md)
- Effective-basis register: [`legal/registers/dfm9-effective-rights-basis.csv`](../../legal/registers/dfm9-effective-rights-basis.csv)

```bash
cd /work/dfm/HRM-Text
python legal/tools/build_dfm9_copyright_review.py
```

## Source-Rights Dependency DAG

Update, 2026-08-17: source lineage and rights status are represented as a DAG,
not a tree. A canonical upstream such as WildChat, Tulu, DOLCI, or OpenHermes
may feed several effective DFM9 datasets. The node register records the local
decision and dependency-completeness state; typed edges record retained source,
seed, generated, transformed, and aggregate relationships. The resolver
propagates an unresolved required descendant to every ancestor and rejects
cycles.

The initial detailed subtree covers `danish-foundation-models/dfm-dyna-instruct`:
its ten exposed components, Apertus's three-way source mixture, Tulu's exact 19
source labels, SmolTalk2's 25 named SFT subsets through shared source nodes,
EuroBlocks's 17 source labels/families, the 12 DOLCI puzzle subsets, three exact
agentic-code upstream repositories, and the WildChat/IFBench shared prompt
dependency. All 161 effective DFM9 sources also exist as canonical
effective-dataset nodes; some are reused as dependencies and therefore are not
graph roots. Sources not yet decomposed are explicitly marked
`top_level_only`, including sources already assigned a working direct or
fallback status.

Update, 2026-08-17: the graph's source-specific knowledge was moved out of the
Python resolver into authoritative declarative node and edge CSVs under
`legal/specs/dfm9-source-dag/`. The similarly named files under
`legal/registers/` are generated dossier mirrors. `set-status` updates the
declarative node file atomically; the resolver now contains only schema,
cross-register, cycle, propagation, leverage, and report logic.

Use one atomic status update and rebuild to propagate a source decision:

```bash
python legal/tools/manage_dfm9_source_dag.py set-status NODE_ID cleared \
  --basis "approved basis" --evidence "evidence path or decision reference"
```

Do not mark an aggregate clear merely because its collection/database licence
is clear. It becomes clear only when its own layer and every required child are
clear. `dependency_completeness=partial` means the named node still needs
decomposition even if a provisional local status exists.

## Purpose-Specific Rights Algebra

Update, 2026-08-17: the source register now has a derived two-layer rights
classification. Non-exclusive atoms preserve facts such as open licence,
public-domain status, agreement, project ownership, Article 3 reliance, and
Article 4 availability. A separate conservative headline is computed for the
current academic/non-commercial scientific-research use.

Required child bases combine by union, as do attribution, ShareAlike, notice,
security, retention, and contractual obligations. The headline uses the
purpose-specific order `unresolved > Article 3 dependent > Article 4 dependent
> generator-terms review > restricted direct > direct`. Thus a mixture of
open-licensed and Article-3-dependent components remains Article 3 dependent,
while the directly licensed fraction is still recorded. Article 3 and Article
4 are alternative statutory projections rather than cumulative permissions.

The umbrella for open-licensed plus public-domain components is
`direct_open_or_public`, not “permissively licensed”: public-domain material is
not licensed, and CC attribution/ShareAlike terms may not be described as
permissive without qualification. Exact public-domain counts remain pending
leaf-level atom assignment because the old source register combined open and
public status.

Rebuild the projection with:

```bash
python legal/tools/build_dfm9_rights_basis_algebra.py
```

## Remaining Human Review

1. Copyright counsel and SDU must approve Article 3 / section 11 c reliance,
   including lawful access, beneficiary, purpose, and safeguards.
2. Classify the DBC and Lex.dk agreements for the Commission template and
   review remaining contract terms; training and model release are confirmed.
3. Approve component-level terms/fallbacks for Sapient, DOLCI, DFM Dyna, and
   OpenHermes. Tulu 3's FLAN v2 and SciRIFF layers now use Article 4. WildChat, TV2R, and the four source-retaining
   transformation datasets now have recorded direct bases.
4. Tulu Persona generator and seed terms were reviewed on 2026-08-17 and are
   direct for the current non-commercial research scope; retain the
   account-specific contractual-evidence caveat.
5. For any non-research acquisition or retraining, capture lawful-access and
   machine-readable rights-reservation evidence at acquisition time.

## Next Audit Priority

Update, 2026-08-17: prioritize remaining audits by effective DFM9 exposure and
shared dependency propagation, not only by the DAG report's single-leaf status
count. The recommended order is:

1. DOLCI Tool Use audit and scoped manual acceptance completed on 2026-08-17.
   Its four residual findings remain documented, but no longer block current
   academic/non-commercial scientific-research training and are not treated as
   requiring Article 3 reliance.
2. Tulu 3 Persona family audit completed on 2026-08-17. Its direct effective
   exposure is about 251M tokens/epoch, and its aliases and filtered variants
   now resolve through DOLCI, Tulu, and DFM Dyna/Apertus mixtures.
3. Sapient synthetic/math families: SYNTH and DMMath contribute about 6.06B
   tokens/epoch together; AMPS Mathematica and Sudoku Extreme add about 576M.
   Audit completed on 2026-08-17: SYNTH, DMMath, and AMPS are direct/open.
   The initial narrow Sudoku compilation/database-right fallback was
   superseded the same day by a project-owner manual low-risk acceptance for
   current academic/non-commercial research use. The DAG now reconciles all
   eight Sapient broad families and exact per-epoch exposure.
4. Sapient factual-FLAN audit completed on 2026-08-17. Its 10.20B
   tokens/epoch are now decomposed across 13 families and source-grouped where
   needed. Non-factual FLAN remains about 4.33B tokens/epoch and is the next
   Sapient task-to-source audit.
5. Shared mixed-source leaves completed for current-purpose classification:
   CoCoNot and WildJailbreak use their publisher terms; FLAN v2 and SciRIFF
   use Article 4 for uncovered expression. Deeper FLAN/SciRIFF provenance
   remains useful for notices and memorisation testing but no longer blocks.
6. Repaired OpenHermes EN/DA: about 1.59B tokens/epoch combined, but fourteen
   retained prompt families make this a larger lineage project.

The best next high-impact Sapient audit is now the retained non-factual FLAN
family. It is the largest unresolved Sapient exposure and requires
task-to-source decomposition rather than a repository-level decision.
Platypus and Tasksource are smaller parallel branches.

Superseding update, 2026-08-18: that audit is complete. All 3,644
non-factual-FLAN, 161 Tasksource, and eight Platypus files were reconciled.
FLAN resolves through four submixtures using direct terms plus the MAN-019
Article 4 determination; Platypus resolves through ARB, OpenBookQA, ScienceQA,
and TheoremQA component terms. Tasksource maps to 124 repositories: 77 files /
78.885M tokens per epoch have specific recognized repository licences, while
84 files / 69.759M tokens per epoch retain Article 3 under MAN-020. See
`legal/reports/dfm9-sapient-flan-tasksource-platypus-audit.md`.

## Sapient Synthetic and Math Audit

Update, 2026-08-17: the local source files, cleaning code, upstream cards, and
official repositories were reconciled in
`legal/reports/dfm9-sapient-synthetic-math-family-audit.md`.

- PleIAs SYNTH contributes 3,454,133,993.8 tokens/epoch under CC-BY-4.0,
  grounded in CC-BY-SA Wikipedia material and generated with models whose
  outputs permit reuse.
- DeepMind Mathematics contributes 2,609,114,656.8 tokens/epoch from the
  Apache-2.0 procedural generator.
- AMPS Mathematica contributes 398,247,764.0 tokens/epoch from the authors'
  generated corpus linked by the MIT-licensed MATH repository.
- Sudoku Extreme contributes 178,000,000.0 tokens/epoch. Individual grids and
  solutions are treated as functional records. The possible protectable
  selection/database layer in the unlicensed community-source fraction is
  manually accepted as low risk for the current scope; Article 3 is not
  invoked.

This supersedes both the earlier undifferentiated treatment of all Sapient
synthetic/math material and the initial narrow Sudoku fallback. The later
factual-FLAN audit separately resolves that branch; aggregate fallback remains
for unresolved Platypus, non-factual FLAN, and Tasksource content.

Superseding update, 2026-08-18: the three named branches are no longer
unresolved. The aggregate fallback is now limited to the Article 3 Tasksource
residual documented under MAN-020.

## Sapient Factual-FLAN Audit

Update, 2026-08-17: all 266 retained factual-FLAN files were reconciled to 13
canonical families and 10,199,566,222.4 tokens/epoch. SQuAD, QuAC, ROPES,
DROP, HotpotQA, WikiDialog, BoolQ, and Natural Questions have direct/open
working bases. The initial conservative Article 3 classification for RACE,
DREAM, WebQuestions, and uncovered CoQA material was superseded later on
2026-08-17 by a project-owner Article 4 / Danish section 11 b determination:
the datasets have lawful long-running public research/Hugging Face
distribution, no known reservation, and no known rightsholder challenge.
Incomplete acquisition-time evidence remains recorded as a caveat.

TriviaQA was decomposed into 14 question-source groups after confirming that
the retained FLAN rows contain questions and short answers but not evidence
documents. Twelve groups (57.065M tokens/epoch) use Article 4. JetPunk and
TriviaCountry (4.043M) remain on Article 3 because JetPunk now expressly says
`ai-train=no` and TriviaCountry disallows all robots. The dataset was complete
by its 9 May 2017 arXiv submission and released as version 1.0 in July 2017;
the paper gives no exact crawl window, so current robots signals do not prove a
reservation at the 2016/early-2017 collection. The ACL paper says the data and
code are available and that the unfiltered release supports research, but it
contains no data-licence, copyright-ownership, source-permission, or TDM-rights
statement. The later Apache-2.0 repository notice is qualified by the project
site's separate statement that UW does not own copyright in the included
questions and documents. See
`legal/reports/dfm9-sapient-factual-flan-family-audit.md`.

Update, 2026-08-17: the project owner subsequently accepted the official
TriviaQA repository's express statement that Apache-2.0 applies to code and
data as the operative basis for the sampled TriviaQA question/answer rows.
This supersedes Article 3/4 as the effective basis, including for JetPunk and
TriviaCountry, while retaining the UW ownership disclaimer, robots findings,
and all 14 source-site records as non-blocking provenance evidence. It does
not extend the decision to the omitted evidence-document corpus.

## Tulu 3 SFT Mixture Audit

Update, 2026-08-17: the effective `allenai/tulu-3-sft-mixture` source was
decomposed into all 19 labels present in the 939,343 local rows. The card lists
18 components and 939,344 rows; the local data additionally contains 50,000
OpenMath2/GSM8K rows and has 7,131 rather than 7,132 OASST rows. Fifteen
families reuse previously cleared direct/open/generated bases. CoCoNot and
WildJailbreak are cleared as synthetic Ai2 releases under their stated terms.
The initial audit cleared FLAN v2 and SciRIFF for current scientific-research
use through direct terms plus Article 3 for uncovered source expression.
Superseding project-owner decision, 2026-08-17: both now use Article 4 / Danish
section 11 b for uncovered expression, and Article 3 is not relied on. Their
deeper provenance remains partial. See
`legal/reports/dfm9-tulu3-mixture-audit.md` and
`legal/registers/dfm9-tulu3-mixture-component-audit.csv`.

Sampling confirmation, 2026-08-17: DFM9 actually samples the eight Sapient
factual-FLAN TriviaQA files at 673,106 selections and about 61.108M tokens per
epoch. Two additional Natural Instructions adaptations (`task1564` and
`task1565`) contribute 217 records / 16,715 source tokens per epoch and are
tracked under that separate dependency branch. No sampled route retains the
TriviaQA evidence-document corpus.

## Manual Acceptance Register

Update, 2026-08-17: all discretionary project-owner decisions that changed a
source from blocking to accepted are consolidated in
`legal/reports/dfm9-manual-acceptances-and-overrides.md`. The register covers
four DOLCI Tool Use residual layers, the complete RLVE prompt family, Sudoku
Extreme's possible compilation layer, the Article 4 decisions for RACE,
DREAM, WebQuestions, and uncovered CoQA material, the TriviaQA Apache-2.0
publisher-representation override, and accepted WildChat user permission.
It also records the later Article 4 determinations for FLAN v2 and SciRIFF.
Each entry records its limited scope, residual caveat, and a future
memorisation/propensity test target. Ordinary open licences, public-domain
findings, and data-owner agreements are deliberately excluded from this
manual-decision list.

## Apertus SFT Mixture Audit

Update, 2026-08-17: the 3.034B-token/epoch Apertus component in DFM Dyna was
audited through Tulu 3, SmolTalk2, and EuroBlocks. Nine former unresolved
leaves (HarmfulQA, three Magpie families, Hermes Function Calling, three NVIDIA
code/SWE datasets, and s1K) now have captured direct terms. Apertus computes as
cleared for the current academic/non-commercial scientific-research purpose,
with partial provenance completeness.

Superseding detail, 2026-08-17: the five aggregate fallback labels were
decomposed. The project owner then accepted MoT's residual prompt/editorial
risk without Article 3 reliance and selected Article 4 for uncovered
Airoboros, Caseus, CoT Alpaca, and Platypus expression. SmolTalk therefore
needs Article 3 only through LongAlign. The remaining Article 3 boundary is
LongAlign source documents through eleven content groups and EuroBlocks's
5,169 source-retaining plus 134,819 seed-derived rows. This is not a blanket
open or commercial-use clearance. See [Apertus Copyright Boundary
Decomposition](apertus-copyright-boundary-decomposition.md) and
`legal/reports/dfm9-apertus-component-audit.md`.

Maintenance rule, 2026-08-17: future project-owner acceptances, overrides, and
purpose-specific statutory-basis determinations must be added to the manual
decision register in the same turn, without requiring a separate prompt.

Superseding review status, 2026-08-18: MAN-017 and MAN-018 approve the
remaining LongAlign and EuroBlocks leaves under Article 3 for the current
academic/non-commercial scientific-research purpose. The Article 3 conditions,
provenance gaps, restrictive-notice evidence, and memorisation-test cohorts
remain. The effective-source DAG now reports 102/161 datasets and 56.932B of
79.939B tokens per epoch as cleared; see
`legal/reports/dfm9-audit-status-2026-08-18.md` for the status split and next
high-impact targets.

Later 2026-08-18 status: MAN-019 and MAN-020 complete the remaining Sapient
branches. The DAG now reports 103/161 effective datasets and 78.312B of
79.939B tokens per epoch as cleared. Of these, 89 datasets / 46.972B tokens per
epoch are cleared without Article 3 reliance, including recorded human Article
4 and low-risk decisions. The Sapient aggregate remains Article-3-involved
only because of 69.759M Tasksource tokens per epoch.

Superseding synthetic-derivative status, 2026-08-18: MAN-021 manually approves
all 70 `schneiderkamplab/sapient-synth-*` datasets for the current project.
Their named upstream-task links remain recorded for provenance and future
memorisation testing but are informational rather than blocking clearance
dependencies. This decision clears the 54 previously partial synthetic
derivatives without independently clearing or relicensing their upstream
datasets. The resulting effective-dataset status is 157/161 datasets and
78.341B/79.939B tokens per epoch cleared (98.00%), with no partial datasets;
only four AllenAI mixtures remain unresolved.

Superseding Tulu-family status, 2026-08-18: the four AllenAI mixtures were
decomposed against their exact local artifacts. Tulu v2 SFT has 326,154 rows;
Tulu v2 SFT Long has 288,554 rows and retains 74,312 Long ShareGPT rows instead
of 111,912 chunks. A focused ID audit supersedes the shorthand that this was
only a chunking difference: split maps to 74,951 original IDs, Long to 74,307,
with 74,159 shared, 792 split-only, and 148 Long-only. SciRIFF Train Mix contains
35,000 SciRIFF and 35,714 sampled Tulu-v2 rows. Every one of the 31,751 IF-SFT
IDs exactly matches a row in the already audited Tulu-3 mixture; its added
constraint and regenerated response form an Ai2 contribution, so IF-SFT is
cleared without new Article 3 reliance. WizardLM's current official release is
MIT, superseding the historical no-licence note in the Tulu card. The only
remaining boundary is ShareGPT participant expression: its unofficial export
has an Apache-2.0 tag, but uploader authority over participant text is not
established. Tulu v2, Tulu v2 Long, and SciRIFF Train Mix therefore remain
partial pending an explicit Article 3 decision or stronger permission evidence.
See `legal/reports/dfm9-tulu-v2-sciriff-if-sft-audit.md`.

The resulting DAG has 158/161 effective datasets and 78.361B/79.939B tokens
per epoch cleared, with three partial datasets and no opaque unresolved roots.
After reconciling MAN-021 in the generated copyright register, 152 cleared
effective datasets / 47.030B tokens per epoch are outside Article 3, including
recorded human Article 4 and low-risk decisions.

Pre-MAN-022 ShareGPT audit conclusion (superseded later on 2026-08-18):
ShareGPT's one-click public pages,
browsing, and documented read API support intentional public availability and
a plausible lawful-access route for Article 3 scientific-research TDM. They do
not establish that the anonymous HF mirror could Apache-license participant
expression. The site had `robots.txt: Disallow: /` from its first day, the
official FastChat/Vicuna team documented legal concerns and did not release its
copy, and no participant-content licence was found. Article 4 is therefore not
the recommended fallback without qualified review. Aggregate scanning of the
74,312 Long rows found 1,882 email-pattern rows, 677 self-identification rows,
13 private-key-block rows, and four AWS-key-pattern rows; these are broad risk
indicators rather than validated secrets or legal personal-data findings.
`LEG-046` remains open for institutional Article 3 approval, with privacy/DPO
and memorisation controls remaining independent. See
`legal/reports/dfm9-sharegpt-boundary-audit.md`.

Superseding ShareGPT decision, 2026-08-18: MAN-022 accepts deliberate
one-click publication to ShareGPT's public sharing/browsing/API service as
participant permission for the current academic/non-commercial research
training. This gives ShareGPT the same operative cleared status as WildChat,
while explicitly recording that the evidence is weaker: ShareGPT has no found
research/model-training consent wording. The anonymous HF mirror added an
Apache-2.0 metadata declaration on 2023-04-02, and the original ShareGPT
repository added an MIT software licence on 2023-04-29; neither event licenses
conversation authors' text. Tulu v2 SFT, Tulu v2 SFT Long, and SciRIFF Train
Mix are now cleared for the current purpose. Raw redistribution, nonresearch
use, privacy/GDPR, credentials, and memorisation testing remain separate.
The rebuilt DAG consequently reports **161/161 effective datasets** and
**79.939B/79.939B tokens per epoch** cleared for the current purpose.

Final Article 3 reconciliation, 2026-08-18: the completed DOLCI component DAG
supersedes the stale aggregate Article 3 label on
`allenai/Dolci-Instruct-SFT` and `allenai/Dolci-Instruct-SFT-No-Tools`. Their
required components resolve through direct terms, MAN-001 through MAN-004,
express permission, or the MAN-013/MAN-014 Article 4 decisions. Consequently
157 effective sources / 54.330B tokens per epoch do not rely on Article 3;
four effective sources / 25.609B tokens per epoch retain Article 3 for at least
one component.

Narrow-boundary update, 2026-08-18: whole-aggregate exposure is not the amount
of Article-3-dependent expression. The measured/estimated component boundary
is about **414.1M sampled tokens per epoch (0.518%)**. Decomposition triage and
the no-manual-override counterfactual are recorded in
[DFM9 Article 3 Boundary Accounting](dfm9-article3-boundary-accounting.md).
