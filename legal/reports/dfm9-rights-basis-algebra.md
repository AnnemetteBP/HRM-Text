# DFM9 Rights-Basis Algebra

Status: proposed engineering/legal classification; not legal advice or counsel approval.

## Exclusive headline projection

This projection is for the current academic/non-commercial scientific-research training use. Article 3 means reliance is required or retained as a fallback; it does not mean the statutory conditions have received final legal approval.

| Headline basis | Sources | Tokens/epoch | Share |
|---|---:|---:|---:|
| `article3_reliance_required` | 4 | 25,608,805,741.2 | 32.04% |
| `article4_backed_mixed` | 6 | 8,907,418,817.0 | 11.14% |
| `direct_open_or_public` | 55 | 34,941,533,749.8 | 43.71% |
| `project_controlled_open_seed` | 9 | 2,146,269,714.0 | 2.68% |
| `express_publisher_permission` | 3 | 1,805,832,029.0 | 2.26% |
| `participant_publication_permission` | 3 | 1,577,333,282.0 | 1.97% |
| `agreement_backed_direct` | 7 | 2,536,915,030.8 | 3.17% |
| `noncommercial_licensed_direct` | 11 | 761,749,536.0 | 0.95% |
| `manual_low_risk_acceptance` | 63 | 1,652,845,178.0 | 2.07% |
| `generator_terms_review` | 0 | 0.0 | 0.00% |

## Non-exclusive factual facets

These overlap and therefore do not sum to 161 sources.

| Facet | Sources | Tokens/epoch | Share |
|---|---:|---:|---:|
| Article 3 reliance (required or fallback) | 4 | 25,608,805,741.2 | 32.04% |
| Article 4 affirmatively cleared | 0 | 0.0 | 0.00% |
| Article 4 conditional, not cleared | 15 | 36,132,755,771.2 | 45.20% |
| Agreement present | 7 | 2,536,915,030.8 | 3.17% |
| Open-licence or public-domain basis present | 79 | 48,113,641,686.8 | 60.19% |
| CC0 declared at top level | 3 | 493,409,033.4 | 0.62% |
| NonCommercial licence | 11 | 761,749,536.0 | 0.95% |
| Express publisher training permission | 3 | 1,805,832,029.0 | 2.26% |
| Participant publication permission accepted for current research | 3 | 1,577,333,282.0 | 1.97% |

## Proposed algebra

Represent each canonical DAG node as `(basis_atoms, coverage, conditions, obligations, review_state)` rather than one label.

- `basis_atoms`: `public_domain`, `open_licence`, `noncommercial_licence`, `agreement`, `express_permission`, `project_owned`, `article3`, `article4`.
- `coverage`: `full`, `partial`, or `unknown` for the node's protected expression.
- `conditions`: intended-purpose constraints such as scientific research, lawful access, NonCommercial use, and no Article 4 reservation.
- `obligations`: attribution, ShareAlike, notices, security, retention, and contract controls; combine by set union.
- `review_state`: `cleared`, `conditional`, `unresolved`, or `generator_terms_review`.

For every required DAG edge, combine facets by union and determine a purpose-specific headline using this conservative order:

```text
unresolved
  > article3_dependent (current scientific-research projection)
  > article4_dependent (general-TDM projection only, if opt-out conditions pass)
  > generator_terms_review
  > restricted_direct (for example CC-BY-NC)
  > direct
```

Examples:

- `open_licence + article3` -> headline `article3_dependent`, while retaining both atoms and the directly covered fraction.
- `open_licence + article4` -> headline `article4_backed_mixed`, while retaining the directly covered fraction and the Article 4 conditions for uncovered expression.
- `agreement + article3` -> headline `article3_dependent`; the agreement remains recorded for covered components.
- `open_licence + public_domain` -> `direct_open_or_public`, not `permissively_licensed`, because public-domain material is not licensed.
- `open_licence + agreement` -> `direct_mixed`; all licence and agreement obligations remain.
- `anything + unresolved` -> `unresolved` until the required node resolves.
- Article 3 and Article 4 are alternative purpose-specific statutory routes, not cumulative permissions. Do not collapse them into one ordering independent of intended use.

## Current limitation

The source-level register combines open licence and public-domain status. Consequently, `declared_cc0` is only a lower bound on public-domain/CC0 sources. Exact separation requires basis atoms on the canonical DAG leaves.
