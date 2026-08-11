---
type: Policy Record
title: English Eval Remediation Hypothesis
description: 'Part of Data Mix Policy: English Eval Remediation Hypothesis.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# English Eval Remediation Hypothesis

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Recorded on 2026-05-31. Updated on 2026-06-12. Confidence: medium for causal
attribution, high for local source-filter facts.

Problem: DFM/DFM2 improves Danish coverage but can underperform the original
Sapient run on English factual/commonsense/reading-comprehension evaluations
such as `MMLU`, `Winogrande`, `ARC-C`, `HellaSwag`, `DROP`, and `BoolQ`.

Local evidence:

- Original Sapient sampling had broad `flan` as the largest component:
  `23,896,311,328` covered tokens across four epochs, or `42.6%` of the
  original covered-token budget. It also had `tasksource` at `617,688,319`
  covered tokens.
- The source filter now denies broad `sapient_cleaned/data_clustered/flan/**`
  and `sapient_cleaned/data_clustered/tasksource/**`, with narrow allow
  overrides only for selected math/science/commonsense/reasoning tasks.
- The denied FLAN/Tasksource space included many English benchmark-adjacent
  instruction families: ARC, BoolQ, DROP, SQuAD, TriviaQA, Natural Questions,
  SuperGLUE/GLUE, ANLI/SNLI/MNLI, CoQA/QuAC, summarization/news, dialogue, and
  broad commonsense tasks.
Superseded, 2026-06-12: the older claim that `scienceqa.jsonl` is denied is
stale. Current DFM4 source filtering includes ScienceQA. The current Platypus
denials are only `reclor.jsonl` and `scibench.jsonl`, plus the Tasksource
ReClor recast.

Likely explanation:

- `MMLU` loss is probably mostly factual/world-knowledge and broad
  instruction coverage loss, not just missing exact MMLU-style rows.
- `ARC-C`, `BoolQ`, and `DROP` loss is likely direct removal of related
  QA/reading-comprehension formats from broad FLAN.
- `Winogrande` and `HellaSwag` are partially protected because narrow FLAN
  allow overrides include `winogrande` and `hellaswag`, but the current caps
  may still be much smaller than the original broad FLAN exposure.

Updated DFM4 assessment, 2026-06-12:

- The direct FLAN train-derived sources for `Winogrande`, `HellaSwag`,
  `ARC`, `BoolQ`, `DROP`, `RACE`, `TriviaQA`, `SQuAD`, and several
  commonsense/science families are included by current source filtering.
- The excluded original Sapient files most likely to hurt these English evals
  are indirect support sources rather than the exact benchmark families:
  Natural Questions and MS MARCO for factual/open QA and BoolQ-like reading;
  ReClor and SciBench for hard reasoning/science transfer; dialogue/social
  commonsense families for Winogrande/HellaSwag-style pragmatics; and broad
  review/sentiment/opinion classification for general instruction-following and
  classification calibration.
- WMT/newscomm exclusions are mainly a translation/multilingual loss and are
  not expected to be first-order drivers for Winogrande, HellaSwag, ARC, BoolQ,
  or MMLU, except through general English exposure.

Per-source risk review for the first four high-impact excluded families,
2026-06-12. Confidence: high for local excluded-file counts and source-filter
state; medium for upstream provenance/GDPR judgments from dataset cards/papers.

1. Natural Questions / MS MARCO: `10` excluded Sapient FLAN files. Natural
   Questions files are derived from real Google search queries with Wikipedia
   answers. MS MARCO files are derived from real Bing queries, web passages,
   and human-written answers. Provenance risk is medium/high because project
   policy treats Google/Bing search-derived data as harsh-robots/relevant-path
   cases; MS MARCO terms also disclaim ownership of underlying web documents.
   GDPR/PII risk is medium because queries are anonymized/aggregated but still
   originate from real users and can contain personal or sensitive facts.
   Affected local files: the four `natural_questions_open` FLAN variants, two
   NIV2 `naturalquestion_answer_generation` variants, and four NIV2
   `msmarco_answer_generation` / `msmarco_question_generation` variants.

