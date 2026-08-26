# DFM9 Article 3 Component Audit

Status: evidence-based engineering/legal triage, not legal advice or
institutional approval. Reviewed 2026-08-17.

## Effective-sample correction

The earlier source-level builder incorrectly treated
`data/sampled_dfm9/metadata.json:total_length` (`93,929,976,190`) as sampled
tokens per epoch. It is the concatenated token-store size. The authoritative
sampling analytics report **399,693,515,389 covered tokens across five epoch
index sets**, averaging **79,938,703,077.8 tokens/epoch**.

Seven repositories listed as prospective/tokenized DFM9 additions are absent
from `data/show_analytics_dfm9.md` and the effective sampled coverage:
Nemotron SWE, Nemotron Terminal, code-meta-reasoning, Natural Instructions,
NuminaMath 1.5, CoEdIT, and ASSET. They are excluded from the corrected DFM9
rights register. Their tokenized artifacts do not prove training exposure.

## Audit outcomes

### DFM Dyna Instruct

The exact downloaded revision is
`bf1024f4f5b5c42586961a53946fbc5f2cc1eb80`. The DFM9 tokenized exposure is:

| Component | Average tokens/epoch | Working result |
|---|---:|---|
| Apertus SFT mixture | 3,033,512,464 | Mixed fallback: ODC-By mixture composed principally from Tulu 3, SmolTalk2, and EuroBlocks |
| WildChat Qwen | 189,868,452 | Express permission for current research training accepted from WildChat's affirmative consent; privacy controls remain separate |
| Wiki Instruct DA | 164,686,585 | Direct Wikipedia CC-BY-SA lineage |
| Translation 100K | 98,008,752 | Direct CC-BY-SA EU legal/administrative lineage |
| Agentic Code SFT | 34,769,924 | Direct CC-BY component claim, subject to retained notices |
| Danish Verifiable Reasoning | 9,064,406 | Direct: Synquid's contribution is authorized DFM work and Ai2 identifies the retained logic puzzles as new Ai2 prompts |
| MT-DA DeepSeek | 8,883,200 | Generated DynaWord-grounded component; direct source/project terms |
| When2Call | 3,797,583 | Synthetic CC-BY component claim |
| IFBench Train | 1,262,590 | Authorized Synquid contribution plus accepted WildChat express permission; privacy controls remain separate |
| DA Refusals | 17,706 | Synthetic CC-BY component claim |

Approximately 310.2M tokens/epoch have a direct component basis. The aggregate
remains `article3_research_tdm_for_uncovered_components`, principally because
of Apertus/Tulu content. WildChat expression-use permission is
accepted for current research training.

The canonical dependency representation is now the machine-readable DAG in
`legal/registers/dfm9-source-dag-{nodes,edges,resolution}.csv`, rendered in
`legal/reports/dfm9-source-rights-dependency-dag.md`. It avoids duplicating
shared WildChat, Tulu, DOLCI, OpenHermes, and other upstream nodes. Resolving a
canonical node therefore updates every effective DFM9 ancestor on rebuild.

### DOLCI

The three active DOLCI repositories contribute 7.338B tokens/epoch. The full
mixture identifies 22 source labels. Apache/MIT sources and newly authored or
generated prompt families are direct candidates. WildChat expression-use is
accepted for current research training; ODC-By families, FLAN, SciRIFF, and
other retained third-party prompts remain source-specific.
The no-tools variant contains transformed versions of the same instruction
material; the tool-use variant is built from five Ai2 ToolU sources. The
2026-08-17 ToolU audit traced these to SimFC, Science QA, and DeepResearch and
replaced the opaque leaves with direct generated layers and explicit retained
schema/text dependencies. Removing tools or regenerating responses does not
remove rights in retained prompts, API schemas, scholarly abstracts, or web
snippets.

Result before manual acceptance: component-level Article 3 fallback remained
only for the unassigned SimFC schema pool, third-party scholarly content, five
residual DRv4 prompts, and source-specific web snippets. On 2026-08-17 the
project owner manually accepted those four low-risk residual layers for current
academic/non-commercial scientific-research training and determined that no
material reason to invoke Article 3 had been identified. The policy DAG
therefore clears the Tool Use branch. Article 4 is recorded only as a
conditional alternative where lawful access and absence of an effective
reservation can be evidenced. All source findings remain recorded. Detailed
counts and decision scope are in
`legal/reports/dfm9-dolci-toolu-component-audit.md`.

Subsequent Tulu 3 mixture work on 2026-08-17 cleared CoCoNot and WildJailbreak
as synthetic releases under their stated terms and initially supplied an
Article 3 basis for uncovered FLAN v2 and SciRIFF expression. That fallback was
superseded later the same day by a project-owner Article 4 / Danish section 11
b determination for both sources. The rebuilt dependency DAG computes the
full DOLCI and DOLCI-No-Tools nodes as `cleared`; FLAN v2 and SciRIFF no longer
rely on Article 3, although their provenance remains partial.

