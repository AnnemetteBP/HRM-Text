# DFM9 Mixture-of-Thoughts Copyright-Risk Assessment

Status: evidence-based engineering/legal triage, not legal advice. Audit date:
2026-08-17.

## Finding

Mixture-of-Thoughts has **medium-high source-expression risk for raw data use**
and **lower, but non-zero, model-output risk**. On 2026-08-17 the project owner
accepted the residual risk for current use based on captured immediate package
and per-sample terms plus this prompt-level assessment; no material reason to
invoke Article 3 was identified. This is not a finding that every embedded work
was relicensed or is freely sublicensable.

The risk comes from the construction, not from chain-of-thought as such:

1. The user prompt preserves the source math, code, or science problem.
2. Code `solutions_w_editorials` prompts also embed the complete human-written
   contest editorial. This is the highest-risk layer.
3. DeepSeek-R1 generates the reasoning and code. That expression is usually
   new, but it can restate a problem or closely follow an editorial or official
   solution.
4. Source-package terms are useful evidence but may not establish that the
   package curator owned every embedded contest, forum, textbook, or benchmark
   question.

## Domain assessment

| Domain | Rows | Main exposure | Risk |
|---|---:|---|---|
| Math | 93,733 | NuminaMath problem wording, including 8,345 AoPS forum prompts and competition questions | Medium-high; accepted residual risk, with AoPS and distinctive contest prose highest |
| Code | about 83,100 | Codeforces/ICPC/IOI statements, notes, examples, and in some configs full editorials | High for editorial-conditioned prompts; accepted residual risk |
| Science | 172,514 | Scientific and educational questions selected from NVIDIA's science split | Medium-high where textbook/benchmark expression is retained; accepted residual risk |
| Generated traces | about 349,000 | DeepSeek-R1 reasoning/code | Low-medium; accepted subject to overlap testing |

The detailed source table is
`legal/registers/dfm9-mot-expression-risk.csv`.

## Specific inconsistencies and controls

- `open-r1/codeforces-cots` currently exposes `cc-by-4.0` in Hub metadata but
  states ODC-By in its README. Preserve both as an evidence conflict; neither
  alone proves rights in organizer-authored statements/editorials.
- NVIDIA states that its prompts are public/open or synthetic and supplies
  per-sample licences, predominantly CC-BY-4.0 with WildChat and StackOverflow
  exceptions. Preserve the per-row licence field when available.
- Before raw-row redistribution or non-research use, run exact and fuzzy
  overlap tests from generated traces to editorials/official solutions and
  stratify math prompts by their `source` field.
- For model memorization/propensity testing, prioritize AoPS, AMC/AIME,
  editorial-conditioned code, and long science questions with source-specific
  wording.
