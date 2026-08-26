#!/usr/bin/env python3
"""Build the source-level DFM9 copyright and EU TDM triage register.

This is evidence-driven legal triage, not a legal conclusion. In particular,
repository-level licence metadata is not treated as proof that third-party
content embedded in a mixture is covered by that licence.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_REGISTER = ROOT / "legal/registers/dataset-legal-basis-register.csv"
HF_METADATA = ROOT / "legal/registers/dfm9-hf-current-metadata-register.csv"
HF_SNAPSHOTS = ROOT / "legal/registers/hf-snapshot-register.csv"
OUTPUT = ROOT / "legal/registers/dfm9-copyright-basis-register.csv"
REPORT = ROOT / "legal/reports/dfm9-copyright-tdm-review.md"

DFM8_TOTAL = 70_479_308_606
# `metadata.total_length` is the concatenated token-store size, not sampled
# exposure. The final DFM9 analytics contain 399,693,515,389 covered tokens
# across five epoch index sets. Keep that exact integer as the denominator.
DFM9_EPOCHS = 5
DFM9_TOTAL_EXPOSURE = 399_693_515_389

# Exact five-epoch covered-token totals for categories whose DFM9 sampling
# differs from the DFM8 source register. Every other source retains its DFM8
# per-epoch exposure and is multiplied by DFM9_EPOCHS.
DFM9_EXPOSURE_OVERRIDES = {
    "sapientinc/HRM-Text-data-io-cleaned-20260515": 106_900_172_584,
    "allenai/verifiable-reasoning-filtered-o4-mini": 400_993_502,
    "DBC": 1_780_571_594,
    "nvidia/Nemotron-SFT-Multilingual-v1": 2_064_291_177,
    "oliverkinch/machine-translation-da-ar": 697_776_712,
    "oliverkinch/machine-translation-da-en": 1_421_792_985,
    "oliverkinch/machine-translation-da-uk": 347_475_470,
    "schneiderkamplab/opus-da-en-permissive": 14_517_186_295,
}

AGREEMENT_SOURCES = {"DBC", "Lex.dk"}
NONCOMMERCIAL_LICENCES = {"cc-by-nc-4.0", "cc-by-nc-sa-4.0"}
RECOGNISED_OPEN_PREFIXES = (
    "apache-",
    "bsd-",
    "cc-by-",
    "cc0-",
    "etalab-",
    "mit",
)

PROJECT_GENERATED = {
    "schneiderkamplab/dfm8-synthetic-code-debugging",
    "schneiderkamplab/dfm8-synthetic-constrained-format-following",
    "schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls",
    "schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat",
    "schneiderkamplab/dfm8-synthetic-native-tool-calling",
    "schneiderkamplab/dfm8-synthetic-strict-math-answer-contract",
}

# The project regenerated these four FLAN renderings independently. Their task
# provenance is AESLC, whose official repository declares CC BY-NC-SA 4.0.
AESLC_SYNTHETIC_REPLACEMENTS = {
    "schneiderkamplab/sapient-synth-flan-flan-fsnoopt-data-aeslc-1.0.0",
    "schneiderkamplab/sapient-synth-flan-flan-fsopt-data-aeslc-1.0.0",
    "schneiderkamplab/sapient-synth-flan-flan-zsnoopt-data-aeslc-1.0.0",
    "schneiderkamplab/sapient-synth-flan-flan-zsopt-data-aeslc-1.0.0",
}

QRECC_SYNTHETIC_REPLACEMENTS = {
    "schneiderkamplab/sapient-synth-flan-dialog-fsopt-data-qrecc",
    "schneiderkamplab/sapient-synth-flan-dialog-fsopt-data-qrecc-ii",
    "schneiderkamplab/sapient-synth-flan-dialog-zsopt-data-qrecc",
    "schneiderkamplab/sapient-synth-flan-dialog-zsopt-data-qrecc-ii",
}

OPINION_ABSTRACTS_SYNTHETIC_REPLACEMENTS = {
    f"schneiderkamplab/sapient-synth-flan-flan-{regime}-data-opinion-abstracts-{source}"
    for regime in ("fsnoopt", "fsopt", "zsnoopt", "zsopt")
    for source in ("rotten-tomatoes", "idebate")
}

# The project owner confirmed on 2026-08-17 that Giannor created these
# derivatives while working as part of the DFM project. The retained TV2R text
# remains governed by its source licence.
PROJECT_GENERATED_OPEN_SOURCE_DERIVATIVES = {
    "giannor/dala_tv2r_it",
    "giannor/gec_dala_tv2r_it",
}

PROJECT_GENERATED_DOLCI_PUZZLE_DERIVATIVES = {
    "synquid/danish-verifiable-reasoning",
}

# This AllenAI subset retains problems and generated solutions from NVIDIA's
# CC-BY-4.0 OpenMathInstruct-2, whose GSM8K seed is MIT, and replaces the
# assistant response with DeepSeek-R1-family output. DeepSeek's MIT terms
# expressly permit distillation and training other models.
TRACEABLE_OPEN_MATH_DERIVATIVES = {
    "allenai/open_math_2_50k_r1-original",
}

# The project owner confirmed on 2026-08-17 that Oliver Kinch and Synquid work
# as part of DFM. Their authored transformations/generations are authorized DFM
# contributions; this does not alter the rights status of retained source data.
DFM_CONTRIBUTOR_PREFIXES = ("oliverkinch/", "synquid/")

# Aggregates for which the repository/container licence does not by itself
# resolve copyright in every embedded record.
MIXED_ARTICLE3 = {
    "sapientinc/HRM-Text-data-io-cleaned-20260515",
    "danish-foundation-models/dfm-dyna-instruct",
    "Muennighoff/natural-instructions",
    "AI-MO/NuminaMath-1.5",
    "allenai/code-meta-reasoning-cleaned-final-string-id",
    "schneiderkamplab/dfm8-openhermes-en",
    "schneiderkamplab/dfm8-openhermes-da",
}

# MAN-022 accepts deliberate ShareGPT one-click publication plus public-API
# access as participant permission for this academic/non-commercial research
# training. This is not treated as an Apache licence or as evidence equivalent
# to WildChat's explicit research/product-development consent flow.
SHAREGPT_PUBLICATION_PERMISSION = {
    "allenai/tulu-v2-sft-mixture",
    "allenai/tulu-v2-sft-long-mixture",
    "allenai/SciRIFF-train-mix",
}

# Component-audited mixtures whose retained source expression is covered by
# direct subset terms plus a project-owner Article 4 determination.
AUDITED_MIXED_ARTICLE4 = {
    "allenai/tulu-3-sft-mixture",
}

# The complete DOLCI decomposition now resolves every required component via
# direct terms, Article 4 (FLAN v2 and SciRIFF), express permission, or the
# MAN-001 through MAN-004 low-risk decisions. Keep the mixture classification
# separate from Tulu 3 so its Tool Use decision remains explicit.
AUDITED_DOLCI_MIXED_ARTICLE4 = {
    "allenai/Dolci-Instruct-SFT",
    "allenai/Dolci-Instruct-SFT-No-Tools",
}

AUDITED_TULU3_DERIVATIVES = {
    "allenai/IF_sft_data_verified",
}

OPENHERMES_DERIVATIVES_ARTICLE4 = {
    "schneiderkamplab/dfm8-openhermes-en",
    "schneiderkamplab/dfm8-openhermes-da",
}

MANUALLY_ACCEPTED_LOW_RISK = {
    "allenai/Dolci-Instruct-SFT-Tool-Use",
}

MANUALLY_ACCEPTED_SYNTHETIC_REPAIRS_PREFIX = "schneiderkamplab/sapient-synth-"

MIXED_OPEN = {
    "allenai/RLVR-MATH",
    "allenai/big-reasoning-traces",
    "ccdv/govreport-summarization",
    "common-pile/arxiv_papers_filtered",
    "oliverkinch/danish-summarization",
    "oliverkinch/danish-university-portals-bt",
    "oliverkinch/eur-lex-bt",
    "oliverkinch/eur-lex-sum-instruct",
    "synquid/wiki-instruct-da",
    "schneiderkamplab/opus-da-en-permissive",
    "schneiderkamplab/common-pile-denoising",
    "schneiderkamplab/common-pile-paragraph-reordering",
    "schneiderkamplab/common-pile-prefix-continuation",
    "schneiderkamplab/common-pile-span-filling",
    "danish-foundation-models/ai_arena_udtraek",
    "synquid/translation-100k",
    "synquid/mt-da-deepseek",
}

EXPLICIT_TRAINING_PERMISSION = {
    "nvidia/Nemotron-SFT-Instruction-Following-Chat-v2",
    "synquid/ifbench-train",
    "synquid/wildchat-100k-qwen-messages",
}

TULU_PERSONA_DIRECT = {
    "allenai/tulu-3-sft-personas-algebra",
    "allenai/tulu-3-sft-personas-code",
    "allenai/tulu-3-sft-personas-instruction-following",
    "allenai/tulu-3-sft-personas-math",
}

# The project owner confirmed on 2026-08-17 that every instruct-bt component
# (DynaWord, dkmedier, odense and danskerhverv) is covered either by its source
# terms or by a DFM/data-owner agreement permitting model training and release.
MIXED_OPEN_AND_AGREEMENT = {
    "oliverkinch/instruct-bt",
}

DYNAWORD_DERIVATIVES = {
    "oliverkinch/autodata-da-sft",
    "oliverkinch/da-instruct-dynaword",
    "oliverkinch/da-instruct-dynaword-contemporary",
    "oliverkinch/da-instruct-dynaword-contemporary-hq",
    "oliverkinch/da-instruct-dynaword-hq",
    "oliverkinch/dynaword-bt",
    "schneiderkamplab/danish-dynaword-denoising",
    "schneiderkamplab/danish-dynaword-paragraph-reordering",
    "schneiderkamplab/danish-dynaword-prefix-continuation",
    "schneiderkamplab/danish-dynaword-span-filling",
}

ODC_BY_CARD_TEXT = {
    "allenai/tulu-3-sft-personas-algebra",
    "allenai/tulu-3-sft-personas-code",
    "allenai/tulu-3-sft-personas-math",
}

TRANSFORMATION_DERIVATIVES = {
    "schneiderkamplab/transformations-danish-danish",
    "schneiderkamplab/transformations-danish-english",
    "schneiderkamplab/transformations-english-danish",
    "schneiderkamplab/transformations-english-english",
}


def load_csv(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def licence_kind(licence: str) -> str:
    values = {value.strip().lower() for value in licence.split(";") if value.strip()}
    if values & NONCOMMERCIAL_LICENCES:
        return "noncommercial"
    if any(value.startswith("odc-by") for value in values):
        return "database_only"
    if any(value.startswith(RECOGNISED_OPEN_PREFIXES) for value in values):
        return "open"
    return "none"


def mixed_open_rationale(source_id: str) -> str:
    if source_id in DYNAWORD_DERIVATIVES:
        return (
            "DynaWord-derived aggregate governed by per-source open/public-domain terms; "
            "selected seed status was confirmed by the project owner on 2026-08-16."
        )
    if source_id == "oliverkinch/danish-university-portals-bt":
        return "Source card identifies oliverkinch/danish-university-portals-cc-by as the passage source."
    if source_id == "oliverkinch/danish-summarization":
        return (
            "Two-source aggregate: EUR-Lex Sum is public-domain/CC-BY derived, and the "
            "Nordjylland component is part of the accepted DynaWord source family; "
            "confirmed by the project owner on 2026-08-17."
        )
    if source_id in {"oliverkinch/eur-lex-bt", "oliverkinch/eur-lex-sum-instruct"}:
        return (
            "Derived from reusable EUR-Lex legal material; generated instructions do not "
            "introduce a separate third-party corpus. Confirmed by the project owner on 2026-08-17."
        )
    if source_id == "schneiderkamplab/opus-da-en-permissive":
        return "Selected OPUS corpora are governed by retained per-corpus permissive/public-domain terms."
    if source_id.startswith("schneiderkamplab/common-pile-") or source_id == "common-pile/arxiv_papers_filtered":
        return "Common Pile derivative governed by retained per-record open/public-domain source terms."
    if source_id == "synquid/wiki-instruct-da":
        return "Wikipedia-derived instructions remain governed by the applicable CC-BY-SA source terms."
    if source_id == "synquid/translation-100k":
        return (
            "Every retained row names oliverkinch/machine-translation-da-en and its "
            "underlying OPUS corpus; follow those per-corpus open/public terms."
        )
    if source_id == "danish-foundation-models/ai_arena_udtraek":
        return (
            "The card identifies this as a Danish extraction of the ComparIA conversations "
            "and reactions datasets under Etalab Open Licence 2.0; privacy is reviewed separately."
        )
    if source_id == "ccdv/govreport-summarization":
        return (
            "GovReport consists of GAO and CRS reports and their published summaries; the "
            "source paper records them as US-government public-domain material. Preserve "
            "GAO/CRS attribution and do not assume separately credited embedded works are covered."
        )
    if source_id == "allenai/RLVR-MATH":
        return (
            "All 7,500 rows identify MATH as their dataset; the official Hendrycks MATH "
            "repository is MIT licensed. Preserve the source notice and citation."
        )
    if source_id == "synquid/mt-da-deepseek":
        return (
            "Project-generated dialogues use DynaWord source excerpts or handcrafted seeds; "
            "the project owner confirmed the retained DynaWord passages are open/public-domain."
        )
    if source_id == "allenai/big-reasoning-traces":
        return "Card identifies a compilation of permissively licensed component datasets; preserve component provenance."
    return "Aggregate is usable only to the extent its per-record source manifest supports the stated terms."


ARTICLE3_RATIONALES = {
    "sapientinc/HRM-Text-data-io-cleaned-20260515": (
        "All eight retained broad families are decomposed. Platypus, synthetic/math, factual FLAN, "
        "and non-factual FLAN use direct terms, Article 4, or recorded low-risk decisions. Article 3 "
        "remains necessary only for 69.759M tokens/epoch in 84 Tasksource files whose source-repository "
        "metadata is blank, unknown, other, or generic CC; MAN-020 approves that current research use."
    ),
    "danish-foundation-models/dfm-dyna-instruct": (
        "The DFM Dyna dependency DAG is fully resolved for current scientific research. Direct terms "
        "cover the DFM-authored, WildChat-consented, Tulu-audited, and nine directly licensed Apertus "
        "boundaries. FLAN v2, SciRIFF, and four uncovered OpenHermes families use Article 4 by "
        "project-owner determination; Mixture-of-Thoughts uses a recorded residual-risk acceptance. "
        "Article 3 remains necessary only for LongAlign source documents (including SmolTalk imports) "
        "and EuroBlocks annealing seeds; MAN-017 and MAN-018 approve those fallbacks for the current "
        "academic/non-commercial scientific-research purpose."
    ),
    "allenai/Dolci-Instruct-SFT": (
        "The 22 source labels mix directly licensed/generated material with ODC-By, FLAN, "
        "WildChat, SciRIFF and other source-dependent prompts."
    ),
    "allenai/Dolci-Instruct-SFT-No-Tools": (
        "The no-tools corpus contains the same 21 non-tool source families as the full DOLCI "
        "mixture. Ai2-authored sources are directly covered, while FLAN, CoCoNot, SciRIFF, "
        "Tulu persona and WildJailbreak dependencies remain source-specific."
    ),
    "allenai/Dolci-Instruct-SFT-Tool-Use": (
        "The five ToolU labels are decomposed into direct Ai2-generated trajectory layers and "
        "named licensed sources. On 2026-08-17 the project owner accepted the remaining "
        "unassigned/adapted SimFC schemas, third-party scholarly content, five residual DRv4 "
        "prompts, and retained web-search snippets as low risk for current academic/non-commercial "
        "scientific-research training, with no identified material reason to invoke Article 3."
    ),
    "allenai/tulu-3-sft-mixture": (
        "The 939,343 local rows resolve to 19 source labels. Fifteen component families have "
        "direct/open or previously accepted bases; CoCoNot and WildJailbreak are synthetic "
        "Ai2 releases under stated terms. FLAN v2 and SciRIFF use Article 4 / Danish section "
        "11 b for uncovered source expression by project-owner determination."
    ),
    "allenai/tulu-v2-sft-mixture": (
        "All 16 local labels are mapped. WizardLM is MIT; direct/noncommercial terms or recorded "
        "FLAN/SciRIFF Article 4 decisions cover every other component. ShareGPT participant "
        "expression is covered for current research by MAN-022 deliberate-publication permission acceptance."
    ),
    "allenai/tulu-v2-sft-long-mixture": (
        "The Long reconstruction has the same non-ShareGPT composition and 74,312 ShareGPT rows. "
        "A focused ID audit found 74,159 original IDs shared with the split artifact, 792 split-only, "
        "and 148 Long-only. WizardLM is MIT; ShareGPT expression is covered for current research by MAN-022."
    ),
    "schneiderkamplab/dfm8-openhermes-en": (
        "Project repair preserves prompts from fourteen OpenHermes source families, including "
        "Chatbot Arena and ShareGPT; output repair does not erase prompt rights."
    ),
    "schneiderkamplab/dfm8-openhermes-da": (
        "Project translation/repair preserves prompts from fourteen OpenHermes source families, "
        "including Chatbot Arena and ShareGPT; translation does not erase prompt rights."
    ),
    "allenai/IF_sft_data_verified": (
        "Every local ID exactly matches an audited Tulu 3 row. Ai2 adds the constraint and regenerates "
        "the response; the retained prompt inherits the completed Tulu 3 component basis."
    ),
    "allenai/SciRIFF-train-mix": (
        "The exact local split is 35,000 SciRIFF rows and 35,714 sampled Tulu v2 rows. SciRIFF uses "
        "MAN-014 Article 4; the Tulu half is resolved including MAN-022 for ShareGPT participant expression."
    ),
    "allenai/open_math_2_50k_r1-original": (
        "Rows trace to NVIDIA OpenMathInstruct-2 (CC-BY-4.0): 8,988 GSM8K and "
        "40,841 augmented-GSM8K problems, with regenerated DeepSeek-R1-family answers. "
        "GSM8K is MIT and DeepSeek's MIT model terms expressly permit distillation and "
        "training other models; preserve attribution and notices."
    ),
    "allenai/verifiable-reasoning-filtered-gpt-41": (
        "The schema-only release maps to the MIT-licensed RLVE-Gym generators, but RLVE source "
        "comments link 122 of the 250 retained environment variants to external problem sources "
        "(115 to Luogu, plus Codeforces, HDU, SPOJ, X and Wikipedia). Generator-code licensing "
        "does not automatically license source problem expression. A 250-variant prompt audit "
        "narrowed plausible close/carryover expression, and the project owner manually accepted "
        "the complete RLVE family for current academic/research training and downstream-mixture "
        "consideration on 2026-08-17; Article 3 remains the fallback where needed."
    ),
    "allenai/verifiable-reasoning-filtered-o4-mini": (
        "The schema-only release maps to the MIT-licensed RLVE-Gym generators, but RLVE source "
        "comments link 122 of the 250 retained environment variants to external problem sources "
        "(115 to Luogu, plus Codeforces, HDU, SPOJ, X and Wikipedia). Generator-code licensing "
        "does not automatically license source problem expression. A 250-variant prompt audit "
        "narrowed plausible close/carryover expression, and the project owner manually accepted "
        "the complete RLVE family for current academic/research training and downstream-mixture "
        "consideration on 2026-08-17; Article 3 remains the fallback where needed."
    ),
    "giannor/dala_tv2r_it": (
        "The retained TV2R sentences trace to the CC-BY-SA 4.0 TV2R component of Danish "
        "Gigaword/DynaWord, but the Giannor repository has no captured licence for its added "
        "sentence selection, synthetic corruptions, labels, or instruction wrapper. Article 3 "
        "is therefore only the fallback for that uncovered derivative/database layer."
    ),
    "giannor/gec_dala_tv2r_it": (
        "The retained TV2R sentences trace to the CC-BY-SA 4.0 TV2R component of Danish "
        "Gigaword/DynaWord, but the Giannor repository has no captured licence for its added "
        "sentence selection, synthetic corrections, metadata, or instruction wrapper. Article 3 "
        "is therefore only the fallback for that uncovered derivative/database layer."
    ),
    "synquid/danish-verifiable-reasoning": (
        "Synquid's generated prompts, answers, and wrappers are authorized DFM contributions. "
        "The inherited DOLCI puzzle-source rights still follow the DOLCI component audit."
    ),
    "synquid/ifbench-train": (
        "Synquid's constraints, answers, and wrappers are authorized DFM contributions. Rows "
        "retain prompts from danish-foundation-models/danish-wildchat4.8M, whose rights remain unresolved."
    ),
    "synquid/wildchat-100k-qwen-messages": (
        "Synquid's generated continuations and wrappers are authorized DFM contributions. The "
        "corpus retains 69,688 original user/assistant conversations and extends 30,000 with "
        "generated follow-ups; retained conversation rights remain unresolved."
    ),
}


def classify(source_id: str, licence: str) -> tuple[str, str, str, str, str]:
    """Return class, current basis, non-research basis, confidence, rationale."""
    if source_id in AGREEMENT_SOURCES:
        return (
            "agreement_or_contract",
            "direct DFM/data-owner agreement permitting model training and model release",
            "same direct basis within the agreement; other downstream uses remain scope-dependent",
            "high",
            "On 2026-08-17 the project owner confirmed that the DBC and Lex.dk agreements permit training and model release.",
        )
    if source_id in EXPLICIT_TRAINING_PERMISSION:
        if source_id.startswith("synquid/"):
            return (
                "explicit_publisher_training_permission",
                "affirmative WildChat user consent for research/product-development use and third-party publication/sharing, accepted by the project owner as express permission for current research model training",
                "downstream use remains limited by the documented consent scope, dataset terms, and independent privacy obligations",
                "high",
                "The ICLR 2024 WildChat paper documents a two-step affirmative collection/use/publication consent flow; on 2026-08-17 the project owner accepted that consent as express permission for the current research training use.",
            )
        return (
            "explicit_publisher_training_permission",
            "publisher expressly permits free use to train and evaluate, with ODC-By attribution",
            "same express permission; retain attribution and applicable terms",
            "high",
            "NVIDIA identifies itself as owner, states commercial readiness, and expressly permits training and evaluation.",
        )
    if source_id in SHAREGPT_PUBLICATION_PERMISSION:
        return (
            "mixed_direct_and_participant_publication_permission",
            "direct component terms plus MAN-022 acceptance of deliberate ShareGPT public sharing and public-API access as participant permission for current academic/non-commercial research training",
            "nonresearch use remains source- and scope-specific; MAN-022 is not a blanket Apache licence or raw-redistribution permission",
            "high",
            ARTICLE3_RATIONALES[source_id]
            + " On 2026-08-18 the project owner accepted the deliberate publication flow as permission for the current research use; unlike WildChat, no explicit research/product-development consent wording was found.",
        )
    if source_id in TULU_PERSONA_DIRECT:
        return (
            "mixed_open_and_noncommercial_licences",
            "ODC-By Ai2 release plus PersonaHub CC-BY-NC-SA and assigned generator-output rights; no Article 3 reliance",
            "commercial use is not cleared because the PersonaHub conditioning layer is NonCommercial; preserve attribution and ShareAlike scope",
            "high",
            "The Tulu 3 report identifies PersonaHub conditioning, Ai2-authored seeds, GPT-4o generation, and Claude 3.5 Sonnet Python solutions. Provider terms assign outputs to the customer; Ai2 released the subsets under ODC-By. Account-specific generation compliance is not independently archived.",
        )
    if source_id in PROJECT_GENERATED:
        return (
            "project_generated_direct",
            "project-held/generated rights plus open-licensed/public-domain DynaWord or Common Pile seed passages",
            "same basis if the project has authority to license/release the generated material",
            "high",
            "Rows were generated and audited by the project; on 2026-08-16 the project owner confirmed that retained DynaWord/Common Pile seed passages are public domain or open licensed.",
        )
    if source_id in AESLC_SYNTHETIC_REPLACEMENTS:
        return (
            "direct_noncommercial_licence",
            "project-generated Apache-2.0 layer; AESLC task provenance licensed CC BY-NC-SA 4.0 for the current academic/non-commercial use",
            "commercial use is not cleared by AESLC's NonCommercial licence; adaptation/share-alike scope requires review",
            "high",
            "The official AESLC repository declares CC BY-NC-SA 4.0. The DFM replacement rows were generated with Gemma 4 31B and accepted only after PII, task-preservation, and low-overlap review; all published rows are marked accepted.",
        )
    if source_id in QRECC_SYNTHETIC_REPLACEMENTS:
        return (
            "direct_open_licence_or_public_terms",
            "project-generated Apache-2.0 layer; QReCC task provenance licensed CC BY-SA 3.0",
            "same direct basis subject to attribution, ShareAlike, notices, and adaptation-scope review",
            "high",
            "Apple's official QReCC repository declares the dataset CC BY-SA 3.0. The DFM replacement rows were generated with Gemma 4 31B and accepted only after PII, task-preservation, and low-overlap review; all published rows are marked accepted.",
        )
    if source_id in PROJECT_GENERATED_OPEN_SOURCE_DERIVATIVES:
        return (
            "project_generated_derivative_of_open_source",
            "DFM project-generated derivative plus the TV2R source licence",
            "same direct basis if TV2R attribution/share-alike obligations are retained",
            "high",
            "On 2026-08-17 the project owner confirmed that Giannor created the derivative "
            "as part of the DFM project. Retained TV2R sentences trace to Danish "
            "Gigaword/DynaWord; apply the stricter captured CC-BY-SA 4.0 terms.",
        )
    if source_id in PROJECT_GENERATED_DOLCI_PUZZLE_DERIVATIVES:
        return (
            "project_generated_derivative_of_open_source",
            "authorized DFM/Synquid translation and solution layer plus Ai2-authored DOLCI puzzle prompts released for research under ODC-By",
            "same direct basis if attribution and applicable DOLCI/DFM notices are retained",
            "high",
            "The project owner confirmed Synquid's authored contribution is authorized, and the DOLCI card identifies the logic-puzzle prompts as new prompts from Ai2.",
        )
    if source_id in TRACEABLE_OPEN_MATH_DERIVATIVES:
        return (
            "direct_open_licence_or_public_terms",
            "NVIDIA OpenMathInstruct-2 CC-BY-4.0 lineage, GSM8K MIT seed, and DeepSeek-R1 MIT distillation permission",
            "same direct basis subject to attribution, notices, and preservation of source lineage",
            "high",
            ARTICLE3_RATIONALES[source_id],
        )
    if source_id in MANUALLY_ACCEPTED_LOW_RISK:
        return (
            "mixed_direct_and_manual_low_risk_acceptance",
            "direct licensed/generated layers plus project-owner low-risk acceptance; no Article 3 reliance identified for residual layers",
            "Article 4 is a conditional alternative only where lawful access and absence of an effective rights reservation are evidenced",
            "medium",
            ARTICLE3_RATIONALES[source_id]
            + " The detailed findings and provenance gaps remain recorded; this is not an open-licence classification.",
        )
    if source_id.startswith(MANUALLY_ACCEPTED_SYNTHETIC_REPAIRS_PREFIX):
        return (
            "mixed_direct_and_manual_low_risk_acceptance",
            "project-generated and audited replacement layer accepted under MAN-021; no Article 3 reliance for the effective synthetic derivative",
            "upstream task records and nonresearch uses remain source-specific; MAN-021 does not relicense source datasets",
            "high",
            "MAN-021 accepts the generated replacement as the operative training work for the current project. Named upstream links remain provenance and memorisation-test evidence rather than blocking dependencies.",
        )
    if source_id in AUDITED_MIXED_ARTICLE4:
        return (
            "mixed_licences_and_article4",
            "ODC-By container and direct component terms; Article 4 / Danish section 11 b for uncovered FLAN v2 and SciRIFF source expression",
            "same basis only while Article 4 lawful-access and no-effective-reservation conditions remain satisfied; otherwise component-specific permission is required",
            "high",
            ARTICLE3_RATIONALES[source_id]
            + " See legal/reports/dfm9-tulu3-mixture-audit.md.",
        )
    if source_id in AUDITED_DOLCI_MIXED_ARTICLE4:
        return (
            "mixed_licences_and_article4",
            "ODC-By mixture layer plus direct component terms, MAN-001 through MAN-004 for Tool Use residuals, and Article 4 for uncovered FLAN v2 and SciRIFF expression",
            "same component-specific basis only while Article 4 conditions and direct-term obligations remain satisfied",
            "high",
            ARTICLE3_RATIONALES[source_id]
            + " The complete DOLCI DAG has no remaining Article 3-dependent required child; see legal/reports/dfm9-dolci-toolu-component-audit.md and the source-rights DAG.",
        )
    if source_id in AUDITED_TULU3_DERIVATIVES:
        return (
            "mixed_licences_and_article4",
            "Ai2 constraint/regenerated-response layer plus the fully audited Tulu 3 component bases",
            "same Tulu 3 component bases, including Article 4 conditions for uncovered FLAN v2 and SciRIFF expression",
            "high",
            ARTICLE3_RATIONALES[source_id]
            + " Every local ID exactly matches a row in the audited Tulu 3 mixture; see legal/reports/dfm9-tulu-v2-sciriff-if-sft-audit.md.",
        )
    if source_id in OPENHERMES_DERIVATIVES_ARTICLE4:
        return (
            "mixed_licences_and_article4",
            "direct OpenHermes component terms plus Article 4 / Danish section 11 b for uncovered Airoboros, Caseus, CoT-Alpaca, and Platypus expression",
            "same basis only while Article 4 lawful-access and no-effective-reservation conditions remain satisfied; preserve component-specific direct terms",
            "high",
            ARTICLE3_RATIONALES[source_id]
            + " Project-owner Article 4 determination MAN-016 supersedes the initial Article 3 fallback.",
        )
    if source_id == "danish-foundation-models/dfm-dyna-instruct":
        return (
            "mixed_licences_and_article3_fallback",
            "CC-BY-4.0 collection and direct component terms; DSM Article 3 only for uncovered retained source expression in the audited Tulu/Apertus branches",
            "Article 4 is only a conditional alternative for general/nonresearch use; otherwise component-by-component permission is required for Article 3-backed layers",
            "high",
            ARTICLE3_RATIONALES[source_id]
            + " See legal/reports/dfm9-apertus-component-audit.md and legal/reports/dfm9-tulu3-mixture-audit.md.",
        )
    if source_id in OPINION_ABSTRACTS_SYNTHETIC_REPLACEMENTS:
        return (
            "article3_research_tdm_for_uncovered_components",
            "project-generated Apache-2.0 replacement layer; Article 3 candidate for historical use of unlicensed crawled Opinion Abstracts seed text",
            "commercial/general use of the seed material is not cleared; the low-overlap generated output requires adaptation-scope review",
            "high",
            "TFDS identifies Rotten Tomatoes professional reviews/editorial consensus or iDebate claims/arguments as crawled source text but supplies no source-content licence. The DFM rows are accepted low-overlap synthetic recreations with no unchanged PII detections.",
        )
    if source_id in MIXED_ARTICLE3:
        return (
            "article3_research_tdm_for_uncovered_components",
            "DSM Article 3 candidate for scientific research, lawful access and secure retention required",
            "DSM Article 4 only if lawful access and no effective rights reservation are evidenced",
            "medium",
            ARTICLE3_RATIONALES.get(
                source_id,
                "Container/output licence does not establish permission for every incorporated upstream work.",
            ),
        )
    if source_id in TRANSFORMATION_DERIVATIVES:
        return (
            "mixed_direct_licences_and_agreements",
            "project-generated Apache-2.0 layer plus direct licence/agreement for every identified seed family",
            "same direct basis if attribution, ShareAlike, notices, and agreement scope are retained",
            "high",
            "Exact accepted-row matching identifies the Danish seed families as DynaWord, Laerebogen, "
            "Wikipedia instructions, Oliver Kinch sources and Lex.dk; English rows trace to scientific/arXiv "
            "summaries, DBC, Lex.dk and ASSET. Existing source decisions cover all identified families.",
        )
    if source_id in MIXED_OPEN or source_id in DYNAWORD_DERIVATIVES:
        return (
            "mixed_open_or_public_domain_licences",
            "direct per-record/per-corpus licence or public-domain status, with attribution/share-alike compliance",
            "same direct basis if obligations and provenance are retained",
            "medium",
            mixed_open_rationale(source_id),
        )
    if source_id in MIXED_OPEN_AND_AGREEMENT:
        return (
            "mixed_open_licences_and_training_release_agreements",
            "direct per-source licence or DFM/data-owner agreement permitting training and model release",
            "same direct basis within the applicable source terms and agreement scope",
            "high",
            "On 2026-08-17 the project owner confirmed coverage for DynaWord, dkmedier, odense and danskerhverv.",
        )

    kind = licence_kind(licence)
    if kind == "noncommercial":
        return (
            "direct_noncommercial_licence",
            "direct licence for academic/non-commercial use, subject to attribution/share-alike terms",
            "direct only for non-commercial uses; commercial/general use not cleared by this review",
            "medium",
            "The declared licence contains a NonCommercial restriction.",
        )
    if kind == "open":
        return (
            "direct_open_licence_or_public_terms",
            "direct licence, subject to attribution/share-alike/notice and source-scope verification",
            "same direct basis within licence scope",
            "medium",
            "Repository declares an open/public licence; embedded third-party content still needs scope verification.",
        )
    if kind == "database_only":
        return (
            "database_licence_article3_for_content",
            "ODC-By for database rights; Article 3 candidate for uncleared copyright in contents",
            "ODC-By plus Article 4 only where content access and no-reservation conditions are evidenced",
            "medium",
            "ODC-By does not by itself establish copyright permission for every database content item.",
        )
    return (
        "article3_research_tdm_candidate",
        "DSM Article 3 candidate for scientific research, lawful access and secure retention required",
        "DSM Article 4 only if lawful access and no effective rights reservation are evidenced",
        "low",
        ARTICLE3_RATIONALES.get(
            source_id,
            "No adequate direct copyright licence was captured in repository metadata.",
        ),
    )


def source_lineage(source_id: str) -> str:
    if source_id == "oliverkinch/danish-summarization":
        return "Two-source aggregate: oliverkinch/eur-lex-sum and alexandrainst/nordjylland-news-summarization."
    if source_id in EXPLICIT_TRAINING_PERMISSION:
        if source_id.startswith("synquid/"):
            return "Authorized DFM/Synquid contribution retaining WildChat prompts covered by affirmative user consent accepted for current research training."
        return "Publisher-owned hybrid/synthetic instruction corpus with express training permission."
    if source_id in SHAREGPT_PUBLICATION_PERMISSION:
        return "Component-audited mixture; ShareGPT expression is covered for current research by MAN-022 deliberate-publication permission acceptance, with privacy safeguards independent."
    if source_id in TULU_PERSONA_DIRECT:
        return "Synthetic PersonaHub-conditioned prompts/responses generated by GPT-4o and, for Python solutions, Claude 3.5 Sonnet; Ai2 seeds and IFEval taxonomy also apply to instruction following."
    if source_id in AESLC_SYNTHETIC_REPLACEMENTS:
        return "Project-generated, PII-audited, low-overlap recreation of one of four FLAN AESLC rendering regimes; task provenance is the CC BY-NC-SA 4.0 AESLC corpus."
    if source_id in QRECC_SYNTHETIC_REPLACEMENTS:
        return "Project-generated, PII-audited, low-overlap recreation of one of four FLAN QReCC dialogue regimes; task provenance is the CC BY-SA 3.0 QReCC corpus."
    if source_id in OPINION_ABSTRACTS_SYNTHETIC_REPLACEMENTS:
        return "Project-generated, PII-audited, low-overlap recreation of a FLAN Opinion Abstracts regime; historical seed use follows Article 3 because no direct source-content licence was found."
    if source_id.startswith("schneiderkamplab/sapient-synth-"):
        return "Synthetic repair of named Sapient/FLAN/NIV2 source; upstream expression may remain."
    if source_id.startswith("schneiderkamplab/dfm8-synthetic-"):
        return "Project-generated and audited; verify seed manifests for retained source expression."
    if source_id in PROJECT_GENERATED_OPEN_SOURCE_DERIVATIVES:
        return "DFM project-generated derivative of CC-licensed TV2R text from Danish Gigaword/DynaWord."
    if source_id in TRACEABLE_OPEN_MATH_DERIVATIVES:
        return "Subset of NVIDIA OpenMathInstruct-2 problems/solutions with DeepSeek-R1-family regenerated responses."
    if source_id in MIXED_ARTICLE3:
        return "Mixture/derived repository; component-level rights control."
    if source_id in AUDITED_TULU3_DERIVATIVES:
        return "Constraint-augmented and response-regenerated derivative of the fully audited Tulu 3 mixture."
    if source_id in DYNAWORD_DERIVATIVES:
        return "Derived from Danish DynaWord; constituent source licence/status controls."
    if source_id in TRANSFORMATION_DERIVATIVES:
        return "Derived from multiple seed families; seed-level licence/agreement controls."
    if source_id in MIXED_OPEN:
        return "Aggregate selected from multiple licensed/public-domain source corpora."
    if source_id in MIXED_OPEN_AND_AGREEMENT:
        return "Aggregate of DynaWord and agreement-covered Danish data-owner sources."
    return "Top-level dataset repository or agreement source."


def main() -> None:
    base = load_csv(BASE_REGISTER, "source_id")
    metadata = load_csv(HF_METADATA, "source_id")
    snapshots = load_csv(HF_SNAPSHOTS, "repository_id")

    rows: list[dict[str, str]] = []
    for source_id in sorted(base, key=str.casefold):
        item = base[source_id]
        meta = metadata.get(source_id, {})
        licence = meta.get("declared_licence", "") or meta.get("licence_tags", "")
        if source_id in ODC_BY_CARD_TEXT:
            licence = "odc-by (local card text)"
        five_epoch_tokens = DFM9_EXPOSURE_OVERRIDES.get(
            source_id,
            int(item["sampled_tokens_per_epoch"]) * DFM9_EPOCHS,
        )
        average_tokens = Decimal(five_epoch_tokens) / DFM9_EPOCHS
        category, current_basis, nonresearch_basis, confidence, rationale = classify(source_id, licence)
        if source_id in OPINION_ABSTRACTS_SYNTHETIC_REPLACEMENTS:
            if source_id.endswith("opinion-abstracts-rotten-tomatoes"):
                nonresearch_basis = (
                    "Article 4 is unavailable for fresh use under Rotten Tomatoes' current explicit data-mining and AI-training reservation; "
                    "historical applicability and the separately hosted corpus copy require counsel review"
                )
                article4_status = "reservation_detected_not_available"
                rationale += (
                    " A 2026-08-17 audit found an express data-mining and AI-training prohibition in Rotten Tomatoes terms updated 2026-01-06. "
                    "The academic distribution host and TFDS layer expose no TDM signal, but cannot waive underlying rights."
                )
            else:
                nonresearch_basis = (
                    "Article 4 remains conditional: no express current TDM/AI reservation was found, but iDebate's general reuse terms restrict modification and unlisted uses"
                )
                article4_status = "conditional_not_cleared"
                rationale += (
                    " A 2026-08-17 audit found no explicit TDM reservation, TDMRep record, HTTP TDM header, or HTML TDM metadata at iDebate; "
                    "its general copyright/reuse terms still require counsel interpretation."
                )
        else:
            article4_status = (
                "conditional_not_cleared" if "Article 4" in nonresearch_basis else "not_needed_within_direct_scope"
            )
        if source_id.startswith(DFM_CONTRIBUTOR_PREFIXES):
            rationale += (
                " The project owner confirmed on 2026-08-17 that the publisher works as part "
                "of DFM; its authored contribution is authorized, without changing upstream provenance."
            )
        snapshot = snapshots.get(source_id, {})
        rows.append(
            {
                "source_id": source_id,
                "source_url": item.get("source_url", ""),
                "dfm9_prefix_or_category": item.get("dfm8_prefix", ""),
                "sampled_tokens_five_epochs": str(five_epoch_tokens),
                "average_sampled_tokens_per_epoch": f"{average_tokens:.1f}",
                "dfm9_share": f"{five_epoch_tokens / DFM9_TOTAL_EXPOSURE:.8%}",
                "captured_declared_licence": licence,
                "copyright_class": category,
                "current_scientific_research_basis": current_basis,
                "nonresearch_or_commercial_basis": nonresearch_basis,
                "article3_required": (
                    "fallback"
                    if "article3_fallback" in category
                    else "yes"
                    if "article3" in category
                    else "no"
                ),
                "article4_status": article4_status,
                "lineage_scope": source_lineage(source_id),
                "confidence": confidence,
                "rationale": rationale,
                "acquisition_evidence": snapshot.get("metadata_path", "") or item.get("evidence", ""),
                "current_metadata_evidence": meta.get("api_url", ""),
                "human_review_required": "yes"
                if category
                not in {
                    "direct_open_licence_or_public_terms",
                    "mixed_direct_and_manual_low_risk_acceptance",
                    "mixed_direct_and_participant_publication_permission",
                    "mixed_open_and_noncommercial_licences",
                    "project_generated_direct",
                    "project_generated_derivative_of_open_source",
                }
                else "scope_check",
            }
        )

    if len(rows) != 161:
        raise RuntimeError(f"Expected 161 effective DFM9 source rows, got {len(rows)}")
    if sum(int(row["sampled_tokens_five_epochs"]) for row in rows) != DFM9_TOTAL_EXPOSURE:
        raise RuntimeError("DFM9 token accounting does not match final metadata total")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["copyright_class"] for row in rows)
    tokens = defaultdict(int)
    by_class = defaultdict(list)
    for row in rows:
        tokens[row["copyright_class"]] += int(row["sampled_tokens_five_epochs"])
        by_class[row["copyright_class"]].append(row["source_id"])

    direct_categories = {
        "agreement_or_contract",
        "direct_noncommercial_licence",
        "direct_open_licence_or_public_terms",
        "mixed_open_or_public_domain_licences",
        "mixed_open_licences_and_training_release_agreements",
        "mixed_open_and_noncommercial_licences",
        "mixed_direct_and_manual_low_risk_acceptance",
        "mixed_direct_and_participant_publication_permission",
        "explicit_publisher_training_permission",
        "project_generated_direct",
        "project_generated_derivative_of_open_source",
    }
    article3_categories = {
        "article3_research_tdm_candidate",
        "article3_research_tdm_for_uncovered_components",
        "database_licence_article3_for_content",
    }
    fallback_categories = {
        "mixed_licences_agreements_and_article3_fallback",
        "mixed_licences_and_article3_fallback",
    }
    article4_categories = {
        "mixed_licences_and_article4",
    }

    def aggregate(categories: set[str]) -> tuple[int, int]:
        selected = [row for row in rows if row["copyright_class"] in categories]
        return len(selected), sum(int(row["sampled_tokens_five_epochs"]) for row in selected)

    direct_count, direct_tokens = aggregate(direct_categories)
    article3_count, article3_tokens = aggregate(article3_categories)
    fallback_count, fallback_tokens = aggregate(fallback_categories)
    article4_count, article4_tokens = aggregate(article4_categories)

    lines = [
        "# DFM9 Copyright and EU TDM Triage",
        "",
        "Status: source-level legal triage for the effective final DFM9 sample; not legal advice or final institutional approval.",
        "",
        "## Scope and method",
        "",
        f"The register covers **{len(rows)} top-level effective sources** and reconciles to **{DFM9_TOTAL_EXPOSURE:,} sampled tokens across five epoch index sets** "
        f"(average **{DFM9_TOTAL_EXPOSURE / DFM9_EPOCHS:,.1f} tokens/epoch**). It starts from the exhaustive DFM8 inventory and replaces the affected source exposures with exact DFM9 analytics.",
        "",
        "A Hugging Face card or repository licence is treated as metadata, not proof that the publisher owned every embedded work. "
        "Mixtures and transformation datasets therefore retain their upstream lineage classification.",
        "",
        "## Legal interpretation used",
        "",
        "- [DSM Directive Articles 3 and 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790) are implemented in Denmark by [Copyright Act sections 11 c and 11 b](https://www.retsinformation.dk/eli/lta/2023/1093). Section 11 c is the candidate basis for reproductions/extractions by a qualifying research organisation for scientific research, where the project has lawful access and stores copies with appropriate security. Rights holders cannot contract out of section 11 c.",
        "- Section 11 b is the general TDM route. It also requires lawful access, but fails where rights were expressly reserved in an appropriate manner. The project did not preserve complete acquisition-time opt-out evidence. FLAN v2, SciRIFF, and four uncovered OpenHermes families are recorded as project-owner Article 4 determinations despite that evidentiary limitation; this is not a general clearance of other sources under Article 4.",
        "- Direct licences/public-domain status and agreements are used first. Article 3 is a fallback only for uncovered copyright/database-right components; it does not cure lack of lawful access.",
        "- CC-BY-NC and CC-BY-NC-SA are direct permission only for uses satisfying NonCommercial and the other licence conditions. They are not treated as permission for future commercial use.",
        "",
        "## Summary",
        "",
        "| Classification | Sources | Tokens/epoch | Share |",
        "|---|---:|---:|---:|",
    ]
    for category in sorted(counts):
        lines.append(
            f"| `{category}` | {counts[category]} | {tokens[category] / DFM9_EPOCHS:,.1f} | {tokens[category] / DFM9_TOTAL_EXPOSURE:.2%} |"
        )

    lines += [
        "",
        "## Answer to the three-way question",
        "",
        f"1. **OK through other licensing/status:** {direct_count} sources, {direct_tokens / DFM9_EPOCHS:,.1f} average tokens/epoch ({direct_tokens / DFM9_TOTAL_EXPOSURE:.2%}), but only within the recorded scope and obligations.",
        f"2. **Require the research TDM exception for the current project:** {article3_count} sources, {article3_tokens / DFM9_EPOCHS:,.1f} average tokens/epoch ({article3_tokens / DFM9_TOTAL_EXPOSURE:.2%}), for all or some content. Another {fallback_count} mixed derivative sources, {fallback_tokens / DFM9_EPOCHS:,.1f} average tokens/epoch ({fallback_tokens / DFM9_TOTAL_EXPOSURE:.2%}), may require Article 3 only for uncovered components.",
        f"3. **Use the regular/non-research TDM exception:** {article4_count} mixed sources, {article4_tokens / DFM9_EPOCHS:,.1f} average tokens/epoch ({article4_tokens / DFM9_TOTAL_EXPOSURE:.2%}), currently use section 11 b/Article 4 for uncovered FLAN v2, SciRIFF, and four OpenHermes source families by project-owner determination. Other Article-3-dependent sources/components would also need Article 4 for non-research retraining unless direct permission is obtained, but are not currently cleared under that route.",
        "",
        "## Sources by classification",
        "",
    ]
    for category in sorted(by_class):
        lines += [f"### `{category}`", ""]
        lines.extend(f"- `{source_id}`" for source_id in by_class[category])
        lines.append("")

    lines += [
        "## Blocking human/legal checks",
        "",
        "- Confirm SDU/DFM and this training activity satisfy Article 3's research-organisation, scientific-research, lawful-access, beneficiary and secure-retention conditions.",
        "- Classify the DBC and Lex.dk agreements for the Commission template and review any unconfirmed retention, source-redistribution, attribution, duration, security and downstream-use terms; training and model release are confirmed.",
        "- Preserve the recorded component decisions for Sapient, DOLCI, and DFM Dyna; FLAN v2, SciRIFF, and four OpenHermes families use project-owner Article 4 determinations, MoT uses a residual-risk acceptance, and WildChat, TV2R, and four source-retaining transformation datasets have recorded direct bases, with privacy controls separate.",
        "- Review third-party generator-output terms for the four Tulu persona sources.",
        "- For any non-research retraining, perform a fresh Article 4 opt-out check at acquisition time; current HF tags are not enough.",
        "",
        f"Machine-readable detail: `{OUTPUT.relative_to(ROOT)}`.",
        "Component-level evidence: `legal/reports/dfm9-article3-component-audit.md`.",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {OUTPUT}")
    print(f"Wrote report to {REPORT}")


if __name__ == "__main__":
    main()
