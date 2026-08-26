# DFM9 DOLCI Tool Use Component Audit

Status: engineering/legal evidence triage, not legal advice. Audit date:
2026-08-17. The authoritative graph decisions are in
`legal/specs/dfm9-source-dag/`.

## Scope and result

The corrected `dolci_native_tool_use` conversion contributes approximately
1.62B sampled tokens per DFM9 epoch. Its 227,579 non-SA source rows decompose
exactly into five internal labels. The OLMo 3 paper identifies the 200,000-row
label as SimFC, the three `S2` labels as the 22,576-row Science QA set, and the
5,003-row `DRv4` label as Web Search QA.

**Superseded status, 2026-08-17:** before project-owner review, all five
components were `partial` through four specific residual source layers. The
Ai2-generated trajectory layers were already cleared for current
academic/research use under the DOLCI ODC-By research release. The residual
issues concern retained API schemas or third-party source text, not the
generated responses as such.

**Manual policy override, 2026-08-17:** Professor Peter Schneider-Kamp, as
project owner, accepts the four documented residual layers as low risk for
current academic/non-commercial scientific-research model training and
downstream dataset/mixture consideration. No material reason to invoke Article
3 was identified for these residual layers. This clears the five Tool Use
components and the Tool Use effective dataset in the policy DAG, but it is not
a finding that every residual item is openly licensed or unprotected. Article
4 may provide an alternative TDM basis only for items for which lawful access
and the absence of an effective rights reservation are evidenced; the current
audit does not affirmatively establish those conditions for every item. The
source findings, attribution and source-specific obligations, and provenance
gaps remain recorded. Reassess before source-corpus redistribution,
non-research training, or materially broader deployment.

## SimFC / BFCL-labelled component

The name `bfclv3-decontaminated` describes benchmark decontamination; the paper
identifies the data itself as SimFC, generated with GPT-4o, GPT-4.1, and GPT-5.
The API pool came from existing tool datasets including xLAM and ToolACE plus
public MCP servers.

Local canonical/name/description comparison found:

| Observation | Rows |
|---|---:|
| At least one xLAM schema match | 93,593 |
| At least one ToolACE schema match | 45,577 |
| Both xLAM and ToolACE matches | 31,970 |
| No xLAM or ToolACE schema match | 92,800 |

The ToolACE count is a lower bound because 423 of 11,300 local ToolACE source
rows did not expose the card's common parseable system-schema form. The 92,800
unmatched rows are an upper bound on public-MCP provenance because Ai2 may have
adapted source schemas. xLAM is CC-BY-4.0 and ToolACE is Apache-2.0. The
unmatched/adapted pool remains unresolved until a source/API manifest or a
current-research Article 3 decision is recorded.

## Science QA components

Ai2 generated citation-graph and content-grounded questions and collected real
ASTA/Semantic Scholar tool interactions. The Semantic Scholar API agreement
expressly permits internal training and evaluation of ML models for legitimate
non-commercial research or education, but also preserves underlying
third-party content terms.

| Label | Rows | Rows with abstract fields | Environment characters |
|---|---:|---:|---:|
| M3 | 8,074 | 1,580 | 131,226,427 |
| M4v2 | 9,085 | 8,838 | 761,334,423 |
| M5v2 | 5,417 | 5,304 | 337,707,708 |

At row level, M4v2 and M5v2 overwhelmingly retain abstracts. Recorded paper
licences include CC-BY, CC-BY-SA, CC0/public domain, CC-BY-NC/ND variants,
publisher-specific open-access terms, and unspecified/other-open-access
markers; many M3 rows carry metadata without a licence field. Therefore the
generated query/trajectory contribution is direct, while retained scholarly
expression requires per-paper terms or the Article 3 research-TDM fallback.

## DeepResearch DRv4

All 5,003 user prompts were traced by normalized exact comparison:

| Prompt source | Rows | Working basis |
|---|---:|---|
| SearchArena | 2,572 | Consented prompts; CC-BY-4.0 |
| OpenSciLM queries | 1,685 | CC-BY-4.0 |
| TaskCraft | 692 | MIT |
| WebWalkerQA silver | 49 | Current Apache-2.0 metadata; earlier card recorded CC-BY-NC-4.0, both compatible with current academic/non-commercial use |
| Residual OpenScholar-labelled prompts | 5 | Four unique prompts; source release not identified |

The paper states that fetched webpages were summarized by GPT-5 and only the
summaries were retained. Serper search-result snippets remain verbatim in
environment messages, however, so source-specific expression still requires
direct terms or Article 3. The generated trajectories and summaries are Ai2's
released contribution.

## Evidence

- Local DOLCI parquets and exact `dataset_source` counts.
- OLMo 3 paper source, section 5 and the tool-use appendix, arXiv 2512.13961.
- DOLCI Tool Use card and ODC-By research/education notice.
- Salesforce xLAM and Team-ACE ToolACE cards.
- Semantic Scholar API License Agreement.
- DR Tulu SFT rows compared with TaskCraft, WebWalkerQA, OpenSciLM, and the
  named SearchArena source labels.

The external cache used for exact comparisons is under
`/work/dfm/.cache/legal-audit/`; it is evidence cache, not part of the legal
dossier or training pipeline.
