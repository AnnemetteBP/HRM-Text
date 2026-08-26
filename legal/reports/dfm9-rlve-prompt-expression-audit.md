# DFM9 RLVE Prompt-Expression Audit

Date: 2026-08-17

This audit compares the parameterized user-prompt templates behind the two
AllenAI verifiable-reasoning datasets with the problem sources cited in the
RLVE-Gym environment code. It addresses whether the prompts appear to retain
source expression; it is not a final copyrightability or infringement opinion.

## Coverage and result

All 250 dataset ID-prefix variants were reconciled. Of these, 246 map by
normalized exact name to an RLVE environment and four do not. The mapped
environments comprise 124 without an external `Source` comment and 122 with
one. Source pages were captured for 117 of the 122 cited variants. Four other
sources were assessed from their identified primary task or available mirrors;
Luogu `K4767` remained unavailable.

| Prompt-level bin | Variants | GPT-4.1 rows | GPT-4.1 tokens | o4-mini rows | o4-mini tokens |
|---|---:|---:|---:|---:|---:|
| Native RLVE generator; no external source comment | 124 | 152,034 | 327,679,335 | 131,099 | 53,359,534 |
| Functional abstraction or material rewrite | 61 | 66,247 | 133,616,396 | 55,226 | 22,183,588 |
| Close but constrained restatement | 45 | 45,074 | 101,308,612 | 37,563 | 12,220,201 |
| Expressive or source-specific carryover | 15 | 14,311 | 25,337,588 | 11,484 | 5,434,273 |
| Cited source unavailable | 1 | 2,233 | 4,795,039 | 1,786 | 513,407 |
| Dataset variant unmatched to RLVE | 4 | 4,921 | 13,065,826 | 4,107 | 944,660 |
| **Total** | **250** | **284,820** | **605,802,796** | **241,265** | **94,655,663** |

The narrow carryover bin is about **5.0% of GPT-4.1 rows** and **4.8% of
o4-mini rows**. The close-restatement bin is about 15.8% and 15.6%,
respectively. This is materially narrower than treating every environment with
a source comment as source-expression dependent.

## Meaning of the bins

- **Native/no comment:** the mapped MIT-licensed RLVE environment contains no
  external source comment. This is useful provenance evidence, but absence of a
  comment is not proof of independent creation.
- **Functional abstraction/rewrite:** the source story, examples, and
  presentation were stripped, or the generated prompt materially changes the
  objective/output. The comparison found algorithmic ideas, mathematics,
  constraints, or task functionality rather than material source expression.
- **Close but constrained:** the prompt closely paraphrases a short/formal
  specification. Much of the wording is dictated by mathematics, game rules,
  or output semantics, but a human legal review is still appropriate because
  originality can lie in selection or arrangement.
- **Expressive/source-specific carryover:** the prompt preserves unusually
  distinctive examples, diagrams, coined terminology, narrative machinery, or
  a bespoke rule system. Direct permission or the research-TDM fallback is the
  prudent treatment unless counsel clears the individual prompt.
- **Unavailable/unmatched:** lineage could not be compared and remains
  unresolved.

## Carryover variants

The 15 higher-risk variants are:

`abprogramsimulation`, `blockimage`, `campfireparty`,
`circulatingdecimalcounting`, `digitliscounting`, `fbi_binarytree`, `fibtrain`,
`kth_binarytree`, `multipleflippinggame`, `negativebase`, `powercycle`,
`powernest`, `splittinggame`, `stonegame`, and `taskarrangement`.

The strongest examples are `blockimage`, which retains the cube ASCII diagrams
and adjacency examples; `powernest`, which retains the recursive notation and
the same 137 example; `fbi_binarytree`, which retains the coined B/I/F and FBI
classification; and `abprogramsimulation`, which retains the distinctive A::B
token-rewrite system. The register records a finding for every variant rather
than relying on these examples alone.

### Copyright-concern severity within the carryover bin

The 15 variants are not equally concerning:

