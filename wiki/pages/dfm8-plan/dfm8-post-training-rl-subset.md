---
type: Plan Record
title: DFM8 Post-Training / RL Subset
description: 'Part of DFM8 Plan: DFM8 Post-Training / RL Subset.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# DFM8 Post-Training / RL Subset

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Post-training subset plan, 2026-07-12. Confidence: medium. Starting from the
DFM6-DFM7 XL gas2 epoch-5 checkpoint, a DFM8 subset for further
mid-training/post-training should be narrower than the full DFM8 mix and should
target behavior rather than broad capability. Prioritize:

1. Multi-turn chat and instruction-following:
   - `dfm8-synthetic-multiturn-danish-english-chat`
   - `dfm8-synthetic-constrained-format-following`
   - `dfm8-openhermes-en` and `dfm8-openhermes-da`, sampled after positive
     audit
   - `kobprof_skolegpt_instruct`
   - `no_robots`, `allenai_if_sft_verified`,
     `allenai_if_multi_constraints_upto5`, and `allenai_rlvr_ifeval`
2. Agentic/tool calling:
   - `dfm8-synthetic-native-tool-calling`
   - corrected native-tool sources: `dolci_native_tool_use`,
     `glaive_native_tool_use`, `toolace_native_tool_use`,
     `xlam_native_tool_use`
   - `nemotron_agentic` and `nemotron_instruction_reasoning_off`, capped and
     converted to the same Gemma4/native tool-call contract
3. Communication/control tasks:
   - `dfm8-synthetic-danish-summarization-rewrite-controls`
   - selected Danish instruction data such as `oliverkinch_*`,
     `synquid_ifbench_train`, `synquid_wiki_instruct_da`, and
     `synquid_danish_verifiable_reasoning`
4. Keep only small anchors for broad ability:
   - small slices of strict math/code and high-quality general SFT to prevent
     regression, but do not let math/code/pretraining-style data dominate this
     phase.

Suggested SFT/post-training proportions:

| Bucket | Approx share |
| --- | ---: |
| Tool/agentic trajectories | 30-40% |
| Multi-turn chat | 15-25% |
| Instruction/format following | 15-25% |
| Danish instruction and summarization controls | 15-25% |
| Broadly sampled math/code/general anchors | 20% |

Use Gemma4 chat template and the same native tool-call representation used in
evaluation. For this phase, avoid continuation-style and broad transform data
unless the goal is still broad capability training rather than alignment. The
20% anchor slice is deliberate regression control, not a return to broad
pretraining-style sampling.

Implementation status, 2026-07-12. Confidence: high from local file inspection
and syntax checks.

DFM8-post now has separate sampling artifacts:

- `scripts/build_tokenized_dfm8_post_tree.py`: builds
  `data/tokenized_dfm8_post` as a filtered symlink union from
  `data/tokenized_dfm8`. This is required because `data_io/sample_tokenized.py`
  samples unmatched tasks with default `repeat=1`; pointing the sampler at full
  DFM8 would leak broad sources into the post-training mix.
- `data_io/prefix_config_dfm8_post.yaml`: post-training sampler config. It
  prioritizes DFM8 synthetic tool/chat/format/summarization data, audited
  English/Danish OpenHermes derivatives, native tool-use sources, Danish
  instruction/control sources, and a deliberately restrained broad-anchor
  section intended to be about 20% of sampled tokens after report-driven tuning.
- `scripts/prepare_dfm8_post_data.sh`: builds the filtered tree and samples
  `data/sampled_dfm8_post`, writing analytics to
  `data/show_analytics_dfm8_post.md`.
- `config/data/dfm8_post.yaml`: training data config pointing at
  `data/sampled_dfm8_post`.

Run after the final DFM8 tokenized tree is ready:

```bash
cd /work/dfm/HRM-Text
bash scripts/prepare_dfm8_post_data.sh
```

After sampling, inspect `data/show_analytics_dfm8_post.md` and tune
`data_io/prefix_config_dfm8_post.yaml` if the broad-anchor tasks are not close
to 20% of sampled tokens. The current sampler controls mix weights through
per-source caps and repeats rather than hard token-budget buckets.

Lightweight validation on the current incomplete DFM8 tokenized tree:

