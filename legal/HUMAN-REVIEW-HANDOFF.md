# Mimir Human Review Handoff

**Prepared:** 2026-08-15  
**State:** All repository-resolvable evidence work complete; remaining actions
require authority, professional judgment, partner attestation, contracts, or
external operational records.

The authoritative row-level queue is
`legal/registers/action-register.csv`: 4 actions are
`resolved_engineering`, 3 are `resolved_human`, and 38 are `human_required`.
No row remains generically `open` or `in_progress`.

## Recommended Review Order

## Effect of an Approved Non-GPAI Determination

If the authorised legal reviewer approves the current Commission-criterion
position for Mimir v1, the legal programme changes from **GPAI compliance** to
**scope evidence plus ordinary release law and governance**:

- retain a signed, version-specific non-GPAI scope memo, independently reviewed
  FLOP calculation, immutable release hashes, and reassessment triggers;
- preserve the drafted Article 53 public summary, Annex XI/XII files,
  GPAI-specific copyright-policy form, AI Office cooperation material, energy
  appendix, and GPAI Code work as contingency/voluntary documentation rather
  than treating them as release-blocking statutory deliverables;
- continue source-rights, DBC/Lex.dk contract, copyright/TDM, privacy/GDPR,
  licence authority, repository ownership, public-contact, and correction work,
  because those duties and risks do not depend on GPAI classification;
- separately assess any hosted chat/API or downstream AI system. A non-GPAI
  model determination does not exempt an AI system built from the model.

No action-register row closes automatically under this scenario. First close
`LEG-027` (independent compute review), `LEG-002` (legal scope approval), and
`LEG-003`/`LEG-045` (responsible legal entity and release authority). The legal
review should then approve a row-level disposition that marks GPAI-only work as
not applicable to Mimir v1 while retaining independent-law and governance
actions. Until then, the present human-required queue remains conservative.

### 1. Provider and scope gate

The accountable technical/compliance owner is Professor Peter Schneider-Kamp,
University of Southern Denmark. Have qualified SDU legal staff or external EU
AI Act counsel decide GPAI scope, Article 2(6), legal placement
characterisation, and the responsible provider entity or entities.

Actions: `LEG-002`, `LEG-003`, `LEG-042`, `LEG-045`.

Evidence ready: scope memo, exact `1.19e22` FLOP engineering bound, release
repository date, artifact hashes, capability evaluation inventory, and model
licence/report references.

### 2. Source, copyright, and public-summary gate

Have the provider/partners attest source completeness and acquisition facts;
have copyright counsel review public sources and the confidential DBC/Lex.dk
agreements; approve Article 3/4 and rights-reservation handling.

Actions: `LEG-007` through `LEG-010`, `LEG-013`, `LEG-014`, `LEG-016` through
`LEG-019`.

Evidence ready: exact historical task/source exposure, final 161-source
register, 159-source current HF metadata snapshot, 116 local snapshot records,
source-filter policy, synthetic pipeline evidence, and provider/data
attestation template.

The latest repository-evidenced final source date is 2026-07-14. Professor
Peter Schneider-Kamp attested on 2026-08-15 that no later source was acquired.

### 3. Data-protection gate

Assign the DPO reviewer, determine controller/joint-controller/processor roles,
review data-subject and personal-data categories, decide DPIA/Article 14 needs,
and approve public wording and transfer safeguards.

Actions: `LEG-011`, `LEG-034` through `LEG-041`.

Evidence ready: exact phase exposure, source-level privacy triage, controls
assessment, no-provider-service-collection repository finding, and Lex.dk
extraction probe. The evidence does **not** support categorical wording that
all personal information was excluded.

### 4. Technical, energy, safety, and release gate

Have the relevant owners attest the historical environment/runtime, approve
the design rationale and compute/energy methodology, define the safety threat
model and thresholds, approve acceptable use, and publish the required contact
and correction routes.

Actions: `LEG-020` through `LEG-025`, `LEG-027` through `LEG-033`,
`LEG-043`, `LEG-044`.

Evidence ready: training phases and config, current serving environment,
release hashes, compute arithmetic, conservative energy bounds, 39-task
evaluation register, 1,252-file evaluation hash manifest, existing smoke and
memorisation probes, and explicit safety-coverage gaps.

## Facts Humans Must Not Infer Away

- The model is below the compute thresholds discussed in the scope memo, but
  ordinary GPAI scope and the scientific-R&D exclusion still require counsel.
- Current Hub licence metadata is not acquisition-time legal evidence.
- No direct crawler or provider-user-data path was found in the repository,
  but only partner/contractor attestation can make that cross-project claim.
- Model-judge filtering is not copyright, illegal-content, or privacy
  clearance.
- Energy numbers are conservative nameplate estimates, not measurements.
- Capability benchmarks and limited qualitative/privacy probes are not a
  completed safety evaluation.

## Closure Protocol

For each `human_required` row, record the named reviewer/owner, decision date,
signed or immutable evidence location, approved public wording where relevant,
and any new engineering follow-up. Do not change a row to resolved based only
on an unauthorised technical inference. A fact supplied by the accountable
owner may be marked `resolved_human`; legal conclusions still require the
qualified reviewer named by the relevant action.
