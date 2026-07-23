#!/usr/bin/env python3
"""Build a filtered tokenized union for the DFM8-post mix.

The sampler includes unmatched task directories with default repeat=1, so the
post-training mix must point at a filtered tokenized tree rather than directly
at the full DFM8 tokenized tree.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


FOCUS_PREFIXES = [
    # DFM8-specific synthetic behavior data. These may only appear after the
    # OpenHermes/targeted-synthetic uploads have been integrated and tokenized.
    "dfm8-synthetic-native-tool-calling__",
    "dfm8-synthetic-constrained-format-following__",
    "dfm8-synthetic-multiturn-danish-english-chat__",
    "dfm8-synthetic-danish-summarization-rewrite-controls__",
    "dfm8-openhermes-en__",
    "dfm8-openhermes-da__",
    # Native tool-use and agentic SFT.
    "dolci_native_tool_use__",
    "glaive_native_tool_use__",
    "toolace_native_tool_use__",
    "xlam_native_tool_use__",
    "nemotron_agentic__",
    "nemotron_instruction_reasoning_off__",
    # Instruction and constraint following.
    "allenai_if_sft_verified__",
    "allenai_if_multi_constraints_upto5__",
    "allenai_rlvr_ifeval__",
    "no_robots__",
    "no_robots.jsonl",
    "synquid_ifbench_train__",
    # Danish chat, QA, summary, and instruction control.
    "kobprof_skolegpt_instruct__",
    "ai_arenaen_conversations__",
    "ai_arena_udtraek__",
    "kaenguruen__",
    "laerebogen_with_followups__",
    "lexdk__",
    "dbc__dbc-faktalink",
    "dbc__dbc-farfatterweb",
    "dbc__dbc-abstracts_",
    "dbc__dbc-reviews",
    "synquid_wiki_instruct_da__",
    "synquid_danish_verifiable_reasoning",
    "oliverkinch_instruct_bt__",
    "oliverkinch_multi_wiki_qa_high_quality__",
    "oliverkinch_danish_qa__",
    "oliverkinch_danish_summarization__",
    "oliverkinch_autodata_da_sft__",
    "oliverkinch_da_instruct_dynaword__",
    "oliverkinch_da_instruct_dynaword_hq__",
    "oliverkinch_da_instruct_dynaword_contemporary__",
    "oliverkinch_da_instruct_dynaword_contemporary_hq__",
    "oliverkinch_eur_lex_sum_instruct__",
    "oliverkinch_dst_table_prompts_bt__",
    "oliverkinch_tidsskrift_dk_bt__",
    "oliverkinch_dynaword_bt__",
    "oliverkinch_danish_university_portals_bt__",
    "oliverkinch_danmarks_statistik_bt__",
    "oliverkinch_doab_da_bt__",
    "oliverkinch_eur_lex_bt__",
    # Summarization/control anchors already used in DFM4/5+ eval work.
    "dfm4_govreport_summarization__",
    "dfm4_wiki_cat_sum_summarization__",
    "dfm4_arxiv_paper_summarization__",
    "dfm4_laion_scientific_summaries__",
]


BROAD_ANCHOR_PREFIXES = [
    # Keep roughly 20% broad anchors for regression control, but avoid raw
    # continuation and huge transform families in the post-training phase.
    "dfm8-synthetic-strict-math-answer-contract__",
    "dfm8-synthetic-code-debugging__",
    "openmathinstruct2__",
    "allenai_rlvr_gsm__",
    "allenai_rlvr_math__",
    "allenai_open_math_2_50k_r1__",
    "allenai_tulu_3_personas_code__",
    "allenai_tulu_3_personas_math__",
    "allenai_tulu_3_personas_algebra__",
    "allenai_tulu_3_sft_mixture__",
    "dolci_instruct_sft_no_tools__",
    "dolci_instruct_sft__",
    "Platypus__",
    "gsm8k_train.jsonl",
    "math_train.jsonl",
    "webinstruct_verified.jsonl",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/tokenized_dfm8"))
    parser.add_argument("--output", type=Path, default=Path("data/tokenized_dfm8_post"))
    parser.add_argument("--prefix", action="append", dest="extra_prefixes", default=[])
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def task_dirs(root: Path) -> list[Path]:
    tasks: list[Path] = []
    if not root.exists():
        return tasks
    for dirpath, _, filenames in os.walk(root, followlinks=True):
        if "metadata.json" in filenames:
            tasks.append(Path(dirpath))
    return sorted(tasks)


def task_name(src: Path, root: Path) -> str:
    return "__".join(src.relative_to(root).parts)


def link_task(src: Path, src_root: Path, dst_root: Path) -> None:
    rel = src.relative_to(src_root)
    dst = dst_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(dst)
    dst.symlink_to(src.resolve(), target_is_directory=True)


def main() -> None:
    args = parse_args()
    prefixes = tuple(FOCUS_PREFIXES + BROAD_ANCHOR_PREFIXES + list(args.extra_prefixes))

    if args.output.exists():
        if not args.force:
            raise SystemExit(f"{args.output} exists; pass --force to rebuild")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    tokenizer_info = args.root / "tokenizer_info.json"
    if not tokenizer_info.exists():
        raise FileNotFoundError(tokenizer_info)
    (args.output / "tokenizer_info.json").symlink_to(tokenizer_info.resolve())

    linked = 0
    scanned = 0
    linked_by_bucket = {"focus": 0, "broad_anchor": 0, "extra": 0}
    for src in task_dirs(args.root):
        scanned += 1
        name = task_name(src, args.root)
        if name.startswith(tuple(FOCUS_PREFIXES)):
            bucket = "focus"
        elif name.startswith(tuple(BROAD_ANCHOR_PREFIXES)):
            bucket = "broad_anchor"
        elif args.extra_prefixes and name.startswith(tuple(args.extra_prefixes)):
            bucket = "extra"
        else:
            continue
        link_task(src, args.root, args.output)
        linked += 1
        linked_by_bucket[bucket] += 1

    manifest = {
        "root": str(args.root),
        "output": str(args.output),
        "scanned_tasks": scanned,
        "linked_tasks": linked,
        "linked_by_bucket": linked_by_bucket,
        "focus_prefixes": FOCUS_PREFIXES,
        "broad_anchor_prefixes": BROAD_ANCHOR_PREFIXES,
        "extra_prefixes": args.extra_prefixes,
        "note": "DFM8-post uses a filtered tokenized tree because sample_tokenized.py includes unmatched tasks by default.",
    }
    (args.output / "union_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
