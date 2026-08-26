#!/usr/bin/env python3
"""Build the concise DFM8 generation, translation, and audit evidence register."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "legal" / "registers" / "synthetic-pipeline-evidence.csv"


def main() -> None:
    rows: list[dict[str, object]] = []
    targeted = json.loads(
        (ROOT / "export-upload-dfm8-synthetic" / "build_summary.json").read_text()
    )
    rows.append(
        {
            "pipeline": "dfm8_targeted_synthetic",
            "family": "ALL_FAMILIES",
            "source_or_seed": "pipeline-specific public/source-derived seeds",
            "generator": "Gemma 4 31B (posttrain-gemma-teacher)",
            "judge": "Gemma 4 31B (posttrain-gemma-teacher)",
            "input_or_generated_rows": targeted["generated_rows"],
            "audited_rows": targeted["audit_rows"],
            "accepted_rows": sum(item["accepted_rows"] for item in targeted["families"].values()),
            "evidence": "export-upload-dfm8-synthetic/build_summary.json",
            "limitations": "aggregate pipeline counts; family manifests preserve accepted counts only",
        }
    )
    for family, item in sorted(targeted["families"].items()):
        rows.append(
            {
                "pipeline": "dfm8_targeted_synthetic",
                "family": family,
                "source_or_seed": "pipeline-specific public/source-derived seeds",
                "generator": "Gemma 4 31B (posttrain-gemma-teacher)",
                "judge": "Gemma 4 31B (posttrain-gemma-teacher)",
                "input_or_generated_rows": "",
                "audited_rows": "",
                "accepted_rows": item["accepted_rows"],
                "evidence": "export-upload-dfm8-synthetic/build_summary.json",
                "limitations": "per-family generated/audited denominator is not in the upload manifest",
            }
        )

    openhermes = json.loads(
        (ROOT / "export-upload-dfm8-openhermes-repaired" / "build_summary.json").read_text()
    )
    rows.extend(
        [
            {
                "pipeline": "dfm8_openhermes_repair",
                "family": "english",
                "source_or_seed": "teknium/OpenHermes-2.5",
                "generator": "Gemma 4 31B repair",
                "judge": "Gemma 4 31B source and repair audit",
                "input_or_generated_rows": openhermes["english_audit"]["source_audit_rows"],
                "audited_rows": openhermes["english_audit"]["source_audit_rows"],
                "accepted_rows": openhermes["english"]["rows"],
                "evidence": "export-upload-dfm8-openhermes-repaired/build_summary.json",
                "limitations": "accepted total combines clean and repaired rows; source rights remain inherited",
            },
            {
                "pipeline": "dfm8_openhermes_translation_repair",
                "family": "danish",
                "source_or_seed": "teknium/OpenHermes-2.5 plus accepted English repairs",
                "generator": "Gemma 4 31B translation and repair",
                "judge": "Gemma 4 31B Danish audit",
                "input_or_generated_rows": openhermes["danish_base"]["generated_rows"],
                "audited_rows": openhermes["danish_base"]["audit_rows"],
                "accepted_rows": openhermes["danish"]["rows"],
                "evidence": "export-upload-dfm8-openhermes-repaired/build_summary.json",
                "limitations": "final total includes replacements and accepted retries; source rights remain inherited",
            },
        ]
    )

    transform_root = ROOT / "data" / "dfm8_transform_expansion_filtered"
    for summary_path in sorted(transform_root.glob("*/filter_summary.json")):
        item = json.loads(summary_path.read_text())
        rows.append(
            {
                "pipeline": "dfm8_broad_transform_expansion",
                "family": item["dataset"],
                "source_or_seed": "Common Pile" if item["dataset"].startswith("common-pile") else "Danish DynaWord",
                "generator": "deterministic task transform plus Gemma 4 31B generation where applicable",
                "judge": "Gemma 4 31B audit; accepted rows only",
                "input_or_generated_rows": item["seen"],
                "audited_rows": item["seen"],
                "accepted_rows": item["kept"],
                "evidence": str(summary_path.relative_to(ROOT)),
                "limitations": "transformed output retains source provenance and may retain source expression",
            }
        )

    fields = list(rows[0])
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
