# DFM9 EuroBlocks Embedded-Seed Audit

Status: evidence-based engineering/legal triage, not legal advice. Audit date:
2026-08-17.

## Result

All 5,169 high-risk EuroBlocks rows contain a parseable complete `<document>`
block. They reduce to 2,607 unique normalized documents:

- 2,558 documents occur exactly twice;
- 47 occur once;
- two occur three times;
- 5,120 occurrences are `instruction-generation` and 49 are
  `instruction-generation-ifeval`;
- two unique documents occur in both subsets.

This shows that the nominal row count nearly doubles the source-document
exposure. Rights review and memorisation testing should use the 2,607 unique
document hashes first, then retain occurrence counts as training-weight
information.

## Marker Strata

| Marker stratum | Unique documents | Source-retaining rows | Assessment |
|---|---:|---:|---|
| No explicit marker | 2,474 | 4,904 | Unknown, not cleared: absence of a notice is not permission. URL/provenance recovery or Article 3 remains necessary. |
| Generic copyright/bibliographic marker | 101 | 201 | Manual source/edition mapping required. |
| Explicit open-licence marker | 21 | 42 | Direct-clearance candidate after licence and scope verification. |
| Explicit restrictive notice | 8 | 16 | Highest-priority removal or Article 3-only cohort. |
| Explicit public-domain marker | 3 | 6 | Direct-clearance candidate after jurisdiction/edition verification. |

No row lacked a document block. Document lengths range from 31 to 25,903
characters, with median 5,130, p95 15,005, and p99 21,175. Languages by unique
document are English 918, Portuguese 505, Italian 420, Spanish 380, French 265,
German 96, and Hindi 23.

## Content Strata

| Group | Unique documents | Source-retaining rows |
|---|---:|---:|
| Unclassified/mixed | 1,354 | 2,685 |
| Scholarly/research | 497 | 983 |
| Government/legal/procurement | 338 | 669 |
| News/blog/general web | 159 | 317 |
| Books/literary/publisher | 78 | 156 |
| Encyclopedia/reference | 76 | 152 |
| Manual/technical documentation | 43 | 86 |
| Education/course/textbook | 34 | 65 |
| Corporate/financial/ESG | 15 | 30 |
| Software/code/technical Q&A | 7 | 14 |
| Public-domain/library | 6 | 12 |

The content classifier is intentionally conservative: 1,354 documents remain
mixed/unclassified. Only 266 unique documents expose a URL, spanning 382
domains; URL absence is the main obstacle to work-level rights resolution.

## Reproducible Register

`legal/registers/dfm9-euroblocks-embedded-seed-documents.csv` contains one row
per normalized document hash with occurrence/subset counts, language, length,
content and marker strata, flags, script, and domains. It excludes document
text.

Rebuild it with:

```bash
python legal/tools/analyze_apertus_boundary_rows.py euroblocks-seeds \
  /path/to/parquet-directory \
  --output legal/registers/dfm9-euroblocks-embedded-seed-documents.csv
```

Until source URLs or licences are recovered, the current Article 3 fallback
remains appropriate for the unknown and restrictive cohorts. The 24 explicit
open/public candidates can be reviewed separately without treating the whole
5,169-row family as one rights boundary.

## Project Decision

On 2026-08-18 the project owner approved the 5,169 source-retaining rows/2,607
unique documents and the 134,819 seed-derived rows for the current
academic/non-commercial scientific-research training under Article 3 / Danish
section 11 c (`MAN-018`). The source hashes, marker strata, and unresolved
lineage remain mandatory evidence and memorisation-test cohorts. The decision
does not authorize source-record redistribution or general/commercial use.
