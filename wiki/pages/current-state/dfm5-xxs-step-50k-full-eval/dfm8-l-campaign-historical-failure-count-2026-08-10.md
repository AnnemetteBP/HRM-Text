---
type: Operational Record
title: DFM8 L Campaign Historical Failure Count (2026-08-10)
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 L Campaign Historical Failure
  Count (2026-08-10).'
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
# DFM8 L Campaign Historical Failure Count (2026-08-10)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high from active `plan.tsv`, scheduler events, vLLM server logs, and
the current filesystem/PATH state.

The `failed=188` scheduler summary consists entirely of historical
`step_750000` rows: 187 eval shards exhausted six attempts because persistent
vLLM startup returned scheduler status 71, and the original
`campaign-train-750000` row failed once with an NCCL collective timeout. The
training failure was recovered by the completed
`campaign-train-750000-resume720000` replacement.

The eval failures were infrastructure failures, not benchmark/model failures.
Their shared vLLM traceback is:

```text
RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist
```

FlashInfer's vLLM sampling JIT found `ninja` in the `hrm` environment, but the
CUDA compiler/toolkit was absent at failure time. These failed rows should not
be interpreted as model scores.

Superseded later on 2026-08-10: CUDA Toolkit 13.2 was installed under
`/usr/local/cuda-13.2`, with `/usr/local/cuda` pointing to it. Absolute `nvcc`
reports release `13.2` (`V13.2.78`), and FlashInfer's own `get_cuda_path()` now
resolves `/usr/local/cuda`. The shell and already-running scheduler do not have
`/usr/local/cuda/bin` on `PATH`, but FlashInfer resolves the default CUDA path
directly, so the original startup cause is repaired. Adding that bin directory
to future runner PATHs remains preferable for explicit diagnostics.

The same vLLM server log independently confirms `Using FlashAttention version
4`. FA4 handles model attention. FlashInfer was used only by vLLM's top-k/top-p
sampling operation during its dummy sampler profile; this does not represent an
attention-backend fallback from FA4.

After CUDA 13.2 was verified, all 187 failed `step_750000` eval rows were
atomically reset to `pending` with attempt zero. The original failed
`campaign-train-750000` row remains failed as historical evidence because its
`campaign-train-750000-resume720000` replacement already completed; resetting
the original would risk duplicate training. The scheduler summary consequently
shows `failed=1`, and the reset evals remain gated by GPU headroom while the
current training segment is active.
