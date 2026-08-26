# Mimir Release, Risk, and Maintenance Plan

**Status:** Draft

## Ownership

| Function | Accountable owner | Backup | Contact |
|---|---|---|---|
| Technical/compliance decision owner | Professor Peter Schneider-Kamp, University of Southern Denmark |  |  |
| Technical documentation | [OPEN: LEG-042] |  |  |
| Dataset/copyright review | [OPEN: LEG-016] |  |  |
| Data protection | [OPEN: LEG-034] |  |  |
| Model evaluation/safety | [OPEN: LEG-043] |  |  |
| Security/incident response | [OPEN: LEG-044] |  |  |
| Public model repository | [OPEN: LEG-045] |  |  |

## Versioned Release Record

Each release record must bind:

- model name, semantic version, repository SHA, weight hash, config/tokenizer/
  template hashes;
- training checkpoint, EMA mode, corpus phases, sampling indices and source
  versions;
- compute and energy calculation version;
- model card, licence, public training summary, downstream information, and
  technical-document versions;
- evaluation code/data revisions, raw results, risk acceptance and approvers;
- release timestamp and distribution channels.

## Pre-Release Gate

- scope/provider memo approved;
- licence authority confirmed;
- public training summary complete and published if applicable;
- copyright policy operational and source register approved;
- Annex XI/Annex XII documents complete if applicable;
- DPO review and DPIA decision complete;
- capability, safety, bias, privacy/memorisation and security evaluations
  reviewed;
- downstream instructions reproduce reference outputs;
- rights, privacy, security and technical contacts live;
- known limitations and unresolved risks explicitly accepted.

## Change and Reassessment

Review after further training, data changes, altered intended use, new licence,
new API/product distribution, capability expansion, material incident, rights
claim, provider change, or regulatory update. The public training summary must
be updated at the cadence and materiality thresholds required by the Commission
template.

## Complaints, Corrections, and Withdrawal

Maintain linked registers for copyright, privacy, safety, and security reports.
Triage severity and affected versions; preserve evidence; notify responsible
owners; decide correction, new release, access restriction, or withdrawal;
communicate changes on every distribution channel.

## Incidents

Mimir is not currently treated as systemic-risk. A proportionate internal
incident process remains required for good governance and downstream support.
If systemic-risk status changes, replace this section with the Article 55
serious-incident reporting and cybersecurity procedures.

## Evidence Retention

The retention schedule must cover immutable model artifacts, source manifests,
contracts and legal reviews, transformation/audit records, training logs,
compute/energy evidence, evaluations, release approvals, and complaints.
Duration and access controls: [OPEN: LEG-020].
