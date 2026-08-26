---
type: Runbook
title: DFM9 Source-Rights LaTeX Appendix
description: Deterministic rendering of the DFM9 copyright register and declarative dependency DAG as linked publication tables.
tags: [dfm9, copyright, provenance, latex, datasets]
status: stable
last_updated: 2026-08-22
confidence: high
---
# DFM9 Source-Rights LaTeX Appendix

`legal/tools/build_dfm9_source_dependency_appendix.py` joins the 161-row
top-level copyright register to the authoritative 424-node, 556-edge source
DAG and writes the self-contained document
`legal/reports/dfm9-source-rights-dependency-appendix.tex`.

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

The resulting
`legal/reports/dfm9-source-rights-dependency-appendix.pdf` has 54 pages.
Long identifiers, URLs, and evidence paths use break-aware rendering and the
tables reserve inter-column padding explicitly. The second-pass log contained
zero overfull boxes, underfull boxes, unresolved references, and rerun
warnings.
