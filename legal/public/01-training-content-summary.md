# Public Summary of Training Content for DFM Mimir v1

**Status:** Draft following the European Commission Article 53(1)(d) template  
**Do not publish until P0 actions are resolved.**

## Document Control

| Field | Value |
|---|---|
| Summary version | `0.1-draft` |
| Last update | 2026-08-15 |
| Previous versions | None |

## 1. General Information

### 1.1 Provider Identification

| Field | Value |
|---|---|
| Provider name and contact details | [OPEN: LEG-003] |
| Authorised representative | Not applicable if all provider entities are established in the EU; confirm after provider determination. |

### 1.2 Model Identification

| Field | Value |
|---|---|
| Versioned model name | DFM Mimir v1 |
| Model repository | https://huggingface.co/danish-foundation-models/DFM-Mimir |
| Technical report | https://arxiv.org/abs/2608.13517 |
| Model dependencies | Trained from scratch; no upstream GPAI model weights. The Gemma 4 tokenizer and chat-template conventions were used. Synthetic training data was generated with Gemma 4 31B. |
| Public release and distribution | Project-declared release date: 2026-08-15. Distributed as open weights through Hugging Face Hub. The repository was created 2026-08-03T10:47:24Z. Qualified legal review must still determine the AI Act placement and provider characterisation under LEG-002 and LEG-003. [RESOLVED HUMAN FACT: LEG-004] |

### 1.3 Modalities, Size, and Characteristics

| Field | Draft response |
|---|---|
| Modality | Text only. |
| Training-data size range | `1 billion to 10 trillion tokens`. Final DFM8 sampled mean: 70,479,308,606 source tokens/epoch. The sampler metadata value 70,479,433,697 is the concatenated token-store length, not a conflicting per-epoch statistic. Nominal lifetime batch-token presentations: 432,537,600,000; exact consumed non-padding source tokens reconstructed from sampled indices: 431,832,565,530. [RESOLVED ENGINEERING: LEG-005] |
| Content types | Danish and English instructions, question answering, dialogue, mathematical reasoning, source code, tool use, translation, summarisation, scientific material, encyclopaedic material, synthetic transformations, and limited agreement-supplied cultural/book metadata and articles. |
| Latest acquisition date | Latest repository-evidenced final-source creation/acquisition: 2026-07-14 (final repaired English/Danish OpenHermes artifacts). Professor Peter Schneider-Kamp attested on 2026-08-15 that no source was acquired after that date. [RESOLVED HUMAN: LEG-006] |
| Languages | Final DFM8 recipe: English 68.62%, Danish 24.74%, bilingual Danish/English 6.54%, other 0.20%. Exact historical source exposure is attached; source-level language classification for earlier phases is part of the upstream-card human review in LEG-007. |
| Other characteristics | The training mixture includes public datasets, agreement-supplied private data, provider-generated synthetic/audited data, translated/audited data, and derived tasks. It includes repeated and capped sampling. |
| Tokenisation | Gemma 4 tokenizer, vocabulary 262,144; Gemma-native chat template; maximum context 4,096 model tokens. |

## 2. List of Data Sources

### 2.1 Publicly Available Datasets

**Used:** Yes. **Modality:** Text.

The final DFM8 recipe includes 159 Hugging Face repositories/groups accounting
for 69,809,785,782 sampled tokens per epoch. The complete current inventory is
maintained in [`../../docs/dfm8-datasets.md`](../../docs/dfm8-datasets.md) and
materialised one-source-per-row in
[`../registers/dataset-legal-basis-register.csv`](../registers/dataset-legal-basis-register.csv).
The exact source-prefix/task union actually consumed in DFM6, DFM7, and DFM8 is
recorded in `legal/registers/phase-source-exposure-register.csv` and
`phase-task-exposure-register.csv`, including the partial final DFM8 epoch.

Using 3% of final-DFM8 public sampled tokens as the provisional large-dataset
threshold (`~2.094B` tokens), the large public sources are:

| Dataset | Link | Sampled tokens/epoch | Selection note |
|---|---|---:|---|
| HRM-Text cleaned collection | https://huggingface.co/datasets/sapientinc/HRM-Text-data-io-cleaned-20260515 | 11.92B | Curated source allow-list; exact consumed subcollections are attached in the phase task-exposure register. |
| Lærebogen | https://huggingface.co/datasets/danish-foundation-models/laerebogen | 8.32B | Repeated sampling; source base approximately 2.08B tokens. |
| OpenMathInstruct-2 | https://huggingface.co/datasets/nvidia/OpenMathInstruct-2 | 6.60B | Converted to training format. |
| Nemotron SFT Agentic v2 | https://huggingface.co/datasets/nvidia/Nemotron-SFT-Agentic-v2 | 4.27B | Selected agentic files and converted formatting. |
| DFM Dyna Instruct | https://huggingface.co/datasets/danish-foundation-models/dfm-dyna-instruct | 3.54B | Converted to Gemma-native training format. |
| Dolci Instruct SFT No Tools | https://huggingface.co/datasets/allenai/Dolci-Instruct-SFT-No-Tools | 3.49B | Repeated twice in final recipe. |
| OPUS Danish-English permissive | https://huggingface.co/datasets/schneiderkamplab/opus-da-en-permissive | 2.90B | Selected from permissively licensed OPUS Danish-English corpora. |
| Dolci Instruct SFT | https://huggingface.co/datasets/allenai/Dolci-Instruct-SFT | 2.24B | Converted to training format. |

