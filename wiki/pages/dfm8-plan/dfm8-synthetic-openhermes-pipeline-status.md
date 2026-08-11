---
type: Plan Record
title: DFM8 Synthetic/OpenHermes Pipeline Status
description: 'Part of DFM8 Plan: DFM8 Synthetic/OpenHermes Pipeline Status.'
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
# DFM8 Synthetic/OpenHermes Pipeline Status

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Snapshot, 2026-07-12 20:46 CEST. Confidence: high from local process, queue,
manifest inspection, HF upload commit URLs, and HF-side file-count verification.

Completed stages:

- Broad transform expansion/audit finished:
  `logs/dfm8_transform_expansion_dynamic_audits_c64_u070_20260709T110453`
  has `176` done, `0` failed, `0` pending/running. Source manifest reports
  `1,495,662` accepted transformed rows after the Common Pile prefix cap.
  Superseded 2026-07-12 20:46 CEST: the earlier 2026-07-12 19:01 note said
  this stage was local-only. The additional accepted rows have now been uploaded
  additively to the eight existing `schneiderkamplab/*` transform dataset repos
  as `data/dfm8-extra-train-*.jsonl.gz`, with each repo also receiving its
  local `filter_summary.json`. The accidental HRM-Text README files in
  `data/dfm8_transform_expansion_filtered/*/README.md` were deliberately not
  uploaded. Upload log:
  `logs/hf_upload_dfm8_transform_expansion_20260712T204643.json`.

  New uploaded DFM8 transform-expansion rows:

  | HF dataset repo | New rows | New files | Commit |
  |---|---:|---:|---|
  | `schneiderkamplab/common-pile-denoising` | `580,434` | `470` | `692ba5faebd4a64247dac93c4ada8c9f858e9508` |
  | `schneiderkamplab/common-pile-paragraph-reordering` | `43,821` | `14` | `4e9a98cb4b5694cbe52839b28ae920ebde0a29f7` |
  | `schneiderkamplab/common-pile-prefix-continuation` | `703,658` | `229` | `e69fb584d078a9a44ae586985c2c98eb98e73e45` |
  | `schneiderkamplab/common-pile-span-filling` | `572,098` | `1,423` | `95878b6da460dd61e2bc17df2c450889bdf628c7` |
  | `schneiderkamplab/danish-dynaword-denoising` | `137,520` | `86` | `fedf451723440a365253b508810702259ed16fb1` |
  | `schneiderkamplab/danish-dynaword-paragraph-reordering` | `34,931` | `22` | `bcd114189098e5f88cb4ef5530b1eee00a484603` |
  | `schneiderkamplab/danish-dynaword-prefix-continuation` | `201,507` | `88` | `0bd798071d400d280fed4b766f77b04f777bd516` |
  | `schneiderkamplab/danish-dynaword-span-filling` | `124,414` | `268` | `88219d9d022d24897df646e4491f938bc038e5e8` |
  | **Total** | **`2,398,383`** | **`2,600`** | |

  HF-side verification after upload showed the expected extra file counts:
  `470`, `14`, `229`, `1423`, `86`, `22`, `88`, and `268`, respectively, and
  `filter_summary.json` present in each repo.

  The older accepted transform datasets remain uploaded under `schneiderkamplab`:
  - `common-pile-denoising`
    (`f911cf777c891c454d571cbfbf0b04670f4c81a4`, `7` JSONL.GZ files)
  - `common-pile-paragraph-reordering`
    (`e227c5f1e5f2b64231c6a56fd0eb2f42651fcc95`, `16` JSONL.GZ files)
  - `common-pile-prefix-continuation`
    (`819dc27acb1f8debfcc7b5ab63ad4ee0e4c89156`, `19` JSONL.GZ files)
  - `common-pile-span-filling`
    (`58160ebc1320488dbc2e8c50d8284cc94cb09f99`, `7` JSONL.GZ files)
  - `danish-dynaword-denoising`
    (`6860137828a44c0785490f35923a720882a906d1`, `4` JSONL.GZ files)
  - `danish-dynaword-paragraph-reordering`
    (`52a85233f1e8d4c887ab6bcd435d875ca79b4db2`, `3` JSONL.GZ files)
  - `danish-dynaword-prefix-continuation`
    (`d0902a56428d8fb2493fb313482bf6bf5ac15c21`, `2` JSONL.GZ files)
  - `danish-dynaword-span-filling`
    (`d237f85be7b90963e405ea9a968525e41f1d1abc`, `2` JSONL.GZ files)
  - `transformations-danish-danish`
    (`178b5009f3f8a03af5a14e469204d60c90fb03c0`, `251` JSONL.GZ files)
  - `transformations-danish-english`
    (`b935c7770b5233dd6b03fce101968ec3804c75bd`, `251` JSONL.GZ files)
  - `transformations-english-danish`
    (`eec08f3429f6d5060fd2bfab5952f5361408181a`, `410` JSONL.GZ files)
  - `transformations-english-english`
    (`b5599187244c037e68e18076a0c4e7411d6cb5cc`, `389` JSONL.GZ files)
