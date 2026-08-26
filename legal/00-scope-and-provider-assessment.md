# Mimir v1 Scope and Provider Assessment

**Status:** Draft for counsel  
**Classification:** Confidential  
**Assessment date:** 2026-08-15  
**Decision owner:** Professor Peter Schneider-Kamp, University of Southern Denmark  
**Legal reviewer:** [OPEN: LEG-002]

## Question Presented

Does the EU AI Act apply to DFM Mimir v1 as a general-purpose AI model placed
on the Union market, which legal person or persons are its provider, and which
GPAI obligations follow?

## Verified Facts

| Fact | Current evidence |
|---|---|
| Model | DFM Mimir v1, text-generation model, approximately 1B parameters. |
| Capability | Danish and English generation evaluated across English, Danish, mathematics, code, reasoning, translation, summarisation, and instruction-following tasks. |
| Architecture | HRM-Text; 1,536 hidden size; 32 configured layers with half-layer H/L stacks; 12 heads; 4,096-token context; 262,144-token vocabulary. |
| Training | 1,650,000 optimizer steps; 262,144 tokens/step; 8 NVIDIA B200 GPUs; approximately three weeks. |
| Token presentations | `432,537,600,000` nominal tokens (`1,650,000 * 262,144`), subject to confirmation of skipped or partial steps. |
| Compute | Engineering recurrence-aware upper bound `1.19e22` FLOPs. Methodology requires independent review. |
| Release | Project-declared open-weight release through Hugging Face Hub on 2026-08-15. The repository was created 2026-08-03T10:47:24Z and uses gated automatic access. Legal Union-market characterisation remains for LEG-002/LEG-003. |
| Licence | MIMIR License v1.0, non-commercial research only; teaching, evaluation, modification, and redistribution permitted within its terms; commercial rights may be separately available. |
| Development | Multi-institution collaboration involving SDU, Aarhus University, University of Copenhagen, and Alexandra Institute under Danish Foundation Models. |

## Legal Tests

### 1. GPAI model

Commission guidance uses an indicative criterion of more than `1e23` training
FLOPs and a qualifying generative modality. Mimir is below that compute
criterion. This is not dispositive: a below-threshold model may qualify if it
shows significant generality and can competently perform a wide range of tasks.
Mimir's own report contains evidence supporting broad generality.

**Preliminary position:** compute points away from GPAI classification; breadth
of capability creates material residual uncertainty. Obtain a reasoned legal
conclusion rather than treating the threshold as a safe harbour.

#### Primary non-GPAI position under current Commission guidance

The least assumption-dependent route is a version-specific determination based
on section 2.1, paragraph 17 of the Commission GPAI scope guidelines. Its
current indicative criterion is conjunctive: training compute greater than
`1e23` FLOPs and generation of language, text-to-image, or text-to-video.
Mimir generates language but the repository-reconstructed recurrence-aware
upper bound is `1.19e22` FLOPs, or 11.9% of the compute criterion. An unmodelled
multiplier greater than approximately 8.4 would be required to cross it.

To rely primarily on this position, the provider should:

1. bind the assessment to the exact released checkpoint, weight/config hashes,
   1,650,000 optimizer steps, architecture, recurrence/BP assumptions, and
   token presentations;
2. have an independent technical reviewer reproduce the calculation under the
   Commission guideline's training-compute convention and approve a sensitivity
   analysis for disputed FLOP-counting conventions;
3. have the authorised legal reviewer approve the conclusion that the current
   Commission criterion indicates Mimir v1 should not be treated as a GPAI
   model, while acknowledging that the statutory definition and Commission
   criterion are not the same as a formal certification or immutable safe
   harbour;
4. retain the calculation, source evidence, signed decision, and public wording
   with the release record, without presenting it as an AI Office decision;
5. monitor cumulative further training, material modifications, successor
   models, capability expansion, and changes to Commission criteria or
   enforcement guidance, and reassess before the affected release.