2. ReClor / SciBench: `3` excluded files:
   `sapient_cleaned/data/Platypus/reclor.jsonl`,
   `sapient_cleaned/data/Platypus/scibench.jsonl`, and
   `sapient_cleaned/data_clustered/tasksource/reclor.parquet`. ReClor says
   passages come from websites/books not owned by the dataset authors and is
   non-commercial research only. SciBench says problems are sourced from
   instructional/college textbooks. Provenance/copyright risk is high; GDPR/PII
   risk is low. They remain excluded as eval-only/provenance-sensitive sources.

3. Dialogue/chat: `82` excluded files. This bucket includes QReCC/wiki_dialog
   FLAN variants, DailyDialog/dailydialog, PersonaChat/persona, AirDialogue,
   Deal-or-No-Deal, CaSiNo, Curiosity Dialogs, DialogRE, DREAM, MUTUAL,
   Dialogue NLI, MRDA, and Switchboard recasts. Provenance risk varies:
   QReCC combines NQ/TREC/QuAC-style sources and a large web-passage retrieval
   collection; DailyDialog is human-written and CC-BY-NC-SA; other dialogue
   datasets range from crowd-written/role-play to conversation transcripts.
   GDPR/PII risk is medium/high because many files contain human or simulated
   conversations, named entities, personal preferences, or relationship facts.
   Even synthetic/crowd-written chat can encourage memorization of realistic
   personal profiles. Current project policy keeps this bucket excluded.

4. Social/toxicity/emotion/sarcasm: `97` excluded files. This bucket includes
   TweetEval/twitter/tweet QA/emotion/sarcasm files, HateXplain, HateEval,
   hate_speech_offensive, implicit-hate, Dynahate, Civil Comments/Jigsaw,
   GoEmotions, CrowdFlower text emotion, WNUT, and Twitter financial news
   sentiment. Provenance risk is medium: some datasets are CC0 or benchmark
   releases, but many are social-platform posts, comments, or rehosted user
   content with platform/API constraints. GDPR/PII risk is high because the
   text is generated by real users, often includes handles, names, URLs,
   identity attributes, abusive content, or event-specific sensitive opinions.
   Civil Comments is better documented and CC0, but still contains public
   comments from identifiable contexts; TweetEval/HateXplain-style sources
   remain excluded under the non-public-person personal-data policy.

DFM5 policy adjustments, 2026-06-12. Confidence: medium.

DFM5 baseline intent update, 2026-06-12. Confidence: high for local filter
inspection and file counts; medium for whether each current exclusion remains
final policy. DFM5 should be the mix that includes all locally available
original Sapient cleaned sources except sources still explicitly excluded by
`config/data/source_filter.yaml`, plus later non-Sapient additions. With the
current source-filter semantics (`allow_overrides` wins before `deny`),
Sapient cleaned data files are:

Superseded by the applied reconsideration immediately below.

```text
allowed: 4,835
denied:    378
```

Current denied Sapient categories by file count:

```text
FLAN reviews/opinion/email:                  154 files, ~123.16 GB
FLAN dialogue/chat/persona:                   66 files, ~0.19 GB
FLAN toxicity/hate/emotion/comments:          56 files, ~0.05 GB
FLAN WMT / News Commentary harsh-robots:      42 files, ~64.33 GB
FLAN Twitter/TweetEval/social:                20 files, ~0.03 GB
Tasksource social/toxicity/emotion/spam:      16 files, ~0.02 GB
FLAN SMS/spam:                                 6 files, ~0.01 GB
FLAN Natural Questions / NQ Open:              6 files, ~0.05 GB
FLAN MS MARCO:                                 4 files, ~0.01 GB
Tasksource dialogue/chat/transcripts:          3 files, small
Platypus ReClor/SciBench:                      2 files, ~0.01 GB
Tasksource reviews/opinion:                    2 files, small
Tasksource ReClor:                             1 file, small
```