Other public sources include English and Danish instruction data, reasoning,
translation, science, summarisation, tool use, public conversations, synthetic
and audited datasets, and transformations derived from Common Pile and Danish
DynaWord. Dates of source collection are generally inherited from upstream
dataset documentation and need a source-card extraction pass. [OPEN: LEG-007]

### 2.2 Private Non-Publicly Available Datasets

**Used:** Yes. **Modality:** Text.

| Source | Description | Sampled tokens/epoch | Agreement category |
|---|---|---:|---|
| DBC datasets | Book abstracts/reviews and Faktalink/Forfatterweb content supplied under a DFM/data-owner agreement permitting model training and model release. | 356,125,374 | Agreement category pending (`LEG-008`) |
| Lex.dk articles | Danish encyclopaedic articles supplied under an agreement permitting model training and model release. | 313,397,450 | Agreement category pending (`LEG-009`) |

Confirm whether each agreement is a commercial rightsholder licence under
section 2.2.1 or another third-party agreement under section 2.2.2. Do not
publish confidential contract terms.

### 2.3 Data Crawled or Scraped Directly by the Provider

**Repository audit response:** No direct provider-operated crawling has been identified.
Common Pile and Danish DynaWord were obtained as third-party public datasets,
then sampled and transformed. The repository downloader uses Hugging Face
`snapshot_download`; 116 local snapshot records are captured in
`legal/registers/hf-snapshot-register.csv`. Partner and contractor attestation
is still required. [HUMAN REQUIRED: LEG-010]

### 2.4 User Data

**Draft response:** No data collected through Mimir or other provider-operated
services was intentionally used. Some third-party public datasets contain
conversation or user-generated content; these are disclosed under section 2.1,
not as provider-collected user data. Confirm the statement across all partners.
[OPEN: LEG-011]

### 2.5 Synthetic Data

**Used:** Yes. **Modality:** Text.

Provider-generated synthetic and audited data was produced with Gemma 4 31B.
It includes Common Pile and Danish DynaWord transformations, DFM8 targeted
synthetic instruction datasets, repaired/translated OpenHermes-derived data,
and synthetic replacements for selected Sapient tasks. The final DFM8 report
classifies 7.81B tokens/epoch as synthetic and audited, with additional
translated/audited and derived-task categories. The 91 final-recipe entries
whose form is generated, synthetic, translated, or derived are inventoried in
`legal/registers/synthetic-data-register.csv`.
`synthetic-pipeline-evidence.csv` consolidates generator/judge identity,
generated/audited/accepted counts, and source evidence for the six targeted
families, repaired English/Danish OpenHermes, and eight broad transformation
families. Prompt and recipe paths remain preserved in the source register.
[RESOLVED ENGINEERING: LEG-012]

### 2.6 Other Sources

No commissioned human-labelling or offline digitisation outside the sources
above has been identified. Confirm against contracts and project records.
[OPEN: LEG-013]

## 3. Data Processing Aspects

### 3.1 Rights Reservations

Danish Foundation Models applies the draft copyright policy in
[`../policies/02-copyright-compliance-policy.md`](../policies/02-copyright-compliance-policy.md).
The final response must identify whether the provider signs the GPAI Code of
Practice and describe the opt-out protocols and controls actually used by the
provider and upstream suppliers. [OPEN: LEG-014]

### 3.2 Removal of Illegal Content

The project applied source allow/deny policies, format conversion, quality
filters, synthetic-data audits, and exclusions intended to remove sources with
identified copyright, personal-data, or provenance concerns. The controls were
not designed as a comprehensive illegal-content classifier. Their measures,
measured coverage, exception handling, and limitations are documented in
`legal/controls/07-data-content-controls-assessment.md`. [RESOLVED ENGINEERING:
LEG-015; HUMAN APPROVAL REQUIRED FOR PUBLIC WORDING]

### 3.3 Other Information

Sampling is not uniform: sources are capped, repeated, filtered, or excluded to
shape language and task coverage. The public technical report lists all 161
sources in the final DFM8 recipe and their sampled token contributions. The
historical phase union will supersede that table for this Summary if it differs.