Suggested external wording after approval: "Based on the European
Commission's current indicative GPAI criterion and a documented conservative
training-compute estimate of `1.19e22` FLOPs, Mimir v1 is not currently treated
by the provider as a general-purpose AI model for purposes of Chapter V. This
assessment is version-specific and will be reviewed following material further
training or regulatory guidance changes."

This position avoids depending on the Article 53(2) open-source exemption or
Article 2(6) sole-scientific-R&D exclusion. It does not exempt downstream AI
systems built with Mimir, and it does not affect copyright, GDPR, contracts, or
other applicable law. The existing compliance dossier remains useful as
voluntary evidence and as contingency material if the classification changes.

### 2. Scientific research and development exclusion

Article 2(6) excludes models specifically developed and put into service for
the sole purpose of scientific research and development. The research licence,
academic partners, funding, and stated research purpose support the exclusion.
Countervailing considerations include teaching and other defined Research Uses,
the model's broad assistant positioning, public distribution, and the statement
that commercial rights may be separately available.

**Effect if Article 2(6) applies:** the AI Act does not apply to the model or
its output, rather than merely exempting the provider from selected Article 53
GPAI duties. This does not displace copyright, data-protection, contractual, or
other applicable Union or national law. The exclusion is narrower than a model
being useful for research: the model must have been specifically developed and
put into service for the **sole** purpose of scientific R&D. Public release is
not expressly incompatible with that test, but the documented intended
purpose, licence, release controls, actual positioning, and absence of
non-research deployment must support it.

Article 2(8) is separate and only excludes research, testing, and development
activities before market placement or putting into service. It does not by
itself cover the post-release Hugging Face distribution. A later commercial or
other non-research release or deployment requires reassessment, and a
downstream actor's non-research AI system is not made exempt merely because it
uses Mimir.

**Questions for counsel:**

1. Is the model's documented intended purpose sufficiently limited to the sole
   purpose of scientific R&D?
2. Does teaching within the licence exceed that sole purpose?
3. Does availability of separate commercial rights affect the present release
   or only a future separately licensed placement?
4. What technical or contractual controls are needed to preserve the exclusion?

#### Prospective licence and release alignment

Licence wording can support, but cannot by itself establish, Article 2(6). A
counsel-drafted successor release intended to maximise reliance on the
exclusion should consider:

- replacing `Non-Commercial Research Use` with a defined **sole scientific
  research and development purpose**; commercial sponsorship is not itself the
  relevant test, while operational or product use is;
- defining scientific R&D as systematic investigation or experimental
  development directed at new knowledge, reproducibility, model understanding,
  capability or safety research, and permitting evaluation, benchmarking,
  publication, and collaboration only when ancillary to that purpose;
- removing standalone teaching, general study, personal experimentation, and
  other uses that are not necessarily scientific R&D, or placing them under a
  separate release that does not rely on Article 2(6);
- expressly prohibiting production deployment, public or internal operational
  services, automated decision-making, product integration, and use of model
  outputs outside scientific R&D, whether paid or free;
- requiring derivative models and redistribution to preserve the same
  scientific-R&D-only purpose and notices;
- removing the statement advertising separately available commercial rights
  from the research release, while treating any later commercial or
  non-research version as a separate release requiring a new scope assessment;
- aligning the model card, repository description, access gate, intended-use
  statement, examples, and release approval with the same narrow purpose, and
  obtaining recipient purpose attestations where proportionate.

These changes trade breadth of permitted use for stronger Article 2(6)
evidence. An unrestricted free/open-source licence generally permits use for
any purpose and therefore points in the opposite direction from a sole-R&D
position.

Mimir v1 was already distributed under License v1.0. A revised licence should
be prospective and versioned; it cannot be assumed to revoke accepted v1.0
rights or erase the original release facts. Counsel should determine whether a
new release/version, changes to future access, and notices concerning the old
release are appropriate.

