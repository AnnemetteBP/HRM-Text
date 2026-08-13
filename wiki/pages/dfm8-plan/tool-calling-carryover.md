---
type: Plan Record
title: Tool-Calling Carryover
description: 'Part of DFM8 Plan: Tool-Calling Carryover.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# Tool-Calling Carryover

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Carry over the DFM7 native tool-use rebuild:

- Keep corrected `dolci_native_tool_use`.
- Keep `glaive_native_tool_use`, `toolace_native_tool_use`, and
  `xlam_native_tool_use`.
- Keep malformed original DOLCI tool-use rows capped to zero unless they have
  been converted.
- Keep `when2call` as auxiliary no-call/when-to-call data only unless converted
  to top-level `tools` plus assistant `tool_calls`.

DFM8 should add an explicit BFCL-shaped native tool-call SFT bucket with:

- exact function selection,
- exact argument formation,
- no-tool cases,
- multi-tool cases,
- and a failure-bucket smoke script for `no tool call`, `malformed`,
  `wrong function`, `wrong arguments`, and `correct`.

Refinement, 2026-07-09. Confidence: medium from DFM6-to-DFM7 eval trend and
epoch_5 smoke generations.

The DFM6-to-DFM7 switch improved tool calling temporarily but did not stabilize
it. The final epoch_5 smoke test shows partial native syntax learning:

- With a `get_weather` tool, the model emitted `call:get_weather{...}`, but
  repeated/malformed the call instead of emitting one clean call.
- With a `search_web` tool available for a greeting that needed no tool, the
  model avoided the tool but incorrectly refused the simple greeting because it
  over-focused on tool availability.

DFM8 tool-call fixes should therefore go beyond adding more rows:

1. Audit every tool-call source after rendering through the Gemma4 template.
   Check for exactly one assistant target per example, valid top-level `tools`,
   valid assistant `tool_calls`, no XML leftovers, no Python-call string
   targets, and no repeated calls unless the row genuinely requires multiple
   calls.
2. Build explicit no-tool examples where tools are present but the correct
   answer is ordinary text. These should be sampled strongly enough to prevent
   "tool availability means I must call or refuse" behavior.
3. Add malformed-output prevention rows: one clean function call, exact JSON-ish
   arguments, stop after the call, and no repeated call loops.
4. Add held-out smoke/eval buckets for `must_call`, `must_not_call`,
   `multi_call`, `wrong_tool_available`, and `tool_response_followup`.
5. Inspect whether Nemotron Agentic, Glaive, ToolACE, XLAM, and corrected DOLCI
   all use the same canonical final assistant representation after conversion.
   If not, normalize or split/cap the inconsistent buckets.
