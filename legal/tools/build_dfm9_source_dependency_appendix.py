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
