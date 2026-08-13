---
type: Playbook
title: OKF Maintenance Playbook
description: Repository rules for authoring and maintaining the HRM-Text Open Knowledge Format bundle.
tags: [okf, documentation, maintenance, agents]
status: stable
last_updated: 2026-08-11
confidence: high
sources:
  - id: okf-v0-2
    resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
    title: Open Knowledge Format v0.2 specification
    author: org:GoogleCloudPlatform
---
# OKF Maintenance Playbook

The [`wiki/`](/index.md) directory is an Open Knowledge Format (OKF) v0.2
bundle. It replaces the repository's earlier lightweight LLM-wiki convention
while preserving its Markdown content and confidence annotations.[^okf-v0-2]

[^okf-v0-2]: Open Knowledge Format v0.2 specification

## Bundle Structure

- `index.md`: bundle entry point and progressive-disclosure map.
- `pages/`: policies, plans, runbooks, technical references, operational state,
  and issue registers.
- `entities/`: dataset and software catalogs.
- `sessions/`: chronological session digests.
- `sources/`: external references retained as knowledge concepts.
- `log.md`: concise bundle-level update history, newest first.

Each directory has an `index.md`. Indexes describe immediate children rather
than duplicating their content.

## Concept Frontmatter

Every Markdown file except reserved `index.md` and `log.md` files must begin
with parseable YAML frontmatter containing a non-empty `type`.

Use these fields:

```yaml
---
type: Runbook
title: Human-readable title
description: One sentence describing the concept.
tags: [operations, evaluation]
status: stable
last_updated: 2026-08-11
confidence: high
---
```

`last_updated` and `confidence` are repository extensions. Confidence values
retain their established meanings:

- `high`: verified local commands, inspected files, or direct tool output.
- `medium`: source-card metadata or reasoned integration decisions.
- `low`: estimates and unverified assumptions.

Use OKF's standard `sources`, `generated`, `verified`, `status`, and
`stale_after` fields when their semantics are actually known. Do not infer a
human verification event from a legacy confidence marker.

## Concept Boundaries

A concept should have one retrievable purpose. Prefer a new topic-specific
concept over appending unrelated material to an aggregate page. Link concepts
with standard Markdown links; use bundle-relative links such as
`[DFM9 plan](/pages/dfm9-plan.md)` when practical.

The 2026-08-11 migration split oversized aggregate documents at semantic
headings and dated update boundaries. Compatibility collection pages retain the
original paths and section headings, while focused concepts live in same-named
subdirectories. This preserves incoming paths and anchors without duplicating
the detailed content.

Concepts must remain below 50,000 bytes. Split earlier when a document contains
several independently useful topics, becomes difficult to scan, or mixes
current truth with historical operations. Preserve an established path as a
small `Knowledge Collection` when incoming links exist; do not restore detailed
content to compatibility collections.

## Durable Update Rule

In the same turn, record durable knowledge such as:

- dataset and source-policy decisions;
- commands that worked or failed in an instructive way;
- dependency and build decisions;
- architecture or checkpoint-format changes;
- filtering changes, risks, and blockers.

When new information contradicts an existing claim, retain the context, mark
the old claim `Superseded` with a date, and add the replacement. Do not silently
rewrite history.

Update the concept's `last_updated`, the relevant directory `index.md` when
discovery changes, and `wiki/log.md` for structural or substantial bundle
changes. Routine factual additions do not each require a log entry.

## Validation

Run the local conformance check after structural edits:

```bash
cd /work/dfm/HRM-Text
python scripts/validate_okf.py wiki
```

The validator checks OKF version declaration, reserved-file structure,
parseable concept frontmatter, required `type` values, lifecycle/confidence
values, local Markdown links, complete immediate-child coverage in every
directory index, and the 50,000-byte concept-size boundary.
