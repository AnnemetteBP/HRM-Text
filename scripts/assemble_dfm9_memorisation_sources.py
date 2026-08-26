#!/usr/bin/env python3
"""Assemble the locally available DFM9 memorisation reference material.

The output is a symlink tree: source data is not copied.  Each link is labelled
as an original, retained proxy, mixture proxy, or audit evidence in manifest.tsv.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOWNLOADS = REPO / "data/downloads/datasets"
AUDIT_CACHE = Path("/work/dfm/.cache/legal-audit")
DEFAULT_OUTPUT = REPO / "data/legal/dfm9_memorisation_sources"


@dataclass(frozen=True)
class Material:
    category: str
    cohort: str
    basis: str
    role: str
    path: Path
    selector: str = "all records"
    note: str = ""


@dataclass(frozen=True)
class Gap:
    category: str
    cohort: str
    missing_material: str
    available_proxy: str
    action: str


def add_tree(
    materials: list[Material],
    category: str,
    cohort: str,
    basis: str,
    role: str,
    path: Path,
    *,
    selector: str = "all records",
    note: str = "",
) -> None:
    if path.exists():
        materials.append(Material(category, cohort, basis, role, path, selector, note))


def inventory_rows() -> list[dict[str, str]]:
    path = REPO / "legal/registers/dfm9-sapient-instruction-family-inventory.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def factual_flan_files() -> dict[str, list[str]]:
    text = (REPO / "data/show_analytics_dfm9.md").read_text(encoding="utf-8")
    names = re.findall(r"^\| \*\*flan_factual__(.+?\.parquet)\*\*", text, re.MULTILINE)
    needles = {
        "C-01": "race",
        "C-02": "dream",
        "C-03": "web_questions",
        "C-04": "coqa",
        "D-07": "trivia_qa",
    }
    return {cohort: sorted({name for name in names if needle in name}) for cohort, needle in needles.items()}


def build_inventory() -> tuple[list[Material], list[Gap]]:
    m: list[Material] = []
    gaps: list[Gap] = []

    # A: direct agreement material.
    add_tree(m, "A", "A-01", "agreement", "original", DOWNLOADS / "lexdk/lexdk_articles.jsonl.gz")
    for path in sorted((DOWNLOADS / "dbc").glob("dbc-abstracts_*.jsonl.gz")):
        add_tree(m, "A", "A-02", "agreement", "original", path)
    add_tree(m, "A", "A-03", "agreement", "original", DOWNLOADS / "dbc/dbc-reviews.jsonl.gz")
    add_tree(m, "A", "A-04", "agreement", "original", DOWNLOADS / "dbc/dbc-faktalink.jsonl.gz")
    add_tree(
        m,
        "A",
        "A-05",
        "agreement",
        "original",
        DOWNLOADS / "dbc/dbc-farfatterweb.jsonl.gz",
        note="The downloaded filename contains the historical 'farfatterweb' typo.",
    )
    add_tree(
        m,
        "A",
        "A-06",
        "agreement",
        "retained_source_proxy",
        DOWNLOADS / "oliverkinch_instruct_bt/data/train-00000-of-00001.parquet",
        selector="subset in {dkmedier, odense, danskerhverv}",
        note="Only the three agreement-backed subsets are in scope; contributor-created material is otherwise excluded.",
    )

    # B: Article 3 source-expression boundary.
    add_tree(m, "B", "B-01", "article_3", "audit_evidence", REPO / "legal/registers/dfm9-rlve-prompt-expression-audit.csv")
    for name in ("allenai_verifiable_reasoning_gpt41", "allenai_verifiable_reasoning_o4mini"):
        add_tree(m, "B", "B-01", "article_3", "retained_source_proxy", DOWNLOADS / name)
    gaps.append(Gap("B", "B-01", "Canonical source statement for one unavailable-source RLVE item", "RLVE audit row and retained prompts", "Preserve the gap; recover only from a lawful source snapshot."))

    add_tree(m, "B", "B-02", "article_3", "original", AUDIT_CACHE / "zai-org__LongAlign-10k/long.jsonl")
    add_tree(m, "B", "B-02", "article_3", "audit_evidence", REPO / "legal/registers/dfm9-longalign-content-groups.csv")
    add_tree(m, "B", "B-02", "article_3", "audit_evidence", REPO / "legal/registers/dfm9-longalign-copyright-marker-rows.csv")

    euroblocks = AUDIT_CACHE / "utter-project__EuroBlocks-SFT-Synthetic-1124/data"
    add_tree(m, "B", "B-03", "article_3", "original_embedded_document", euroblocks, selector="source-retaining rows; deduplicate the 2,607 embedded document hashes")
    add_tree(m, "B", "B-03", "article_3", "audit_evidence", REPO / "legal/registers/dfm9-euroblocks-embedded-seed-documents.csv")
    add_tree(m, "B", "B-04", "article_3", "generated_proxy", euroblocks, selector="seed-derived rows without embedded document")
    add_tree(m, "B", "B-04", "article_3", "audit_evidence", REPO / "legal/registers/dfm9-euroblocks-seed-risk.csv")
    gaps.append(Gap("B", "B-04", "Canonical annealing seeds for 134,819 EuroBlocks rows", "Generated EuroBlocks prompt/answer rows", "Obtain seed corpus/IDs from the publisher; do not call the generated proxy original text."))

    rows = inventory_rows()
    tasksource_rows = [row for row in rows if row["audit_bucket"] == "tasksource_residual_research_tdm"]
    if len(tasksource_rows) != 84:
        raise RuntimeError(f"Expected 84 Tasksource residual files, found {len(tasksource_rows)}")
    for row in tasksource_rows:
        add_tree(
            m,
            "B",
            "B-05",
            "article_3",
            "retained_source_proxy",
            DOWNLOADS / "sapient_cleaned/data_clustered/tasksource" / row["filename"],
            selector=f"upstream_repo={row['upstream_repo'] or 'unresolved'}",
        )
    add_tree(m, "B", "B-05", "article_3", "audit_evidence", REPO / "legal/registers/dfm9-sapient-instruction-family-inventory.csv", selector="audit_bucket=tasksource_residual_research_tdm")
    gaps.append(Gap("B", "B-05", "Canonical upstream records for some Tasksource residual files", "84 Sapient materialized files with upstream mappings where known", "Recover per upstream repository and join by source ID/hash."))

    # C: Article 4 source-expression boundary.
    flan_dir = DOWNLOADS / "sapient_cleaned/data_clustered/flan"
    factual = factual_flan_files()
    expected = {"C-01": 72, "C-02": 28, "C-03": 22, "C-04": 8}
    for cohort, count in expected.items():
        if len(factual[cohort]) != count:
            raise RuntimeError(f"Expected {count} factual-FLAN files for {cohort}, found {len(factual[cohort])}")
        for filename in factual[cohort]:
            add_tree(m, "C", cohort, "article_4", "retained_source_proxy", flan_dir / filename)
        gaps.append(Gap("C", cohort, "Canonical upstream source release", f"{count} factual-FLAN materializations", "Recover upstream records and deduplicate prompt templates."))

    family_cohorts = {
        "C-05": ("niv2_", "NIv2"),
        "C-06": ("t0_", "T0/P3"),
        "C-07": ("flan_", "FLAN 2021"),
        "C-08": ("cot_", "CoT"),
    }
    for cohort, (prefix, label) in family_cohorts.items():
        selected = [row for row in rows if row["category"].lower() == "flan" and row["family"].startswith(prefix)]
        for row in selected:
            add_tree(m, "C", cohort, "article_4", "retained_source_proxy", flan_dir / row["filename"])
        gaps.append(Gap("C", cohort, f"Canonical upstream {label} records", f"{len(selected)} Sapient materialized files", "Recover by task/source-row ID; content-hash across templates."))
    add_tree(m, "C", "C-05_C-08", "article_4", "audit_evidence", REPO / "legal/registers/dfm9-sapient-instruction-family-inventory.csv", selector="category=flan")

    add_tree(m, "C", "C-09", "article_4", "mixture_proxy", DOWNLOADS / "allenai_tulu_3_sft_mixture", selector="FLAN v2 Converted component")
    add_tree(m, "C", "C-09", "article_4", "audit_evidence", REPO / "legal/registers/dfm9-tulu3-mixture-component-audit.csv")
    gaps.append(Gap("C", "C-09", "Standalone ai2-adapt-dev/flan_v2_converted source", "Tulu 3 mixture component", "Recover standalone rows and join to C-05 through C-08."))

    add_tree(m, "C", "C-10", "article_4", "mixture_proxy", DOWNLOADS / "allenai_sciriff_train_mix", selector="SciRIFF half of the mixed parquet")
    add_tree(m, "C", "C-10", "article_4", "audit_evidence", REPO / "legal/registers/dfm9-tulu-v2-sciriff-if-sft-component-audit.csv")
    gaps.append(Gap("C", "C-10", "Canonical papers/passages keyed by SciRIFF paper ID", "SciRIFF Train Mix retained rows", "Resolve paper IDs to lawful source copies and preserve per-paper licence."))

    openhermes = REPO / "export-upload-dfm8-openhermes-repaired/dfm8-openhermes-en"
    openhermes_selectors = {
        "C-11": "openhermes_source=airoboros2.2",
        "C-12": "openhermes_source=caseus_custom",
        "C-13": "openhermes_source=cot_alpaca_gpt4",
        "C-14": "openhermes_source=platypus; residual uncovered rows only",
    }
    for cohort, selector in openhermes_selectors.items():
        add_tree(m, "C", cohort, "article_4", "retained_source_proxy", openhermes, selector=selector)
    add_tree(m, "C", "C-11_C-14", "article_4", "audit_evidence", REPO / "legal/registers/dfm9-openhermes-component-audit.csv")
    gaps.append(Gap("C", "C-11_C-14", "Raw Airoboros/Caseus/CoT-Alpaca/residual Platypus source records", "Modernized retained English OpenHermes prompts", "Recover originals where possible; raw OpenHermes is intentionally absent from the training pipeline."))

    # D: revised non-Article-3/4 cohorts. Explicitly excluded source families
    # are intentionally absent here; see the report's 2026-08-18 scope note.
    add_tree(m, "D", "D-01", "participant_permission", "retained_source_proxy", DOWNLOADS / "synquid_wildchat_100k_qwen_messages", selector="human WildChat prompts only", note="Synquid-authored response material is excluded; this proxy locates underlying participant prompts.")
    add_tree(m, "D", "D-01", "participant_permission", "audit_evidence", REPO / "legal/registers/dfm9-wildchat-personal-data-audit.csv")

    add_tree(m, "D", "D-02", "participant_publication", "retained_source_proxy", AUDIT_CACHE / "dr-tulu-sft-data.train.jsonl", selector="ShareGPT component")
    add_tree(m, "D", "D-02", "participant_publication", "audit_evidence", REPO / "legal/registers/dfm9-tulu-v2-sciriff-if-sft-component-audit.csv")

    add_tree(m, "D", "D-03", "open_licence_and_participant_controls", "original_or_near_original", DOWNLOADS / "ai_arena_udtraek", note="Direct DFM extraction; contributor-authored derivatives are excluded.")

    add_tree(m, "D", "D-04", "manual_low_risk", "retained_source_proxy", DOWNLOADS / "dolci_instruct_sft_tool_use")
    for path in (
        AUDIT_CACHE / "openscilm_queries.jsonl",
        AUDIT_CACHE / "taskcraft.multihop_subtask_trace.jsonl",
        AUDIT_CACHE / "taskcraft.pure_qa.jsonl",
        AUDIT_CACHE / "webwalkerqa-main.jsonl",
        AUDIT_CACHE / "webwalkerqa-silver.jsonl",
    ):
        add_tree(m, "D", "D-04", "manual_low_risk", "upstream_source", path)
    add_tree(m, "D", "D-04", "manual_low_risk", "audit_evidence", REPO / "legal/registers/dfm9-dolci-toolu-component-audit.csv")

    add_tree(m, "D", "D-05", "manual_residual_risk", "mixture_proxy", DOWNLOADS / "dfm_dyna_instruct/data/apertus-sft-mixture/apertus-sft-mixture.parquet", selector="open-r1/Mixture-of-Thoughts rows")
    add_tree(m, "D", "D-05", "manual_residual_risk", "audit_evidence", REPO / "legal/registers/dfm9-mot-expression-risk.csv")
    gaps.append(Gap("D", "D-05", "Standalone open-r1/Mixture-of-Thoughts rows and canonical linked problem/editorial records", "Apertus mixture materialization", "Recover source IDs before canonical extraction tests."))

    add_tree(m, "D", "D-06", "manual_database_selection", "original_or_near_original", DOWNLOADS / "sapient_cleaned/data_clustered/sudoku_extreme/all.parquet")

    trivia = factual["D-07"]
    for filename in trivia:
        add_tree(m, "D", "D-07", "publisher_apache_representation", "retained_source_proxy", flan_dir / filename)
    for name in ("dfm9-triviaqa-source-rights.csv", "dfm9-triviaqa-source-grouping.json", "dfm9-triviaqa-current-reservation-probe.json"):
        add_tree(m, "D", "D-07", "publisher_apache_representation", "audit_evidence", REPO / "legal/registers" / name)
    gaps.append(Gap("D", "D-07", "Standalone canonical TriviaQA records", f"{len(trivia)} factual-FLAN materializations", "Recover and group canonical questions by question_source."))

    synth_paths = sorted(path for path in (REPO / "export-upload").glob("sapient-synth-*") if path.is_dir())
    if len(synth_paths) != 70:
        raise RuntimeError(f"Expected 70 sapient-synth dataset directories, found {len(synth_paths)}")
    for path in synth_paths:
        add_tree(m, "D", "D-08", "project_generated_manual_acceptance", "generated_training_source", path)

    for name in (
        "no_robots",
        "kobprof_skolegpt_instruct",
        "textbook_reasoning",
        "allenai_tulu_3_personas_algebra",
        "allenai_tulu_3_personas_code",
        "allenai_tulu_3_personas_if",
        "allenai_tulu_3_personas_math",
    ):
        add_tree(m, "D", "D-09", "direct_noncommercial_terms", "dataset_source", DOWNLOADS / name)

    for name in (
        "openmathinstruct2",
        "openthoughts2_1m",
        "allenai_big_reasoning_traces",
        "allenai_open_math_2_50k_r1",
        "allenai_code_meta_reasoning",
        "natural_reasoning",
        "numinamath_1_5",
        "omni_math",
        "hendrycks_math",
        "nemotron_agentic",
        "nemotron_multilingual",
        "toolace",
        "glaive_function_calling_v2",
        "xlam_function_calling_60k",
    ):
        add_tree(m, "D", "D-10", "direct_dataset_terms", "dataset_source", DOWNLOADS / name)
    gaps.append(Gap("D", "D-10", "Standalone local nvidia/AceReason-1.1-SFT source", "Tokenized/sampled DFM9 exposure only", "Recover the pinned dataset revision before testing AceReason source-text extraction."))

    return m, gaps


def safe_name(path: Path) -> str:
    try:
        label = str(path.relative_to(REPO))
    except ValueError:
        label = str(path).lstrip("/")
    return re.sub(r"[^A-Za-z0-9._-]+", "__", label)


def assemble(output: Path, force: bool) -> None:
    if output.exists():
        if not force:
            raise SystemExit(f"Output exists: {output}. Use --force to rebuild it.")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    materials, gaps = build_inventory()
    manifest_rows: list[dict[str, object]] = []
    seen_destinations: set[Path] = set()
    for item in materials:
        cohort_dir = output / item.category / item.cohort
        cohort_dir.mkdir(parents=True, exist_ok=True)
        destination = cohort_dir / safe_name(item.path)
        suffix = 2
        while destination in seen_destinations:
            destination = cohort_dir / f"{safe_name(item.path)}__{suffix}"
            suffix += 1
        seen_destinations.add(destination)
        destination.symlink_to(item.path.resolve(), target_is_directory=item.path.is_dir())
        manifest_rows.append(
            {
                "category": item.category,
                "cohort": item.cohort,
                "basis": item.basis,
                "material_role": item.role,
                "selector": item.selector,
                "source_path": str(item.path.resolve()),
                "assembled_path": str(destination.relative_to(output)),
                "source_kind": "directory" if item.path.is_dir() else "file",
                "size_bytes": "" if item.path.is_dir() else item.path.stat().st_size,
                "note": item.note,
            }
        )

    with (output / "manifest.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(manifest_rows)

    with (output / "gaps.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(Gap.__dataclass_fields__), delimiter="\t")
        writer.writeheader()
        writer.writerows(gap.__dict__ for gap in gaps)

    counts: dict[str, int] = {}
    for item in materials:
        counts[item.category] = counts.get(item.category, 0) + 1
    readme = "# DFM9 memorisation source material\n\n"
    readme += "Generated by `scripts/assemble_dfm9_memorisation_sources.py`. Data entries are symlinks; no bulk source data is copied.\n\n"
    readme += "- `manifest.tsv` labels each artifact as original, proxy, mixture proxy, generated source, or audit evidence and records any row selector.\n"
    readme += "- `gaps.tsv` records original source material that is not available locally.\n"
    readme += "- Category directories correspond to agreement (A), Article 3 (B), Article 4 (C), and revised other-basis (D) cohorts.\n"
    readme += "- The exclusions in the legal report are deliberately absent. A-06 remains because it is agreement-backed.\n\n"
    readme += "Artifact links by category: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)) + ".\n"
    (output / "README.md").write_text(readme, encoding="utf-8")

    print(f"Output: {output}")
    print(f"Material links: {len(materials)} ({', '.join(f'{key}={counts[key]}' for key in sorted(counts))})")
    print(f"Recorded gaps: {len(gaps)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    assemble(args.output.resolve(), args.force)


if __name__ == "__main__":
    main()