### Tulu 3 Persona family

The four directly sampled Persona datasets contribute 251.016M tokens/epoch;
older aliases and filtered/grade-filtered variants also propagate through
DOLCI, Tulu/OLMo, and DFM Dyna. The Tulu 3 report establishes a synthetic
lineage based on approximately 250,000 PersonaHub personas,
`GPT-4o-2024-08-06`, Claude 3.5 Sonnet for Python solutions, 33 Ai2-authored
instruction-following examples, and the IFEval constraint taxonomy.

Result: Article 3 is not required for the current academic/non-commercial
research use. Ai2 released the family under ODC-By; PersonaHub is
CC-BY-NC-SA-4.0; IFEval code/data are open; and generation-era provider terms
assign output rights to the customer. Preserve attribution, ShareAlike, and
NonCommercial scope. Ai2's account-specific generation compliance is not
independently archived and remains a contractual evidence caveat. See
`legal/reports/dfm9-tulu3-persona-family-audit.md`.

### Tulu 3 SFT mixture

The directly sampled effective mixture contributes 1.571B tokens/epoch in the
legal exposure register. Exact local inspection found 939,343 rows and 19
source labels, including a 50,000-row OpenMath2/GSM8K component omitted from
the card's prose list. Fifteen families reuse direct/open/generated decisions;
CoCoNot and WildJailbreak are cleared synthetic Ai2 releases. The initial
Article 3 fallback for uncovered FLAN v2 and SciRIFF expression was
superseded by the project-owner Article 4 determination.

Result: the effective Tulu 3 source and its DOLCI ancestors compute as cleared
without Article 3 reliance from FLAN v2 or SciRIFF. Both retain `partial`
provenance completeness and Article 4's factual conditions must remain
satisfied. See
`legal/reports/dfm9-tulu3-mixture-audit.md`.

### Sapient cleaned aggregate

Corrected average exposure is 21.380B tokens/epoch, comprising Platypus,
SYNTH, AMPS Mathematica, DMMath, FLAN, factual FLAN, Sudoku Extreme, and
Tasksource. The source filter removes 328 current files for privacy or other
policy reasons, but the retained files still span many distinct upstream
licences. Synthetic/math families are not assumed to have the same rights as
FLAN and Tasksource.

The 2026-08-17 synthetic/math audit clears PleIAs SYNTH (CC-BY-4.0 with
open-licensed seeds), DeepMind Mathematics (Apache-2.0), and AMPS Mathematica
(MIT author release), together accounting for 6.461B tokens/epoch. Sudoku
Extreme adds 178M tokens/epoch; its individual grids are functional records.
The project owner manually accepted the residual low risk from possible
compilation/database rights in unlicensed community collections for the
current academic/non-commercial research use, without Article 3 reliance.

Result: all four synthetic/math families are cleared. The later factual-FLAN
audit also clears all 266 factual task files using direct terms, Article 4, and
Article 3 only for the JetPunk and TriviaCountry question-source groups.
Superseding update, 2026-08-18: Platypus, non-factual FLAN, and Tasksource were
subsequently reconciled in
`legal/reports/dfm9-sapient-flan-tasksource-platypus-audit.md`. The aggregate
now retains Article 3 only for 69.759M tokens/epoch in the Tasksource residual.
See
`legal/reports/dfm9-sapient-synthetic-math-family-audit.md` and
`legal/reports/dfm9-sapient-factual-flan-family-audit.md`.

### Tulu

Superseding update, 2026-08-18: Tulu 3 is fully component-audited and does not
rely on Article 3. Tulu v2 and its Long reconstruction are decomposed across
all 16 local labels. WizardLM has an official MIT release, and direct or
noncommercial terms plus recorded FLAN/SciRIFF Article 4 decisions cover the
other components. MAN-022 accepts deliberate ShareGPT publication as
participant permission for the current academic/non-commercial research use,
so ShareGPT no longer requires Article 3 in the operative project
classification. This is not a blanket Apache licence; privacy indicators and
nonresearch use remain independent. The four Persona datasets are explicitly
synthetic and do not require Article 3 under the generator-output analysis.

### Nemotron Instruction Following Chat v2

NVIDIA identifies itself as dataset owner, describes the corpus as hybrid and
synthetic, states that it is ready for commercial use, and expressly says the
data may be freely used to train and evaluate. This express permission is more
specific than the ODC-By database-right grant.

Result: direct publisher training permission; Article 3 not required within
that scope. Preserve the card revision and attribution.