```bash
cd /work/dfm/HRM-Text
python scripts/build_tokenized_dfm8_post_tree.py --force
```

This linked `4,146` current tasks into `data/tokenized_dfm8_post`: `4,096`
focus tasks and `50` broad-anchor tasks. DFM8-specific synthetic/OpenHermes
derivatives will only appear after they have been integrated into
`data/tokenized_dfm8`.

RL / preference plan, 2026-07-12. Confidence: medium. For the same goals, start
with DPO-style preference tuning before PPO/GRPO. Sources:

- build DPO pairs from DFM8 tool-call audits and smoke/eval failures:
  chosen = valid one-call/native-tool output or correct clarification/no-tool
  answer; rejected = malformed calls, repeated calls, wrong tool, missing tool,
  over-eager tool use, or answer-without-required-tool.
- build instruction-following pairs from IFEval/IFBench-style constraints:
  chosen follows all constraints; rejected violates one constraint while being
  fluent.
- use judge-generated preference pairs for Danish summaries and multi-turn chat:
  chosen preserves requested length/tone/format and handles follow-ups; rejected
  is verbose, ignores language, loses constraints, or resets conversation state.
- consider public function-calling preference datasets such as
  `roborovski/glaive-tool-usage-dpo`,
  `roborovski/synthetic-tool-calls-v2-dpo-pairs`, and
  `interstellarninja/tool-calls-dpo` after conversion/audit.

How to obtain DPO pair sources, 2026-07-12. Confidence: medium from Hugging
Face search metadata and local pipeline design.

There are three acquisition paths:

1. Public HF DPO datasets. Download and convert them like other HF sources:

```bash
cd /work/dfm/HRM-Text
huggingface-cli download roborovski/glaive-tool-usage-dpo \
  --repo-type dataset \
  --local-dir data/downloads/datasets/roborovski_glaive_tool_usage_dpo
huggingface-cli download roborovski/synthetic-tool-calls-v2-dpo-pairs \
  --repo-type dataset \
  --local-dir data/downloads/datasets/roborovski_synthetic_tool_calls_v2_dpo_pairs
huggingface-cli download interstellarninja/tool-calls-dpo \
  --repo-type dataset \
  --local-dir data/downloads/datasets/interstellarninja_tool_calls_dpo
```

Then add explicit downloader manifest entries and a DPO converter that emits
`prompt/messages`, `chosen`, `rejected`, task-family tags, tool schema metadata,
and conversion/audit diagnostics. Do not mix these into DFM8 SFT by default;
keep them in a DPO-specific export.

2. Project-generated pairs from DFM8 audits and eval failures. For tool calling,
format following, summaries, and multi-turn chat, the best project-specific
pairs come from artifacts we already produce: rejected audit rows, smoke-test
failures, eval generations, and corrected/regenerated rows. Convert these as:
chosen = audited/fixed response; rejected = malformed, over-eager, wrong-tool,
wrong-format, verbose, or constraint-violating response. These pairs are more
valuable than generic preference data because they target exactly the failure
modes seen in DFM5-DFM7.

3. Environment/verifier-generated pairs. For BFCL-shaped tool calling,
math-answer-contract, and exact-format tasks, generate multiple candidate
responses from checkpoints or teachers, score them with deterministic
validators, and build chosen/rejected pairs from pass/fail or higher/lower
scores. This should be the bridge between SFT DFM8-post and later GRPO/PPO.

All DPO sources should be rendered/audited against the same Gemma4 chat and
native tool-call contract as DFM8. Store them separately from
`data/sampled_dfm8_post` until the DPO training code and loss path are explicit.

DFM8-preference export status, 2026-07-12. Confidence: high from local
downloads, schema inspection, conversion, and marker audits.

The first public-HF DPO/preference batch has been downloaded under
`data/downloads/datasets/` and converted to a separate Gemma4-template-safe
preference export at `data/dfm8_preference_pairs`. This is intentionally not
mixed into SFT sampling. The converter is
`scripts/prepare_dfm8_preference_data.py`.

Command that worked:

```bash
cd /work/dfm/HRM-Text
python scripts/prepare_dfm8_preference_data.py --force
```