Important policy conflict to resolve before final DFM5 sampling: earlier DFM5
notes proposed including Natural Questions / Natural Questions Open subject to
PII inspection, but the current filter still denies local Sapient NQ/NQ-Open
FLAN transforms as a harsh-robots/search-derived family. MS MARCO remains
under review and is also denied. WikiDialog, DREAM, and MuTual have already
been allow-overridden for DFM5 despite broader dialogue deny patterns, so they
are not part of the 378 denied files.

DFM5 source-filter reconsiderations applied, 2026-06-12. Confidence: high for
local filter dry-run and exact allow-overrides. `config/data/source_filter.yaml`
now allow-overrides the accepted factual QA and lower-risk dialogue/role-play
families:

```text
natural_questions_open
naturalquestion
dailydialog / daily_dialog
personachat
deal_or_no
casino
air_dialogue
wiki_dialog
dream
mutual
tasksource/mutual.parquet
```

The first seven entries above were newly added in this update; WikiDialog,
DREAM, and MuTual were already applied earlier. The broad deny rules remain as
defaults for unreconsidered chat/search/social sources. Dry-run verification
was followed by rebuilding the filtered source symlink tree:

```text
Input:          data/downloads/datasets
Allowed files: 10,605
Denied files:     328
Allowed bytes: 820,913,796,916
```

Rebuild log: `logs/build_filtered_source_tree_dfm5_reconsiderations_20260612.log`.

Sapient-only data-file counts after the update:

```text
allowed: 4,885
denied:    328
```

Remaining denied Sapient categories:

```text
FLAN reviews/opinion/email:                  154 files, ~123.16 GB
FLAN toxicity/hate/emotion/comments:          56 files, ~0.05 GB
FLAN WMT / News Commentary harsh-robots:      42 files, ~64.33 GB
FLAN dialogue/chat/persona residual:          22 files, ~0.09 GB
FLAN Twitter/TweetEval/social:                20 files, ~0.03 GB
Tasksource social/toxicity/emotion/spam:      16 files, ~0.02 GB
FLAN SMS/spam:                                 6 files, ~0.01 GB
FLAN MS MARCO:                                 4 files, ~0.01 GB
Tasksource dialogue/chat/transcripts:          3 files, small
Platypus ReClor/SciBench:                      2 files, ~0.01 GB
Tasksource reviews/opinion:                    2 files, small
Tasksource ReClor:                             1 file, small
```

Verification found no denied files matching the reconsidered NQ/NQ-Open,
DailyDialog, PersonaChat, Deal-or-No-Deal, CaSiNo, AirDialogue, WikiDialog,
DREAM, or MuTual terms. MS MARCO remains under review and denied.

Remaining-denied reconsideration pass, 2026-06-12. Confidence: high for local
file lists and sampled local rows; medium for policy recommendations.

Potentially includable after an explicit DFM5 decision:

- `msmarco`: `4` FLAN/NIV2 files, about `0.01 GB`. Local rows retain only
  transformed `instruction`, `response`, and `condition`, not source URLs. The
  sampled examples are factual web-passage QA. Main residual risk is Bing/web
  provenance rather than obvious PII in the transformed rows. If included, use
  the original generic FLAN cap or a tighter DFM5 cap.
- `qrecc`: `4` FLAN dialogue files, about `0.05 GB`. It is conversational QA
  with web/Wikipedia-style retrieval origins. Local samples looked noisy, so
  include only if we value conversational QA coverage and accept quality
  review/capping.
- `curiosity_dialogs`: `6` FLAN files, about `0.025 GB`. Information-seeking
  dialogue; sampled rows looked like generic factual dialogue rather than
  private personal chat. Candidate for inclusion with generic FLAN caps.
