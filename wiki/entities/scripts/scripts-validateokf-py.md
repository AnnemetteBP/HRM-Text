---
type: Software Reference
title: '`scripts/validate_okf.py`'
description: 'Part of Script Entities: `scripts/validate_okf.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/validate_okf.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-08-11. Confidence: high from local conformance runs and four
focused regression tests. Validates the `wiki/` OKF v0.2 bundle, including the
root version declaration, reserved files, YAML frontmatter, required concept
types, lifecycle/confidence values, legacy wiki-link absence, local Markdown
links, per-directory indexes, and immediate-child index coverage. Run it from
the repository root with `python scripts/validate_okf.py wiki`.
