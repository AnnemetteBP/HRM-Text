# Mimir EU Copyright and Related-Rights Compliance Policy

**Status:** Draft  
**Policy owner:** [OPEN: LEG-016]  
**Legal reviewer:** [OPEN: LEG-017]  
**Effective date:** [OPEN]  
**Review cycle:** Six months and before each material model release

## 1. Purpose

This policy governs acquisition, transformation, training use, documentation,
and correction of copyright-protected and related-rights content used to
develop Mimir models. It is intended to support Article 53(1)(c) of the EU AI
Act and applicable implementations of Directive (EU) 2019/790.

## 2. Scope

The policy applies to public datasets, agreement-supplied datasets, synthetic
data, translated or transformed data, evaluation data, vendors and contractors,
and every further-training phase. It does not assert that model outputs are
free of third-party rights.

## 3. Permitted Source Bases

A source may enter training only with a documented basis in the dataset register:

1. permissive licence authorising the relevant reproduction/TDM use;
2. direct agreement with the rightsholder or authorised supplier;
3. Article 3 scientific-research TDM based on lawful access and the required
   research-organisation/cultural-heritage conditions;
4. Article 4 TDM based on lawful access and absence of an effective rights
   reservation;
5. public-domain or otherwise unprotected material;
6. provider-generated synthetic content with documented source and generator
   terms; or
7. another basis approved in writing by copyright counsel.

Dataset availability on Hugging Face is not itself a legal basis.

## 4. Intake Controls

Before approval, the responsible data owner records:

- dataset identity, version/commit, supplier, URL, acquisition date, and files;
- provenance and content categories;
- licence or statutory basis, including territorial and research restrictions;
- whether the source contains third-party works not covered by its top-level
  licence;
- rights-reservation/robots/metadata information where Article 4 is relied on;
- personal-data and illegal-content indicators;
- transformations, filters, and intended sampling;
- approval, reviewer, date, and retained evidence.

Unknown or conflicting terms result in quarantine until resolved. Changes to
upstream terms trigger reassessment; they do not silently rewrite the basis for
a lawfully acquired immutable version.

## 5. Article 3 Scientific-Research TDM

Where Article 3 or its national implementation is relied on, retain evidence
that the activity was conducted by or for a qualifying research organisation
or cultural-heritage institution, for scientific research, with lawful access
and appropriate security. Record which institution performed the act and under
which national implementation. [OPEN: LEG-018]

## 6. Article 4 Rights Reservations

Where Article 4 is relied on:

- identify and honour machine-readable reservations, including relevant
  robots, metadata, website terms, and accepted state-of-the-art protocols;
- require suppliers/crawlers to document equivalent controls;
- do not circumvent access controls, paywalls, or effective technical measures;
- keep logs of checks, exclusions, and the applicable acquisition date;
- support removal or future-training exclusion when a valid reservation or
  rights claim is established.

The current project did not identify direct provider crawling; this must be
verified. Third-party packaged datasets still require supplier and legal-basis
review. [OPEN: LEG-010, LEG-014]

## 7. Agreements and Private Data

The project owner confirmed on 2026-08-17 that the DBC and Lex.dk agreements
permit model training and model release. Material remains subject to the exact
parties, duration, security, attribution, source-redistribution and other
downstream-use terms of those agreements. Contract summaries and approvals are
retained separately; confidential terms are not placed in public
documentation. Commission-template categorisation and the remaining terms are
tracked in `LEG-008` and `LEG-009`.

## 8. Synthetic and Transformed Data

Synthetic generation or transformation does not automatically remove rights in
source material. Record the source basis, generator model and terms, prompt and
audit procedure, similarity/memorisation controls, accepted/rejected counts,
and whether outputs can reproduce protected source expression.

## 9. Complaints and Rights-Holder Requests

Publish a contact route for rights holders. Each request receives an identifier
and records claimant, work/source, evidence, affected dataset/model versions,
assessment, response, and corrective action. Available actions include source
quarantine, future-training exclusion, public-summary correction, model-card
notice, and model withdrawal where proportionate.

Contact and service-level targets: [OPEN: LEG-019]

## 10. Outputs

The model licence and user documentation must state that generated outputs can
contain or resemble protected material and that users remain responsible for
their use. Maintain proportionate memorisation/extraction tests for high-risk
sources and record results, including the completed Lex.dk prefix-extraction
probe.

## 11. Evidence and Audit

The policy owner maintains the dataset legal-basis register, immutable source
identifiers, approvals, opt-out evidence, filtering logs, contracts, complaints,
and release mappings. Evidence must be reproducible for the model version and
retained under the approved retention schedule. [OPEN: LEG-020]
