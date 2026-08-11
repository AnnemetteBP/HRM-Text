---
type: Plan Record
title: DFM6-to-DFM7 XL Eval Scheduler Extension
description: 'Part of DFM7 Plan: DFM6-to-DFM7 XL Eval Scheduler Extension.'
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
# DFM6-to-DFM7 XL Eval Scheduler Extension

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Update, 2026-07-02. Confidence: high from local scheduler plan inspection and
locked `eval_scheduler plan create --append` commands.

The active DFM6-to-DFM7 XL eval plan was extended in place:

```text
plan_dir: logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253
checkpoint path: checkpoints/dfm7/XL-gas2-from-dfm6-epoch3
W&B target: DFM5 / dfm6-dfm7-xl-gas2
```

Added checkpoint eval blocks:

```text
step_1050000 epoch 4.297464085872718 port_base 45000
step_1100000 epoch 4.494099606107069 port_base 46000
step_1150000 epoch 4.690735126341419 port_base 47000
step_1200000 epoch 4.88737064657577  port_base 48000
step_1250000 epoch 5.08400616681012  port_base 49000
```

Each appended block has 217 rows, skips only `valeu-da`, waits for a fully
written checkpoint, exports an EMA HF/vLLM checkpoint to
`exports/dfm6_dfm7_XL_gas2_step_<step>_ema_hf_hrmenv_202253`, and uses the
same DFM7 eval settings as the earlier blocks: Gemma4 chat template, FA4,
vLLM GPU memory utilization `0.25`, EuroEval-first order, standard batch `64`,
DFM batch `32`, DFM IFEval batch/shards `32`, EuroEval batch `32`, and managed
`unsloth/gemma-4-E4B-it` judge rows for judged DFM tasks.

Follow-up, 2026-07-03. Confidence: high from local vLLM/proxy logs, patched
proxy code, rerun status, and generated result artifact. The `step_900000`
EuroEval BFCL-v2 row initially failed all six attempts with vLLM/Gemma4 native
tool parser error:

```text
OverflowError: cannot convert float infinity to integer
```

The model had emitted an invalid native tool-call argument (`Infinity`) for an
integer-like schema field. That should count as an incorrect BFCL item, not as
an infrastructure failure that aborts the whole benchmark. The proxy
`scripts/native_compatible_openai_proxy.py` now catches this narrow BFCL native
tool parser/coercion 400 and returns a valid OpenAI response containing an
empty/invalid BFCL tool-call answer. EuroEval then scores the item as wrong and
continues.

After resetting only `eval-00238` to `pending`, the rerun completed:

```text
eval-00238 step_900000 euroeval:bfcl-v2 status_0
BFCL-v2 Tool Calling Accuracy: 2.32% +/- 0.51%
```

The blocked `step_900000` EuroEval average, math/code average, headline average,
and report rows then completed with status `0`.
