# DFM9 OpenHermes 2.5 Component Audit

Status: evidence-based engineering/legal triage, not legal advice. Audit date:
2026-08-17.

## Result

All 1,001,551 OpenHermes 2.5 rows were assigned to 19 identifiable blocks or
source labels. The source-specific decomposition materially narrows the prior
aggregate fallback:

- direct open/current-scope terms cover CamelAI, Chatbot Arena, Teknium custom,
  DataForge economics, both WizardLM blocks, Glaive, GPT-4 comparison data,
  GPTeacher, CogStack medical, MetaMath, Collective Cognition, and Unnatural
  Instructions;
- SlimOrca resolves through MIT plus the project's recorded Article 4 decision
  for uncovered FLAN expression;
- LMSYS-Chat-1M has express research use/collection consent but remains partial
  because output-model terms are per sample;
- Article 4 / Danish section 11 b was selected by the project owner on
  2026-08-17 for the uncovered parts of Airoboros, the unidentified Caseus
  custom block, the source-lost CoT Alpaca block, and residual
  unlicensed/Airoboros components inside Open-Platypus. This supersedes the
  initial Article 3 fallback while preserving the provenance gaps.

The exact table is
`legal/registers/dfm9-openhermes-component-audit.csv`.

## Reconstruction method

Fourteen non-null `source` values account for 504,808 rows. The remaining
496,743 rows were separated by contiguous offsets and verified against the
first/last row shapes of the named upstream datasets:

| Inferred block | Rows |
|---|---:|
| GPTeacher | 28,811 |
| SlimOrca | 414,062 |
| Collective Cognition | 2,719 |
| WizardLM EvolInstruct V2 | 51,093 |
| Teknium custom | 58 |

The OpenHermes card lists ShareGPT as a source, but the current 1,001,551-row
artifact has no separately identifiable ShareGPT block. It does have 1,631
`lmsys1m` rows and 3,136 `LMSys Chatbot Arena` rows. This audit does not count
the card heading as evidence of a separate row block.

## Project derivatives

The same lineage decisions apply to `schneiderkamplab/dfm8-openhermes-en` and
`schneiderkamplab/dfm8-openhermes-da`. Repairing an answer or translating a
conversation adds project-authored expression but does not remove rights in
the inherited prompt. The local final English package accepted 918,095 rows;
the Danish package accepted 967,334 rows. Their `openhermes_source` fields
remain available for source-stratified memorization testing.

## Primary evidence

- `teknium/OpenHermes-2.5` card and row statistics at revision
  `b82037821055c377bed0d495e72e46de3bc72e84`.
- `export-upload-dfm8-openhermes-repaired/build_summary.json` and final local
  accepted row metadata.
- Official upstream source cards and repositories listed in the component
  register.
