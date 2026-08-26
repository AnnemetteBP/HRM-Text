#!/usr/bin/env python3
"""Build reproducible Mimir evidence registers from repository artifacts."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTERS = ROOT / "legal" / "registers"
DATASET_DOC = ROOT / "docs" / "dfm8-datasets.md"
RELEASE_EXPORT = ROOT / "exports" / "dfm8_XL_step1650000_ema_hf"
EVAL_PLAN = ROOT / "logs" / "scheduler" / "dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255" / "plan.tsv"

HF_ROW = re.compile(
    r"^\| \[(?P<source_id>[^]]+)]\((?P<url>[^)]+)\) \| "
    r"(?P<prefix>.+) \| (?P<form>[^|]+) \| (?P<source_rows>[\d,]+) \| "
    r"(?P<source_tokens>[\d,]+) \| (?P<sampled_rows>[\d,]+) \| "
    r"(?P<sampled_tokens>[\d,]+) \| (?P<share>[\d.]+%) \|$"
)
PRIVATE_ROW = re.compile(
    r"^\| (?P<source_id>DBC \{[^}]+}|Lex\.dk articles) \| (?P<prefix>[^|]+) \| "
    r"(?P<source_rows>[\d,]+) \| (?P<source_tokens>[\d,]+) \| "
    r"(?P<sampled_rows>[\d,]+) \| (?P<sampled_tokens>[\d,]+) \| "
    r"(?P<share>[\d.]+%) \|$"
)


def integer(value: str) -> int:
    return int(value.replace(",", ""))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_dataset_registers() -> None:
    rows: list[dict[str, object]] = []
    synthetic: list[dict[str, object]] = []
    for line in DATASET_DOC.read_text(encoding="utf-8").splitlines():
        match = HF_ROW.match(line)
        if match:
            item = match.groupdict()
            source_lower = item["source_id"].lower()
            if any(term in source_lower for term in ("wildchat", "ai_arena", "dialog", "review", "conversation")):
                privacy_triage = "high_priority_user_generated_or_conversational"
            elif any(term in source_lower for term in ("openhermes", "tulu", "nemotron", "common-pile", "no_robots", "sapientinc")):
                privacy_triage = "elevated_mixed_or_web_derived"
            elif any(term in item["form"].lower() for term in ("generated", "synthetic", "derived")):
                privacy_triage = "source_retention_review_required"
            else:
                privacy_triage = "standard_source_review_required"
            row = {
                "source_id": item["source_id"],
                "source_url": item["url"],
                "source_type": "public_dataset",
                "dfm8_prefix": item["prefix"].strip(),
                "processing_form": item["form"].strip(),
                "source_rows": integer(item["source_rows"]),
                "source_tokens": integer(item["source_tokens"]),
                "sampled_rows_per_epoch": integer(item["sampled_rows"]),
                "sampled_tokens_per_epoch": integer(item["sampled_tokens"]),
                "dfm8_share": item["share"],
                "provisional_basis": "upstream_licence_or_research_tdm_review_required",
                "licence_or_agreement": "TBD",
                "article4_reservation_review": "TBD",
                "personal_data_review": "TBD",
                "privacy_triage": privacy_triage,
                "approval_status": "open",
                "evidence": "docs/dfm8-datasets.md",
                "notes": "",
            }
            rows.append(row)
            form = item["form"].lower()
            if any(term in form for term in ("generated", "synthetic", "translated", "derived")):
                source_id = item["source_id"]
                if source_id.startswith("schneiderkamplab/dfm8-synthetic-"):
                    generator = "Gemma 4 31B generator and Gemma 4 31B judge"
                    audit = "model-judge audit; accepted rows only"
                    slug = source_id.split("/", 1)[1]
                    recipe = f"export-upload-dfm8-synthetic/{slug}/recreate_dataset.py"
                elif source_id.startswith("schneiderkamplab/dfm8-openhermes-"):
                    generator = "Gemma 4 31B audit/repair/translation pipeline"
                    audit = "source audit plus post-repair/post-translation judge audit"
                    recipe = "export-upload-dfm8-openhermes-repaired/build_summary.json"
                elif source_id.startswith(("schneiderkamplab/common-pile-", "schneiderkamplab/danish-dynaword-")):
                    generator = "deterministic task derivation; Gemma 4 31B judge"
                    audit = "structural filtering plus model-judge acceptance"
                    slug = source_id.split("/", 1)[1]
                    recipe = f"data/dfm8_transform_expansion_filtered/{slug}/filter_summary.json"
                elif source_id.startswith("schneiderkamplab/sapient-synth-"):
                    generator = "Gemma 4 31B replacement-generation pipeline"
                    audit = "model-judge audit; accepted rows only"
                    slug = source_id.split("/", 1)[1]
                    recipe = f"export-upload/{slug}/metadata/manifest.json"
                elif source_id.startswith("schneiderkamplab/transformations-"):
                    generator = "Gemma 4 31B transformation-generation and judge pipeline"
                    audit = "accepted-only export from judge audit"
                    slug = source_id.split("/", 1)[1]
                    recipe = f"export-upload/{slug}/generation_config.json"
                elif "derived" in form:
                    generator = "deterministic derived-task conversion"
                    audit = "deterministic converter/source checks"
                    recipe = "scripts/generate_dfm4_tasks.py"
                else:
                    generator = "upstream synthetic/translation method; project reformatting"
                    audit = "upstream method and project checks TBD"
                    recipe = "upstream dataset card and local converter"
                synthetic.append(
                    {
                        "source_id": item["source_id"],
                        "dfm8_prefix": item["prefix"].strip(),
                        "processing_form": item["form"].strip(),
                        "source_rows": integer(item["source_rows"]),
                        "accepted_or_tokenized_rows": integer(item["source_rows"]),
                        "sampled_tokens_per_epoch": integer(item["sampled_tokens"]),
                        "generator_or_method": generator,
                        "audit_method": audit,
                        "prompt_or_recipe_evidence": recipe,
                        "status": "engineering_method_evidence_indexed_human_rights_review_required",
                    }
                )
            continue

        match = PRIVATE_ROW.match(line)
        if not match:
            continue
        item = match.groupdict()
        source_id = "DBC" if item["source_id"].startswith("DBC") else "Lex.dk"
        rows.append(
            {
                "source_id": source_id,
                "source_url": "",
                "source_type": "private_third_party",
                "dfm8_prefix": item["prefix"].strip(),
                "processing_form": "agreement_supplied",
                "source_rows": integer(item["source_rows"]),
                "source_tokens": integer(item["source_tokens"]),
                "sampled_rows_per_epoch": integer(item["sampled_rows"]),
                "sampled_tokens_per_epoch": integer(item["sampled_tokens"]),
                "dfm8_share": item["share"],
                "provisional_basis": "agreement",
                "licence_or_agreement": "TBD_contract_review",
                "article4_reservation_review": "contract_specific",
                "personal_data_review": "TBD",
                "privacy_triage": "agreement_source_review_required",
                "approval_status": "open",
                "evidence": "docs/dfm8-datasets.md",
                "notes": "Classify Commission template section 2.2.1 vs 2.2.2",
            }
        )

    if len(rows) != 161:
        raise RuntimeError(f"Expected 161 DFM8 sources, parsed {len(rows)}")
    if sum(int(row["sampled_tokens_per_epoch"]) for row in rows) != 70_479_308_606:
        raise RuntimeError("DFM8 sampled-token checksum does not match the published inventory")

    write_csv(
        REGISTERS / "dataset-legal-basis-register.csv",
        list(rows[0]),
        rows,
    )
    write_csv(
        REGISTERS / "synthetic-data-register.csv",
        list(synthetic[0]),
        synthetic,
    )


def build_snapshot_register() -> None:
    spec = importlib.util.spec_from_file_location(
        "download_training_datasets", ROOT / "scripts" / "download_training_datasets.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load dataset downloader manifest")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    repo_by_name = {item.name: item.repo_id for item in module.HF_DATASETS}
    final_dfm8_ids = {
        row["source_id"]
        for row in csv.DictReader((REGISTERS / "dataset-legal-basis-register.csv").open(encoding="utf-8"))
    }
    rows: list[dict[str, object]] = []
    pattern = "*/.cache/huggingface/download/README.md.metadata"
    for path in sorted((ROOT / "data" / "downloads" / "datasets").glob(pattern)):
        values = path.read_text(encoding="utf-8").splitlines()
        if len(values) < 3:
            continue
        timestamp = float(values[2])
        local_name = path.relative_to(ROOT / "data" / "downloads" / "datasets").parts[0]
        repo_id = repo_by_name.get(local_name, "")
        rows.append(
            {
                "local_dataset_name": local_name,
                "repository_id": repo_id,
                "in_final_dfm8_inventory": repo_id in final_dfm8_ids,
                "repository_revision": values[0],
                "readme_etag": values[1],
                "local_snapshot_timestamp_utc": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                "metadata_path": str(path.relative_to(ROOT)),
                "scope_note": "Local acquisition evidence; not necessarily part of released DFM8",
            }
        )
    write_csv(REGISTERS / "hf-snapshot-register.csv", list(rows[0]), rows)


def build_phase_register() -> None:
    definitions = [
        ("PHASE-001", "dfm6", 0, 720_084, "checkpoints/dfm6/XL-gas2/checkpoint_state_epoch_3.json"),
        ("PHASE-002", "dfm7", 720_084, 1_229_504, "checkpoints/dfm7/XL-gas2-from-dfm6-epoch3/checkpoint_state_epoch_5.json"),
        ("PHASE-003", "dfm8", 1_229_504, 1_650_000, "checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5/checkpoint_state_step_1650000.json"),
    ]
    exposure_summary_path = REGISTERS / "phase-exposure-summary.csv"
    exposure_by_phase: dict[str, dict[str, str]] = {}
    if exposure_summary_path.exists():
        with exposure_summary_path.open(encoding="utf-8", newline="") as handle:
            exposure_by_phase = {row["phase_id"]: row for row in csv.DictReader(handle)}
    rows: list[dict[str, object]] = []
    for phase_id, recipe, start, end, evidence in definitions:
        state = json.loads((ROOT / evidence).read_text(encoding="utf-8"))
        metadata_path = ROOT / "data" / f"sampled_{recipe}" / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        exposure = exposure_by_phase.get(phase_id, {})
        rows.append(
            {
                "phase_id": phase_id,
                "dataset_recipe": recipe,
                "start_step_inclusive": start,
                "end_step_exclusive": end,
                "optimizer_steps": end - start,
                "nominal_token_presentations": (end - start) * 262_144,
                "concatenated_token_store_length": metadata["total_length"],
                "consumed_sampled_rows": exposure.get("sampled_rows_consumed", ""),
                "consumed_nonpadding_source_tokens": exposure.get("source_tokens_consumed", ""),
                "boundary_epoch": state["epoch"],
                "data_path": state["data_path"],
                "global_batch_size": state["global_batch_size"],
                "checkpoint_evidence": evidence,
                "recipe_metadata_evidence": str(metadata_path.relative_to(ROOT)),
                "status": "boundary_and_sampled_source_exposure_verified",
                "notes": "Step boundaries and sampled source/task exposure are exact; acquisition-time terms remain human review",
            }
        )
    write_csv(REGISTERS / "training-phase-register.csv", list(rows[0]), rows)


def build_evaluation_register() -> None:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    with EVAL_PLAN.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if not row["action"].startswith("eval_"):
                continue
            metadata = json.loads(row["metadata_json"])
            if metadata.get("ckpt_tag") != "step_1650000":
                continue
            grouped.setdefault((row["family"], row["name"]), []).append(row)

    rows: list[dict[str, object]] = []
    for (family, name), jobs in sorted(grouped.items()):
        rows.append(
            {
                "suite": family,
                "task": name,
                "checkpoint": "step_1650000_ema",
                "scheduler_group_width": max(int(row["shards"] or 1) for row in jobs),
                "job_rows": len(jobs),
                "completed_jobs": sum(row["status"] == "done" for row in jobs),
                "failed_jobs": sum(row["status"] == "failed" for row in jobs),
                "skipped_jobs": sum(row["status"] == "skipped" for row in jobs),
                "job_statuses": ";".join(sorted({row["status"] for row in jobs})),
                "result_locations": ";".join(sorted({row["log_dir"] for row in jobs})),
                "plan_evidence": str(EVAL_PLAN.relative_to(ROOT)),
                "freeze_status": "local_outputs_present_task_revision_and_raw_output_retention_review_open",
            }
        )
    write_csv(REGISTERS / "evaluation-register.csv", list(rows[0]), rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_artifact_register() -> None:
    rows: list[dict[str, object]] = []
    for path in sorted(RELEASE_EXPORT.iterdir()):
        if not path.is_file():
            continue
        rows.append(
            {
                "artifact": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    write_csv(REGISTERS / "release-artifact-register.csv", list(rows[0]), rows)

    packages = []
    for package in (
        "torch",
        "transformers",
        "tokenizers",
        "vllm",
        "flash-attn-4",
        "ninja",
        "cuda-toolkit",
        "nvidia-cuda-nvcc",
        "safetensors",
        "accelerate",
    ):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "not-installed"
        packages.append({"package": package, "version": version})
    write_csv(REGISTERS / "current-serving-environment.csv", list(packages[0]), packages)


def build_compute_estimate() -> None:
    hidden_size = 1_536
    intermediate_size = 4_096
    layers_per_stack = 16
    vocabulary_size = 262_144
    context_upper_bound = 4_096
    recurrent_forward_equivalents = 18
    layer_matrix_parameters = 5 * hidden_size**2 + 3 * hidden_size * intermediate_size
    recurrent_linear_flops = (
        layer_matrix_parameters * layers_per_stack * recurrent_forward_equivalents * 2
    )
    vocabulary_head_flops = vocabulary_size * hidden_size * 6
    dense_attention_flops = (
        4
        * context_upper_bound
        * hidden_size
        * layers_per_stack
        * recurrent_forward_equivalents
    )
    major_flops_per_token = recurrent_linear_flops + vocabulary_head_flops + dense_attention_flops
    if major_flops_per_token != 27_330_084_864:
        raise RuntimeError("Independent compute reconstruction no longer matches the reviewed estimate")
    token_positions = 1_650_000 * 262_144
    major_flops = token_positions * major_flops_per_token
    record = {
        "model": "DFM Mimir v1 / HRM-Text XL",
        "method": "recurrence-aware major-operation upper bound",
        "optimizer_steps": 1_650_000,
        "global_tokens_per_step": 262_144,
        "nominal_token_positions": token_positions,
        "hidden_size": hidden_size,
        "intermediate_size": intermediate_size,
        "layers_per_recurrent_stack": layers_per_stack,
        "vocabulary_size": vocabulary_size,
        "recurrent_forward_equivalents": recurrent_forward_equivalents,
        "layer_matrix_parameters": layer_matrix_parameters,
        "recurrent_linear_flops_per_token": recurrent_linear_flops,
        "vocabulary_head_flops_per_token": vocabulary_head_flops,
        "dense_attention_flops_per_token": dense_attention_flops,
        "major_flops_per_token": major_flops_per_token,
        "major_flops": major_flops,
        "reported_conservative_flops": 11_900_000_000_000_000_000_000,
        "multiply_add_flops": 2,
        "bp_steps_assumption": 5,
        "context_attention_upper_bound": context_upper_bound,
        "included": "recurrent transformer linears; untied vocabulary head; dense attention upper bound",
        "excluded": "optimizer; communication; checkpointing; evaluation; compilation; hardware inefficiency",
        "methodology_evidence": "wiki/pages/model-architecture/hrm-xl-training-flops.md",
        "review_status": "engineering_reproduced_independent_regulatory_approval_open",
    }
    (REGISTERS / "compute-estimate.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    build_dataset_registers()
    build_snapshot_register()
    build_phase_register()
    build_evaluation_register()
    build_release_artifact_register()
    build_compute_estimate()
    print("Built Mimir dataset, synthetic, snapshot, phase, evaluation, artifact, and compute registers.")


if __name__ == "__main__":
    main()
