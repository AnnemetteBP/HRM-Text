---
type: Plan Record
title: Math Answer-Contract Fix
description: 'Part of DFM8 Plan: Math Answer-Contract Fix.'
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
# Math Answer-Contract Fix

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Current DFM7 state, verified 2026-07-02:

- Corrected `allenai_rlvr_gsm` and `allenai_rlvr_math` rows teach boxed answers,
  but they contribute only about 6.76M target tokens over 5 epochs.
- Large inherited math-ish sources dominate the target-token budget:
  `openmathinstruct2 + dmmath + ampsmathematica + flan` contribute about
  46.40B target tokens over 5 epochs, roughly 6,861x the boxed RLVR target
  weight.
- Source-row audit showed:
  - `openmathinstruct2__cot` often contains `\boxed{...}` but rarely ends with
    a boxed answer.
  - `openmathinstruct2__direct` and `dmmath` mostly teach bare direct answers.
  - `ampsmathematica` teaches `$...$` LaTeX answers.
  - FLAN GSM8K-style rows teach prose answers such as `The answer: 24.`

Therefore, simply training longer on the current DFM7 mix should not be
expected to reliably fix freeform math formatting.

DFM8 remediation plan:

1. Build DFM8-specific math converters instead of reusing inherited math rows
   verbatim.
2. For freeform direct math rows, convert targets to exactly
   `\boxed{answer}` whenever the answer can be parsed safely.
3. For freeform CoT rows, preserve reasoning but rewrite/append the final line
   to exactly one `\boxed{answer}` when the final answer can be extracted.
4. For sources where answer extraction is unreliable, either exclude them from
   the strict math-contract slice or keep them in a separately capped
   "math reasoning, mixed format" bucket.
5. Keep MCQ math separate. MCQ prompts should request exactly one option
   letter and should not be mixed with freeform boxed-answer rows.
6. Keep raw/prose answer formats only if deliberately sampled as auxiliary
   diversity, and cap them below the strict boxed-contract slice.

Suggested source-specific handling:

| Source | DFM8 action |
| --- | --- |
| `allenai_rlvr_gsm`, `allenai_rlvr_math` | Keep; increase weight substantially. Fix nested-LaTeX boxed detection in audits so matrix/vector answers are not miscounted. |
| `openmathinstruct2__direct` | Convert bare answers to exact boxed direct answers. |
| `openmathinstruct2__cot` | Extract final answer and enforce final line `\boxed{...}`; exclude or cap rows where extraction fails. |
| `dmmath` | Convert direct bare numeric/algebraic answers to boxed answers, or cap if too synthetic/direct-heavy. |
| `ampsmathematica` | Convert `$...$` targets to `\boxed{...}` where safe; keep `$...$` only inside boxed content. |
| FLAN GSM8K/math rows | Convert prose final-answer rows to boxed answers only when extraction is robust; otherwise cap tightly. |
| `kaenguruen` and other MCQ math | Keep as MCQ letter-answer data only. |

Sampling policy:

- The strict boxed-freeform math bucket should have enough target-token weight
  to dominate freeform math answer style. As a starting point, target at least
  low single-digit billions of boxed math target tokens per epoch, not millions.
- Mixed-format math rows should be capped below the strict boxed bucket until
  smoke tests show the model reliably ends freeform math with one boxed answer.
- Track `strict_boxed_math`, `mixed_math_reasoning`, and `math_mcq` as separate
  analytics categories.

Validation gates before sampling:

1. Run a source-row audit over every math source and report:
   `contains_boxed`, `ends_boxed`, `exact_boxed`, `bare_numeric`,
   `$...$-wrapped`, prose-final-answer, and extraction-failure rates.
2. Fail the build if strict boxed sources have less than a chosen threshold of
   exact or ends-boxed rows.
3. Sample rendered examples after Gemma4 chat-template tokenization and verify
   that the visible prompt contract and assistant target match.
4. Run smoke generations on early checkpoints for GSM-style, MATH-style, and
   MCQ math separately.

Refinement, 2026-07-09. Confidence: medium from local eval behavior and
epoch_5 smoke generations.

Tracking different math types should mean two things, not only new evals:

1. Training-data analytics: every math row should be tagged into at least
   `strict_boxed_freeform`, `mixed_format_freeform`, `gsm_style_numeric`,
   `mcq_letter`, `proof_or_explanation`, and `code_or_symbolic_math`.
   Sampling analytics should report target-token counts by these tags.
2. Diagnostic eval slices: keep the headline `MATH`, `GSM8K`, and MMLU results,
   but add small controlled eval suites that separately test:
   - GSM-style arithmetic with required bare numeric and boxed variants.
   - MATH-style freeform with required final `\boxed{...}`.
   - MCQ math with one-letter answer contract.
   - Format-only scoring: correct answer but wrong final format, no final
     answer, multiple boxed answers, and answer after token cap.

These diagnostic evals are not meant to replace the headline benchmark numbers.
They should explain why a checkpoint loses points: capability, answer contract,
reasoning-length cutoff, or extraction/scoring failure.

DFM6-DFM7 epoch_5 smoke evidence:

- The final `epoch_5` HF export solved two easy math prompts correctly in
  content, but ignored an explicit instruction to finish with exactly one
  `\boxed{...}` answer.
- This supports the hypothesis that the current mix has a format-contract
  problem. It does not by itself rule out reasoning-length limits on harder
  MATH items.

MATH regression investigation plan:

- Compare old Sapient/original and DFM5 generations against DFM7 on a shared
  fixed sample of MATH rows, storing full generations and classifying failures
  as `wrong reasoning`, `right answer wrong format`, `no boxed final`,
  `multiple boxed answers`, `truncated`, or `extractor mismatch`.
- Check prompt/template differences: original HRM condition-token evals versus
  Gemma4 chat-template evals can change whether the model starts a reasoning
  trace, a direct answer, or a final boxed line.
- Check generation limits: if DFM7 gives long unfinished traces while earlier
  models were shorter/directer, MATH can fall even when underlying reasoning is
  not worse.
- Check data mix: DFM7 inherited far more mixed-format math than strict boxed
  math, so answer-style drift is a plausible primary cause until the fixed
  sample says otherwise.
