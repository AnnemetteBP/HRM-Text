# Mimir v1 Data-Protection Assessment

**Status:** Initial issue list; not a completed DPIA  
**Classification:** Confidential  
**DPO reviewer:** [OPEN: LEG-034]

## Purpose

The AI Act does not replace GDPR or other privacy law. This document identifies
the evidence needed to substantiate the report's statement that training
excluded personal information and to determine whether a DPIA is required.

## Roles and Processing Map

| Question | Status |
|---|---|
| Controller(s) for collection, conversion, training, release | [OPEN: LEG-035] |
| Joint-controller arrangement among project partners | [OPEN: LEG-036] |
| Processors, cloud/HPC providers, synthetic-model providers | [OPEN: LEG-037] |
| Categories of data subjects and personal data | [OPEN: LEG-038] |
| Special-category, criminal-offence, minors' data | [OPEN: LEG-039] |
| International transfers | [OPEN: LEG-040] |

## Source Categories Requiring Focused Review

- public conversation datasets, including WildChat-style sources;
- reviews, dialogue, social-media, and instruction datasets containing names or
  autobiographical information;
- DBC and Lex.dk agreement-supplied material;
- Common Pile and DynaWord source material used for transformations;
- synthetic data that may retain source personal data;
- model outputs and evaluation logs containing prompts or generated personal
  data.

## Required GDPR Analysis

1. Purpose and lawful basis per processing phase and source category.
2. Research derogations and safeguards under applicable Danish/EU law.
3. Article 14 transparency or exemption analysis for indirectly obtained data.
4. Necessity, proportionality, data minimisation, and retention.
5. DPIA screening and, if indicated, completed DPIA before continued release.
6. Accuracy, special-category/minors controls, and source-level PII detection.
7. Security measures, access controls, deletion, and incident response.
8. Data-subject rights intake, identity verification, dataset/model traceability,
   response options, and limitations of model unlearning.
9. Processor agreements and international-transfer safeguards.

## Existing Evidence

- source allow/deny decisions and provenance reviews in the repository wiki;
- synthetic audit/filter summaries;
- complete 161-source final-DFM8 inventory and sampling counts in
  `legal/registers/dataset-legal-basis-register.csv`, including a preliminary
  privacy triage that prioritises conversational/user-generated, mixed-web,
  source-retaining synthetic, and agreement-supplied sources;
- exact historical DFM6/DFM7/DFM8 source-prefix and task exposure registers;
- a repository audit finding no provider-service collection or direct crawler
  path, subject to partner attestation;
- measured data/content-control scope and limitations in
  `legal/controls/07-data-content-controls-assessment.md`;
- Lex.dk source-specific extraction probe;
- model licence disclaimers concerning personal data.

### WildChat Historical Screening Evidence

Repository history records a 2026-06-01 regex screening of all `99,688` rows
in `synquid/wildchat-100k-qwen-messages`. The recorded aggregate indicators
were `65` email-like rows, `2,052` phone-number-like rows, `1,797` URL rows,
and `4,619` rows matching address/name/contact terms. The notes expressly say
that many matches were false positives, while manually observed candidates
included order-contact details and named family members.

The evidence chain is incomplete. The aggregate results are preserved in
commit `332260d`, `wiki/entities/datasets.md`, and the historical DFM4 policy
page. The locally retained input is
`data/downloads/datasets/synquid_wildchat_100k_qwen_messages/data/train.jsonl`.
No original scanner, exact regex definitions, row-level hit manifest,
adjudication record, scrubbed-output manifest, or deletion/removal report was
found in the repository on 2026-08-17. A fresh broad-regex screening reproduced
the general scale but not the exact counts (`64` email-like, `2,067`
phone-like, and `1,794` URL rows). This supports the finding that the source
has elevated personal-data risk; it does not establish anonymisation, GDPR
clearance, or absence of personal data in the sampled training rows.

The upstream ICLR 2024 paper documents a two-step affirmative consent flow.
Before chatting, users agreed to collection of their inputs, model outputs, and
technical connection/device information; use for research, service
improvement, and product development; publication or sharing with third
parties; and retention as necessary. A second prompt specifically reconfirmed
publication and sharing. This is meaningful provenance evidence, but the
paper's reported consent categories do not separately name downstream training
of arbitrary third-party models. The dossier therefore must not equate the
documented opt-in with a completed GDPR consent-validity, purpose limitation,
special-category/minors, or downstream-training analysis.

Project decision, 2026-08-17: the project owner accepts the documented
affirmative WildChat consent as express permission for the current research
model training. This closes the source-expression permission question for that
purpose in the project's rights DAG. It does not constitute DPO approval of the
GDPR lawful basis, erase purpose-limitation questions, or satisfy the still-open
PII, minimisation, security, retention, and data-subject-rights controls.

## Material Gaps

- no consolidated record of processing or source-level lawful-basis register;
- no approved Article 14 analysis or public privacy information identified;
- no complete PII detection/removal specification and measured results;
- no reproducible WildChat row-level screening/adjudication artifact or proof
  that candidate rows were removed from the sampled training corpus;
- no documented data-subject request process for training data/model artifacts;
- no approved retention schedule or role allocation;
- no general memorisation/privacy evaluation beyond limited source probes.

The triage labels are workload ordering, not findings that a source is free of
personal data or lawfully processed. In particular, synthetic, translated, or
reformatted content may preserve personal data from its source.

## Preliminary Risk Position

The use of large third-party conversational and web-derived datasets makes a
categorical assertion that personal information was excluded difficult to
support without measured evidence. Public language should instead describe the
controls and residual risk unless a comprehensive audit substantiates the
stronger claim. [OPEN: LEG-041]
