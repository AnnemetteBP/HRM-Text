---
type: Software Reference
title: OKF Collection Refactoring
description: Semantic heading and chronology splitter used to refactor oversized OKF concepts.
tags: [scripts, software, documentation, okf]
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# OKF Collection Refactoring

Part of [Script Entities](/entities/scripts.md).

`scripts/refactor_okf_collections.py` splits oversized concepts at real
top-level Markdown headings while ignoring fenced-code headings. It supports a
controlled raw-heading mode for malformed historical fences and a chronology
mode for dated update paragraphs. Original concept paths become compact
`Knowledge Collection` pages, child concepts receive OKF frontmatter, relative
file links are relocated, and directory indexes are generated.

The migration used a 50,000-byte threshold. Dry-run is the default; `--apply`
is required to write changes. Focused regression tests cover fenced headings,
malformed-fence recovery, chronology boundaries, and relative-link relocation.