### 3. Placing on the market and provider

The AI Act defines provider by development and placement under one's own name
or trademark, whether for payment or free. Making available on the market
requires supply in the course of commercial activity. The facts relevant to
whether this academic release is such activity must be documented.

`Danish Foundation Models` may be a project name rather than a legal person.
The institutions' development, branding, account control, funding agreement,
licensing authority, and release approval must be mapped before naming the
provider or joint providers.

### Review and provider-determination route

No provision identified in the AI Act requires this preliminary scope review
to be performed by an external lawyer or by a specifically certified
profession. The obligations attach to the provider. For this dossier, the
review may therefore be completed by qualified SDU legal staff or external EU
AI Act counsel, provided the reviewer has relevant EU regulatory competence,
records a reasoned conclusion, and the authorised provider representative owns
and signs the resulting decision. Copyright and data-protection issues should
also be routed to the institution's copyright counsel and DPO respectively.

`LEG-003` asks for the responsible legal person, not merely the project lead or
the name of the Hugging Face organisation. Determine which institution or
institutions:

- controlled or commissioned model development and the public release;
- authorised use of the releasing name or brand and the MIMIR licence;
- controls the Hugging Face repository and can change, correct, or withdraw
  the release;
- can receive authority and downstream-provider requests and accept the
  corresponding obligations.

If one institution satisfies those facts, assess it as the provider. If
multiple institutions jointly controlled and released the model under their
names, counsel should assess whether they are joint providers and document
their allocation of responsibilities. Do not infer the legal entity solely
from the `danish-foundation-models` Hub account name.

### 4. Free/open-source GPAI exemption

Do not rely on Article 53(2). The MIMIR License prohibits commercial use and is
not treated as a free and open-source licence. Sections 3 and 5 limit use,
modification, and redistribution to non-commercial research and reserve
commercial rights for separate licensing. Paragraphs 75-80 of section 4.2.1 of
the Commission's GPAI scope guidelines state that the licence must permit use
for any purpose and expressly identify non-commercial/research-only limits and
requirements for separate commercial licences as disqualifying restrictions.
The safety restrictions in section 6 are not the primary blocker; Commission
guidance permits proportionate, objective safety-oriented restrictions.

Even a qualifying open-source release would still require the copyright policy
and public training-content summary under Article 53(1)(c)-(d).

### 5. Systemic risk

The `1.19e22` estimate is far below the `1e25` compute presumption. No evidence
currently suggests Commission designation based on equivalent high-impact
capabilities.

**Preliminary position:** no systemic-risk notification is indicated. Preserve
the compute calculation and reevaluate for materially larger successors.

## Provisional Decision Matrix

| Conclusion after review | Required action |
|---|---|
| Outside AI Act under Article 2(6) | Retain signed scope memo and evidence; monitor purpose, licensing, and deployment changes. |
| In scope but not GPAI | Document reasoning; assess any AI-system obligations for hosted or integrated deployments separately. |
| GPAI, non-systemic | Complete Article 53 package: Annex XI, Annex XII, copyright policy, mandatory public training summary, cooperation process. |
| GPAI with systemic-risk designation | Add Article 52 notification and full Article 55 safety/security, systemic-risk, incident, and cybersecurity package. |

## Reassessment Triggers

- commercial or unrestricted relicensing;
- hosted API or product integration;
- material further training or a successor model;
- cumulative compute approaching `1e23` or `1e25` FLOPs;
- substantial capability expansion or autonomous tool access;
- Commission guidance, designation, or enforcement change;
- change in the entity controlling branding or distribution.

## Approval

| Role | Name/legal entity | Decision | Date |
|---|---|---|---|
| Technical/compliance decision owner | Professor Peter Schneider-Kamp, University of Southern Denmark | Owner recorded | 2026-08-15 |
| EU AI Act counsel | [OPEN: LEG-002] |  |  |
| Provider representative(s) | [OPEN: LEG-003] |  |  |
