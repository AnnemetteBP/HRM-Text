---
type: Plan Record
title: DFM6-DFM7 Step-1050K EuroEval IFEval NLTK Recovery
description: 'Part of DFM7 Plan: DFM6-DFM7 Step-1050K EuroEval IFEval NLTK Recovery.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# DFM6-DFM7 Step-1050K EuroEval IFEval NLTK Recovery

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Recovery note, 2026-07-05. Confidence: high from local scheduler/log output.

- In the active 850K-1250K scheduler plan, two `step_1050000` EuroEval batched
  IFEval rows failed after generation during local scoring:
  - `eval-00879`: `euroeval:ifeval-da`, shard `8/20`
  - `eval-00888`: `euroeval:ifeval`, shard `17/20`
- The failure was a missing NLTK scorer resource, not vLLM/FA4/OOM:
  `LookupError: Resource 'punkt_tab' not found`, attempted path
  `tokenizers/punkt_tab/english/`.
- Fixed in the `hrm` environment by downloading NLTK data into the user-level
  shared path:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python - <<'PY'
import nltk
for pkg in ["punkt_tab", "punkt"]:
    nltk.download(pkg, download_dir="/home/ucloud/nltk_data", quiet=False)
PY
```

- Verified resource locations:
  - `/home/ucloud/nltk_data/tokenizers/punkt_tab/english`
  - `/home/ucloud/nltk_data/tokenizers/punkt/english.pickle`
- The plan was locked, `eval-00879` and `eval-00888` were reset from
  `failed`/attempt `6` to `pending`/attempt `0`, and then unlocked. The
  scheduler immediately picked both rows back up as `running`.
