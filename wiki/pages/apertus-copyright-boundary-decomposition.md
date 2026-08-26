---
type: Reference
title: Apertus Copyright Boundary Decomposition
description: Component-level SmolTalk, OpenHermes, Mixture-of-Thoughts, LongAlign, and EuroBlocks rights findings for DFM9.
tags: [dfm9, copyright, tdm, apertus, provenance]
status: stable
last_updated: 2026-08-18
confidence: high
sources:
  - id: smoltalk-card
    resource: https://huggingface.co/datasets/HuggingFaceTB/smoltalk
    title: SmolTalk dataset card
    author: org:HuggingFaceTB
  - id: smoltalk2-card
    resource: https://huggingface.co/datasets/HuggingFaceTB/smoltalk2
    title: SmolTalk2 dataset card
    author: org:HuggingFaceTB
  - id: openhermes-card
    resource: https://huggingface.co/datasets/teknium/OpenHermes-2.5
    title: OpenHermes 2.5 dataset card
    author: person:Teknium
  - id: mot-card
    resource: https://huggingface.co/datasets/open-r1/Mixture-of-Thoughts
    title: Mixture-of-Thoughts dataset card
    author: org:open-r1
  - id: longalign-card
    resource: https://huggingface.co/datasets/zai-org/LongAlign-10k
    title: LongAlign 10K dataset card
    author: org:zai-org
  - id: euroblocks-card
    resource: https://huggingface.co/datasets/utter-project/EuroBlocks-SFT-Synthetic-1124
    title: EuroBlocks SFT Synthetic dataset card
    author: org:utter-project
---
# Apertus Copyright Boundary Decomposition

The 2026-08-17 follow-up decomposed the five former aggregate Article 3
boundaries inside the Apertus/DFM Dyna branch. This remains legal/engineering
triage rather than legal advice.

## Results

| Boundary | Decomposition | Current conclusion |
|---|---|---|
| SmolTalk | 13 original train subsets and 25 SmolTalk2 SFT recipe rows | Eleven SmolTalk imports/new subsets have direct/current-scope terms. OpenHermes follows its Article 4 decision and MoT its residual-risk acceptance; only LongAlign descendants retain Article 3. |
| OpenHermes 2.5 | All 1,001,551 rows mapped to 19 source blocks | Direct/current-scope terms cover most rows. Article 4 was selected for uncovered Airoboros summaries, Caseus, source-lost CoT Alpaca, and residual Open-Platypus components. |
| Mixture-of-Thoughts | 93,733 math, about 83,100 code, and 172,514 science records | Raw-row risk is medium-high. The project owner accepted residual risk without Article 3 reliance; complete human Codeforces editorials remain a priority test cohort. |
| LongAlign | Eleven content groups plus marker strata | 90.5% of 9,888 rows were grouped; 939 remain mixed. Full scanning finds 1,621 marker rows. MAN-017 approves Article 3 reliance for current research while retaining all document-level gaps and test strata. |
| EuroBlocks seeds | 17 source labels and 2,607 unique embedded documents | 5,169 rows embed full web seed documents and 134,819 are seed-derived. MAN-018 approves Article 3 reliance for current research while retaining unresolved seed provenance. |

## Durable Artifacts

- `legal/reports/dfm9-smoltalk-component-audit.md`
- `legal/reports/dfm9-openhermes-component-audit.md`
- `legal/reports/dfm9-mot-copyright-risk.md`
- `legal/reports/dfm9-longalign-euroblocks-boundary-audit.md`
- `legal/reports/dfm9-longalign-copyright-marker-audit.md`
- `legal/reports/dfm9-euroblocks-embedded-seed-audit.md`
- `legal/reports/dfm9-audit-status-2026-08-18.md`
- corresponding `legal/registers/dfm9-*-audit.csv` and `*-risk.csv` files
- `legal/tools/analyze_apertus_boundary_rows.py` for LongAlign and EuroBlocks
  reproduction
- canonical nodes/edges in `legal/specs/dfm9-source-dag/`

## Operational Implications

Current academic/non-commercial scientific-research training remains cleared
under direct terms, recorded Article 4 decisions, the MoT risk acceptance, and
narrow Article 3 fallbacks for LongAlign and EuroBlocks seed expression. Do not
represent these mixtures as blanket open-licensed collections. Before
non-research use or raw-data redistribution, prioritize document-level
LongAlign and EuroBlocks provenance. Preserve OpenHermes source strata and MoT
editorials for memorisation/propensity testing despite their non-Article-3
project decisions.

Superseding approval, 2026-08-18: MAN-017 and MAN-018 complete project-owner
review of the remaining LongAlign and EuroBlocks Article 3 leaves for the
current research purpose. Their partial provenance status remains intentional;
the approval does not convert either family into open-licensed material.
