# DFM9 LongAlign Copyright-Marker Audit

Status: evidence-based engineering/legal triage, not legal advice. Audit date:
2026-08-17.

## Result

The previously reported `1,572` rows are exactly the rows whose first explicit
marker occurs within the first 120,000 characters used by the original content
classifier. A full-document scan finds another 49 late-marker rows, for 1,621
rows total. The earlier `1,572` statement is therefore superseded as a
full-document count but retained as a reproducible initial-window cohort.

The 1,572-row cohort stratifies as follows:

| Marker stratum | Rows | Assessment |
|---|---:|---|
| Explicit restrictive notice | 745 | Highest-priority exclusion or Article 3-only review cohort; notices include no-reproduction and permission-required language. |
| Mixed restrictive and open/public marker | 54 | Requires document-level review; may combine a public-domain source with a protected edition/introduction or conflicting notices. |
| Generic copyright/bibliographic marker | 616 | Marker proves neither permission nor prohibition; source/edition mapping remains necessary. |
| Explicit public-domain marker | 87 | Candidate for direct clearance after edition, jurisdiction, and marker verification. |
| Explicit open-licence marker | 67 | Candidate for direct clearance after licence identity, scope, and attribution/ShareAlike verification. |
| Government copyright notice | 3 | Jurisdiction-specific review required; government origin is not itself public-domain proof. |

The 49 late-marker rows comprise 24 generic, 15 restrictive, three government,
three open-licence, two public-domain, and two mixed rows. They must be included
in any full-document audit and memorisation-test cohort.

## Content Cross-Tab for the Original 1,572

| Group | Rows | Restrictive | Mixed | Generic | Public domain | Open licence | Government |
|---|---:|---:|---:|---:|---:|---:|---:|
| Books/literary/publisher | 761 | 558 | 26 | 149 | 22 | 5 | 1 |
| Scholarly/research | 252 | 59 | 6 | 141 | 14 | 31 | 1 |
| Government/legal/procurement | 242 | 54 | 6 | 159 | 8 | 14 | 1 |
| Software/code/technical Q&A | 86 | 20 | 1 | 54 | 2 | 9 | 0 |
| Corporate/financial/ESG | 77 | 28 | 2 | 41 | 2 | 4 | 0 |
| News/blog/general web | 62 | 14 | 1 | 41 | 4 | 2 | 0 |
| Public-domain/library | 44 | 0 | 10 | 0 | 34 | 0 | 0 |
| Manual/technical documentation | 19 | 8 | 2 | 9 | 0 | 0 | 0 |
| Unclassified/mixed | 16 | 1 | 0 | 14 | 0 | 1 | 0 |
| Education/course/textbook | 12 | 3 | 0 | 7 | 1 | 1 | 0 |
| Encyclopedia/reference | 1 | 0 | 0 | 1 | 0 | 0 | 0 |

The strongest concentration is books/publisher material: 558 of 761 rows have
an explicit restrictive notice. Marker-bearing prompts are also very long:
median 69,731 characters, p95 227,304, p99 272,442, maximum 332,011. That makes
this cohort a high-value exact/fuzzy prefix-extraction and long-context
memorisation test target.

## Reproducible Register

`legal/registers/dfm9-longalign-copyright-marker-rows.csv` contains one row per
marker-bearing source row. It records source ID/offset, first marker offset,
the 120k-window flag, content and marker strata, marker booleans, script,
length, and extracted domains. It deliberately excludes source passages.

Rebuild it with:

```bash
python legal/tools/analyze_apertus_boundary_rows.py longalign-markers \
  /path/to/long.jsonl \
  --output legal/registers/dfm9-longalign-copyright-marker-rows.csv
```

These heuristics prioritize review; they do not themselves establish licence,
public-domain status, an effective reservation, or infringement.

## Project Decision

On 2026-08-18 the project owner approved all eleven LongAlign content groups
for the current academic/non-commercial scientific-research training under
Article 3 / Danish section 11 c (`MAN-017`). This closes the current human
boundary review without changing the document-level evidence or licensing
classification. Raw redistribution, Article 4 reliance, and commercial use
remain outside the approval.
