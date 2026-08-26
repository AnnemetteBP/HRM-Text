---
type: Assessment
title: Mimir EU AI Act Documentation Gap
description: Provisional scope analysis and documentation gap assessment for the Mimir v1 research release under the EU AI Act GPAI rules.
tags: [mimir, eu-ai-act, gpai, compliance, documentation]
status: draft
last_updated: 2026-08-15
confidence: medium
sources:
  - id: eu-ai-act
    resource: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
    title: Regulation (EU) 2024/1689
    author: org:European-Union
  - id: eu-gpai-guidelines
    resource: https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers
    title: Guidelines on obligations for general-purpose AI providers
    author: org:European-Commission
  - id: eu-training-summary-template
    resource: https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models
    title: Explanatory Notice and Template for the Public Summary of Training Content
    author: org:European-Commission
  - id: mimir-report
    resource: https://arxiv.org/abs/2608.13517
    title: DFM Mimir v1 Technical Report
---
# Mimir EU AI Act Documentation Gap

This is a technical compliance-readiness assessment, not legal advice. It
compares the Mimir v1 model card, MIMIR License v1.0, and technical report with
the EU AI Act and current Commission GPAI guidance.

## Scope Comes First

The project estimate of approximately `10^22` training FLOPs is below the
Commission's indicative `10^23`-FLOP criterion for identifying a language model
as a GPAI model. It is also far below the statutory `10^25`-FLOP presumption for
a GPAI model with systemic risk. The `10^23` criterion is not an absolute safe
harbour: the Commission says a below-threshold model can still qualify if it
displays significant generality and competently performs a wide range of tasks.
Mimir's own report and benchmark coverage are evidence of such generality.

The primary proposed scope position is nevertheless the Commission's current
conjunctive criterion: Mimir generates language but its conservative `1.19e22`
FLOP bound is only 11.9% of `1e23`; crossing the criterion would require an
unmodelled multiplier above approximately 8.4. Reliance on this position means
freezing the version-specific compute evidence, obtaining independent technical
reproduction and qualified legal approval, using carefully qualified public
wording, and reassessing after further training, a successor release, or
guidance changes. It does not depend on either the open-source exemption or the
sole-scientific-R&D exclusion.

If qualified review approves that position, the work programme should pivot:
retain the signed scope memo, independently checked compute annex, release
hashes, and reassessment triggers, but treat Annex XI/XII, the Article 53 public
summary, GPAI-specific policy form, energy appendix, and AI Office/Code material
as contingency or voluntary documentation. Source rights, confidential data
agreements, copyright/TDM, GDPR, licence authority, repository ownership,
contacts, corrections, and any hosted or downstream AI-system assessment remain
independently necessary. No open action is automatically closed before the
legal reviewer approves that row-level disposition.

There is a separate, plausible Article 2(6) argument because Mimir is licensed
only for non-commercial research and the AI Act excludes models specifically
developed and put into service solely for scientific research and development.
That argument needs legal review. The licence also covers teaching and states
that commercial rights may be available separately, and a future commercial
release would require a new scope assessment. Distribution for free does not by
itself remove provider status when a model is otherwise placed on the Union
market.

If Article 2(6) applies, it excludes the model and its output from the AI Act
as a whole; it is not merely an Article 53 documentation exemption. It does not
remove copyright, GDPR, contractual, or other legal duties. The test is narrow:
Mimir must have been specifically developed **and put into service solely** for
scientific R&D. Article 2(8) separately protects pre-release research, testing,
and development, but does not itself cover the public post-release model.

Prospective licence alignment could strengthen this position by defining and
permitting only scientific R&D, making evaluation/publication ancillary to
that purpose, removing standalone teaching and general study, prohibiting paid
or free operational deployment and non-research output use, preserving the
restriction for derivatives, and removing the advertised separate-commercial-
licence path. The model card, access gate, repository positioning, and release
approval must say the same thing. This would narrow downstream utility and
cannot retroactively erase rights or facts from the existing MIMIR License
v1.0 release; counsel should treat any revision as a versioned prospective
release.

Before relying on either argument, create and approve a versioned **scope and
provider determination memo** covering:

- exact cumulative training FLOPs and calculation method;
- capabilities and generality relative to the Commission's below-threshold
  exception;
- intended purpose and evidence supporting the sole-scientific-R&D position;
- whether the Hugging Face distribution is a making-available in the course of
  commercial activity;
- the legal person or persons acting as provider in the multi-institution
  project;
- release date, model version, distribution channels, and reassessment triggers
  such as relicensing, further training, wider deployment, or commercial use.

## Existing Evidence

The scientific materials already cover substantial parts of a compliance file:

- architecture, parameters, context length, tokenizer, training stack, key
  hyperparameters, hardware, duration, steps, and token volume;
- an inventory of 161 training datasets with Hugging Face identifiers, data
  form, sampled tokens, and share of the epoch;
- high-level language, category, repetition, curation, synthetic-generation,
  agreement-supplied, and transformation information;
- benchmark protocols, prompt-shot policy, decoding limits, metrics, results,
  and broad capability limitations;
- licence restrictions and a statement that Article 3 DSM scientific-research
  text-and-data mining was among the legal bases used.

These materials are a useful evidence source, but a technical report and model
licence are not substitutes for the dedicated Article 53 artifacts.

## Missing Or Incomplete If Mimir Is GPAI

| Priority | Artifact | Gap relative to current public materials |
|---|---|---|
| P0 | Provider/scope determination | No documented legal conclusion identifies the provider entity, resolves the research exclusion, or assesses below-threshold generality. |
| P0 | Commission-format public training-content summary | The report's dataset appendix is not the mandatory AI Office template. The template also asks for provider/model identification, source-type disclosures, public/private/scraped/user/synthetic data details, relevant processing, and rights-relevant information. |
| P0 | EU copyright-compliance policy | The licence's Article 3 TDM statement is descriptive, not an operational policy. Document dataset legal-basis review, lawful access, Article 4(3) rights reservations where relevant, crawler/vendor controls, rights-holder contact and complaints, removal/update handling, and retained evidence. |
| P0 | Confidential Annex XI technical file | Consolidate the scattered evidence and add exact FLOPs, calculation methodology, estimated energy, release/distribution details, intended integrations, design rationale, training/testing/validation provenance, data-point counts, selection/filtering methods, bias/source-unsuitability checks, and lifecycle/version control. |
| P1 | Annex XII downstream integration pack | The card lacks a complete usage and integration guide: supported software versions, PrefixLM/FlashAttention requirements, chat template, input/output formats, context/output limits, capabilities, limitations, acceptable uses, infrastructure, dependencies, and evaluation interpretation. |
| P1 | Evaluation and limitation dossier | Existing capability benchmarks are strong, but safety, bias, toxicity, privacy leakage/memorisation, misuse, robustness, security, red-team coverage, and mitigations are not systematically documented. Full Article 55 adversarial/systemic-risk documentation is not indicated at `10^22` FLOPs, but proportionate evidence remains prudent. |
| P1 | Data-protection file | Outside Article 53 itself, retain the GDPR analysis: controller roles, records of processing, lawful bases, Article 14 analysis, DPIA/necessity assessment where applicable, special-category/minors controls, personal-data detection/removal evidence, retention, security, and data-subject request handling. The report's assertion that personal information was excluded is not enough evidence on its own. |
| P2 | Governance and maintenance | Add named compliance ownership, revision history, evidence retention, vulnerability/incident contacts, correction/withdrawal procedures, and triggers for updating the model card, downstream pack, and public training summary. |

The MIMIR research licence is not a free and open-source licence for purposes of
the Article 53(2) exemption. Its sections 3 and 5 restrict use, modification,
and redistribution to non-commercial research and contemplate separate
commercial licensing. Commission GPAI scope guidance section 4.2.1,
paragraphs 75-80, expressly treats non-commercial/research-only restrictions
and separate-commercial-licence requirements as disqualifying. The licence is
therefore accurately described as **open-weight**, not AI-Act free and
open-source. Do not rely on that exemption. Even qualifying free/open-source
GPAI models still need a copyright policy and public training-content summary.

## Recommended Minimum Package

Even if counsel concludes that Mimir v1 is outside the GPAI rules, retain the
scope memo and prepare the following compact package so that the conclusion is
auditable and a later release can be upgraded without reconstructing evidence:

1. `MIMIR-SCOPE-AND-PROVIDER-ASSESSMENT-v1`.
2. Exact compute and energy calculation appendix.
3. Completed Commission public training-content template published beside the
   model.
4. Written EU copyright and related-rights policy with dataset-level evidence.
5. Annex XI-aligned confidential technical file assembled from the report and
   training records.
6. Annex XII-aligned public/downstream integration guide.
7. GDPR and data-governance assessment maintained separately from the AI Act
   dossier.

At the current compute estimate there is no basis for treating Mimir as
systemic-risk by the compute presumption, so Article 55's notification,
systemic-risk management, serious-incident reporting, and enhanced
cybersecurity package are not the immediate documentation target. Reassess if
the Commission designates the model based on equivalent capabilities or a
future version crosses the relevant threshold.

## Draft Dossier Started

On 2026-08-15, the project created a review-oriented compliance dossier under
[`legal/`](../../../legal/README.md). It contains:

