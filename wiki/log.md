# Knowledge Bundle Update Log

## 2026-08-11

* **Migration**: Upgraded the repository knowledge corpus from its lightweight LLM-wiki convention to an OKF v0.2 bundle.
* **Structure**: Added YAML concept metadata, directory indexes, standard Markdown links, lifecycle metadata, and local conformance validation.
* **Superseded Refactoring Decision**: Initially classified mature aggregates as staged split candidates; superseded later the same day by semantic heading and chronology splitting.
* **Validation**: Added regression-tested enforcement that every knowledge directory has an index covering its immediate concepts and subdirectories.
* **Refactoring**: Split nine oversized collections and four nested chronology records into focused heading- or date-bounded concepts while preserving compatibility paths and anchors.
* **Scale**: The refactored bundle contains 461 concepts and 18 indexes; no concept exceeds the enforced 50,000-byte boundary.

## 2026-05-20

* **Initialization**: Created the original Markdown knowledge corpus and agent maintenance rules.
