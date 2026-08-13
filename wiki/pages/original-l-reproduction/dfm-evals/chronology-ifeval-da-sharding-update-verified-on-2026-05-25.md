---
type: Operational Record
title: IFEval-DA sharding update, verified on (2026-05-25)
description: 'Chronological record from dfm-evals: IFEval-DA sharding update, verified
  on (2026-05-25).'
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
# IFEval-DA sharding update, verified on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

IFEval-DA sharding update, verified on 2026-05-25. Confidence: high.

The original single-GPU original+mixed IFEval-DA run was stopped at about `66/541` completed samples because it was dominated by multi-minute generations. `dfm-evals/dfm_evals/tasks/ifeval_da.py` now accepts:

```text
num_shards
shard_index
```

and filters samples by `index % num_shards == shard_index` after the normal dataset load/shuffle/limit path.

Eight shard suites were added in:

```text
config/dfm_evals_hrm_ifeval_da_shards.yaml
```

The safe merge path is:

```text
1. Run each shard as its own Inspect eval on one GPU.
2. Do not log per-shard metrics to W&B.
3. Merge completed shard `.eval` zip files by reading all `samples/*.json`.
4. Recompute IFEval metrics over the union of per-sample `instruction_following` scores.
5. Log only the merged metrics to W&B.
```

Merger script:

```text
scripts/merge_ifeval_da_shards.py
```

Shard launch root:

```text
logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_ifeval_da_sharded
```

Superseded on 2026-05-25: the first eight-shard launch used `BATCH_SIZE=8` and
`INSPECT_MAX_CONNECTIONS=8`. It started successfully but provided poor progress
behavior because a long sample could hold a whole batch open before Inspect
flushed any completed sample records. The run was stopped before metrics were
logged.

Current launch root:

```text
logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_ifeval_da_sharded_b1
```

Current launch mode:

```text
BATCH_SIZE=1
INSPECT_MAX_CONNECTIONS=1
INCREMENTAL_WANDB_SYNC=0
FINAL_WANDB_SYNC=0
```

This still uses one shard per GPU, but logs only the merged metrics after all
shards complete. While the original+mixed training job is active, each eval
server shares a GPU with one training rank, so throughput is expected to be
uneven and lower than a dedicated eval run. Confidence: high.

Completed on 2026-05-25 at 14:02 local time. All eight shards completed and
the merged metrics were logged to W&B run `es1od1in`. The merged union covered
541 samples. Metrics:

```text
dfm_eval/ifeval-da/instruction_following/final_acc: 0.3185721627463338
dfm_eval/ifeval-da/instruction_following/final_stderr: 0.015870416956780143
dfm_eval/ifeval-da/instruction_following/inst_loose_acc: 0.4073226544622426
dfm_eval/ifeval-da/instruction_following/inst_loose_stderr: 0.015647363066797922
dfm_eval/ifeval-da/instruction_following/inst_strict_acc: 0.39931350114416475
dfm_eval/ifeval-da/instruction_following/inst_strict_stderr: 0.01553497876043891
dfm_eval/ifeval-da/instruction_following/prompt_loose_acc: 0.2365988909426987
dfm_eval/ifeval-da/instruction_following/prompt_loose_stderr: 0.018288827582625598
dfm_eval/ifeval-da/instruction_following/prompt_strict_acc: 0.23105360443622922
dfm_eval/ifeval-da/instruction_following/prompt_strict_stderr: 0.018138757170523406
```

Confidence: high.
