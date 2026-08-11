---
type: Experiment Record
title: Standard Evals For Original Plus Mixed
description: 'Part of Original L Reproduction: Standard Evals For Original Plus Mixed.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction.md
---
# Standard Evals For Original Plus Mixed

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

Status, 2026-05-25: standard HRM evals for the active `original_plus_mixed_danish_instruction_rich` L run are run with one independent `evaluation.main` process per GPU and one benchmark per process. The active training job still occupies all eight GPUs, so eval processes share GPUs with training. Use `setsid` plus stdin redirected from `/dev/null` for detached eval jobs; a plain background `nohup` launch from the command runner can exit early with an empty log even though the same foreground command works. Confidence: high.

The checkpoint-1 standard eval fan-out uses:

```bash
cd /work/dfm/HRM-Text
CUDA_VISIBLE_DEVICES=<gpu> OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1 \
python -u -m evaluation.main \
  config=evaluation/config/hrm_benchmarking.yaml \
  ckpt_path=checkpoints/original_plus_mixed_danish_instruction_rich/L \
  ckpt_epoch=1 \
  'run_only=[<BENCHMARK>]' \
  generation_config.batch_size=8
```

Live log roots from the 2026-05-25 launch:

```text
CP1 GSM8k:        logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_direct_epoch1/GSM8k.log
CP1 Winogrande:   logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_direct_epoch1_probe/Winogrande_setsid.log
CP1 other tasks:  logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_direct_epoch1_setsid/*.log
CP2 follow-ons:   logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_direct_epoch2_setsid/*.log
Watcher status:   logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_watchers/status.tsv
```

The 2026-05-25 run uses eight lanes for `GSM8k`, `MATH`, `DROP`, `MMLU`, `ARC`, `HellaSwag`, `Winogrande`, and `BoolQ`. Watchers start the same benchmark on checkpoint 2 as soon as checkpoint 1 for that benchmark finishes and has an `EVALUATION SUMMARY`. Confidence: high.

Update, 2026-05-25: full unsharded MATH evals for checkpoint 1 and checkpoint 2 were stopped because MATH was the bottleneck. `evaluation.benchmarks.MATH` now supports `num_shards` and `shard_index` using the same modulo sharding strategy as `dfm-evals` IFEval-DA: a sample belongs to a shard when `index % num_shards == shard_index`. For 8 shards, local verification showed exactly `625` samples per shard and `5,000` total samples. Confidence: high.

MATH shard logs for the active run are under:

```text
logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_math_shards_v2/epoch_1/MATH_shard_<0-7>_of_8.log
logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_math_shards_v2/epoch_2/MATH_shard_<0-7>_of_8.log
```

Merge completed MATH shards with:

```bash
cd /work/dfm/HRM-Text
scripts/merge_standard_math_shards.py \
  logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_math_shards_v2/epoch_1/MATH_shard_*_of_8.log \
  --epoch 1 \
  --output logs/eval/original_plus_mixed_danish_instruction_rich_L_standard_math_shards_v2/epoch_1/merged_math_metrics.json
```

Use `--log-wandb --project ... --run-id ... --run-name ...` to log the merged `eval/MATH/{n,acc,invalid}` row to W&B using `eval/epoch` as the step metric. Confidence: high.

Restrict benchmark names with `run_only=[GSM8k,MATH,DROP,MMLU,ARC,HellaSwag,Winogrande,BoolQ]` syntax. Lower `generation_config.batch_size` if a benchmark runs out of memory.

Runtime batch grouping, verified from `evaluation/main.py`, `evaluation/config/hrm_benchmarking.yaml`, and active logs on 2026-05-23: the default HRM benchmark config produces three generation groups per checkpoint, because benchmarks with identical generation kwargs are concatenated before generation. The groups are:

- `6319` prompts: `GSM8k` plus `MATH`, using the default `synth,cot`, `batch_size=33`, `max_context=3072`.
- `9536` prompts: `DROP`, using `direct`, `batch_size=33`, `max_context=3072`.
- `29793` prompts: `MMLU`, `ARC`, `HellaSwag`, `Winogrande`, and `BoolQ`, using `direct`, `batch_size=1`, `max_context=4096`, `max_tokens=1`.

Confidence: high.

Completed evaluation results from `logs/eval/original_sapient_L/epoch_{1..4}.log` on 2026-05-23:

| checkpoint | GSM8k acc | MATH acc | DROP EM | DROP F1 | MMLU acc | ARC acc | HellaSwag acc | Winogrande acc | BoolQ acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| epoch 1 | 0.5792 | 0.3462 | 0.5520 | 0.5865 | 0.4175 | 0.4582 | 0.3231 | 0.5422 | 0.7260 |
| epoch 2 | 0.7225 | 0.4524 | 0.6989 | 0.7358 | 0.5074 | 0.6288 | 0.4141 | 0.6417 | 0.8214 |
| epoch 3 | 0.7779 | 0.4792 | 0.7292 | 0.7641 | 0.5317 | 0.6962 | 0.4732 | 0.6654 | 0.8367 |
| epoch 4 | 0.7801 | 0.5012 | 0.7442 | 0.7824 | 0.5523 | 0.7278 | 0.5093 | 0.6669 | 0.8462 |

Confidence: high.

W&B eval backfill, verified on 2026-05-24: `scripts/log_original_l_eval_to_wandb.py` parses the completed eval logs and resumes the healthy original Sapient L W&B run `76sygh18` in project `Original Sapient L HLM-torch`. It logs clean history metrics such as `eval/GSM8k/acc`, `eval/MATH/acc`, `eval/DROP/f1`, and summary keys per epoch/final.

```bash
cd /work/dfm/HRM-Text
python scripts/log_original_l_eval_to_wandb.py --resume must
```

Confidence: high.

Local W&B history completeness, verified on 2026-05-24: the local history for run `76sygh18` is complete but split across three resumed W&B directories:

```text
wandb/run-20260522_073509-76sygh18/run-76sygh18.wandb
  training history: 65,186 history records, steps 0..325925, exit record present

wandb/run-20260524_084549-76sygh18/run-76sygh18.wandb
  first eval backfill: 4 history records, steps 325926..325929, contains 112 bad dotted eval keys

wandb/run-20260524_084613-76sygh18/run-76sygh18.wandb
  corrected eval backfill: 4 history records, steps 325930..325933, contains 196 clean eval keys and no bad dotted eval keys
```

The remote run state is `finished`; its summary `_step` is `325933`, matching training plus both local eval backfill attempts. Confidence: high.

Clean local W&B history merge, verified on 2026-05-24: `scripts/merge_original_l_wandb_history.py` merges the original training datastore and the corrected eval backfill datastore while omitting the first bad eval backfill. The output is local only:

```text
wandb/merged-20260524-76sygh18-clean/run-76sygh18-clean-merged.wandb
wandb/merged-20260524-76sygh18-clean/history.jsonl
wandb/merged-20260524-76sygh18-clean/manifest.json
```

Validation of the merged `.wandb` file showed `65,190` history records, steps `0..325933`, `196` clean eval keys, zero dotted eval keys, and an exit record. Syncing this local merged copy will not delete the already-synced bad history from the original remote run. Confidence: high.

A separate local copy was also prepared for upload into the ongoing mixed-run project:

```text
wandb/merged-20260524-76sygh18-clean-for-ongoing/run-origLclean.wandb
wandb/merged-20260524-76sygh18-clean-for-ongoing/history.jsonl
wandb/merged-20260524-76sygh18-clean-for-ongoing/files/*
wandb/merged-20260524-76sygh18-clean-for-ongoing/logs/*
```

This copy rewrites the local protobuf run metadata to `run_id=origLclean`, `project="Original Plus Mixed Danish Instruction Rich L"`, and `display_name=original-sapient-L-clean-history`. It includes the original run config, summaries, metric definitions, history, console output records, and copied local sidecar files/logs. The local `.wandb` file does not contain a full source-code artifact payload; it only has W&B's `_wandb.code_path` metadata for the original `source-Original_Sapient_L_HLM-torch-pretrain.py` source artifact. Confidence: high.

Upload command, executed and verified on 2026-05-24:

```bash
cd /work/dfm/HRM-Text
wandb sync --no-sync-tensorboard --no-mark-synced \
  --entity peter-sk-sdu \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  --id "origLclean" \
  "/work/dfm/HRM-Text/wandb/merged-20260524-76sygh18-clean-for-ongoing/run-origLclean.wandb"
```

Remote URL:

```text
https://wandb.ai/peter-sk-sdu/Original%20Plus%20Mixed%20Danish%20Instruction%20Rich%20L/runs/origLclean
```

Post-sync verification showed `state=finished`, summary `_step=325933`, `train/loss=0.8746508359909058`, `eval/GSM8k/acc=0.7801`, `eval/MATH/acc=0.5012`, `eval/DROP/f1=0.7824`, and zero dotted eval summary keys. The local merge script was updated to drop `672` bad dotted eval summary updates from the corrected eval-backfill datastore before writing future merged copies. Confidence: high.
