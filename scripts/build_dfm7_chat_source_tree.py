#!/usr/bin/env python3
"""Build a DFM7 chat-tokenization source tree.

DFM7 extends DFM6 with broader Danish instruction/chat/math sources. The output
is a symlink tree intended for `scripts/tokenize_chat_template.py`.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DFM6_DIRECT_FILTERED_PREFIXES = (
    "sapient_cleaned",
    "nemotron_agentic",
    "nemotron_swe",
    "nemotron_instruction_reasoning_off",
    "nemotron_multilingual",
    "dolci_instruct_sft",
    "dolci_instruct_sft_no_tools",
    "dolci_instruct_sft_tool_use",
    "dolci_instruct_sft_tool_use_sa",
    "allenai_rlvr_gsm",
    "allenai_rlvr_math",
    "allenai_open_math_2_50k_r1",
    "allenai_tulu_3_personas_code",
    "allenai_tulu_3_personas_math",
    "allenai_tulu_3_personas_if",
    "allenai_tulu_3_personas_algebra",
    "allenai_big_reasoning_traces",
    "allenai_if_sft_verified",
    "allenai_sciriff_train_mix",
    "allenai_tulu_3_sft_mixture",
    "allenai_tulu_v2_sft_mixture",
    "allenai_tulu_v2_sft_long_mixture",
    "allenai_verifiable_reasoning_gpt41",
    "allenai_verifiable_reasoning_o4mini",
    "no_robots",
    "synquid_wildchat_100k_qwen_messages",
)

DFM7_DIRECT_FILTERED_PREFIXES = (
    "dfm_dyna_instruct",
    "ai_arenaen_conversations",
    "kaenguruen",
    "oliverkinch_danish_qa",
    "oliverkinch_danish_summarization",
    "oliverkinch_da_instruct_dynaword",
    "oliverkinch_da_instruct_dynaword_hq",
    "oliverkinch_da_instruct_dynaword_contemporary",
    "oliverkinch_da_instruct_dynaword_contemporary_hq",
    "oliverkinch_autodata_da_sft",
)


DFM6_CONVERTED_FALLBACK_PREFIXES = (
    "dbc",
    "laerebogen_with_followups",
    "lexdk",
    "opus",
    "oliverkinch_",
    "synquid_danish_verifiable_reasoning",
    "synquid_ifbench_train",
    "synquid_mt_da_deepseek",
    "synquid_translation_100k",
    "synquid_wiki_instruct_da",
    "openmathinstruct2",
    "acereason",
    "openthoughts2",
)


DFM6_EXTRA_SOURCE_ROOTS = (
    Path("data/converted_sources_dfm4_summarization"),
    Path("export-upload"),
)

DFM7_EXTRA_SOURCE_ROOTS = (
    Path("data/dfm7_special_sources"),
)

DFM7_EXCLUDED_DIRECT_FILES = {
    Path("dfm_dyna_instruct/data/apertus-sft-mixture/apertus-sft-mixture.parquet"),
}

DFM7_SHARD_REPLACEMENTS = {
    "dfm_dyna_instruct": (
        Path("data/dfm7_special_sources/dfm_dyna_instruct_apertus_sft_mixture_shards"),
        Path("data/apertus-sft-mixture-shards"),
    ),
}

DFM7_EXTRA_ROOT_EXCLUDED_DIRS = {
    Path("data/dfm7_special_sources"): {
        "dfm_dyna_instruct_apertus_sft_mixture_shards",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filtered-root", type=Path, default=Path("data/filtered_sources"))
    parser.add_argument("--download-root", type=Path, default=Path("data/downloads/datasets"))
    parser.add_argument("--converted-root", type=Path, default=Path("data/converted_sources"))
    parser.add_argument("--output", type=Path, default=Path("data/dfm7_chat_sources"))
    parser.add_argument("--new-only", action="store_true", help="Only link DFM7 additions; reuse data/tokenized_dfm6 for inherited sources.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def link_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(dst)
    dst.symlink_to(src.resolve(), target_is_directory=src.is_dir())


def link_filtered_tree(src: Path, dst: Path, excluded_rel_paths: set[Path]) -> int:
    linked = 0
    for path in sorted(src.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        if rel in excluded_rel_paths:
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(path.resolve())
        linked += 1
    return linked


def link_filtered_root(src: Path, dst: Path, excluded_top_dirs: set[str]) -> int:
    linked = 0
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if rel.parts and rel.parts[0] in excluded_top_dirs:
            continue
        if path.is_dir():
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(path.resolve())
        linked += 1
    return linked


def source_dirs(root: Path, prefixes: tuple[str, ...]) -> list[Path]:
    if not root.exists():
        return []
    return [child for child in sorted(root.iterdir()) if child.name.startswith(prefixes)]


def main() -> None:
    args = parse_args()
    if args.output.exists():
        if not args.force:
            raise SystemExit(f"{args.output} exists; pass --force to rebuild")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    manifest: dict[str, object] = {
        "output": str(args.output),
        "new_only": args.new_only,
        "direct_filtered_prefixes": list(
            DFM7_DIRECT_FILTERED_PREFIXES
            if args.new_only
            else DFM6_DIRECT_FILTERED_PREFIXES + DFM7_DIRECT_FILTERED_PREFIXES
        ),
        "converted_fallback_prefixes": list(() if args.new_only else DFM6_CONVERTED_FALLBACK_PREFIXES),
        "extra_source_roots": [
            str(p)
            for p in (
                DFM7_EXTRA_SOURCE_ROOTS
                if args.new_only
                else DFM6_EXTRA_SOURCE_ROOTS + DFM7_EXTRA_SOURCE_ROOTS
            )
        ],
        "linked": [],
    }
    linked = manifest["linked"]
    assert isinstance(linked, list)

    direct_prefixes = (
        DFM7_DIRECT_FILTERED_PREFIXES
        if args.new_only
        else DFM6_DIRECT_FILTERED_PREFIXES + DFM7_DIRECT_FILTERED_PREFIXES
    )
    for root, mode in ((args.filtered_root, "direct_filtered"), (args.download_root, "direct_download")):
        for src in source_dirs(root, direct_prefixes):
            dst = args.output / src.name
            if dst.exists() or dst.is_symlink():
                continue
            excluded = {
                path.relative_to(src.name)
                for path in DFM7_EXCLUDED_DIRECT_FILES
                if path.parts and path.parts[0] == src.name
            }
            replacement = DFM7_SHARD_REPLACEMENTS.get(src.name)
            if excluded or replacement is not None:
                dst.mkdir(parents=True)
                linked_files = link_filtered_tree(src, dst, excluded)
                linked.append(
                    {
                        "mode": f"{mode}_filtered_tree",
                        "src": str(src),
                        "dst": str(dst),
                        "excluded": [str(path) for path in sorted(excluded)],
                        "linked_files": linked_files,
                    }
                )
                if replacement is not None:
                    replacement_src, replacement_dst_rel = replacement
                    if replacement_src.exists():
                        replacement_dst = dst / replacement_dst_rel
                        link_tree(replacement_src, replacement_dst)
                        linked.append(
                            {
                                "mode": "large_parquet_shards",
                                "src": str(replacement_src),
                                "dst": str(replacement_dst),
                            }
                        )
            else:
                link_tree(src, dst)
                linked.append({"mode": mode, "src": str(src), "dst": str(dst)})

    converted_prefixes = () if args.new_only else DFM6_CONVERTED_FALLBACK_PREFIXES
    for src in source_dirs(args.converted_root, converted_prefixes):
            dst = args.output / src.name
            if dst.exists() or dst.is_symlink():
                continue
            link_tree(src, dst)
            linked.append({"mode": "converted_fallback", "src": str(src), "dst": str(dst)})

    extra_roots = DFM7_EXTRA_SOURCE_ROOTS if args.new_only else DFM6_EXTRA_SOURCE_ROOTS + DFM7_EXTRA_SOURCE_ROOTS
    for root in extra_roots:
        if not root.exists():
            continue
        dst = args.output / root.name
        excluded_top_dirs = DFM7_EXTRA_ROOT_EXCLUDED_DIRS.get(root, set())
        if excluded_top_dirs:
            dst.mkdir(parents=True)
            linked_files = link_filtered_root(root, dst, excluded_top_dirs)
            linked.append(
                {
                    "mode": "extra_root_filtered_tree",
                    "src": str(root),
                    "dst": str(dst),
                    "excluded_top_dirs": sorted(excluded_top_dirs),
                    "linked_files": linked_files,
                }
            )
        else:
            link_tree(root, dst)
            linked.append({"mode": "extra_root", "src": str(root), "dst": str(dst)})

    (args.output / "dfm7_chat_source_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)
    )
    print(
        json.dumps(
            {k: v for k, v in manifest.items() if k != "linked"} | {"linked_count": len(linked)},
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