- Targeted DFM8 synthetic generation/audit/upload is complete in
  `export-upload-dfm8-synthetic`. It generated `4,800,000` rows, audited
  `4,580,233`, and accepted:
  - `dfm8-synthetic-code-debugging`: `340,711`
  - `dfm8-synthetic-constrained-format-following`: `838,905`
  - `dfm8-synthetic-danish-summarization-rewrite-controls`: `825,861`
  - `dfm8-synthetic-multiturn-danish-english-chat`: `414,196`
  - `dfm8-synthetic-native-tool-calling`: `836,675`
  - `dfm8-synthetic-strict-math-answer-contract`: `552,952`
  Upload status: verified on 2026-07-12. The local completed export was pushed
  or confirmed unchanged on Hugging Face under:
  - `schneiderkamplab/dfm8-synthetic-code-debugging`
    (`87e99f9815c1c4b484fecb4485a24e5c18277b1b`)
  - `schneiderkamplab/dfm8-synthetic-constrained-format-following`
    (`61850112550ef6631d04f89eb575b7bddc80cbd2`)
  - `schneiderkamplab/dfm8-synthetic-danish-summarization-rewrite-controls`
    (`3b528aa7510d3a7a5fea22a2b33e89b1a1a0d09c`)
  - `schneiderkamplab/dfm8-synthetic-multiturn-danish-english-chat`
    (`e345d051a5d8714975de3bb19b137e357d76d92c`)
  - `schneiderkamplab/dfm8-synthetic-native-tool-calling`
    (`3c2d177835beb79749a45143fd250fcedad5a6c9`)
  - `schneiderkamplab/dfm8-synthetic-strict-math-answer-contract`
    (`14ff86ffae606f6dee4e959d0a4fe2c5a3b5c1bd`)
- Base Danish OpenHermes translation/audit/upload is complete in
  `export-upload-dfm8-openhermes-da`: `1,001,551` generated rows, `991,114`
  audited rows, and `924,816` accepted rows.
  Upload policy update: do not upload/use this base DaOH as final DFM8 input.
  Wait for the repaired/retranslated merge from
  `export-upload-dfm8-openhermes-repaired`, which will include repaired English
  OpenHermes, Danish translations of repaired rows, and retry rows for
  fixable DaOH failures.

Active stage:

- `dfm8_openhermes_repaired/scripts/watch_daoh_then_run_openhermes_repair.sh`
  detected DaOH completion and launched
  `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`.
- Active log root: `logs/dfm8_openhermes_repaired_20260712T085219`.
- Eight Gemma 4 31B vLLM servers are active on ports `8600-8607` with
  `gpu-memory-utilization=0.7`, `max-num-seqs=64`, and GPUs at about 100%
  utilization.
- Current substage: English OpenHermes source audit before English repair,
  Danish retranslation of repaired rows, DaOH retry translation, and final
  merged `dfm8-openhermes-en`/`dfm8-openhermes-da` upload build.
- Progress at snapshot: `248,164 / 1,001,551` source-audit rows written
  (`24.8%`). The script has not yet reached English repair, Danish
  retranslation, DaOH retry, or final repaired upload build.

Runner order after source audit:

1. `make-repair-requests`
2. `repair-english`
3. `audit-repair`
4. `make-danish-repair-requests`
5. `translate-danish` repaired rows
6. `audit-danish` repaired rows
7. `make-daoh-retry-requests`
8. `translate-danish` retry rows
9. `audit-danish` retry rows
10. `build-upload` to `export-upload-dfm8-openhermes-repaired`

GRPO/PPO should be reserved for executable or simulated environments with
verifiable rewards:

- BFCL-shaped single/multi-turn tool-call tasks for AST/executable/irrelevance
  rewards.
- τ-bench / τ²-bench style customer-service simulations for multi-turn
  tool-use and state tracking.
- small internal tool-call environments where rewards check valid JSON,
  exactly one tool call where required, no repeated-call loops, correct
  arguments, and correct final answer after tool results.

Avoid RL on noisy fluency-only preferences. For DFM8, the most useful reward
signals are structural validity, functional correctness, constraint satisfaction,
and task success, not generic helpfulness.
