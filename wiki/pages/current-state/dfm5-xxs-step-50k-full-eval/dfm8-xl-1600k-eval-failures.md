---
type: Operational Record
title: DFM8 XL 1600K Eval Failures
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 XL 1600K Eval Failures.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 XL 1600K Eval Failures

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-21. Confidence: high from local scheduler status, plan
inspection, environment checks, and failed vLLM logs.

The active plan
`logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255`
currently has `187` failed rows, all for `ckpt_tag=step_1600000`.
The later `1650K`, `1700K`, and `1750K` rows are not failed; their
`wait_checkpoint` rows are still running/blocked pending.

Failure counts by action:

```text
eval_standard: 85
eval_dfm: 51
eval_dfm_ifeval: 32
eval_euroeval: 17
eval_euroeval_batched_ifeval: 2
```

This is an infrastructure/startup failure, not an eval-quality failure, not
checkpoint corruption, and not a GPU OOM. The representative standard MATH log
shows vLLM loading the exported checkpoint and then failing while FlashInfer's
top-k/top-p sampler tries to JIT-build CUDA code:

```text
RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist
RuntimeError: Engine core initialization failed. See root cause above.
```

The current scheduler environment has no `nvcc`, no `ptxas`, `CUDA_HOME` and
`CUDA_PATH` are unset, and `/usr/local/cuda` does not exist. `ninja` is present
in the `hrm` conda env.

This is separate from FlashAttention 4 attention. The plan intentionally sets
`--attention-backend FLASH_ATTN`, and earlier successful logs show
`Using FlashAttention version 4`; the failing component is vLLM selecting
FlashInfer for sampling. The least disruptive next attempt is to stop the
scheduler, reset only the failed `step_1600000` rows, and restart the runner
from the `hrm` conda env with:

```bash
export VLLM_USE_FLASHINFER_SAMPLER=0
python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255 \
  --gpus 0,1,2,3,4,5,6,7
```

That should preserve FA4 attention while avoiding FlashInfer sampler JIT. The
alternative is to install/configure a full CUDA toolkit so `nvcc` is visible to
the scheduler/vLLM process.

Follow-up, 2026-07-21. Confidence: high from local plan edit and active
scheduler status. After the NVIDIA toolkit was installed in the background,
`/usr/local/cuda` points to `/usr/local/cuda-13.2`, and
`/usr/local/cuda/bin/nvcc --version` reports CUDA `13.2`.

The `187` failed `step_1600000` rows were reset under `PlanLock` to
`status=pending` and `attempt=0`; no other failed rows remained. Backup:

```text
logs/scheduler/dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255/plan.before_reset_step1600000_failed_20260721_083319.tsv
```

The active scheduler picked the rows up again immediately. Eight EuroEval
`step_1600000` shards started on GPUs 0-7, and a current vLLM log showed
`Application startup complete` while still using FA4 attention. Old nested
`step_1600000` logs may still contain the earlier startup failure traces; use
fresh process timestamps/status rather than those stale traces when diagnosing
the reset run.
