# Mimir Evaluation and Safety Evidence Assessment

**Status:** Engineering inventory complete; risk acceptance and additional
test scope require accountable human approval  
**Assessment date:** 2026-08-15

## Frozen Capability Evaluation Evidence

The release-checkpoint scheduler evidence contains 39 task groups covering the
standard, DFM, and EuroEval suites. All registered jobs for the step-1,650,000
EMA checkpoint completed. `legal/registers/evaluation-register.csv` records
task names, shard widths, status, result locations, and the production plan.

The following code revisions were present when this dossier was assembled:

- HRM-Text repository: `d7375674c572204b661d482536a63ecc1f79772a`
- dfm-evals: `cda967edccdc197f90a058df7bda7973aa180aca`
- data_io: `fe79a2dbb1de0a3fa650b048cf38de4bfe413dbf`

The working trees contain later modifications, so these commit IDs alone are
not a complete release-evaluation source archive. The production plan, configs,
local outputs, and release artifact hashes are retained together, but an
operator/release owner must attest the exact production revisions.

## Additional Technical Evidence

- Human-readable Danish/English qualitative smoke suites test summarisation,
  rewriting, continuation, multi-turn memory, free-form writing, math, code,
  and tool-format behaviour. The release-adjacent records are under
  `logs/analysis/dfm6_dfm7_epoch5_extended_smoke` and
  `logs/analysis/dfm8_XL_step1350000_smoke`.
- Tool-calling format/proxy probes are retained under `logs/smoke/`.
- The Lex.dk prefix-extraction probe is retained under
  `logs/analysis/lexdk_prefix_extraction_step1650000` and found no exact
  64-token extraction in 1,058,010 generations.
- Source filtering explicitly excluded many named toxicity, hate, offensive,
  social-media, review, spam, and PII-adjacent source patterns. This is a data
  control, not a model-safety evaluation.

## Coverage Gaps

No release-specific, systematic benchmark record was found for:

- harmful-instruction compliance and refusal calibration;
- demographic bias/stereotype disparities;
- toxicity across Danish and English prompts;
- prompt injection and indirect prompt injection;
- privacy extraction outside Lex.dk;
- insecure code generation and cybersecurity misuse;
- tool-use abuse, data exfiltration, or unsafe side effects;
- robustness to adversarial, malformed, or distribution-shifted inputs.

The model documentation already states that the model has no specific safety
alignment. This makes the absence of these evaluations a material limitation,
not evidence of low risk.

## Human Gate

An appointed evaluation/safety owner must approve a proportionate threat model,
the Danish/English test set, success thresholds, reviewer protocol, and release
response. Executing an arbitrary benchmark list without those decisions would
not resolve the governance question. After approval, engineering can execute
and freeze the resulting plan with the existing scheduler.

Until then, public claims must distinguish capability evaluation and limited
qualitative/privacy probes from a completed safety or red-team evaluation.
