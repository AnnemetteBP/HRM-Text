---
type: Experiment Record
title: Evaluate Checkpoints
description: 'Part of Original L Reproduction: Evaluate Checkpoints.'
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
# Evaluate Checkpoints

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

Original-plus-mixed checkpoint 3 standard-eval incremental sync, 2026-05-26: `MMLU` completed and was manually synced to W&B run `original-plus-mixed-danish-instruction-rich-L` (`es1od1in`) under `eval/*` at `eval/epoch=3`. The synced aggregate values were `eval/MMLU/acc=0.5012`, `eval/MMLU/invalid=0.0`, and `eval/MMLU/n=57`; per-subject `acc_*`, `invalid_*`, and `n_*` keys were also logged. The local sync log is `logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/sync_mmlu_20260526T143619.log`. Confidence: high.

Original-plus-mixed checkpoint 3 standard-eval incremental sync, 2026-05-26: `GSM8k` completed and was manually synced to the same W&B run under `eval/*` at `eval/epoch=3`. The synced values were `eval/GSM8k/acc=0.7703`, `eval/GSM8k/invalid=0.0190`, and `eval/GSM8k/n=1319`. The local sync log is `logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/sync_gsm8k_20260526T151211.log`. Confidence: high.

Original-plus-mixed checkpoint 3 partial sync, 2026-05-26: all completed CP3 results except IFEval-DA were manually synced while IFEval-DA shards were still running. The 8 MATH shards were merged and synced under `eval/MATH/*` at `eval/epoch=3`: `acc=0.4594`, `invalid=0.0872`, `n=5000`. The completed non-IFEval dfm-evals tasks were synced under `dfm_eval/*` at `dfm_eval/epoch=3`: `danish-citizen-tests`, `dala`, `gec_dala`, `wmt24pp-en-da`, `multi_wiki_qa`, `piqa`, and `generative-talemaader`. The local sync logs are `logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/sync_all_but_ifeval_20260526T164746.log` and `logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/sync_dfm_all_but_ifeval_20260526T164843.log`. Confidence: high.

Verified from `evaluation/main.py`, `evaluation/engines.py`, and `simple_inference_engine.py` on 2026-05-23: HRM evaluation uses `python -m evaluation.main`, loads `evaluation/config/hrm_benchmarking.yaml` by default, and evaluates the latest epoch if `ckpt_epoch` is omitted. To evaluate all four original-L checkpoints, pass `ckpt_epoch=1`, `2`, `3`, and `4` explicitly.

Run all default benchmarks sequentially on one visible GPU:

```bash
cd /work/dfm/HRM-Text
mkdir -p logs/eval/original_sapient_L
for epoch in 1 2 3 4; do
  CUDA_VISIBLE_DEVICES=0 python -m evaluation.main \
    ckpt_path="checkpoints/original_sapient/L" \
    ckpt_epoch="${epoch}" \
    2>&1 | tee "logs/eval/original_sapient_L/epoch_${epoch}.log"
done
```

Run all four epochs in parallel, one GPU per checkpoint:

```bash
cd /work/dfm/HRM-Text
GPUS=0,1,2,3 scripts/evaluate_original_sapient_l_checkpoints.sh
```

The script writes:

```text
logs/eval/original_sapient_L/epoch_1.log
logs/eval/original_sapient_L/epoch_2.log
logs/eval/original_sapient_L/epoch_3.log
logs/eval/original_sapient_L/epoch_4.log
```

Pass extra Hydra overrides through the script, for example:

```bash
GPUS=0,1,2,3 scripts/evaluate_original_sapient_l_checkpoints.sh generation_config.batch_size=16
```

Verified on 2026-05-25 from `logs/eval/original_sapient_L/epoch_{1,2,3,4}.log`: all four original Sapient L checkpoints completed the full standard eval suite with no tracebacks. Each checkpoint generated `45,648` samples: `1,319` GSM8k, `5,000` MATH, `9,536` DROP, `14,042` MMLU, `1,172` ARC, `10,042` HellaSwag, `1,267` Winogrande, and `3,270` BoolQ. The first grouped generation batch was `6,319` samples, which is `GSM8k + MATH`, so MATH did run on all `5,000` samples. Confidence: high.
