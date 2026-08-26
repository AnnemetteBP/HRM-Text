#!/usr/bin/env python3
"""Inventory the local Tulu v2, SciRIFF mix, and IF-SFT source lineages."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
DOWNLOADS = ROOT / "data/downloads/datasets"
OUTPUT = ROOT / "legal/registers/dfm9-tulu-v2-sciriff-if-sft-component-audit.csv"

TULU_DIRS = {
    "allenai/tulu-v2-sft-mixture": DOWNLOADS / "allenai_tulu_v2_sft_mixture",
    "allenai/tulu-v2-sft-long-mixture": DOWNLOADS / "allenai_tulu_v2_sft_long_mixture",
}

COMPONENTS = {
    "flan_v2": ("component:tulu-v2:flan-v2", "direct terms plus MAN-013/MAN-019 Article 4 for uncovered FLAN expression", "cleared"),
    "cot": ("component:tulu-v2:flan-v2", "direct terms plus MAN-013/MAN-019 Article 4 for uncovered FLAN expression", "cleared"),
    "oasst1": ("hf:OpenAssistant/oasst1", "Apache-2.0", "cleared"),
    "sharegpt": ("hf:anon8231489123/ShareGPT_Vicuna_unfiltered", "Apache-2.0 repository tag does not establish contributor authority; Article 3 decision pending", "unresolved"),
    "gpt4_alpaca": ("source:Instruction-Tuning-with-GPT-4/GPT-4-LLM", "CC-BY-NC-4.0 for current academic/non-commercial use", "cleared"),
    "code_alpaca": ("source:sahil280114/codealpaca", "CC-BY-NC-4.0 for current academic/non-commercial use", "cleared"),
    "lima": ("hf:GAIR/lima", "CC-BY-NC-SA for current academic/non-commercial use", "cleared"),
    "wizardlm": ("hf:WizardLMTeam/WizardLM_evol_instruct_V2_196k", "MIT", "cleared"),
    "open_orca": ("hf:Open-Orca/OpenOrca", "MIT response/package layer plus MAN-013 Article 4 for uncovered FLAN expression", "cleared"),
    "hard_coded": ("generated:allenai:tulu-v2-hardcoded", "Ai2-authored contribution under the ODC-By release", "cleared"),
}


def source_counts(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in sorted(root.rglob("*.parquet")):
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(columns=["dataset"], batch_size=65_536):
            counts.update(batch.column(0).to_pylist())
    for path in sorted(root.rglob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    counts[json.loads(line)["dataset"]] += 1
    return counts


def component_for(label: str) -> tuple[str, str, str]:
    if label.startswith("science."):
        return (
            "hf:allenai/SciRIFF",
            "ODC-By task layer plus MAN-014 Article 4 for uncovered scholarly expression",
            "cleared",
        )
    return COMPONENTS[label]


def tulu_rows() -> list[dict[str, str | int]]:
    rows = []
    for source, root in TULU_DIRS.items():
        for label, count in sorted(source_counts(root).items()):
            component, basis, status = component_for(label)
            rows.append(
                {
                    "effective_source": source,
                    "local_source_label": label,
                    "rows": count,
                    "canonical_component": component,
                    "working_basis": basis,
                    "status": status,
                    "notes": "Local row count from the exact downloaded training artifact.",
                }
            )
    return rows


def sciriff_rows() -> list[dict[str, str | int]]:
    root = DOWNLOADS / "allenai_sciriff_train_mix"
    grouped: Counter[tuple[str, str, str, str]] = Counter()
    for label, count in source_counts(root).items():
        component, basis, status = component_for(label)
        local_group = "SciRIFF tasks" if label.startswith("science.") else label
        grouped[(local_group, component, basis, status)] += count
    return [
        {
            "effective_source": "allenai/SciRIFF-train-mix",
            "local_source_label": label,
            "rows": count,
            "canonical_component": component,
            "working_basis": basis,
            "status": status,
            "notes": "The local artifact has 35,000 SciRIFF rows and 35,714 Tulu-v2 rows.",
        }
        for (label, component, basis, status), count in sorted(grouped.items())
    ]


def if_sft_rows() -> list[dict[str, str | int]]:
    source_by_id: dict[str, str] = {}
    tulu3 = DOWNLOADS / "allenai_tulu_3_sft_mixture"
    for path in sorted(tulu3.rglob("*.parquet")):
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(columns=["id", "source"], batch_size=65_536):
            source_by_id.update(zip(batch.column(0).to_pylist(), batch.column(1).to_pylist()))

    path = DOWNLOADS / "allenai_if_sft_verified/data/train-00000-of-00001.parquet"
    table = pq.read_table(path, columns=["id", "model_completion"])
    counts: Counter[str] = Counter()
    generators: dict[str, Counter[str]] = {}
    unmatched = 0
    for row_id, generator in zip(table.column("id").to_pylist(), table.column("model_completion").to_pylist()):
        source = source_by_id.get(row_id)
        if source is None:
            unmatched += 1
            continue
        counts[source] += 1
        generators.setdefault(source, Counter())[generator] += 1
    if unmatched:
        raise RuntimeError(f"{unmatched} IF-SFT rows do not match the local Tulu-3 mixture")

    return [
        {
            "effective_source": "allenai/IF_sft_data_verified",
            "local_source_label": source,
            "rows": count,
            "canonical_component": "hf:allenai/tulu-3-sft-mixture",
            "working_basis": "Exact Tulu-3 row lineage plus Ai2-added constraint and regenerated-response layer",
            "status": "cleared",
            "notes": "Exact ID match; replacement-response generators: "
            + ", ".join(f"{name}={value}" for name, value in sorted(generators[source].items()))
            + ".",
        }
        for source, count in sorted(counts.items())
    ]


def main() -> None:
    rows = tulu_rows() + sciriff_rows() + if_sft_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} component rows to {OUTPUT}")


if __name__ == "__main__":
    main()
