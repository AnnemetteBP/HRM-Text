#!/usr/bin/env python3
"""Build and maintain the DFM9 source-rights dependency DAG."""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "legal/registers/dfm9-copyright-basis-register.csv"
SPEC_DIR = ROOT / "legal/specs/dfm9-source-dag"
SPEC_NODES = SPEC_DIR / "nodes.csv"
SPEC_EDGES = SPEC_DIR / "edges.csv"
NODES = ROOT / "legal/registers/dfm9-source-dag-nodes.csv"
EDGES = ROOT / "legal/registers/dfm9-source-dag-edges.csv"
RESOLUTION = ROOT / "legal/registers/dfm9-source-dag-resolution.csv"
EXPANSION_QUEUE = ROOT / "legal/registers/dfm9-source-dag-expansion-queue.csv"
REPORT = ROOT / "legal/reports/dfm9-source-rights-dependency-dag.md"

LOCAL_STATUSES = {"cleared", "unresolved", "inherited"}
COMPLETENESS = {"complete", "partial", "top_level_only"}


@dataclass(frozen=True)
class Node:
    node_id: str
    node_type: str
    label: str
    uri: str = ""
    local_status: str = "inherited"
    dependency_completeness: str = "complete"
    average_tokens_per_epoch: str = ""
    basis: str = ""
    evidence: str = ""
    notes: str = ""


@dataclass(frozen=True)
class Edge:
    parent_id: str
    child_id: str
    relation: str
    required_for_clearance: str = "yes"
    average_tokens_per_epoch: str = ""
    evidence: str = ""
    notes: str = ""


def hf(repo: str) -> str:
    return f"hf:{repo}"


def atomic_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_seed(force: bool) -> None:
    # Kept as a backwards-compatible command name. The graph is no longer
    # seeded by Python logic; initialization materializes the declarative spec.
    del force
    nodes, edges = read_graph()
    materialize_registers(nodes, edges)


def read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing declarative DAG file: {path}")
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != fields:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}; expected {fields}")
        return list(reader)


def read_graph() -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    node_rows = read_csv(SPEC_NODES, list(Node.__dataclass_fields__))
    edge_rows = read_csv(SPEC_EDGES, list(Edge.__dataclass_fields__))
    nodes = {r["node_id"]: r for r in node_rows}
    edges = edge_rows
    if len(nodes) != len(node_rows):
        raise ValueError(f"duplicate node_id in {SPEC_NODES}")
    edge_keys = {(e["parent_id"], e["child_id"], e["relation"]) for e in edges}
    if len(edge_keys) != len(edges):
        raise ValueError(f"duplicate parent/child/relation edge in {SPEC_EDGES}")
    for node in nodes.values():
        if node["local_status"] not in LOCAL_STATUSES:
            raise ValueError(f"invalid local status for {node['node_id']}: {node['local_status']}")
        if node["dependency_completeness"] not in COMPLETENESS:
            raise ValueError(f"invalid completeness for {node['node_id']}: {node['dependency_completeness']}")
    for edge in edges:
        if edge["parent_id"] not in nodes or edge["child_id"] not in nodes:
            raise ValueError(f"edge references missing node: {edge}")
        if edge["required_for_clearance"] not in {"yes", "no"}:
            raise ValueError(f"invalid required_for_clearance value: {edge}")

    with REGISTER.open(newline="") as f:
        expected = {hf(r["source_id"]): r for r in csv.DictReader(f)}
    effective = {node_id: node for node_id, node in nodes.items() if node["node_type"] == "effective_dataset"}
    if set(effective) != set(expected):
        missing = sorted(set(expected) - set(effective))
        extra = sorted(set(effective) - set(expected))
        raise ValueError(f"effective-source drift against copyright register; missing={missing}, extra={extra}")
    for node_id, source in expected.items():
        if float(effective[node_id]["average_tokens_per_epoch"]) != float(source["average_sampled_tokens_per_epoch"]):
            raise ValueError(f"token exposure drift for {node_id}")
    return nodes, edges


def materialize_registers(nodes: dict[str, dict[str, str]], edges: list[dict[str, str]]) -> None:
    """Write stable register mirrors from the authoritative declarative spec."""
    atomic_csv(NODES, [nodes[k] for k in sorted(nodes)], list(Node.__dataclass_fields__))
    atomic_csv(
        EDGES,
        sorted(edges, key=lambda x: (x["parent_id"], x["child_id"], x["relation"])),
        list(Edge.__dataclass_fields__),
    )


