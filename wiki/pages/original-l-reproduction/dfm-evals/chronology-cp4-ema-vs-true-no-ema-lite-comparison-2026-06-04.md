---
type: Operational Record
title: CP4 EMA vs true no-EMA lite comparison (2026-06-04)
description: 'Chronological record from dfm-evals: CP4 EMA vs true no-EMA lite comparison
  (2026-06-04).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# CP4 EMA vs true no-EMA lite comparison (2026-06-04)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

CP4 EMA vs true no-EMA lite comparison, 2026-06-04. Confidence: high.

The true CP4 no-EMA lite eval finished with `DONE status_0` after the
`govreport` retry described above. Comparing it against the earlier CP4 default
EMA lite eval shows that EMA is clearly better on almost all headline metrics.
Across 19 inspected metrics, no-EMA was better on 1 (`DALA` macro-F1), EMA was
better on 15, and 3 were ties at zero (`HumanEval`, `GEC-DALA` exact match,
`Talemaader`). Representative EMA vs no-EMA values:

- Standard evals: ARC `0.7278` vs `0.6305`, BoolQ `0.8462` vs `0.7485`, DROP
  F1 `0.7825` vs `0.5908`, GSM8k `0.5333` vs `0.3636`, HellaSwag `0.5031` vs
  `0.4258`, MATH `0.4051` vs `0.2532`, MMLU `0.5607` vs `0.5069`, Winogrande
  `0.6669` vs `0.6188`.
- DFM evals: DALA macro-F1 `0.0039` vs `0.2129` favors no-EMA, Citizen
  accuracy `0.1303` vs `0.0110`, WMT chrf++ `0.2485` vs `0.1770`, MultiWiki F1
  `0.1745` vs `0.0153`, PIQA-da `0.0370` vs `0.0000`, IFEval-DA final acc
  `0.2843` vs `0.1755`, NordjyllandNews BERTScore F1 `0.8640` vs `0.8493`.