### Repaired OpenHermes EN/DA

The project audited, repaired, and translated the outputs, but the datasets
retain prompts from fourteen OpenHermes source families, including Chatbot
Arena and ShareGPT. Transformation does not extinguish upstream prompt rights.

Superseding result, 2026-08-17: direct component terms remain controlling where
captured, and project-owner decision MAN-016 selects Article 4 / Danish section
11 b for uncovered Airoboros, Caseus, CoT-Alpaca, and Platypus expression.
Article 3 is no longer relied on for these derivatives.

### Oliver EUR-Lex derivatives

`eur-lex-bt` rows point to `oliverkinch/eur-lex`; `eur-lex-sum-instruct` rows
point to `oliverkinch/eur-lex-sum`. The project owner confirmed that these use
reusable public-domain/CC-BY-derived EUR-Lex material. Generated instructions
do not introduce another source corpus.

Result: direct per-source terms; Article 3 not required.

### DBC and Lex.dk agreements

On 2026-08-17 the project owner confirmed that both confidential data-owner
agreements permit model training and model release. DBC contributes an average
356,114,318.8 tokens/epoch and Lex.dk contributes 313,397,450 tokens/epoch.

Result: direct agreement basis for training and release; Article 3 is not
required for those acts. The confidential agreements must still be reviewed to
classify them under the Commission template and establish any unconfirmed
retention, source-redistribution, attribution, duration, security, and broader
downstream-use terms.

### Smaller-source pass

The following sources were inspected at row/schema level rather than decided
from repository names alone:

| Source | Average tokens/epoch | Result |
|---|---:|---|
| Verifiable reasoning GPT-4.1 | 604,700,862 | Cleared for the current academic/research use by the project owner's 2026-08-17 manual override after the 250-variant prompt-expression audit; preserve the audit bins and Article 3 fallback evidence |
| Giannor GEC DaLA TV2R | 192,947,845 | Direct: TV2R source terms plus authorized DFM/Giannor derivative |
| WildChat Qwen messages | 189,868,452 | Express permission accepted for current research training; privacy review remains separate |
| SciRIFF train mix | 132,295,148 | Exact 35,000 SciRIFF / 35,714 Tulu-v2 mixture; cleared for current research through MAN-014 and MAN-022 |
| Translation 100K | 98,234,612 | Direct lineage: every row identifies the covered Oliver/OPUS source |
| Verifiable reasoning o4-mini | 80,198,700.4 | Cleared for the current academic/research use by the project owner's 2026-08-17 manual override after the 250-variant prompt-expression audit; preserve the audit bins and Article 3 fallback evidence |
| Open Math 2 50K | 71,816,694 | Direct lineage: OpenMathInstruct-2 CC-BY-4.0, GSM8K MIT, and DeepSeek-R1 MIT distillation terms; retain attribution/notices |
| Giannor DaLA TV2R | 68,526,212 | Direct: TV2R source terms plus authorized DFM/Giannor derivative |
| AI Arena extract | 45,690,600 | Direct Etalab Open Licence 2.0; privacy review remains separate |
| IF SFT verified | 19,940,266 | Cleared by exact-ID inheritance from audited Tulu 3 plus Ai2 constraint/regenerated-response layer |
| Danish verifiable reasoning | 18,131,360 | Direct project/Ai2 contribution: prompts name Ai2-authored DOLCI puzzle subsets |
| IFBench train | 12,689,130 | Direct for current research training: authorized Synquid layer plus accepted WildChat express permission |
| MT-DA DeepSeek | 8,886,412 | Direct project/DynaWord lineage (1,051 DynaWord and 200 handcrafted rows) |
| RLVR MATH | 8,066,943 | Direct MIT MATH lineage; all 7,500 rows identify MATH |
| GovReport | 4,412,112 | Direct US-government publication status; retain GAO/CRS attribution and embedded-work caveat |

These decisions concern copyright/TDM only. Conversation sources still require
the independent privacy and sensitive-content controls in the data-protection
workstream.

## Remaining source-specific queue

The material unresolved by engineering evidence is now concentrated in:

1. Sapient's retained task-level upstream licences.
2. DOLCI, Tulu, DFM Dyna, SciRIFF and OpenHermes component rights.
3. Privacy, PII, minimisation, retention, and data-subject safeguards for
   WildChat-derived datasets. Expression-use permission is accepted for the
   current research training, but that does not resolve the privacy workstream.
4. Generator-output and seed terms for the remaining synthetic persona,
   OpenHermes, Magpie, SmolTalk, and related generated-data families. The
   AllenAI verifiable-reasoning family is manually cleared for the current
   use, and Open Math has direct open-licence lineage.

Those are counsel/source-owner questions, not gaps that can be closed by
another repository metadata scan.