- `dialogue_nli`: `1` Tasksource file, about `0.002 GB`. Persona-style NLI
  statements; conceptually close to PersonaChat, which DFM5 already accepts.
  Candidate for inclusion if we accept persona-like synthetic/crowd-written
  sentences.
- `newscomm`: `14` FLAN files, about `0.024 GB`. Translation/classification
  from News Commentary. It remains denied under the earlier harsh-robots/source
  route rationale, but it is small and translation-oriented; include only if
  that source-route concern is relaxed.

Generally keep excluded:

- Review/opinion/email/user-product corpora, especially Amazon/Yelp/IMDb/app
  reviews/AESLC/opinion abstracts: large user-authored text, highest remaining
  byte share, and easy to replace with cleaner instruction/summarization data.
- Twitter/TweetEval/social, SMS/spam, WNUT, hate/toxicity/offensive/emotion,
  GoEmotions, Civil Comments, and related comment datasets: user text with
  protected attributes, names/handles/URLs, abuse, or event-specific sensitive
  opinions.
- `dialogre`, `pragmeval_mrda`, and `pragmeval_switchboard`: transcript or
  TV/script/dialogue-extraction style sources with named speakers and weaker
  marginal value.
- `wmt`: very large translation block (`28` files, about `64.3 GB`) and still
  covered by the harsh-robots/source-route rationale. Prefer OPUS and approved
  Danish/translation sources unless explicitly relaxing that rule.
- ReClor and SciBench: remain explicit project exclusions.

- Include Natural Questions / Natural Questions Open for DFM5, unless row-level
  PII inspection finds actual personal data in the questions. The rationale is
  that the rows are mostly search-style factual questions and Wikipedia-derived
  answers; the remaining practical risk is PII in query text rather than
  ordinary copyright/licence terms.
- Keep MS MARCO under review rather than include automatically. Local Sapient
  MS MARCO Parquet transforms retain only `instruction`, `response`, and
  `condition`, so source URLs/domains are not available locally. The sampled
  rows contain generic Bing web snippets such as government benefits, health,
  pension/finance advice, company profiles, BBB/D&B-style pages, and technical
  passages. Upstream MS MARCO says passages come from real web documents
  retrieved by Bing and warns that Microsoft may not own underlying document
  rights.
- Keep ReClor and SciBench excluded for DFM5.
- Include DailyDialog and lower-risk role-play/negotiation dialogue sources for
  DFM5: DailyDialog/dailydialog, PersonaChat/persona, Deal-or-No-Deal,
  CaSiNo, and likely AirDialogue after final file-pattern review. Continue to
  exclude QReCC/wiki_dialog, MUTUAL, Switchboard/MRDA, DialogRE, DREAM, and
  other dialogue sources that are web-retrieval, transcript-like, or
  named-entity-heavy unless separately approved.
- Continue excluding Tweet/Twitter/hate/toxicity/emotion/sarcasm sources for
  now. Civil Comments/Jigsaw is lower-provenance-risk than Twitter data because
  it is CC0 and documented as public comments without user IDs, but it remains
  GDPR/PII-sensitive: free-form comments can include names, URLs/contact links,
  political opinions, protected-class references, insults/threats, and
  article/timestamp context. If ever included, use tight caps plus PII/URL/name
  scrubbing and avoid examples likely to reproduce comments verbatim.

Refinement on MuTual / WikiDialog / DREAM, 2026-06-12. Confidence: medium.

- WikiDialog is not a GDPR-heavy source: upstream describes it as synthetic
  information-seeking dialogue grounded in English Wikipedia. The main reasons
  to keep it out are scale/control and synthetic quality. Local Sapient
  WikiDialog transforms are very large (`4.15M`, `1.24M`, `2.08M`, and
  `0.62M` rows across four Parquet files), sometimes awkwardly reconstruct
  previous dialogue from a response, and would inject a large amount of
  Wikipedia-style synthetic dialogue unless capped and reviewed separately.
