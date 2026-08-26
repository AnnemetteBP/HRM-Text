#!/usr/bin/env python3
"""Inventory retained Sapient FLAN, Tasksource, and Platypus families."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASKSOURCE_REVISION = "ef6535aebaed3f6b9c72a833e63106313fdadac0"
TASKSOURCE_TASKS_URL = (
    "https://raw.githubusercontent.com/sileod/tasksource/"
    f"{TASKSOURCE_REVISION}/tasks.md"
)
HF_API = "https://huggingface.co/api/datasets/{}"
TASKSOURCE_FILENAME_ALIASES = {
    "feverevidencerelatedmwongfeverrelated": "feverevidencerelated",
    "nannlijoey234nannli": "nannli",
    "vitaminctalsvitaminc": "vitaminc",
}
DIRECT_TASKSOURCE_LICENSES = {
    "afl-3.0",
    "apache-2.0",
    "cc-by-4.0",
    "cc-by-sa-3.0",
    "cc-by-sa-3.0;gpl-3.0",
    "cc-by-sa-4.0",
    "cc0-1.0",
    "gpl",
    "gpl-3.0",
    "mit",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analytics",
        type=Path,
        default=ROOT / "data/show_analytics_dfm9.md",
    )
    parser.add_argument(
        "--tasksource-tasks",
        type=Path,
        help="Optional local tasks.md; otherwise fetch the pinned revision.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "legal/registers/dfm9-sapient-instruction-family-inventory.csv",
    )
    return parser.parse_args()


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "DFM9-rights-audit/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def parse_analytics(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text().splitlines():
        if not line.startswith("| **"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        name = cells[0].strip("*")
        if "__" not in name:
            continue
        category, filename = name.split("__", 1)
        if category not in {"flan", "tasksource", "Platypus"}:
            continue
        values = []
        for cell in cells[1:]:
            match = re.match(r"([0-9,]+)", cell)
            if not match:
                raise ValueError(f"Cannot parse analytics cell: {cell}")
            values.append(int(match.group(1).replace(",", "")))
        rows.append(
            {
                "category": category,
                "filename": filename,
                "sampled_rows_five_epochs": values[2],
                "sampled_tokens_five_epochs": values[3],
                "tokens_per_epoch": values[3] / 5,
            }
        )
    return rows


def normalized_task_name(value: str) -> str:
    value = value.removesuffix(".parquet")
    return re.sub(r"[^a-z0-9]", "", value.lower())


def parse_tasksource_tasks(text: str) -> dict[str, dict[str, str]]:
    tasks: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        task, repo, config, split, loader, task_type = cells[1:7]
        tasks[normalized_task_name(task)] = {
            "tasksource_task": task,
            "upstream_repo": repo,
            "upstream_config": config,
            "upstream_split": split,
            "tasksource_loader": loader,
            "task_type": task_type,
        }
    return tasks


def hf_metadata(repo: str, cache: dict[str, dict[str, object]]) -> dict[str, object]:
    if repo in cache:
        return cache[repo]
    try:
        raw = json.loads(fetch_text(HF_API.format(repo)))
        card = raw.get("cardData") or {}
        license_value = card.get("license", "")
        if isinstance(license_value, list):
            license_value = ";".join(str(item) for item in license_value)
        value = {
            "hf_license": str(license_value or ""),
            "hf_revision": str(raw.get("sha") or ""),
            "hf_gated": str(raw.get("gated") or "false").lower(),
            "hf_private": str(bool(raw.get("private"))).lower(),
            "hf_disabled": str(bool(raw.get("disabled"))).lower(),
            "metadata_error": "",
        }
    except Exception as exc:  # Evidence collection should retain failed probes.
        value = {
            "hf_license": "",
            "hf_revision": "",
            "hf_gated": "",
            "hf_private": "",
            "hf_disabled": "",
            "metadata_error": f"{type(exc).__name__}: {exc}",
        }
    cache[repo] = value
    return value


def flan_submixture(filename: str) -> str:
    return filename.split("_data__", 1)[0]


def main() -> None:
    args = parse_args()
    analytics = parse_analytics(args.analytics)
    tasks_text = (
        args.tasksource_tasks.read_text()
        if args.tasksource_tasks
        else fetch_text(TASKSOURCE_TASKS_URL)
    )
    tasks = parse_tasksource_tasks(tasks_text)
    metadata_cache: dict[str, dict[str, object]] = {}
    output: list[dict[str, object]] = []

    for row in analytics:
        record = dict(row)
        record.update(
            {
                "family": "",
                "tasksource_task": "",
                "upstream_repo": "",
                "upstream_config": "",
                "upstream_split": "",
                "tasksource_loader": "",
                "task_type": "",
                "hf_license": "",
                "hf_revision": "",
                "hf_gated": "",
                "hf_private": "",
                "hf_disabled": "",
                "metadata_error": "",
                "mapping_status": "",
                "audit_bucket": "",
                "working_basis": "",
            }
        )
        category = str(row["category"])
        filename = str(row["filename"])
        if category == "flan":
            record["family"] = flan_submixture(filename)
            record["mapping_status"] = "flan_submixture"
            record["audit_bucket"] = "flan_collection_uncovered_expression"
            record["working_basis"] = "direct terms where identified; Article 4 for uncovered expression"
        elif category == "Platypus":
            family = filename.split("_", 1)[0] if filename.startswith("arb_") else filename.removesuffix(".jsonl")
            record["family"] = family
            record["mapping_status"] = "platypus_card_family"
            record["audit_bucket"] = "platypus_direct_component_terms"
            record["working_basis"] = "Open-Platypus source-table licence for current non-commercial use"
        else:
            normalized = normalized_task_name(filename)
            mapping = tasks.get(normalized) or tasks.get(TASKSOURCE_FILENAME_ALIASES.get(normalized, ""))
            if mapping:
                record.update(mapping)
                record.update(hf_metadata(mapping["upstream_repo"], metadata_cache))
                record["family"] = mapping["upstream_repo"]
                record["mapping_status"] = "exact_normalized_tasksource_mapping"
                if str(record["hf_license"]).lower() in DIRECT_TASKSOURCE_LICENSES:
                    record["audit_bucket"] = "tasksource_specific_licence"
                    record["working_basis"] = "current upstream repository licence metadata"
                else:
                    record["audit_bucket"] = "tasksource_residual_research_tdm"
                    record["working_basis"] = "Article 3 / Danish section 11 c for current research use"
            else:
                record["mapping_status"] = "unmapped"
        output.append(record)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output[0])
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)

    counts: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0, 0.0])
    for row in output:
        counts[(str(row["category"]), str(row["mapping_status"]))][0] += 1
        counts[(str(row["category"]), str(row["mapping_status"]))][1] += float(row["tokens_per_epoch"])
    for key, (files, tokens) in sorted(counts.items()):
        print(f"{key[0]} {key[1]}: {int(files)} files, {tokens:,.1f} tokens/epoch")
    print(f"Wrote {len(output):,} rows to {args.output}")


if __name__ == "__main__":
    main()
