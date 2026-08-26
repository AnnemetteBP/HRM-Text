---
type: Runbook
title: DFM9 Source-Rights LaTeX Appendix
description: Deterministic rendering of the DFM9 rights, GDPR, memorisation, and declarative dependency audit as a publication appendix.
tags: [dfm9, copyright, gdpr, ai-act, open-source, memorisation, provenance, latex, datasets]
status: stable
last_updated: 2026-08-26
confidence: high
---
# DFM9 Source-Rights LaTeX Appendix

`legal/tools/build_dfm9_source_dependency_appendix.py` joins the 161-row
top-level copyright register to the authoritative 424-node, 556-edge source
DAG and writes the self-contained document
`legal/reports/dfm9-source-rights-dependency-appendix.tex`.

The appendix now opens with the audit framework used to reach the source-level
decisions. Copyright/database-rights and GDPR are independent gates. The
copyright path prefers direct licences, public-domain status, assigned rights,
permissions, and agreements before a purpose-limited DSM Article 3 research
TDM basis or a source-specific Article 4 basis. The GDPR path follows EDPB
Opinion 28/2024 case-by-case, with the 2026 scientific-research,
anonymisation, and generative-AI web-scraping guidelines treated as
consultation drafts and conservative operational guidance rather than final
law. The text also explains why memorisation is relevant to both output
copyright risk and model-anonymity/extractability, while a negative finite
probe is not treated as proof of clearance or anonymity.

A separate memorisation section records the two audits reported in Appendix C
of [Mimir v1](https://arxiv.org/html/2608.13517): the 3,000-prompt generic and
prefix audit over 140,990,504 documents, and the exact 64+64-token audit over
136,612,444 model-input evaluations. It records the category-level rates,
content adjudication, 62 potentially risky outputs (about 0.000045% of all
second-audit evaluations), absence of high-priority copyright findings, and
the limits of the tested threat model. These findings support a low observed
copyright-related memorisation risk; they do not independently establish GDPR
anonymity or eliminate adaptive-extraction risk.

## AI Act Release Position

**Decision added 2026-08-26:** DFM9 does not rely principally on the AI Act
Article 2(6) sole-scientific-R&D exclusion. Broad public use, modification,
redistribution, and downstream integration are intended, while Article 2(8)
only addresses work before release. The intended release route is therefore a
qualifying free/open-source model release. The live
[DFM-Mimir repository](https://huggingface.co/danish-foundation-models/DFM-Mimir)
confirms Apache-2.0, public weights and architecture/configuration, a chat
template, and usage instructions. This supersedes the older scope-dossier fact
pattern that identified MIMIR License v1.0 as the release licence. That
non-commercial/research-only licence would not qualify for Article 53(2), but
it is not the licence shown by the actual DFM-Mimir release.

For a non-systemic GPAI model, qualifying open source removes the Article
53(1)(a)-(b) authority-facing and downstream-provider documentation duties. It
does not remove the copyright-compliance policy or public training-content
summary duties in Article 53(1)(c)-(d), and it does not relicense training data
or exempt downstream systems. The project keeps the fuller dossier
voluntarily.

The documented recurrence-aware training upper bound is `1.19e22` FLOPs. This
is 11.9% of the Commission's non-binding `>1e23` indicative GPAI criterion and
0.119% of the AI Act's `>1e25` systemic-risk compute presumption. These values
support the scope conclusion but are not absolute safe harbours: the statutory
tests retain capability/designation routes, and cumulative compute must be
updated if the same model lifecycle continues.

The first `longtable` has one row per effective DFM9 dataset. It records the
dataset ID and URL, declared licence, current scientific-research basis,
non-research/commercial basis, local and computed status, lineage completeness,
tokens per epoch, applicable manual decisions, and typed direct dependencies.
The second table defines each of the 286 nodes actually referenced as a
dependency, including recursive dependency references, terms/basis, evidence,
status, and applicable manual decisions. The third table states all 22 manual
decisions with their scope, rationale, residual issue, and future
memorisation/propensity-test target.

Stable `Sxxx` and `Dxxx` identifiers are assigned by sorted canonical node ID.
All dependency references are internal LaTeX hyperlinks to concrete `Dxxx`
rows. Manual decisions are linked to concrete `MAN-xxx` rows and include both
node-local and transitively inherited decisions. The effective-source exposure
mapping declared in the manual-decision report is also applied. Informational
edges not used for clearance propagation carry a dagger. The document header
embeds SHA-256 hashes of the authoritative node file, edge file, top-level
copyright register, and manual-decision register.

Regenerate after any source-register or DAG change:

```bash
cd /work/dfm/HRM-Text
python legal/tools/manage_dfm9_source_dag.py build
python legal/tools/build_dfm9_source_dependency_appendix.py
```

Verified on 2026-08-22: deterministic regeneration produced the same output
hash; all 161 source IDs, 286 dependency IDs, and 22 manual-decision IDs were
unique; all dependency and manual-decision rows were referenced; no references
were dangling; all three `longtable` environments were balanced; and the
generated source was ASCII-only. The generator rejects undefined and
unreferenced manual decisions.

**Superseded 2026-08-22:** the initial verification found no local TeX
compiler. After installing Ubuntu's `texlive-latex-extra` package, the
appendix was compiled twice with:

```bash
cd /work/dfm/HRM-Text/legal/reports
pdflatex -interaction=nonstopmode -halt-on-error \
  dfm9-source-rights-dependency-appendix.tex
pdflatex -interaction=nonstopmode -halt-on-error \
  dfm9-source-rights-dependency-appendix.tex
```

The resulting appendix had 54 pages before the 2026-08-26 legal-framework and
memorisation sections were added; the current
`legal/reports/dfm9-source-rights-dependency-appendix.pdf` has 56 pages.
Long identifiers, URLs, and evidence paths use break-aware rendering and the
tables reserve inter-column padding explicitly. The second-pass log contained
zero overfull boxes, underfull boxes, unresolved references, and rerun
warnings.
