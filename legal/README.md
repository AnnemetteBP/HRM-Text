# Mimir Legal and Compliance Dossier

> Draft working material. Not legal advice and not approved for publication or
> submission to an authority.

This directory prepares the legal and evidentiary package for **DFM Mimir v1**.
It is intentionally broader than the public model card and technical report.
Every unresolved fact is tracked in [`registers/action-register.csv`](registers/action-register.csv);
do not remove an `[OPEN: LEG-*]` marker without attaching evidence and recording
the reviewer and date.

The review-ready queue and recommended sign-off order are in
[`HUMAN-REVIEW-HANDOFF.md`](HUMAN-REVIEW-HANDOFF.md).

## Document Map

| Path | Audience | Purpose |
|---|---|---|
| [`00-scope-and-provider-assessment.md`](00-scope-and-provider-assessment.md) | Confidential / counsel | Determine whether Mimir is in scope as GPAI, whether the scientific-R&D exclusion applies, and who is the provider. |
| [`public/01-training-content-summary.md`](public/01-training-content-summary.md) | Public after approval | Draft following the Commission's mandatory Article 53(1)(d) template. |
| [`policies/02-copyright-compliance-policy.md`](policies/02-copyright-compliance-policy.md) | Internal; publish summary | Operational Article 53(1)(c) copyright policy. |
| [`authorities/03-annex-xi-technical-documentation.md`](authorities/03-annex-xi-technical-documentation.md) | Confidential; authorities on request | Annex XI / Code of Practice model documentation file. |
| [`authorities/05-energy-estimate.md`](authorities/05-energy-estimate.md) | Confidential; technical review | Nameplate energy bounds, evidence, assumptions, and unresolved telemetry gap. |
| [`downstream/04-annex-xii-model-information.md`](downstream/04-annex-xii-model-information.md) | Downstream integrators | Integration, capability, limitation, and data information required by Annex XII if applicable. |
| [`data-protection/05-data-protection-assessment.md`](data-protection/05-data-protection-assessment.md) | Confidential / DPO | GDPR and personal-data assessment adjacent to the AI Act dossier. |
| [`governance/06-release-risk-and-maintenance-plan.md`](governance/06-release-risk-and-maintenance-plan.md) | Internal | Ownership, version control, complaints, incidents, corrections, and reassessment gates. |
| [`controls/07-data-content-controls-assessment.md`](controls/07-data-content-controls-assessment.md) | Internal / public-summary evidence | Measured source, filtering, synthetic-audit, and memorisation controls plus explicit limitations. |
| [`controls/08-evaluation-and-safety-evidence.md`](controls/08-evaluation-and-safety-evidence.md) | Internal / risk review | Frozen capability evidence, existing safety-adjacent probes, absent coverage, and human threat-model gate. |
| [`registers/evidence-register.csv`](registers/evidence-register.csv) | Internal | Source-of-truth map for each material claim. |
| [`registers/training-phase-register.csv`](registers/training-phase-register.csv) | Internal | Corpus/version timeline for every training phase. |
| [`registers/phase-source-exposure-register.csv`](registers/phase-source-exposure-register.csv) | Internal | Exact sampled row/token exposure by phase and source prefix. |
| [`registers/phase-task-exposure-register.csv`](registers/phase-task-exposure-register.csv) | Internal | Exact sampled row/token exposure by phase and tokenized task. |
| [`registers/dataset-legal-basis-register.csv`](registers/dataset-legal-basis-register.csv) | Confidential | Complete final-DFM8 source inventory for rights and privacy review. |
| [`registers/dfm9-copyright-basis-register.csv`](registers/dfm9-copyright-basis-register.csv) | Confidential | Token-reconciled source-level DFM9 copyright and Article 3/4 triage. |
| [`registers/dfm9-article3-audit-register.csv`](registers/dfm9-article3-audit-register.csv) | Confidential | Component and row-level decisions for sources initially assigned to Article 3 review. |
| [`registers/dfm9-sapient-instruction-family-inventory.csv`](registers/dfm9-sapient-instruction-family-inventory.csv) | Confidential | Exact sampled FLAN, Tasksource, and Platypus file exposure with pinned upstream mappings and current Tasksource licence metadata. |
| [`registers/dfm9-tulu3-mixture-component-audit.csv`](registers/dfm9-tulu3-mixture-component-audit.csv) | Confidential | Exact 19-label row inventory and rights result for the effective Tulu 3 SFT mixture. |
| [`registers/dfm9-smoltalk-component-audit.csv`](registers/dfm9-smoltalk-component-audit.csv) | Confidential | Exact SmolTalk and SmolTalk2 SFT component terms and residual risks. |
| [`registers/dfm9-openhermes-component-audit.csv`](registers/dfm9-openhermes-component-audit.csv) | Confidential | All 1,001,551 OpenHermes rows assigned to 19 source blocks. |
| [`registers/dfm9-mot-expression-risk.csv`](registers/dfm9-mot-expression-risk.csv) | Confidential | MoT prompt, editorial, and generated-trace copyright-risk strata. |
| [`registers/dfm9-longalign-content-groups.csv`](registers/dfm9-longalign-content-groups.csv) | Confidential | Heuristic content groups for all 9,888 LongAlign rows. |
| [`registers/dfm9-euroblocks-seed-risk.csv`](registers/dfm9-euroblocks-seed-risk.csv) | Confidential | EuroBlocks source-label counts and seed-retention risk. |
| [`registers/dfm9-source-dag-nodes.csv`](registers/dfm9-source-dag-nodes.csv) | Confidential | Canonical source, component, contribution, and rights-boundary nodes for DFM9. |
| [`registers/dfm9-source-dag-edges.csv`](registers/dfm9-source-dag-edges.csv) | Confidential | Typed dependency edges; shared upstreams appear once and may affect several effective datasets. |
| [`registers/dfm9-source-dag-resolution.csv`](registers/dfm9-source-dag-resolution.csv) | Confidential | Recursively computed status and affected effective-source ancestry for every DAG node. |
| [`registers/dfm9-source-dag-expansion-queue.csv`](registers/dfm9-source-dag-expansion-queue.csv) | Confidential | Token-ranked effective sources whose upstream dependencies still need decomposition. |
| [`registers/dfm9-tulu-v2-sciriff-if-sft-component-audit.csv`](registers/dfm9-tulu-v2-sciriff-if-sft-component-audit.csv) | Confidential | Exact local component counts and working bases for Tulu v2, Tulu v2 Long, SciRIFF Train Mix, and IF-SFT Verified. |
| [`registers/dfm9-sharegpt-boundary-audit.csv`](registers/dfm9-sharegpt-boundary-audit.csv) | Confidential | Aggregate ShareGPT lineage, conversation-structure, source-text, PII, and credential-risk indicators; matched text is not retained. |
| [`registers/dfm9-effective-rights-basis.csv`](registers/dfm9-effective-rights-basis.csv) | Confidential | Purpose-specific exclusive headline basis plus overlapping Article 3/4, agreement, licence, public-status, and review facets. |
| [`registers/dfm9-hf-current-metadata-register.csv`](registers/dfm9-hf-current-metadata-register.csv) | Internal | Current HF metadata for 166 candidate repositories: 159 effective public sources plus seven prospective repositories absent from sampled DFM9. |
| [`reports/dfm9-copyright-tdm-review.md`](reports/dfm9-copyright-tdm-review.md) | Confidential / counsel | Human-readable DFM9 copyright and EU TDM review. |
| [`reports/dfm9-article3-component-audit.md`](reports/dfm9-article3-component-audit.md) | Confidential / counsel | Evidence and outcomes from the one-by-one Article 3 candidate audit. |
| [`reports/dfm9-sapient-flan-tasksource-platypus-audit.md`](reports/dfm9-sapient-flan-tasksource-platypus-audit.md) | Confidential / counsel | Complete retained non-factual FLAN, Tasksource, and Platypus decomposition and current-purpose result. |
| [`reports/dfm9-tulu3-mixture-audit.md`](reports/dfm9-tulu3-mixture-audit.md) | Confidential / counsel | Component-level Tulu 3 audit and project-owner Article 4 treatment of uncovered FLAN/SciRIFF expression. |
| [`reports/dfm9-apertus-component-audit.md`](reports/dfm9-apertus-component-audit.md) | Confidential / counsel | Apertus dependency audit separating direct terms from narrow current-research Article 3 fallbacks. |
| [`reports/dfm9-smoltalk-component-audit.md`](reports/dfm9-smoltalk-component-audit.md) | Confidential / counsel | SmolTalk and SmolTalk2 source-by-source reassessment. |
| [`reports/dfm9-openhermes-component-audit.md`](reports/dfm9-openhermes-component-audit.md) | Confidential / counsel | OpenHermes 2.5 reconstruction and source-block reassessment. |
| [`reports/dfm9-mot-copyright-risk.md`](reports/dfm9-mot-copyright-risk.md) | Confidential / counsel | Mixture-of-Thoughts source-expression and generated-output risk assessment. |
| [`reports/dfm9-longalign-euroblocks-boundary-audit.md`](reports/dfm9-longalign-euroblocks-boundary-audit.md) | Confidential / counsel | LongAlign row grouping and EuroBlocks annealing-seed analysis. |
| [`reports/dfm9-memorisation-source-text-cohorts.md`](reports/dfm9-memorisation-source-text-cohorts.md) | Confidential / counsel | Deduplicated original-source cohorts for memorisation testing, grouped by agreement, Article 3, Article 4, and other bases. |
| [`reports/dfm9-memorisation-extraction-probe-ab.md`](reports/dfm9-memorisation-extraction-probe-ab.md) | Confidential / counsel and testing | Completed 64+64 raw/chat extraction probe over stratified agreement and Article-3 source cohorts, with reusable request identities. |
| [`reports/dfm9-memorisation-exact-match-adjudication-abcd.md`](reports/dfm9-memorisation-exact-match-adjudication-abcd.md) | Confidential / counsel and testing | Gemma 4 31B and manual adjudication of every exact-64 occurrence across exhaustive Categories A-D, including strict prose and copyright-relevance review. |
| [`reports/dfm9-manual-acceptances-and-overrides.md`](reports/dfm9-manual-acceptances-and-overrides.md) | Confidential / counsel and testing | Exhaustive project-owner risk acceptances and rights-basis decisions, with future memorisation-test targets. |
| [`reports/dfm9-source-rights-dependency-dag.md`](reports/dfm9-source-rights-dependency-dag.md) | Confidential / counsel | Human-readable dependency status, beginning with the fully mapped documented DFM Dyna lineage. |
| [`reports/dfm9-source-rights-dependency-appendix.tex`](reports/dfm9-source-rights-dependency-appendix.tex) | Confidential / counsel; publication appendix draft | Self-contained LaTeX tables for all 161 effective DFM9 datasets, all 286 referenced dependency nodes, and all 22 manual decisions, with typed cross-references, terms, status, completeness, exposure, rationale, residual issues, and testing targets. |
| [`reports/dfm9-source-rights-dependency-appendix.pdf`](reports/dfm9-source-rights-dependency-appendix.pdf) | Confidential / counsel; publication appendix draft | Compiled 54-page rendering of the source-rights appendix, built twice with pdfLaTeX and verified without box, unresolved-reference, or rerun warnings. |
| [`reports/dfm9-tulu-v2-sciriff-if-sft-audit.md`](reports/dfm9-tulu-v2-sciriff-if-sft-audit.md) | Confidential / counsel | Row-level lineage audit resolving the four former unresolved AllenAI roots, including MAN-022 for their shared ShareGPT boundary. |
| [`reports/dfm9-sharegpt-boundary-audit.md`](reports/dfm9-sharegpt-boundary-audit.md) | Confidential / counsel and DPO | Focused ShareGPT publication, licence-authority, TDM, transformation, privacy, and local-row audit. |
| [`reports/dfm9-rights-basis-algebra.md`](reports/dfm9-rights-basis-algebra.md) | Confidential / counsel | Proposed rights-basis algebra and current DFM9 counts by exclusive projection and non-exclusive facets. |
| [`registers/synthetic-data-register.csv`](registers/synthetic-data-register.csv) | Internal | Synthetic, translated, generated, and derived source-method register. |
| [`registers/synthetic-pipeline-evidence.csv`](registers/synthetic-pipeline-evidence.csv) | Internal | Exact generation/audit/acceptance evidence for the major DFM8 synthetic pipelines. |
| [`registers/hf-snapshot-register.csv`](registers/hf-snapshot-register.csv) | Internal | Recoverable local Hugging Face revisions and acquisition timestamps. |
| [`registers/evaluation-register.csv`](registers/evaluation-register.csv) | Internal | Release-checkpoint evaluation tasks and result locations. |
| [`registers/evaluation-artifact-manifest.csv`](registers/evaluation-artifact-manifest.csv) | Internal | SHA-256 manifest of production evaluation plans, configs, code inputs, and retained outputs. |
| [`registers/release-artifact-register.csv`](registers/release-artifact-register.csv) | Confidential | SHA-256 and size manifest for the local release export. |
| [`tools/build_evidence_registers.py`](tools/build_evidence_registers.py) | Internal | Rebuilds the machine-derived registers and validates source/token checksums. |
| [`tools/build_dfm9_source_dependency_appendix.py`](tools/build_dfm9_source_dependency_appendix.py) | Internal | Deterministically renders the declarative source DAG, copyright register, and manual-decision register as the linked self-contained LaTeX appendix; rejects undefined or unreferenced manual decisions. |
| [`tools/build_phase_source_exposure.py`](tools/build_phase_source_exposure.py) | Internal | Reconstructs exact historical source/task exposure from sampled index offsets. |
| [`tools/build_synthetic_pipeline_register.py`](tools/build_synthetic_pipeline_register.py) | Internal | Rebuilds the concise synthetic pipeline evidence register. |
| [`tools/build_evaluation_artifact_manifest.py`](tools/build_evaluation_artifact_manifest.py) | Internal | Freezes retained release-evaluation evidence with SHA-256. |
| [`tools/validate_dossier.py`](tools/validate_dossier.py) | Internal | Validates action states, source totals, synthetic evidence paths, and evaluation hashes. |
| [`tools/fetch_hf_dataset_metadata.py`](tools/fetch_hf_dataset_metadata.py) | Internal | Captures current HF revisions, dates, gating, and declared licences; does not replace acquisition evidence. |
| [`tools/build_dfm9_copyright_review.py`](tools/build_dfm9_copyright_review.py) | Internal | Rebuilds and token-reconciles the DFM9 copyright/TDM register and report. |
| [`tools/audit_sapient_instruction_families.py`](tools/audit_sapient_instruction_families.py) | Internal | Rebuilds the exact Sapient FLAN/Tasksource/Platypus file inventory and current Tasksource metadata snapshot. |
| [`tools/manage_dfm9_source_dag.py`](tools/manage_dfm9_source_dag.py) | Internal | Initializes, validates, recursively resolves, updates, and renders the source-rights DAG. |
| [`tools/audit_tulu_v2_sciriff_if_sft.py`](tools/audit_tulu_v2_sciriff_if_sft.py) | Internal | Rebuilds exact component and ID-lineage counts for Tulu v2, SciRIFF Train Mix, and IF-SFT. |
| [`tools/audit_sharegpt_boundary.py`](tools/audit_sharegpt_boundary.py) | Internal | Rebuilds aggregate ShareGPT lineage, structure, and privacy/security risk indicators without emitting matched content. |
| [`tools/analyze_apertus_boundary_rows.py`](tools/analyze_apertus_boundary_rows.py) | Internal | Reproduces LongAlign content grouping and EuroBlocks source-label counts. |
| [`tools/build_dfm9_rights_basis_algebra.py`](tools/build_dfm9_rights_basis_algebra.py) | Internal | Rebuilds the purpose-specific rights-basis projection and algebra report. |
| [`../scripts/assemble_dfm9_memorisation_sources.py`](../scripts/assemble_dfm9_memorisation_sources.py) | Internal | Builds the symlinked A-D memorisation source-material bundle, manifest, and explicit source gaps. |
| [`templates/provider-and-data-attestation.md`](templates/provider-and-data-attestation.md) | Confidential | Collects cross-partner facts that source code cannot establish. |
| [`templates/dataset-review.md`](templates/dataset-review.md) | Confidential | Per-revision rights, privacy, provenance, and approval review. |