The converter writes one JSONL file per source plus
`data/dfm8_preference_pairs/manifest.json`. Each row contains
`prompt_messages`, `tools`, `chosen_completion_messages`, and
`rejected_completion_messages`. Tool-call rows are represented as native
Gemma/OpenAI-style message sequences, e.g. `assistant.tool_calls -> tool ->
assistant`, not as literal XML or ChatML strings.

Converted rows:

| Source | Local folder | Rows | Notes |
| --- | --- | ---: | --- |
| `roborovski/glaive-tool-usage-dpo` | `roborovski_glaive_tool_usage_dpo` | 42,014 | Tool-use preference rows; tool schemas extracted from old system text and rendered as native `tools`. |
| `roborovski/synthetic-tool-calls-v2-dpo-pairs` | `roborovski_synthetic_tool_calls_v2_dpo_pairs` | 8,005 | Structured accepted/rejected tool call/result/final-answer trajectories converted to native tool-call sequences. |
| `roborovski/synthetic-toolformer-dpo-pairs` | `roborovski_synthetic_toolformer_dpo_pairs` | 289 | Small structured tool preference set. |
| `interstellarninja/tool-calls-dpo` | `interstellarninja_tool_calls_dpo` | 235 | Small XML-style function-call DPO set; XML targets normalized or skipped. |
| `Hodfa71/saga-da-delta-dpo-r1` | `hodfa71_saga_da_delta_dpo_r1` | 7,410 | Danish grammar/completion preference pairs, wrapped as an instruction to continue Danish text naturally. |
| `Hodfa71/saga-da-delta-dpo-r2` | `hodfa71_saga_da_delta_dpo_r2` | 7,307 | Danish grammar/completion preference pairs, round 2. |
| `allenai/Dolci-Think-DPO-7B` | `allenai_dolci_think_dpo_7b` | 149,882 | General/reasoning preference data; rows with old template markers or excessive length skipped. |
| `argilla/distilabel-math-preference-dpo` | `argilla_distilabel_math_preference_dpo` | 2,418 | Math preference pairs. |
| `tzwilliam0/instruction_following_dpo_filtered` | `tzwilliam0_instruction_following_dpo_filtered` | 10,262 | Instruction-following preference pairs. |
| `tzwilliam0/instruction_following_dpo_filtered_add` | `tzwilliam0_instruction_following_dpo_filtered_add` | 18,813 | Additional instruction-following preference pairs. |
| `mlabonne/chatml-OpenHermes2.5-dpo-binarized-alpha` | `mlabonne_chatml_openhermes25_dpo_binarized_alpha` | 9,197 | OpenHermes-derived DPO; ChatML wrappers are not preserved. |
| `Capx/Agentic-DPO-V0.1` | `capx_agentic_dpo_v01` | 4,744 | General agentic DPO; converted from `data.json`. |

Total exported rows: `260,576`. Family counts:

| Family | Rows |
| --- | ---: |
| `general_reasoning` | 149,882 |
| `tool_calling` | 42,249 |
| `instruction_following` | 29,075 |
| `danish_grammar_completion` | 14,717 |
| `format_following_openhermes` | 9,197 |
| `tool_calling_structured` | 8,294 |
| `agentic_general` | 4,744 |
| `math_preference` | 2,418 |

Language counts: `245,859` English rows and `14,717` Danish rows.

Template-safety audit:

```bash
cd /work/dfm/HRM-Text
python - <<'PY'
from pathlib import Path
import json
bad=[]
markers=['<|im_start|>','<|im_end|>','<tool_call>','</tool_call>','<tools>','</tools>','[/INST]','<s>[INST]','<|endoftext|','<|endoftext|>']
for p in Path('data/dfm8_preference_pairs').glob('*.jsonl'):
    if p.name == 'render_failures.jsonl':
        continue
    with p.open() as f:
        for i,line in enumerate(f):
            row=json.loads(line)
            text=json.dumps(row.get('chosen_completion_messages'), ensure_ascii=False)+json.dumps(row.get('rejected_completion_messages'), ensure_ascii=False)+json.dumps(row.get('prompt_messages'), ensure_ascii=False)
            hit=[m for m in markers if m in text]
            if hit:
                bad.append((p.name,i,hit))
                break
print('bad_files', len(bad))
for item in bad[:20]: print(item)
PY
```