- MuTual is based on Chinese student English listening comprehension exams, and
  local rows are multiple-choice continuation tasks. GDPR risk is low; the
  stronger arguments for exclusion are benchmark-style/eval-adjacent training
  and limited marginal value once HellaSwag/Winogrande/DailyDialog/persona/
  negotiation data are included. It can be reconsidered as an optional tightly
  capped reasoning-dialogue source if benchmark adjacency is accepted.
- DREAM is also exam-derived dialogue reading comprehension. GDPR risk is low,
  but it is a named benchmark with direct train/dev/test style tasks and
  multiple T0/NIV2 transforms in Sapient. Keep excluded if preserving clean
  dialogue-RC evaluation boundaries matters; otherwise it is an optional
  capped source for dialogue reasoning rather than a privacy exclusion.

Superseded later on 2026-06-12 by project decision: include MuTual, WikiDialog,
and DREAM for DFM5 with original Sapient sampling caps.

Implementation note, 2026-06-12. Confidence: high. `config/data/source_filter.yaml`
now allow-overrides:

- `sapient_cleaned/data_clustered/flan/*wiki_dialog*.parquet`
- `sapient_cleaned/data_clustered/flan/*dream*.parquet`
- `sapient_cleaned/data_clustered/flan/*mutual*.parquet`
- `sapient_cleaned/data_clustered/tasksource/mutual.parquet`

No DFM4/DFM5 sampling override was added for these families. They therefore
inherit the original generic Sapient caps already used by the sampling config:
FLAN files match `sapient_cleaned__data_clustered__flan__` with
`max_per_file: 5_000`; Tasksource MuTual matches
`sapient_cleaned__data_clustered__tasksource__` with `max_per_file: 10_000`.
Dry-run verification after the edit reported `10,555` allowed files and `378`
denied files, and all local MuTual, WikiDialog, and DREAM files matched
`allowed`.

Candidate remediation mix:

- Add a small English open-text self-supervised slice, initially `5-10B`
  covered tokens per epoch, from cleaner Common Pile components rather than
  broad web text. Prefer filtered/public-domain/open-license components such as
  Wikimedia, StackExchange, PubMed, arXiv abstracts/papers, USGPO/regulations,
  USPTO, public-domain books/reviews, and Library of Congress material. Avoid
  YouTube/IRC/social-chat components by default because of PII/GDPR and
  conversation-quality risks.
- Convert this slice with the same objective family as DFM2, but in English:
  direct continuation, prefix continuation, denoising, and span filling. This
  should help language modeling, factual recall, and reading-comprehension
  robustness without reintroducing the broad FLAN aggregate.
- Upscale existing approved English instruction sources before re-admitting
  risky Sapient aggregates: `allenai_tulu_*`, `dolci_*`,
  `nemotron_instruction_reasoning_off`, `allenai_if_sft_verified`, selected
  `nemotron_multilingual`, `no_robots`, and retained allowed FLAN/Tasksource
  science/commonsense tasks.
- For benchmark-adjacent train data, make an explicit policy distinction:
  using official train splits of ARC/BoolQ/DROP/HellaSwag/Winogrande is useful
  for capability recovery but should be marked as benchmark-adjacent and kept
  separate from “clean generalization” runs. If included, hash-dedupe against
  evaluation prompts and report it clearly.

Recommended first ablation:

- Keep DFM2 unchanged.
- Add `5B` covered tokens per epoch of English Common-Pile-derived
  self-supervised tasks from the cleaner components above.
- Add `2-4B` covered tokens per epoch by raising caps on approved English SFT
  sources.
- Optionally add a tightly capped, benchmark-adjacent train-only slice for
  ARC/BoolQ/DROP/HellaSwag/Winogrande only in a separate run label.
