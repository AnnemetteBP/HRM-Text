---
type: Operational Record
title: Superseded/context update (2026-05-24)
description: 'Chronological record from dfm-evals: Superseded/context update (2026-05-24).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Superseded/context update (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Superseded/context update, 2026-05-24: W&B reported success when mutating the personal default workspace view, but the UI and a later API read showed only the user's manually changed WMT panel persisted. The public Workspace API also refuses personal user views. A new saved workspace view named `dfm_eval epoch x-axis` was created instead, with all non-axis `dfm_eval` panels keyed and set to `xAxis=dfm_eval/epoch`. URL: `https://wandb.ai/peter-sk-sdu/Original%20Plus%20Mixed%20Danish%20Instruction%20Rich%20L?nw=oi8yv6lpmkn`. Backup spec: `logs/wandb_workspace_specs/20260524T123312Z_saved_view_dfm_eval_epoch_axis.json`. Confidence: high.

W&B workspace cleanup, verified on 2026-05-26: deleting panels from the personal default workspace view again returned a successful `upsertView` response but readback showed the personal view unchanged. The requested cleanup was therefore materialized as a saved workspace view named `eval cleaned: no MMLU n/invalid`, with `96` panels removed from the `eval` section: `45` `eval/MMLU/n_*` panels and `51` `eval/MMLU/invalid_*` panels. API readback of the saved view shows `34` eval panels and `0` matching panels, but the user reported the URL still showed the old panels in the web UI. A follow-up attempt to use the separate `upsertUserProfileView` mutation for the personal view failed with a W&B HTTP 500. URL: `https://wandb.ai/peter-sk-sdu/Original%20Plus%20Mixed%20Danish%20Instruction%20Rich%20L?nw=boh5wwabbfc7`. Backup/spec files: `logs/wandb_workspace_specs/20260526T151707Z_before_delete_mmlu_n_invalid_nw-nwuserpetersk-w.json`, `logs/wandb_workspace_specs/20260526T151707Z_after_delete_mmlu_n_invalid_nw-nwuserpetersk-w.json`, and `logs/wandb_workspace_specs/20260526T151840Z_saved_view_delete_mmlu_n_invalid.json`. Confidence: high.

Additional dfm-evals task inventory, verified on 2026-05-24: local `dfm-evals` is at upstream `main` commit `9b6cf828ccffdbde54dd8ed2e4d06a37f979cd2a`. Registered local task names are `dfm_evals/bfcl-v1`, `dfm_evals/bfcl-v1-da`, `dfm_evals/dala`, `dfm_evals/danish-citizen-tests`, `dfm_evals/gec_dala`, `dfm_evals/generative-talemaader`, `dfm_evals/ifeval-da`, `dfm_evals/multi_wiki_qa`, `dfm_evals/piqa`, `dfm_evals/ruler`, and `dfm_evals/wmt24pp-en-da`. No task named `daisy` exists in this checkout. The HRM-compatible suite already ran the non-judge Danish tasks except `piqa` and `ifeval-da`; `generative-talemaader` requires a judge model, `ruler` needs a <=4096-token configuration for these checkpoints, and BFCL/agentic tasks need tool/calling behavior that the current simple HRM OpenAI shim is not expected to handle well. Confidence: high.