Result: `bad_files 0`. The export size is currently about `3.1G`.

Adjacent sources not yet part of `DFM8-preference`:

- `qnguyen3/dpo-r1`: local schema is SFT-shaped `messages` plus `source`, not
  direct `chosen`/`rejected` pairs.
- `zake7749/Qwen3.6-35B-A3B-Tool-Calling`: useful tool-call SFT source, but
  the local file is final SFT rows (`tools`, `messages`), not the preference
  pairs described in the card.
- `KKACHI-HUB/Tool-DPO-LLaMA-Factory`: metadata is visible with the provided
  token, but file download still returns "awaiting review from repo authors".
  Do not count this source until actual parquet download succeeds.

DFM8-preference next-step plan, 2026-07-12. Confidence: medium.

Keep `DFM8-preference` as a separate preference-training artifact, not part of
`DFM8-post` SFT sampling. The purpose is to support DPO-style tuning after
DFM8/DFM8-post SFT, especially for tool calling, instruction following,
Danish grammaticality, and answer-format control.

Planned stages:

1. Source QA and stratification.
   - Inspect examples by `task_family`, source, language, and length bucket.
   - Verify chosen/rejected semantics for each source; especially review
     `general_reasoning` and `agentic_general` for noisy or stylistically odd
     preferences.
   - Decide caps by family before training. Initial default should not let
     `allenai_dolci_think_dpo_7b` dominate just because it is large.
   - Keep `danish_grammar_completion` as a small targeted Danish slice, not as
     the main Danish alignment signal.
2. Converter hardening.
   - Add an explicit unit/smoke test that renders one row per source through
     `data_io/chat_templates/gemma4_native_chat.jinja`.
   - Add a stricter tool-schema audit: every `tools` item must have
     `type=function`, a valid function name, object parameters, and no old XML
     wrappers in prompt/chosen/rejected messages.
   - Preserve the current marker audit (`bad_files 0`) as a required gate.
3. Include pending/review sources only when safe.
   - Retry `KKACHI-HUB/Tool-DPO-LLaMA-Factory` after HF approval is complete;
     include only if actual parquet download succeeds and rows pass the same
     Gemma4 marker/tool audit.
   - Treat `zake7749/Qwen3.6-35B-A3B-Tool-Calling` and `qnguyen3/dpo-r1` as
     SFT/tool-call sources unless we derive negatives or recover true
     chosen/rejected pairs.
4. Project-specific pair generation.
   - Mine our eval/smoke/audit artifacts for pairs:
     chosen = fixed/audited response; rejected = observed failure.
   - Priority failure modes: wrong or missing tool call, over-eager tool use,
     repeated tool-call loops, malformed JSON/tool args, ignored output format,
     missing final boxed math answer, verbose summaries when brief was asked,
     and Danish language/grammar failures.
   - This path is cheap when using existing artifacts; it should be done before
     launching large new teacher-generation campaigns.
5. Verifier-generated pairs.
   - For tool calling, create BFCL-shaped prompts with deterministic validators
     for function name, JSON/schema, argument values, no repeated calls, and
     correct final answer after tool results.
   - For math, score final-answer extraction/boxed-answer compliance separately
     from reasoning quality.
   - For format following, use deterministic validators for JSON, tables,
     bullet counts, sentence counts, language, and exact labels.
   - Generate multiple candidates from target checkpoints or teachers, then
     build chosen/rejected pairs from validator scores.
6. Training integration.
   - Do not start DPO until there is an explicit DPO training entry point and
     config path. Required knobs: beta, learning rate, reference model path,
     max prompt/response length, family caps, and whether EMA/reference weights
     are used.
   - First run should be a small ablation on a copied checkpoint, not the main
     continuation run.
   - Evaluate before/after with the lite/full eval suites plus focused tool
     and format smoke tests.

Open design question: whether DPO should follow `DFM8-post` SFT or be run as a
short parallel branch from the same DFM8 checkpoint. Default recommendation is
SFT first, then DPO, because DPO assumes the model can already produce the
desired behavior often enough for preference tuning to sharpen it rather than
teach it from scratch.
