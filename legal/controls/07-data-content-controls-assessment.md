# Mimir Data and Content Controls Assessment

**Status:** Engineering evidence complete; legal adequacy and release claims
require human approval  
**Assessment date:** 2026-08-15  
**Scope:** Data used by the released step-1,650,000 EMA checkpoint

## Controls Actually Applied

### Acquisition and source selection

- Public datasets were acquired through Hugging Face `snapshot_download`; no
  provider-operated web crawler was found in the repository.
- `config/data/source_filter.yaml` defines explicit source-level allow
  overrides and deny patterns. `scripts/build_filtered_source_tree.py` checks
  allow overrides first, then denies, and materialises only allowed files.
- The policy excluded or quarantined identified high-risk source families,
  including selected social-media, user-chat, review, toxicity, spam, NER/PII,
  uncertain textbook, search-derived, and rights-reservation cases. Narrow
  exceptions were deliberately re-admitted for named factual, dialogue, and
  reasoning sources.
- DBC and Lex.dk data were limited to named instruction-like files. Their
  contractual legal basis remains a human review item.

### Conversion, generation, and audit

- Conversion normalised training examples to the Gemma 4 chat convention and
  required an assistant target for message-form records.
- The six DFM8 targeted synthetic families generated 4,800,000 rows. The
  Gemma 4 31B audit processed 4,580,233 rows and accepted 3,809,300 rows across
  code debugging, constrained formatting, Danish summarisation/rewrite,
  bilingual multi-turn chat, native tool calling, and strict math answers.
- Repaired OpenHermes processing audited 1,001,551 English source rows. The
  final English set contains 918,095 accepted clean/repaired rows. The final
  Danish set contains 967,334 rows after translation, audit, repair,
  replacement, and retry handling.
- Eight Common Pile/Danish DynaWord transformation families retained only rows
  accepted by their saved model-judge audit records. Their per-family
  `filter_summary.json` files preserve seen, kept, dropped, and audit-file
  evidence.

### Measured format and content checks

`logs/dfm8_source_audit.json` records a bounded source audit that sampled up to
5,000 rows per file:

- 3,956,137 sampled rows;
- 3,936,137 message-form rows;
- 3,936,124 rows with an assistant target;
- 38,265 rows containing tool calls;
- 127 XML-style tool artifacts;
- 45,752 rows containing boxed-answer syntax;
- 218,788 Danish-labelled and 146,212 English-labelled rows in the explicitly
  classified subset.

The Lex.dk exhaustive prefix-extraction probe produced 1,058,010 generations
from original, unconverted source prefixes. It found no exact 64-token
extraction; the maximum longest common prefix was 55 tokens in a constrained
formula. This is source-specific memorisation evidence, not a corpus-wide
privacy or copyright guarantee.

## Historical Exposure Evidence

The released model's actual sampled-index exposure has been reconstructed, not
merely inferred from final-recipe totals:

| Phase | Consumed sampled rows | Consumed source tokens | Consumed tasks |
|---|---:|---:|---:|
| DFM6 | 596,141,430 | 188,459,096,782 | 10,519 |
| DFM7 | 413,941,524 | 133,316,601,173 | 10,641 |
| DFM8 | 340,908,524 | 110,056,867,575 | 10,710 |

The task-level and source-prefix-level mappings, sampled index slices, and
hashes of tokenised length arrays are frozen in
`legal/registers/phase-*-exposure-register.csv`. The source-token totals differ
slightly from nominal global-batch presentations because sampled rows have
variable sequence lengths and padding is not source content.

## Important Limitations

- No comprehensive illegal-content classifier was applied to every training
  token. The controls are source policy, format/quality filtering, and targeted
  audit controls; they cannot substantiate a claim that all illegal content was
  removed.
- No corpus-wide PII or special-category-personal-data scan with measured
  precision/recall was found. Public conversational and web-derived datasets
  retain material privacy risk.
- Packaged third-party datasets do not preserve URL-level robots or rights-
  reservation evidence for every underlying work. Repository evidence can
  establish no direct crawler, but not supplier compliance.
- Synthetic, translated, and transformed outputs can retain source expression
  or personal data. Model-judge acceptance is a quality/format control, not a
  legal clearance.
- The source audit is sampled by file and is not statistically weighted to the
  final training distribution.
- Dataset licences and metadata fetched in August 2026 describe current Hub
  state, not necessarily acquisition-time terms.

## Release Wording Supported by Evidence

The project may accurately say that it applied source allow/deny controls,
targeted quality and format filters, model-judge audits for selected synthetic
and transformed sources, and a Lex.dk extraction probe. It should not say that
personal information or illegal content was categorically excluded unless a
separate comprehensive audit supports that statement.

Human reviewers must decide whether these controls are legally adequate,
approve the public wording, review private-data agreements, and approve any
remaining Article 3/4, GDPR, and rights-reservation reliance.
