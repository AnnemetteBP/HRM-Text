#!/usr/bin/env python3
"""Derive conservative, purpose-specific rights-basis classes for DFM9."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "legal/registers/dfm9-copyright-basis-register.csv"
OUTPUT = ROOT / "legal/registers/dfm9-effective-rights-basis.csv"
REPORT = ROOT / "legal/reports/dfm9-rights-basis-algebra.md"


def dominant(row: dict[str, str]) -> str:
    """Headline projection for current academic/non-commercial research use."""
    if row["article3_required"] in {"yes", "fallback"}:
        return "article3_reliance_required"
    value = row["copyright_class"]
    if value == "synthetic_generator_terms_review":
        return "generator_terms_review"
    if value in {
        "agreement_or_contract",
        "mixed_direct_licences_and_agreements",
        "mixed_open_licences_and_training_release_agreements",
    }:
        return "agreement_backed_direct"
    if value == "mixed_licences_and_article4":
        return "article4_backed_mixed"
    if value in {"direct_noncommercial_licence", "mixed_open_and_noncommercial_licences"}:
        return "noncommercial_licensed_direct"
    if value == "explicit_publisher_training_permission":
        return "express_publisher_permission"
    if value == "mixed_direct_and_participant_publication_permission":
        return "participant_publication_permission"
    if value == "mixed_direct_and_manual_low_risk_acceptance":
        return "manual_low_risk_acceptance"
    if value in {"project_generated_direct", "project_generated_derivative_of_open_source"}:
        return "project_controlled_open_seed"
    if value in {"direct_open_licence_or_public_terms", "mixed_open_or_public_domain_licences"}:
        return "direct_open_or_public"
    raise ValueError(f"unmapped copyright class: {value}")


def has_agreement(row: dict[str, str]) -> bool:
    return row["copyright_class"] in {
        "agreement_or_contract",
        "mixed_direct_licences_and_agreements",
        "mixed_open_licences_and_training_release_agreements",
        "mixed_licences_agreements_and_article3_fallback",
    }


def has_open_or_public(row: dict[str, str]) -> bool:
    return row["copyright_class"] in {
        "direct_open_licence_or_public_terms",
        "mixed_open_or_public_domain_licences",
        "project_generated_derivative_of_open_source",
        "project_generated_direct",
        "mixed_open_licences_and_training_release_agreements",
        "mixed_direct_licences_and_agreements",
        "mixed_licences_agreements_and_article3_fallback",
        "mixed_open_and_noncommercial_licences",
        "mixed_licences_and_article4",
    }


def main() -> None:
    with INPUT.open(newline="") as f:
        source = list(csv.DictReader(f))

    rows = []
    for item in source:
        licence = item["captured_declared_licence"].lower()
        rows.append({
            "source_id": item["source_id"],
            "average_tokens_per_epoch": item["average_sampled_tokens_per_epoch"],
            "dominant_basis_current_research_use": dominant(item),
            "article3_reliance": "required" if item["article3_required"] == "yes" else
                                 "fallback" if item["article3_required"] == "fallback" else "no",
            "article4_status": item["article4_status"],
            "agreement_present": "yes" if has_agreement(item) else "no",
            "open_or_public_basis_present": "yes" if has_open_or_public(item) else "no",
            "declared_cc0": "yes" if "cc0" in licence else "no",
            "noncommercial_restriction": "yes" if item["copyright_class"] in {"direct_noncommercial_licence", "mixed_open_and_noncommercial_licences"} else "no",
            "express_publisher_permission": "yes" if item["copyright_class"] == "explicit_publisher_training_permission" else "no",
            "participant_publication_permission": "yes" if item["copyright_class"] == "mixed_direct_and_participant_publication_permission" else "no",
            "generator_terms_review": "yes" if item["copyright_class"] == "synthetic_generator_terms_review" else "no",
            "dependency_scope": item["lineage_scope"],
        })

    fields = list(rows[0])
    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    total = sum(float(x["average_tokens_per_epoch"]) for x in rows)
    counts = Counter(x["dominant_basis_current_research_use"] for x in rows)
    tokens: dict[str, float] = defaultdict(float)
    for row in rows:
        tokens[row["dominant_basis_current_research_use"]] += float(row["average_tokens_per_epoch"])

    facets = {
        "Article 3 reliance (required or fallback)": lambda x: x["article3_reliance"] != "no",
        "Article 4 affirmatively cleared": lambda x: x["article4_status"] == "cleared",
        "Article 4 conditional, not cleared": lambda x: x["article4_status"] == "conditional_not_cleared",
        "Agreement present": lambda x: x["agreement_present"] == "yes",
        "Open-licence or public-domain basis present": lambda x: x["open_or_public_basis_present"] == "yes",
        "CC0 declared at top level": lambda x: x["declared_cc0"] == "yes",
        "NonCommercial licence": lambda x: x["noncommercial_restriction"] == "yes",
        "Express publisher training permission": lambda x: x["express_publisher_permission"] == "yes",
        "Participant publication permission accepted for current research": lambda x: x["participant_publication_permission"] == "yes",
    }

    lines = [
        "# DFM9 Rights-Basis Algebra", "",
        "Status: proposed engineering/legal classification; not legal advice or counsel approval.", "",
        "## Exclusive headline projection", "",
        "This projection is for the current academic/non-commercial scientific-research training use. "
        "Article 3 means reliance is required or retained as a fallback; it does not mean the statutory conditions have received final legal approval.", "",
        "| Headline basis | Sources | Tokens/epoch | Share |", "|---|---:|---:|---:|",
    ]
    order = [
        "article3_reliance_required", "article4_backed_mixed", "direct_open_or_public", "project_controlled_open_seed",
        "express_publisher_permission", "participant_publication_permission", "agreement_backed_direct",
        "noncommercial_licensed_direct", "manual_low_risk_acceptance",
        "generator_terms_review",
    ]
    for key in order:
        lines.append(f"| `{key}` | {counts[key]} | {tokens[key]:,.1f} | {tokens[key] / total:.2%} |")

    lines += ["", "## Non-exclusive factual facets", "", "These overlap and therefore do not sum to 161 sources.", "",
              "| Facet | Sources | Tokens/epoch | Share |", "|---|---:|---:|---:|"]
    for label, predicate in facets.items():
        selected = [x for x in rows if predicate(x)]
        value = sum(float(x["average_tokens_per_epoch"]) for x in selected)
        lines.append(f"| {label} | {len(selected)} | {value:,.1f} | {value / total:.2%} |")

    lines += [
        "", "## Proposed algebra", "",
        "Represent each canonical DAG node as `(basis_atoms, coverage, conditions, obligations, review_state)` rather than one label.", "",
        "- `basis_atoms`: `public_domain`, `open_licence`, `noncommercial_licence`, `agreement`, `express_permission`, `project_owned`, `article3`, `article4`.",
        "- `coverage`: `full`, `partial`, or `unknown` for the node's protected expression.",
        "- `conditions`: intended-purpose constraints such as scientific research, lawful access, NonCommercial use, and no Article 4 reservation.",
        "- `obligations`: attribution, ShareAlike, notices, security, retention, and contract controls; combine by set union.",
        "- `review_state`: `cleared`, `conditional`, `unresolved`, or `generator_terms_review`.", "",
        "For every required DAG edge, combine facets by union and determine a purpose-specific headline using this conservative order:", "",
        "```text",
        "unresolved",
        "  > article3_dependent (current scientific-research projection)",
        "  > article4_dependent (general-TDM projection only, if opt-out conditions pass)",
        "  > generator_terms_review",
        "  > restricted_direct (for example CC-BY-NC)",
        "  > direct",
        "```", "",
        "Examples:", "",
        "- `open_licence + article3` -> headline `article3_dependent`, while retaining both atoms and the directly covered fraction.",
        "- `open_licence + article4` -> headline `article4_backed_mixed`, while retaining the directly covered fraction and the Article 4 conditions for uncovered expression.",
        "- `agreement + article3` -> headline `article3_dependent`; the agreement remains recorded for covered components.",
        "- `open_licence + public_domain` -> `direct_open_or_public`, not `permissively_licensed`, because public-domain material is not licensed.",
        "- `open_licence + agreement` -> `direct_mixed`; all licence and agreement obligations remain.",
        "- `anything + unresolved` -> `unresolved` until the required node resolves.",
        "- Article 3 and Article 4 are alternative purpose-specific statutory routes, not cumulative permissions. Do not collapse them into one ordering independent of intended use.", "",
        "## Current limitation", "",
        "The source-level register combines open licence and public-domain status. Consequently, `declared_cc0` is only a lower bound on public-domain/CC0 sources. Exact separation requires basis atoms on the canonical DAG leaves.", "",
    ]
    REPORT.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