## Current Classification

- Engineering compute estimate: **`1.19e22` FLOPs upper bound**, pending
  independent verification and approval of the methodology.
- Commission indicative GPAI criterion: `>1e23` FLOPs plus a qualifying
  generative modality; below-threshold models may still qualify based on
  significant generality.
- Systemic-risk compute presumption: `>1e25` FLOPs.
- Mimir is **not presumed systemic-risk** on current evidence.
- Ordinary GPAI scope remains **unresolved** because broad demonstrated
  capability must be considered alongside compute and the possible
  sole-scientific-R&D exclusion.
- The non-commercial MIMIR License is **not** treated as a free/open-source
  licence for the Article 53(2) exemption.

## Source Hierarchy

1. EU AI Act and Commission instruments.
2. Signed institutional records, contracts, approvals, and infrastructure
   measurements.
3. Immutable training artifacts and logs.
4. Published Mimir model card and technical report.
5. Repository wiki and engineering estimates.

The report's DFM8 table is not assumed to be the complete historical training
content until the DFM6 -> DFM7 -> DFM8 phase register has been reconciled.

## Review Gate

Before publication or submission:

1. Resolve all P0 actions.
2. Have the provider determination and research exclusion reviewed by EU AI
   Act counsel.
3. Have the copyright policy and source register reviewed by copyright counsel.
4. Have the data-protection assessment reviewed by the responsible DPO.
5. Obtain sign-off from each legal provider entity identified in the scope memo.
6. Freeze evidence hashes and document versions for the released model revision.

Validate the machine-readable dossier with:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python legal/tools/validate_dossier.py
```

## Engineering Closure State

As of 2026-08-15, every repository-resolvable action has either been completed
or reduced to a specific human decision/attestation. The action register uses
three states:

- `resolved_engineering`: reproducible technical evidence is attached;
- `resolved_human`: an accountable person supplied or approved the recorded
  fact, with owner and date;
- `human_required`: institutional authority, counsel/DPO judgment, partner
  attestation, external telemetry/contracts, public contact, or risk acceptance
  is required.

There are no generic `open` or `in_progress` rows. This does not mean the
dossier is legally complete; it means the remaining blockers cannot be closed
by further unauthorised repository inference.

## Authoritative References

- [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- [Commission GPAI scope guidance](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers)
- [Mandatory public training-content template](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models)
- [GPAI Code of Practice](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai)
- [Mimir technical report](https://arxiv.org/abs/2608.13517)
- [Mimir model repository](https://huggingface.co/danish-foundation-models/DFM-Mimir)