- a confidential scope and provider assessment;
- a public training-content summary following the Commission's mandatory
  section structure;
- an operational copyright-compliance policy;
- Annex XI and Annex XII draft documentation;
- a GDPR/data-protection issue assessment;
- release, risk, correction, and maintenance governance;
- evidence, action, training-phase, and dataset-legal-basis registers.

The dossier records a new P0 evidence issue: Mimir's published checkpoint was
continued through DFM6, DFM7, and DFM8 recipes. The public training summary and
Annex XI file must cover the union and exact exposure of all content actually
used across those phases, rather than treating the final 161-source DFM8 recipe
as the entire training history without reconciliation.

## Repository-Evidenced Closure Work

Update, 2026-08-15. Confidence: high for immutable local artifacts; medium for
legal characterisation and source histories that still require human review.

- Exact checkpoint sidecars establish the curriculum boundaries:
  - DFM6: steps `0..720083`, `188,765,700,096` nominal token presentations;
  - DFM7: steps `720084..1229503`, `133,541,396,480` nominal tokens;
  - DFM8: steps `1229504..1649999`, `110,230,503,424` nominal tokens.
- The final DFM8 inventory has been materialised as a 161-row legal-review
  register. Its `70,479,308,606` source-token per-epoch mean matches
  `docs/dfm8-datasets.md`. The sampler metadata value `70,479,433,697` is the
  concatenated token-store length, not a conflicting per-epoch measurement;
  the earlier discrepancy interpretation is superseded.
- The downloader uses Hugging Face `snapshot_download`; 116 recoverable local
  revisions/timestamps are registered. No provider-operated crawler was found
  in the repository, but partner/contractor attestation remains necessary.
- A separate live HF API snapshot covers all 159 public final-DFM8 sources:
  129 currently declare a licence and 30 do not. Live repository metadata is
  useful triage but must not be confused with acquisition-time terms or a
  source-level legal approval.
- Saved release-run configuration proves that no validation corpus was used:
  `validation_path=null`, `validation_interval=0`, and
  `validation_batches=0`. Monitoring used training metrics and periodic
  benchmark evaluations.
- The recurrence-aware compute arithmetic was independently reproduced from
  the documented constants: `1.18212893148708864e22` major-operation FLOPs,
  rounded conservatively to `1.19e22` after elementwise work.
- No metered energy record was found. At `<1.1` seconds per step, active time is
  below `504.17` hours. Nameplate bounds are `<4.033 MWh` for eight 1-kW B200s
  and `<7.210 MWh` using a DGX-B200 14.3-kW whole-system analogue. These are not
  actual consumption measurements.
- The local release export is SHA-256 frozen, the current tested serving
  package versions are registered, and 39 release-checkpoint evaluation task
  groups are mapped to their production scheduler outputs.
- Exact sampled-index attribution maps 1,350,991,478 consumed rows and
  431,832,565,530 non-padding source tokens across DFM6, DFM7, and DFM8 to
  31,868 phase/task records. This supersedes the earlier historical-source-
  union gap; acquisition-time legal terms still need human review.
- The release evaluation plan, retained result artifacts, configs, and key code
  inputs are frozen in a 1,252-row SHA-256 manifest. Data/content controls and
  safety-evaluation coverage gaps are documented separately under `legal/controls/`.

Rebuild these machine-derived records with:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python legal/tools/build_evidence_registers.py
/home/ucloud/miniforge3/envs/hrm/bin/python legal/tools/build_phase_source_exposure.py
/home/ucloud/miniforge3/envs/hrm/bin/python legal/tools/build_synthetic_pipeline_register.py
/home/ucloud/miniforge3/envs/hrm/bin/python legal/tools/build_evaluation_artifact_manifest.py
/home/ucloud/miniforge3/envs/hrm/bin/python legal/tools/validate_dossier.py
```

Provider identity, contractual rights, DPO decisions, Article 3/4 legal bases,
complaints contacts, facility telemetry, partner attestations, threat-model
approval, and legal approvals cannot be resolved from repository evidence
alone and remain human-required in `legal/registers/action-register.csv`.

## Human Facts Recorded on 2026-08-15

Professor Peter Schneider-Kamp of the University of Southern Denmark is the
accountable technical and compliance decision owner (`LEG-001`). The project
declared an open-weight release through Hugging Face Hub on 2026-08-15
(`LEG-004`) and attested that no source was acquired after the latest
repository-evidenced source date of 2026-07-14 (`LEG-006`). These facts do not
determine the legal provider or whether the release constitutes Union-market
placement; those conclusions remain reserved for `LEG-002` and `LEG-003`.
