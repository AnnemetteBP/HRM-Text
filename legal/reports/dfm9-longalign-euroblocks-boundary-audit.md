# DFM9 LongAlign Grouping and EuroBlocks Seed Audit

Status: evidence-based engineering/legal triage, not legal advice. Audit date:
2026-08-17.

## LongAlign row grouping

Yes, LongAlign can be grouped usefully, but not reliably cleared by group name
alone. A deterministic content-signature classifier assigned 8,949 of 9,888
rows (90.5%) to ten broad classes and left 939 as mixed/unclassified. The
largest groups were scholarly/research (2,168), government/legal/procurement
(1,955), software/code/technical Q&A (1,479), and books/publisher material
(1,203). Superseding count, 2026-08-17: 1,572 rows have their first explicit
marker in the classifier's initial 120k-character window, while a full-document
scan finds 49 additional late-marker rows, for 1,621 total.

The books/publisher group includes complete ebooks and explicit
no-reproduction notices. The government group is not automatically public
domain: jurisdiction and document-level rules differ. The 121 rows with
public-domain/library markers are candidates for direct clearance, not a final
public-domain determination.

The grouping is in `legal/registers/dfm9-longalign-content-groups.csv` and can
be reproduced with:

```bash
python legal/tools/analyze_apertus_boundary_rows.py longalign /path/to/long.jsonl
```

Heuristic caveats: 1,540 rows had tied top category scores before deterministic
tie-breaking, and content classes do not identify authors, acquisition dates,
or licences. The grouping is suitable for stratified human review and
memorization tests, not automatic legal clearance. The detailed marker audit
is `legal/reports/dfm9-longalign-copyright-marker-audit.md`.

## EuroBlocks annealing seeds

The 340,286-row EuroBlocks artifact has 17 source labels. Seed exposure divides
into three practical levels:

1. **High:** 5,120 `instruction-generation` and 49
   `instruction-generation-ifeval` rows embed the complete web seed document
   in the user prompt. Llama terms govern generated output but do not replace
   rights in that document.
2. **Medium:** 134,819 multilingual Llama instruction/IFEval rows derive facts
   and tasks from filtered EuroLLM annealing documents without exposing the
   full seed. They can still be derivative or reproduce distinctive passages.
3. **Medium, separate benchmark issue:** 5,219 ARC-like and 927 MMLU-like rows
   retain or closely adapt complete multiple-choice questions. These also
   create evaluation-contamination concerns.

The remaining 194,032 rows resolve through direct Magpie, Aya, HarmfulQA,
EuroLLM, or project-authored terms and do not identify the same annealing-seed
dependency. Exact counts and bases are in
`legal/registers/dfm9-euroblocks-seed-risk.csv`.

The EuroBlocks card does not identify the underlying annealing corpus or seed
document licences. Current research therefore retains Article 3 only for the
uncovered seed expression, with the 5,169 source-retaining rows prioritized for
review. Those 5,169 rows reduce to 2,607 unique embedded documents; only 24
unique documents have explicit open-licence or public-domain markers, eight
have restrictive notices, and 2,474 have no explicit marker. For non-research
use, capture source URLs/licences or remove unresolved rows and overlap-test
the derived families. See
`legal/reports/dfm9-euroblocks-embedded-seed-audit.md`.

## Reproducibility

The audit used current official revisions:

- `zai-org/LongAlign-10k` revision
  `12f17c4baff1001f0d44c4f8feab09ee2ee8c6dc`;
- `utter-project/EuroBlocks-SFT-Synthetic-1124` revision
  `cf980461f41751104ff591ccc0f0dd04189bba57`.

EuroBlocks counts can be reproduced with:

```bash
python legal/tools/analyze_apertus_boundary_rows.py euroblocks /path/to/parquet-directory
```
