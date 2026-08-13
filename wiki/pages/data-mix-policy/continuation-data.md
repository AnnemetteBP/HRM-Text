---
type: Policy Record
title: Continuation Data
description: 'Part of Data Mix Policy: Continuation Data.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# Continuation Data

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Only Danish continuation data is currently allowed:

- Include: `danish-foundation-models/danish-dynaword`
- Exclude: Common Pile. Common Pile was removed from the downloader manifest.

Recommended continuation share: capped auxiliary slice, roughly 5-10% of total tokens if used.
