#!/usr/bin/env python3
"""Render the declarative DFM9 source-rights DAG as a self-contained LaTeX appendix."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from manage_dfm9_source_dag import REGISTER, SPEC_EDGES, SPEC_NODES, read_graph, resolve


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "legal/reports/dfm9-source-rights-dependency-appendix.tex"
MANUAL_DECISIONS = ROOT / "legal/reports/dfm9-manual-acceptances-and-overrides.md"

MANUAL_ID_RE = re.compile(r"MAN-(\d{3})")
MANUAL_RANGE_RE = re.compile(r"MAN-(\d{3})\s+through\s+MAN-(\d{3})")
CODE_SPAN_RE = re.compile(r"\x60([^\x60]+)\x60")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_manual_decisions(path: Path) -> list[dict[str, str]]:
    """Read the five-column decision register from its authoritative Markdown report."""
    decisions: list[dict[str, str]] = []
    in_register = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line == "## Decision Register":
            in_register = True
            continue
        if in_register and raw_line.startswith("## "):
            break
        if not in_register or not raw_line.startswith("| MAN-"):
            continue
        cells = [cell.strip() for cell in raw_line.strip().strip("|").split("|")]
        if len(cells) != 5:
            raise ValueError(f"Malformed manual-decision row: {raw_line}")
        decisions.append(
            dict(
                decision_id=cells[0],
                scope=cells[1],
                decision=cells[2],
                residual_issue=cells[3],
                test_target=cells[4],
            )
        )
    expected = [f"MAN-{index:03d}" for index in range(1, len(decisions) + 1)]
    actual = [row["decision_id"] for row in decisions]
    if actual != expected:
        raise ValueError(f"Manual decisions must be unique and sequential: {actual}")
    return decisions


def manual_ids_in_text(value: object) -> set[str]:
    text = str(value or "")
    ids = {f"MAN-{int(match):03d}" for match in MANUAL_ID_RE.findall(text)}
    for start_text, end_text in MANUAL_RANGE_RE.findall(text):
        start, end = int(start_text), int(end_text)
        if end < start:
            raise ValueError(f"Invalid manual-decision range MAN-{start_text} through MAN-{end_text}")
        ids.update(f"MAN-{index:03d}" for index in range(start, end + 1))
    return ids


def read_manual_effective_source_map(
    path: Path, effective_source_ids: set[str]
) -> dict[str, set[str]]:
    """Read effective-dataset exposure declarations from the manual-decision report."""
    mapped: dict[str, set[str]] = defaultdict(set)
    in_table = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line == "### Deduplicated effective-dataset exposure":
            in_table = True
            continue
        if in_table and raw_line.startswith("### "):
            break
        if not in_table or not raw_line.startswith("| MAN-"):
            continue
        cells = [cell.strip() for cell in raw_line.strip().strip("|").split("|")]
        if len(cells) != 4:
            raise ValueError(f"Malformed effective-source exposure row: {raw_line}")
        decision_ids = manual_ids_in_text(cells[0])
        source_patterns = CODE_SPAN_RE.findall(cells[1])
        matched_sources: set[str] = set()
        for pattern in source_patterns:
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                matched_sources.update(
                    source_id for source_id in effective_source_ids if source_id.startswith(prefix)
                )
            elif pattern in effective_source_ids:
                matched_sources.add(pattern)
            else:
                raise ValueError(f"Unknown effective source in manual-decision mapping: {pattern}")
        if not matched_sources:
            raise ValueError(f"No effective sources matched manual-decision row: {raw_line}")
        for source_id in matched_sources:
            mapped[f"hf:{source_id}"].update(decision_ids)
    return mapped


def tex(value: object) -> str:
    text = str(value or "")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def nolinkurl(value: object) -> str:
    return rf"\nolinkurl{{{str(value or '')}}}"


def url(value: object) -> str:
    return rf"\url{{{str(value or '')}}}"


def evidence_text(value: str) -> str:
    rendered = []
    for segment in value.split("; "):
        if segment.startswith(("http://", "https://")):
            rendered.append(url(segment))
        elif "/" in segment and " " not in segment:
            rendered.append(nolinkurl(segment))
        else:
            rendered.append(tex(segment))
    return "; ".join(rendered)


def compact_tokens(value: str) -> str:
    number = float(value or 0)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.3f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.3f}M"
    if number >= 1_000:
        return f"{number / 1_000:.3f}K"
    return f"{number:.0f}"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_cell(
    parent_id: str,
    edges_by_parent: dict[str, list[dict[str, str]]],
    dependency_ids: dict[str, str],
) -> str:
    edges = sorted(
        edges_by_parent.get(parent_id, []),
        key=lambda row: (dependency_ids[row["child_id"]], row["relation"]),
    )
    if not edges:
        return r"\textit{None recorded}"
    rendered = []
    for edge in edges:
        reference = dependency_ids[edge["child_id"]]
        optional = r"$^{\dagger}$" if edge["required_for_clearance"] == "no" else ""
        relation = tex(edge["relation"])
        rendered.append(rf"\hyperlink{{dep:{reference}}}{{{reference}}}{optional} ({relation})")
    return "; ".join(rendered)


def manual_decision_map(
    nodes: dict[str, dict[str, str]],
    edges_by_parent: dict[str, list[dict[str, str]]],
) -> dict[str, set[str]]:
    """Return direct and transitively inherited manual decisions for every DAG node."""
    memo: dict[str, set[str]] = {}
    visiting: set[str] = set()

    def visit(node_id: str) -> set[str]:
        if node_id in memo:
            return memo[node_id]
        if node_id in visiting:
            raise ValueError(f"Cycle while resolving manual decisions at {node_id}")
        visiting.add(node_id)
        node = nodes[node_id]
        ids = manual_ids_in_text(" ".join(node.values()))
        for edge in edges_by_parent.get(node_id, []):
            ids.update(manual_ids_in_text(" ".join(edge.values())))
            ids.update(visit(edge["child_id"]))
        visiting.remove(node_id)
        memo[node_id] = ids
        return ids

    for node_id in nodes:
        visit(node_id)
    return memo


def manual_decisions_cell(decision_ids: set[str]) -> str:
    if not decision_ids:
        return r"\textit{None}"
    return ", ".join(
        rf"\hyperlink{{manual:{decision_id}}}{{\texttt{{{decision_id}}}}}"
        for decision_id in sorted(decision_ids)
    )


def node_identity(node: dict[str, str]) -> str:
    label = tex(node["label"])
    parts = [rf"\textbf{{{label}}}", nolinkurl(node["node_id"])]
    uri = node["uri"]
    if uri:
        parts.append(rf"URI: {url(uri)}")
    return r"\newline ".join(parts)


def status_text(node: dict[str, str], computed: str) -> str:
    return (
        rf"local: \texttt{{{tex(node['local_status'])}}}\newline "
        rf"computed: \texttt{{{tex(computed)}}}\newline "
        rf"lineage: \texttt{{{tex(node['dependency_completeness'])}}}"
    )


def terms_text(node: dict[str, str]) -> str:
    parts = [tex(node["basis"])]
    if node["evidence"]:
        parts.append(rf"\textit{{Evidence:}} {evidence_text(node['evidence'])}")
    if node["notes"]:
        parts.append(rf"\textit{{Note:}} {tex(node['notes'])}")
    return r"\newline ".join(part for part in parts if part)


def top_level_terms(row: dict[str, str]) -> str:
    licence = row["captured_declared_licence"] or "No separate top-level declaration captured"
    parts = [
        rf"\textbf{{Declared:}} {tex(licence)}",
        rf"\textbf{{Research basis:}} {tex(row['current_scientific_research_basis'])}",
        rf"\textbf{{Non-research/commercial:}} {tex(row['nonresearch_or_commercial_basis'])}",
    ]
    return r"\newline ".join(parts)


def build() -> str:
    nodes, edges = read_graph()
    states = resolve(nodes, edges)
    manual_decisions = read_manual_decisions(MANUAL_DECISIONS)
    valid_manual_ids = {row["decision_id"] for row in manual_decisions}
    register = {f"hf:{row['source_id']}": row for row in read_rows(REGISTER)}
    effective_ids = sorted(register, key=lambda node_id: register[node_id]["source_id"].casefold())
    source_ids = {node_id: f"S{index:03d}" for index, node_id in enumerate(effective_ids, 1)}

    dependency_node_ids = sorted({edge["child_id"] for edge in edges})
    dependency_ids = {
        node_id: f"D{index:03d}" for index, node_id in enumerate(dependency_node_ids, 1)
    }
    edges_by_parent: dict[str, list[dict[str, str]]] = defaultdict(list)
    for edge in edges:
        edges_by_parent[edge["parent_id"]].append(edge)
    decisions_by_node = manual_decision_map(nodes, edges_by_parent)
    for node_id, row in register.items():
        decisions_by_node[node_id].update(manual_ids_in_text(" ".join(row.values())))
    effective_source_map = read_manual_effective_source_map(
        MANUAL_DECISIONS, {row["source_id"] for row in register.values()}
    )
    for node_id, decision_ids in effective_source_map.items():
        decisions_by_node[node_id].update(decision_ids)
    referenced_manual_ids = set().union(*decisions_by_node.values())
    unknown_manual_ids = referenced_manual_ids - valid_manual_ids
    if unknown_manual_ids:
        raise ValueError(f"DAG references undefined manual decisions: {sorted(unknown_manual_ids)}")
    unreferenced_manual_ids = valid_manual_ids - referenced_manual_ids
    if unreferenced_manual_ids:
        raise ValueError(f"Manual decisions not referenced by the DAG: {sorted(unreferenced_manual_ids)}")

    lines = [
        r"\documentclass[9pt,a4paper]{article}",
        r"\usepackage[margin=12mm]{geometry}",
        r"\usepackage{array,booktabs,longtable,pdflscape}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\usepackage{xurl}",
        r"\setlength{\LTpre}{0pt}",
        r"\setlength{\LTpost}{8pt}",
        r"\setlength{\tabcolsep}{3pt}",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}",
        r"\newcommand{\srcid}[1]{\hypertarget{src:#1}{\texttt{#1}}}",
        r"\newcommand{\depid}[1]{\hypertarget{dep:#1}{\texttt{#1}}}",
        r"\newcommand{\manid}[1]{\hypertarget{manual:#1}{\texttt{#1}}}",
        r"\title{DFM9 Source-Rights and Dependency Register}",
        r"\author{Danish Foundation Models}",
        rf"\date{{Generated {date.today().isoformat()}}}",
        r"\begin{document}",
        r"\maketitle",
        r"\section*{Scope and interpretation}",
        (
            "This appendix is an engineering and legal-triage rendering of the declarative DFM9 "
            "source-rights dependency directed acyclic graph (DAG); it is not legal advice. "
            f"It contains {len(effective_ids)} effective training datasets, "
            f"{len(dependency_node_ids)} dependency rows, {len(edges)} typed edges, and "
            f"{len(manual_decisions)} manual decisions. "
            "Each top-level source cites concrete dependency rows by identifier. Dependencies may "
            "themselves cite further dependency rows, and therefore shared components are stated "
            "once rather than duplicated under every parent."
        ),
        "",
        (
            r"The status fields distinguish the node's local decision from the computed DAG status. "
            r"A computed \texttt{cleared} status means that the node's own layer and all required "
            r"dependencies are cleared for the stated scientific-research use. "
            r"Lineage completeness is independent: \texttt{top\_level\_only} indicates that the "
            r"current working decision exists but further provenance decomposition remains desirable. "
            r"A dagger ($\dagger$) marks an informational edge that is not required for upward clearance."
        ),
        "",
        rf"\noindent\textbf{{Authoritative node specification SHA-256:}} {nolinkurl(digest(SPEC_NODES))}\\",
        rf"\textbf{{Authoritative edge specification SHA-256:}} {nolinkurl(digest(SPEC_EDGES))}\\",
        rf"\textbf{{Top-level copyright register SHA-256:}} {nolinkurl(digest(REGISTER))}\\",
        rf"\textbf{{Manual-decision register SHA-256:}} {nolinkurl(digest(MANUAL_DECISIONS))}",
        r"\section{Copyright and data-protection audit framework}",
        r"\subsection{Two independent legal gates}",
        (
            r"The project treats copyright and database rights on the one hand, and data "
            r"protection on the other, as independent gates. A copyright licence or text-and-data-"
            r"mining (TDM) exception does not supply a GDPR legal basis, and a GDPR legal basis "
            r"does not authorise acts restricted by copyright or database rights. Passing one "
            r"review therefore never cures a failure in the other. The operational starting point "
            r"is to identify the exact effective source, revision, acquisition route, retained "
            r"fields, transformations, repetitions, and upstream dependencies before assigning "
            r"either status."
        ),
        r"\subsection{Copyright and TDM decision path}",
        (
            r"The first preference is a direct basis: public-domain status, an applicable open "
            r"licence, assigned rights, express permission, or an institutional agreement. Terms "
            r"are applied component by component where a mixture or derivative has multiple rights "
            r"layers. Attribution, notice, share-alike, non-commercial, field-of-use, and "
            r"redistribution conditions remain attached to the relevant layer. Synthetic or "
            r"transformed data are not presumed rights-free merely because a model or script made "
            r"them; retained source expression and seed provenance remain dependencies."
        ),
        (
            r"Where no sufficient direct basis covers a reproduction or extraction, the project "
            r"considers Articles 3 and 4 of Directive (EU) 2019/790 (the DSM Directive), as "
            r"implemented in Denmark by Copyright Act sections 11 c and 11 b."
            r"\footnote{DSM Directive: \url{https://eur-lex.europa.eu/eli/dir/2019/790/oj}. "
            r"Danish Copyright Act: \url{https://www.retsinformation.dk/eli/lta/2023/1093}.} "
            r"Article 3 is the research route: it covers reproductions and extractions by a "
            r"qualifying research organisation or cultural-heritage institution for scientific "
            r"research, only for material to which it has lawful access. Copies must be secured and "
            r"may be retained for research and verification; contractual terms may not override "
            r"that exception. The project records Article 3 as a purpose- and actor-specific basis, "
            r"not as a general licence or permission to redistribute source material."
        ),
        (
            r"Article 4 is the general TDM route. It likewise requires lawful access, permits "
            r"retention only for as long as necessary for TDM, and is unavailable where the "
            r"rightsholder expressly reserved the use in an appropriate manner, including machine-"
            r"readable means for online content. The project therefore records acquisition-time "
            r"terms, repository cards, robots or TDM signals, and other reservation evidence where "
            r"available. Missing evidence is not converted into an assumption that no reservation "
            r"existed. Article 4 determinations in this register are source-specific and must be "
            r"rechecked for a fresh acquisition or a materially different use. Neither TDM article "
            r"authorises publication of protected training copies or guarantees that generated "
            r"outputs are non-infringing."
        ),
        r"\subsection{GDPR interpretation and controls}",
        (
            r"For sources that contain or may contain personal data, the project separately records "
            r"the controller, purposes, categories and sources of data, Article 6 basis, any Article "
            r"9 condition, transparency route, retention, access controls, data-subject-rights "
            r"handling, and whether a data-protection impact assessment is required. Public "
            r"availability does not by itself remove GDPR protection or make the processing "
            r"reasonably expected. Data minimisation, purpose limitation, accuracy, storage "
            r"limitation, security, and accountability apply throughout collection, preparation, "
            r"training, evaluation, release, and deployment."
        ),
        (
            r"The project reads EDPB Opinion 28/2024 as requiring a documented, case-by-case "
            r"assessment rather than a categorical claim that trained models are anonymous."
            r"\footnote{EDPB Opinion 28/2024: "
            r"\url{https://www.edpb.europa.eu/documents/opinion-of-the-board-art-64/opinion-282024-on-certain-data-protection-aspects-related-to_en}.} "
            r"Where legitimate interest is relied upon, the record must identify a lawful, precise, "
            r"real and present interest; establish necessity and the absence of a less intrusive "
            r"effective alternative; and balance that interest against the rights and reasonable "
            r"expectations of affected people, with concrete mitigations. Unlawful upstream "
            r"processing may affect later deployment, especially where personal data remain in the "
            r"model."
        ),
        (
            r"The EDPB's 2026 Guidelines 1/2026 on scientific research, 02/2026 on "
            r"anonymisation, and 03/2026 on web scraping for generative AI are treated as "
            r"consultation drafts, not final law or independent legal bases."
            r"\footnote{EDPB 2026 consultations: "
            r"\url{https://www.edpb.europa.eu/public-consultations_en}.} "
            r"They are nevertheless used as conservative operational guidance: define the research "
            r"purpose and safeguards specifically; assess anonymisation against record isolation, "
            r"linkage, and inference using means reasonably likely for the relevant actors; and, for "
            r"web-derived data, document provenance and collection time, source reliability, "
            r"minimisation, accuracy, transparency, and incidental special-category data. Their "
            r"draft status and later revisions must be checked at release and on material reuse."
        ),
        r"\subsection{EU AI Act scope and open-source release strategy}",
        (
            r"The EU AI Act is a third, independent compliance layer."
            r"\footnote{Regulation (EU) 2024/1689: "
            r"\url{https://eur-lex.europa.eu/eli/reg/2024/1689/oj}. Commission GPAI scope "
            r"guidelines: \url{https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act}.} "
            r"It does not replace copyright, GDPR, contractual, research-ethics, or product-sector "
            r"review. Article 2(6) excludes models specifically developed and put into service for "
            r"the sole purpose of scientific research and development; Article 2(8) separately "
            r"excludes research, testing, and development before market placement or putting into "
            r"service. The project does not choose Article 2(6) as its principal release position. "
            r"The intended public release permits broad inspection, reuse, modification, "
            r"redistribution, and downstream integration rather than confining the model and every "
            r"derivative to a sole scientific-R\&D purpose. Article 2(8) also ceases to answer the "
            r"question once the model is released. Relying on either exclusion would therefore make "
            r"the legal position depend on a narrow purpose limitation that conflicts with the "
            r"chosen release objective."
        ),
        (
            r"Instead, DFM-Mimir is published under the Apache License 2.0 on the Danish Foundation "
            r"Models Hugging Face repository, with its weights, architecture/configuration, chat "
            r"template, and model-usage instructions publicly available."
            r"\footnote{DFM-Mimir release: "
            r"\url{https://huggingface.co/danish-foundation-models/DFM-Mimir}.} "
            r"Apache-2.0 permits access, use, modification, and distribution without a non-"
            r"commercial or research-only purpose restriction and therefore supports the Article "
            r"53(2) free/open-source conditions. This verified release fact supersedes the older "
            r"scope-dossier assumption that MIMIR License v1.0, a non-commercial/research-only "
            r"licence, governed the release. The model licence grants only rights controlled by the "
            r"provider: it does not relicense third-party training works, remove their attribution "
            r"or non-commercial conditions, or authorise infringing model outputs."
        ),
        (
            r"Open source is chosen for substantive and regulatory reasons. It supports independent "
            r"inspection, reproducibility, adaptation, Danish-language research and innovation, "
            r"security review, and broad downstream access without forcing the project to police a "
            r"sole-research purpose. If the model is nevertheless classified as a general-purpose "
            r"AI (GPAI) model, Article 53(2) exempts a qualifying non-systemic open-source provider "
            r"from Article 53(1)(a)--(b): the authority-facing technical-documentation duty and the "
            r"downstream-provider information duty. It does not exempt the Article 53(1)(c) Union-"
            r"copyright compliance policy or the Article 53(1)(d) sufficiently detailed public "
            r"training-content summary, and the exemption does not apply to a GPAI model with "
            r"systemic risk. Open source likewise does not exempt downstream AI systems from their "
            r"own applicable obligations. This dossier retains fuller documentation voluntarily "
            r"because it supports accountability and makes the project robust if classification or "
            r"guidance changes."
        ),
        r"\subsection{Training-compute thresholds}",
        (
            r"The Commission's current, non-binding GPAI scope guidelines use a conjunctive "
            r"indicative criterion of more than $10^{23}$ cumulative training FLOPs and generation "
            r"of language, text-to-image, or text-to-video. The statutory definition remains "
            r"capability-based: a model below the indicative compute value can still be GPAI if it "
            r"displays significant generality and competently performs a wide range of distinct "
            r"tasks, while an exceptional model above it may lack such generality. Article 51(2) "
            r"separately presumes high-impact capabilities, and therefore systemic-risk GPAI status, "
            r"above $10^{25}$ cumulative training FLOPs; the Commission may also designate a model "
            r"on equivalent capabilities or impact under Article 51(1)."
        ),
        (
            r"The project's recurrence-aware engineering upper bound for the released DFM9/Mimir "
            r"training run is $1.19\times10^{22}$ FLOPs. It counts multiply-add as two operations, "
            r"assumes five backpropagation steps from the beginning, and covers the documented "
            r"1,650,000-step lifecycle. The estimate is 11.9\% of $10^{23}$ (about 8.4 times below "
            r"the indicative GPAI compute criterion) and 0.119\% of $10^{25}$ (about 840 times below "
            r"the systemic-risk compute presumption). Thus compute does not trigger either current "
            r"threshold, even under the project's conservative recurrence assumption. The value "
            r"must still receive independent technical review, remain bound to the exact checkpoint "
            r"and methodology, and be updated for continued training or other development in the "
            r"same model lifecycle. The below-threshold result supports, but does not alone decide, "
            r"the GPAI or systemic-risk classification."
        ),
        r"\subsection{Audit workflow and role of memorisation}",
        r"\begin{enumerate}",
        (
            r"\item Freeze a source inventory and exposure manifest, including revisions, files, "
            r"fields, transformations, row counts, token exposure, repetition, and acquisition "
            r"evidence."
        ),
        (
            r"\item Decompose mixtures and derivatives into a dependency DAG; evaluate every "
            r"required rights layer and preserve notices and obligations transitively."
        ),
        (
            r"\item Apply direct permissions first, then a documented Article 3 or source-specific "
            r"Article 4 analysis where necessary. Exclude, replace, or escalate unresolved material."
        ),
        (
            r"\item Run the independent GDPR review, including personal- and special-category-data "
            r"screening, legal basis, necessity and balancing, transparency, rights, security, "
            r"retention, and DPIA/DPO escalation."
        ),
        (
            r"\item Audit outputs and model behaviour for extractability and memorisation, record "
            r"residual risk, and make release and access controls proportionate to the evidence."
        ),
        (
            r"\item Reassess when a source, reservation signal, purpose, controller, training "
            r"exposure, model, attack method, or release mode materially changes."
        ),
        r"\end{enumerate}",
        (
            r"Memorisation matters to both gates. Verbatim or identifying extraction can increase "
            r"copyright risk in outputs and can show that personal data remain practically "
            r"extractable or associated with training subjects, weakening an anonymity claim. "
            r"Conversely, a negative finite audit cannot prove non-infringement, erase an unlawful "
            r"collection, establish anonymity, or rule out stronger adaptive attacks. It is one "
            r"empirical control within the broader provenance, legal-basis, minimisation, security, "
            r"and release assessment."
        ),
        r"\section{DFM9 memorisation audit and results}",
        (
            r"The Mimir technical report describes two independent memorisation audits over four "
            r"rights/provenance categories (A--D)."
            r"\footnote{Mimir v1 technical report, Appendix C: "
            r"\url{https://arxiv.org/html/2608.13517}.} "
            r"Category A contains synthetic instruction data seeded from agreement-covered sources; "
            r"B contains Hugging Face instruction data for which row-level opt-out status could not "
            r"be established reliably; C contains Hugging Face instruction data with high confidence "
            r"that no applicable row-level opt-out had been exercised; and D contains other synthetic "
            r"and reasoning data with no identified material copyright concern but without a "
            r"coherent open-licence, licensed, or public-domain status."
        ),
        r"\subsection{Prefix and generic-prompt audit}",
        (
            r"The first audit used 1,000 ordinary non-adversarial prompts across Danish and English "
            r"and 500 targeted 50-token-prefix extraction prompts per category, 3,000 prompts in "
            r"total, against 140,990,504 training documents. In generic settings, matches of at "
            r"least 50 tokens appeared only once for English/B and once for English/D, and not in "
            r"the other English or any Danish comparison. Under prefix attacks, any-length matches "
            r"were found in 0.073\% of A documents, 0.887\% of B, 0.029\% of C, and 0.046\% of D. "
            r"Spans of at least 50 tokens occurred in 26, 271, 293, and 257 documents respectively: "
            r"0.00022\%, 0.015\%, 0.00031\%, and 0.00074\% of the checked documents. Average longest "
            r"spans were 8.8, 17.1, 12.4, and 22.3 tokens. Longer B and D matches were often numbers, "
            r"formulae, matrices, code, algorithms, structured tasks, or mathematical solutions."
        ),
        r"\subsection{Exact 64-token continuation and content adjudication}",
        (
            r"The second audit used a fixed greedy 64-token prefix plus 64-token continuation "
            r"protocol. Across 136,612,444 model-input evaluations it found 5,562 exact-match "
            r"occurrences (0.0041\%), representing 3,423 unique prefix--continuation pairs. The "
            r"category counts were 15/2,732,080 for A (0.0005\%), 7/411,508 for B (0.0017\%), "
            r"4,874/124,246,748 for C (0.0039\%), and 666/9,222,108 for D (0.0072\%). LLM "
            r"adjudication followed by human review classified 61/5,562 matches (1.10\%) as coherent "
            r"prose and one (0.018\%) as expressive prose. The report identified no high-priority "
            r"copyright finding; its single medium-priority case was a predictable continuation of "
            r"a traditional repetitive song."
        ),
        r"\subsection{Conclusion and limits}",
        (
            r"The combined evidence did not show systematic reconstruction of long, distinctive "
            r"expressive passages and supports a low observed copyright-related memorisation risk "
            r"under the tested conditions. Potentially risky outputs represented 62 of 136,612,444 "
            r"model-input evaluations (approximately 0.000045\%). This is a measured result, not a "
            r"zero-risk finding: adaptive prompts, longer prefixes, alternative decoding, future "
            r"attacks, and personal-data-specific extraction or inference may produce different "
            r"results. The audit therefore supports, but does not by itself establish, GDPR "
            r"anonymity or copyright clearance."
        ),
        r"\begin{landscape}",
        r"\section{Effective DFM9 training sources}",
        r"\scriptsize",
        r"\begin{longtable}{@{}L{0.03\linewidth}L{0.14\linewidth}L{0.26\linewidth}L{0.09\linewidth}L{0.09\linewidth}L{0.265\linewidth}L{0.045\linewidth}@{}}",
        r"\toprule",
        r"ID & Dataset & Licence and operative terms & Status & Manual decisions & Direct dependencies & Tokens/\newline epoch \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{7}{l}{\textit{Effective DFM9 training sources (continued)}}\\",
        r"\toprule",
        r"ID & Dataset & Licence and operative terms & Status & Manual decisions & Direct dependencies & Tokens/\newline epoch \\",
        r"\midrule",
        r"\endhead",
        r"\midrule\multicolumn{7}{r}{\textit{Continued on next page}}\\\endfoot",
        r"\bottomrule\endlastfoot",
    ]
    for node_id in effective_ids:
        row = register[node_id]
        node = nodes[node_id]
        source_id = source_ids[node_id]
        dataset = (
            rf"\textbf{{{nolinkurl(row['source_id'])}}}\newline "
            rf"{url(row['source_url'])}\newline "
            rf"DFM9 share: {tex(row['dfm9_share'])}"
        )
        lines.append(
            " & ".join(
                (
                    rf"\srcid{{{source_id}}}",
                    dataset,
                    top_level_terms(row),
                    status_text(node, states[node_id]),
                    manual_decisions_cell(decisions_by_node[node_id]),
                    dependency_cell(node_id, edges_by_parent, dependency_ids),
                    compact_tokens(node["average_tokens_per_epoch"]),
                )
            )
            + r" \\"
        )
    lines += [
        r"\end{longtable}",
        r"\section{Dependency-node register}",
        (
            r"Every identifier cited in the preceding table is defined below. The relation shown "
            r"beside a dependency reference describes the edge from the current row to that child."
        ),
        r"\begin{longtable}{@{}L{0.035\linewidth}L{0.185\linewidth}L{0.27\linewidth}L{0.09\linewidth}L{0.10\linewidth}L{0.24\linewidth}@{}}",
        r"\toprule",
        r"ID & Canonical node & Terms, basis, and evidence & Status & Manual decisions & Direct dependencies \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{6}{l}{\textit{Dependency-node register (continued)}}\\",
        r"\toprule",
        r"ID & Canonical node & Terms, basis, and evidence & Status & Manual decisions & Direct dependencies \\",
        r"\midrule",
        r"\endhead",
        r"\midrule\multicolumn{6}{r}{\textit{Continued on next page}}\\\endfoot",
        r"\bottomrule\endlastfoot",
    ]
    for node_id in dependency_node_ids:
        node = nodes[node_id]
        dependency_id = dependency_ids[node_id]
        identity = node_identity(node) + rf"\newline Type: \texttt{{{tex(node['node_type'])}}}"
        lines.append(
            " & ".join(
                (
                    rf"\depid{{{dependency_id}}}",
                    identity,
                    terms_text(node),
                    status_text(node, states[node_id]),
                    manual_decisions_cell(decisions_by_node[node_id]),
                    dependency_cell(node_id, edges_by_parent, dependency_ids),
                )
            )
            + r" \\"
        )
    lines += [
        r"\end{longtable}",
        r"\section{Manual decisions and overrides}",
        (
            r"This register states every project-owner decision cited by the DAG. References in "
            r"the preceding tables include both decisions stated at a node and decisions inherited "
            r"through its dependencies. The decisions are purpose-limited and do not replace the "
            r"residual qualifications or future testing targets stated here."
        ),
        r"\begin{longtable}{@{}L{0.06\linewidth}L{0.18\linewidth}L{0.30\linewidth}L{0.18\linewidth}L{0.20\linewidth}@{}}",
        r"\toprule",
        r"ID & Scope & Decision and reason & Residual issue & Memorisation/propensity target \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{5}{l}{\textit{Manual decisions and overrides (continued)}}\\",
        r"\toprule",
        r"ID & Scope & Decision and reason & Residual issue & Memorisation/propensity target \\",
        r"\midrule",
        r"\endhead",
        r"\midrule\multicolumn{5}{r}{\textit{Continued on next page}}\\\endfoot",
        r"\bottomrule\endlastfoot",
    ]
    for decision in manual_decisions:
        lines.append(
            " & ".join(
                (
                    rf"\manid{{{decision['decision_id']}}}",
                    tex(decision["scope"]),
                    tex(decision["decision"]),
                    tex(decision["residual_issue"]),
                    tex(decision["test_target"]),
                )
            )
            + r" \\"
        )
    lines += [
        r"\end{longtable}",
        r"\end{landscape}",
        r"\end{document}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
