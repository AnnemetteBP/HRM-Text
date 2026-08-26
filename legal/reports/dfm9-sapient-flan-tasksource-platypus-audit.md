# DFM9 Sapient FLAN, Tasksource, and Platypus Audit

Status: engineering/legal evidence triage, not legal advice. Audit date:
2026-08-18.

## Result

The three previously unresolved Sapient branches are now reconciled to every
sampled file and resolved for the current academic/non-commercial scientific
research use.

| Branch | Files | Tokens/epoch | Working result |
|---|---:|---:|---|
| Non-factual FLAN | 3,644 | 4,327,889,931.6 | Direct terms where identified; Article 4 for uncovered expression under MAN-019 |
| Tasksource | 161 | 148,643,148.2 | 78.885M under specific repository licences; 69.759M under Article 3 under MAN-020 |
| Platypus | 8 | 64,438,800.0 | Direct component terms, including a non-commercial ScienceQA licence |
| **Total** | **3,813** | **4,540,971,879.8** | **Resolved; Article 3 remains only in the Tasksource residual** |

The complete file-to-family mapping, exact DFM9 token exposure, pinned
Tasksource mapping, current repository revision, and current licence metadata
are in
`legal/registers/dfm9-sapient-instruction-family-inventory.csv`.

## Historical Inclusion Policy

The source-filter history intended to retain math, science, commonsense,
factual QA, dialogue reasoning, NLI, logic, and selected medical/scientific
tasks while denying ReClor, SciBench, harsh-robots routes, and higher-privacy
social/chat/review/toxicity sources. DFM4 and DFM5 then added explicit
allow-overrides for benchmark-adjacent factual sources and selected dialogue
families.

The implementation checks allow-overrides first, deny patterns second, and
otherwise allows every included file. Consequently, the comments describing a
"narrow" FLAN or Tasksource allowlist are not a literal default-deny policy.
DFM9 samples 161 Tasksource files, including many files not named in the
allow-overrides. This audit follows the sampled corpus rather than the intended
short list. Copyright resolution does not supersede the separate privacy and
personal-data controls for social or user-derived rows.

## FLAN

Google describes the FLAN Collection as a compilation of FLAN 2021, P3/T0,
Super-Natural-Instructions v2, CoT, and dialogue submixtures. Its Apache-2.0
repository licence covers Google's code and transformation contribution; it
does not automatically replace source-dataset terms. DFM9 retained no dialogue
submixture under the ordinary `flan` category.

| Submixture | Files | Canonical tasks | Tokens/epoch | Rights treatment |
|---|---:|---:|---:|---|
| CoT | 36 | 18 | 101,174,105.0 | Source-specific terms plus MAN-019 Article 4 fallback |
| FLAN 2021 | 200 | 50 | 291,355,542.6 | Source-specific terms plus MAN-019 Article 4 fallback |
| NIv2 | 2,860 | 1,430 | 2,399,621,335.4 | Apache instructions/schema; instances follow original terms; MAN-019 for uncovered expression |
| T0/P3 | 548 | 137 | 1,535,738,948.6 | Apache P3/prompt layer; source terms plus MAN-019 for uncovered expression |

MAN-019 extends the already recorded MAN-013 treatment of retained FLAN-v2
expression to the equivalent Sapient materialization. It does not claim that
Google's Apache licence covers all upstream instances. Attribution and any
identified source-specific obligations remain controlling.

## Tasksource

Tasksource is a harmonization and preprocessing framework. The audited pinned
revision maps all 161 flattened Sapient files to 124 upstream repositories.
The Tasksource repository's CC-BY-4.0 licence covers its contribution, not
necessarily every source record.

The current upstream Hub metadata yields this conservative split:

| Metadata bucket | Files | Tokens/epoch | Treatment |
|---|---:|---:|---|
| Specific Apache, MIT, CC-BY, CC-BY-SA, CC0, GPL, or AFL identifier | 77 | 78,884,609.4 | Direct repository terms, with source-provenance caveat |
| Blank, `unknown`, `other`, or generic `cc` | 84 | 69,758,538.8 | Article 3 / Danish section 11 c under MAN-020 |

The residual is not a finding that all 84 source works are protected or that
none has direct permission. It is a conservative consequence of incomplete or
nonspecific repository metadata. MAN-020 is purpose-limited and does not clear
raw redistribution, nonresearch training, privacy issues, or provenance lost
inside a derived task repository.

## Platypus

Only eight files survive filtering. Open-Platypus publishes a source table
that identifies MIT for ARB and TheoremQA, Apache-2.0 for OpenBookQA, and
CC-BY-NC-SA-4.0 for ScienceQA. The current project is academic and
non-commercial, so the ScienceQA restriction is compatible with this use.

| Family | Files | Tokens/epoch | Licence |
|---|---:|---:|---|
| ARB | 5 | 3,478,980.0 | MIT |
| OpenBookQA | 1 | 4,443,600.0 | Apache-2.0 |
| ScienceQA | 1 | 55,947,160.0 | CC-BY-NC-SA-4.0 |
| TheoremQA | 1 | 569,060.0 | MIT |

ReClor and SciBench were historically excluded and are not part of this
ordinary Platypus branch. Their separately regenerated project artifacts have
their own DAG dependencies and are not changed by this finding.

## Evidence

- Exact sampled exposure: `data/show_analytics_dfm9.md`.
- Filter implementation and policy: `scripts/build_filtered_source_tree.py`
  and `config/data/source_filter.yaml`.
- Generated inventory:
  `legal/registers/dfm9-sapient-instruction-family-inventory.csv`.
- Inventory builder:
  `legal/tools/audit_sapient_instruction_families.py`.
- FLAN repository and mixture description:
  <https://github.com/google-research/FLAN/tree/main/flan/v2>.
- Super-Natural-Instructions repository and instance-licence statement:
  <https://github.com/allenai/natural-instructions>.
- P3 card and Apache-2.0 metadata:
  <https://huggingface.co/datasets/bigscience/P3>.
- Tasksource mapping revision `ef6535aebaed3f6b9c72a833e63106313fdadac0`:
  <https://github.com/sileod/tasksource>.
- Open-Platypus source licence table, revision
  `7ba474641ec326a6c595d49d486b8a5779124da7`:
  <https://huggingface.co/datasets/garage-bAInd/Open-Platypus/blob/7ba474641ec326a6c595d49d486b8a5779124da7/README.md>.