| Working severity | Variants | Reason |
|---|---|---|
| Higher | `blockimage`, `powernest`, `fbi_binarytree`, `abprogramsimulation` | Retained diagrams, worked examples, coined taxonomy/structure, or a distinctive prompt-defined rewrite system provide plausible original expression beyond the bare task function. |
| Medium | `negativebase`, `digitliscounting`, `circulatingdecimalcounting`, `fibtrain`, `campfireparty`, `kth_binarytree` | Retain a source-specific example, coined term, scenario, or ordered rule presentation, but protection may be thin because much is mathematically or functionally constrained. |
| Lower | `multipleflippinggame`, `powercycle`, `splittinggame`, `stonegame`, `taskarrangement` | The retained substance is predominantly a game, recurrence, or scheduling functionality expressed in new parameterized language; concern is selection/arrangement rather than literal prose. |

This is a triage judgment, not a legal conclusion. EU copyright requires an
original expression reflecting free and creative choices; ideas, procedures,
methods of operation, and mathematical concepts are not protected as such.
Even the lower group should remain under the conservative fallback until a
qualified reviewer accepts that the rewritten prompt contains no protectable
source selection or arrangement.

**Manual policy override, 2026-08-17:** the project owner accepts the complete
RLVE prompt family, including all close, carryover, unavailable, and unmatched
bins, for the current academic/research model-training scope and for
considering downstream datasets or mixtures that inherit these prompts to be
acceptable. This is a risk-acceptance and inclusion decision, not a finding
that the source statements are unprotected or openly licensed. The prompt-level
findings above remain visible, and Article 3 remains the fallback where
protected expression is retained and no direct permission applies. Reassess
before source-corpus redistribution, non-research training, or materially
broader deployment.

## Source-comment defects found

Source comments are not reliable enough to serve as the sole dependency map:

- `stoneintervalsgame` defines an adjacent-empty-pile collection game, while
  cited Luogu P3235 defines balanced heap splitting.
- `gcdone_counting` asks for coprime pairs, while cited P2257 asks for
  prime-GCD pairs.
- `maxpermutation` asks for a largest integer concatenation, while cited P1018
  partitions one digit string to maximize a product.
- `sumgcdwithindividual` asks for `sum_i gcd(i,N)`, while cited P4449 asks for a
  two-dimensional sum of `gcd(i,j)^K`.

Those variants are binned from the actual prompt comparison, not from the
comment.

## Rights implications

RLVE's MIT licence covers its code and authored generator layer; it does not by
itself grant rights in third-party source statements. Luogu's current user
agreement says site text belongs to Luogu or other rightsholders and limits
unconsented use to private/non-commercial use. Its user-content grant runs to
Luogu, not generally to downstream users. No broad downstream licence was
identified for the cited Codeforces, HDU, SPOJ, or X statements. The Wikipedia
3-partition source is CC-BY-SA, subject to attribution and licence conditions.

For EU copyright triage, functionality, algorithms, mathematical ideas, and
principles are not protected as such, while sufficiently original expression
and original selection/arrangement can be. Accordingly:

1. Do not apply Article 3 automatically to the 124 native/no-comment variants
   or the 61 functional-rewrite variants based only on an RLVE source family.
2. Keep the 15 carryover variants under direct-permission-or-Article-3 review.
3. Keep the 45 close/constrained variants in a prompt-specific human-review
   queue; a conservative corpus policy may treat them like the carryover bin
   until cleared.
4. Keep `axis_kcenter` and the four unmatched variants unresolved.

## Method and limitations

The review extracted all RLVE `prompt_template` values, mapped local row IDs to
environment variants, counted raw rows/tokens from both parquet releases, and
compared each cited template against the available source description. Shared
normalized token runs and four-gram coverage were used only to prioritize the
manual comparison. The 3% four-gram threshold marks the close-restatement
triage bin; explicit manual overrides identify the carryover and known
mismatch cases.

Many Luogu English pages currently identify their English text as a machine
translation. Those pages are comparison proxies for the underlying problem,
not proof of the exact historical text seen by RLVE's authors. The audit also
does not decide whether any individual statement crosses the applicable
originality threshold, whether a particular competition organizer owns it, or
whether research TDM conditions are met.

The full 250-row evidence register is
`legal/registers/dfm9-rlve-prompt-expression-audit.csv`. It includes source URL,
source domain, comparison metrics, per-release row/token exposure, bin, review
status, and a prompt-level finding.
