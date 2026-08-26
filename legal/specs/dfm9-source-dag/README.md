# DFM9 Source-Rights DAG Specification

This directory is the authoritative declarative specification for the DFM9
source-rights dependency DAG. Source-specific facts do not belong in the DAG
resolver.

## Files

- `nodes.csv`: canonical effective datasets, component datasets, source works,
  agreements, and generated contributions.
- `edges.csv`: typed dependency relationships between canonical nodes.

`legal/registers/dfm9-source-dag-{nodes,edges}.csv` are generated mirrors for
the wider legal dossier. Do not edit those mirrors directly.

## Status semantics

- `local_status`: `cleared`, `unresolved`, or `inherited`.
- `dependency_completeness`: `complete`, `partial`, or `top_level_only`.
- `required_for_clearance=yes` makes the child participate in upward status
  propagation. Use `no` only for genuinely informational provenance edges.

The resolver validates that every effective source in the DFM9 copyright
register has exactly one effective-dataset node with matching token exposure.
It also rejects duplicate nodes, duplicate typed edges, dangling edges,
invalid enums, and cycles.

## Commands

```bash
python legal/tools/manage_dfm9_source_dag.py build
python legal/tools/manage_dfm9_source_dag.py set-status NODE_ID cleared \
  --basis "reviewed basis" --evidence "primary evidence"
python legal/tools/build_dfm9_source_dependency_appendix.py
```

`set-status` atomically updates `nodes.csv` and rebuilds all generated outputs.
For structural changes, edit the specification CSVs and run `build`.
`initialize` remains as a compatibility alias that materializes the
declarative specification; it does not construct source facts in Python.

The appendix builder joins this DAG to the top-level copyright-basis register
and the manual-decision register in
`legal/reports/dfm9-manual-acceptances-and-overrides.md`, then writes the
self-contained LaTeX appendix
`legal/reports/dfm9-source-rights-dependency-appendix.tex`. Its stable `Sxxx`
and `Dxxx` identifiers are deterministic for a given sorted node set. Linked
`MAN-xxx` references include direct and transitively inherited decisions; a
third table records each decision's scope, rationale, residual issue, and
future testing target. The header embeds SHA-256 hashes of all four
authoritative inputs.