def resolve(nodes: dict[str, dict[str, str]], edges: list[dict[str, str]]) -> dict[str, str]:
    children: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge["required_for_clearance"] == "yes":
            children[edge["parent_id"]].append(edge["child_id"])
    state: dict[str, str] = {}
    visiting: set[str] = set()

    def visit(node_id: str) -> str:
        if node_id in state:
            return state[node_id]
        if node_id in visiting:
            raise ValueError(f"cycle detected at {node_id}")
        visiting.add(node_id)
        local = nodes[node_id]["local_status"]
        child_states = [visit(x) for x in children[node_id]]
        if local == "unresolved":
            result = "unresolved"
        elif any(x == "unresolved" for x in child_states):
            result = "partial"
        elif any(x == "partial" for x in child_states):
            result = "partial"
        elif local == "inherited" and not child_states:
            result = "unresolved"
        else:
            result = "cleared"
        visiting.remove(node_id)
        state[node_id] = result
        return result

    for node_id in nodes:
        visit(node_id)
    return state


def build_outputs() -> None:
    nodes, edges = read_graph()
    materialize_registers(nodes, edges)
    states = resolve(nodes, edges)
    parents: dict[str, list[str]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge["required_for_clearance"] == "yes":
            parents[edge["child_id"]].append(edge["parent_id"])
            children[edge["parent_id"]].append(edge["child_id"])

    def ancestors(node_id: str) -> set[str]:
        out: set[str] = set()
        todo = list(parents[node_id])
        while todo:
            item = todo.pop()
            if item not in out:
                out.add(item)
                todo.extend(parents[item])
        return out

    roots = {x for x in nodes if not parents[x]}
    rows = []
    for node_id in sorted(nodes):
        affected_nodes = ancestors(node_id)
        if nodes[node_id]["node_type"] == "effective_dataset":
            affected_nodes.add(node_id)
        affected = sorted(a for a in affected_nodes if nodes[a]["node_type"] == "effective_dataset")
        rows.append({
            "node_id": node_id,
            "computed_status": states[node_id],
            "is_root": "yes" if node_id in roots else "no",
            "required_children": str(len(children[node_id])),
            "affected_effective_sources": ";".join(affected),
        })
    atomic_csv(RESOLUTION, rows, list(rows[0]))

    queue = []
    for node_id, node in nodes.items():
        if node["node_type"] != "effective_dataset" or node["dependency_completeness"] != "top_level_only":
            continue
        queue.append({
            "node_id": node_id,
            "average_tokens_per_epoch": node["average_tokens_per_epoch"],
            "computed_status": states[node_id],
            "current_basis": node["basis"],
            "next_action": "identify retained works, generated contributions, and shared upstream dependencies",
        })
    queue.sort(key=lambda x: float(x["average_tokens_per_epoch"] or 0), reverse=True)
    atomic_csv(EXPANSION_QUEUE, queue, list(queue[0]))

    dfm = hf("danish-foundation-models/dfm-dyna-instruct")
    descendants: set[str] = set()
    todo = [dfm]
    while todo:
        item = todo.pop()
        if item not in descendants:
            descendants.add(item)
            todo.extend(children[item])
    counts = defaultdict(int)
    for node_id in descendants:
        counts[states[node_id]] += 1
    leaves = [x for x in descendants if not children[x]]
    unresolved_leaves = [x for x in leaves if states[x] != "cleared"]
    all_unresolved_leaves = [x for x in nodes if not children[x] and states[x] != "cleared"]

    leverage = []
    for node_id in all_unresolved_leaves:
        simulated = {key: value.copy() for key, value in nodes.items()}
        simulated[node_id]["local_status"] = "cleared"
        simulated_states = resolve(simulated, edges)
        changed = [key for key in nodes if simulated_states[key] != states[key]]
        affected = {
            key for key in ancestors(node_id) | {node_id}
            if nodes[key]["node_type"] == "effective_dataset"
        }
        exposure = sum(float(nodes[key]["average_tokens_per_epoch"] or 0) for key in affected)
        leverage.append((len(changed), len(affected), exposure, node_id, changed))
    leverage.sort(reverse=True)

    lines = [
        "# DFM9 Source-Rights Dependency DAG", "",
        "Status: engineering/legal triage, not legal advice. Generated from the authoritative declarative node and edge specifications.", "",
        "## DFM Dyna Instruct", "",
        f"The subtree has **{len(descendants)} canonical nodes** and **{sum(1 for e in edges if e['parent_id'] in descendants)} dependency edges**. "
        f"Computed status: **{states[dfm]}**.", "",
        "| Computed status | Nodes |", "|---|---:|",
    ]
    for status in ("cleared", "partial", "unresolved"):
        lines.append(f"| {status} | {counts[status]} |")
    lines += ["", "### Component status", "", "| Component | Tokens/epoch | Status |", "|---|---:|---|"]
    for edge in edges:
        if edge["parent_id"] == dfm:
            child = nodes[edge["child_id"]]
            lines.append(f"| {child['label']} | {int(float(child['average_tokens_per_epoch'])):,} | {states[edge['child_id']]} |")
    lines += ["", "### Unresolved leaves and audit boundaries", "", "| Node | Basis / remaining issue | Completeness |", "|---|---|---|"]
    for node_id in sorted(unresolved_leaves, key=lambda x: nodes[x]["label"].lower()):
        node = nodes[node_id]
        lines.append(f"| `{node_id}` | {node['basis'] or node['notes']} | {node['dependency_completeness']} |")
    lines += ["", "### Highest immediate resolution leverage", "",
              "This simulates clearing one unresolved leaf while holding every other node constant.", "",
              "| Leaf | Computed statuses changed | Effective sources reached | Tokens/epoch reached |",
              "|---|---:|---:|---:|"]
    for changed_count, source_count, exposure, node_id, _ in leverage[:10]:
        lines.append(f"| `{node_id}` | {changed_count} | {source_count} | {exposure:,.1f} |")
    lines += [
        "", "## Whole-DFM9 expansion state", "",
        f"All **{sum(1 for n in nodes.values() if n['node_type'] == 'effective_dataset')} effective DFM9 sources** are present as canonical effective-dataset nodes. "
        "Some are also reused as dependencies and therefore are not graph roots. The DFM Dyna subtree is decomposed to its documented source boundaries; remaining top-level-only sources retain their current audited status until their dependencies are added.", "",
        "| Dependency completeness | Nodes |", "|---|---:|",
    ]
    complete_counts = defaultdict(int)
    for node in nodes.values():
        complete_counts[node["dependency_completeness"]] += 1
    for value in ("complete", "partial", "top_level_only"):
        lines.append(f"| {value} | {complete_counts[value]} |")
    lines += ["", "### Next roots to expand", "", "| Effective source | Tokens/epoch | Current status |", "|---|---:|---|"]
    for item in queue[:25]:
        lines.append(f"| `{item['node_id']}` | {int(float(item['average_tokens_per_epoch'])):,} | {item['computed_status']} |")
    lines.append("")
    lines.append(f"The complete **{len(queue)}-row** work queue is `legal/registers/dfm9-source-dag-expansion-queue.csv`.")
    lines += [
        "", "## Status semantics", "",
        "- `cleared`: the node's own layer is resolved and all required children are cleared.",
        "- `unresolved`: the node itself needs a rights/terms decision, or an inherited node lacks children.",
        "- `partial`: the node's own layer is clear/inherited but at least one required descendant is unresolved.",
        "- `dependency_completeness` is independent: `partial` or `top_level_only` means more lineage expansion is still required even if a current working status is recorded.",
        "", "## Maintenance", "",
        "Edit the declarative files under `legal/specs/dfm9-source-dag/` or use `set-status`, then rebuild:", "",
        "```bash", "python legal/tools/manage_dfm9_source_dag.py build", "```", "",
        "A source is cleared upward automatically only after every required child resolves. Shared nodes are resolved once and affect every parent path.", "",
    ]
    REPORT.write_text("\n".join(lines))


def set_status(node_id: str, status: str, basis: str, evidence: str) -> None:
    if status not in LOCAL_STATUSES:
        raise SystemExit(f"status must be one of {sorted(LOCAL_STATUSES)}")
    nodes, _ = read_graph()
    if node_id not in nodes:
        raise SystemExit(f"unknown node: {node_id}")
    rows = list(nodes.values())
    for row in rows:
        if row["node_id"] == node_id:
            row["local_status"] = status
            if basis:
                row["basis"] = basis
            if evidence:
                row["evidence"] = evidence
    atomic_csv(SPEC_NODES, sorted(rows, key=lambda x: x["node_id"]), list(Node.__dataclass_fields__))
    build_outputs()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("initialize", help="materialize the declarative DAG specification")
    init.add_argument("--force", action="store_true")
    sub.add_parser("build", help="validate, resolve, and render the current DAG")
    update = sub.add_parser("set-status", help="atomically update one node and rebuild")
    update.add_argument("node_id")
    update.add_argument("status", choices=sorted(LOCAL_STATUSES))
    update.add_argument("--basis", default="")
    update.add_argument("--evidence", default="")
    args = parser.parse_args()
    if args.command == "initialize":
        write_seed(args.force)
        build_outputs()
    elif args.command == "build":
        build_outputs()
    else:
        set_status(args.node_id, args.status, args.basis, args.evidence)


if __name__ == "__main__":
    main()
