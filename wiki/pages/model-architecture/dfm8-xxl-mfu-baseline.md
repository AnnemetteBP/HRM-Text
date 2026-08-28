---
type: Technical Reference
title: DFM8 XXL MFU Baseline
description: Recurrence-aware model-FLOP utilization estimate for the single-node DFM8 XXL production geometry.
tags: [dfm8, xxl, training, performance, mfu, b200]
status: stable
last_updated: 2026-08-28
confidence: medium
sources:
  - id: nvidia-hgx-b200-spec
    resource: https://www.nvidia.com/en-in/data-center/hgx/
    title: NVIDIA HGX Platform specifications
    author: org:NVIDIA
---
# DFM8 XXL MFU Baseline

The measured single-node production baseline is approximately `3.56 s/step`
on eight B200 GPUs. It uses BF16 forward/backward compute, `262144` tokens per
optimizer step, GAS 4, BP 5, 4K context, and the 3,978,299,136-parameter XXL
configuration. NVIDIA specifies 36 PFLOP/s sparse FP16/BF16 tensor throughput
for an eight-GPU HGX B200; the corresponding dense peak is 18 PFLOP/s.

The ordinary decoder-only approximation `6 * parameters * tokens` gives only
6.257 PFLOP per optimizer step and an apparent MFU of 9.8%. That estimate is
not appropriate for HRM because the same stored H/L parameters are applied
recurrently. It substantially undercounts executed model work.

Using the project's recurrence-aware FLOP formula with 36 H layers, 36 L
layers, `H_cycles=2`, `L_cycles=3`, and BP 5 gives:

| PrefixLM attention assumption | Model FLOP/step | MFU at 3.56 s |
|---|---:|---:|
| Exclude attention entirely | 15.078 PFLOP | 23.5% |
| 1,024 attended keys/token | 16.498 PFLOP | 25.7% |
| 2,048 attended keys/token | 17.918 PFLOP | 28.0% |
| Dense 4,096-key upper bound | 20.758 PFLOP | 32.4% |

The current defensible estimate is therefore approximately **25--29% MFU**,
with a hard recurrence-aware range of **23.5--32.4%** until the actual allowed
PrefixLM query-key count is instrumented. The corresponding impossible-perfect
compute floor is about `0.84--1.15 s/step`; communication, memory traffic,
elementwise operations, optimizer work, data movement, and launch overhead
prevent reaching that floor.

A realistic optimization target of 40--50% recurrence-aware MFU would imply
roughly `1.8--2.5 s/step`, depending on attention density. This suggests about
`1.4--2.0x` realistic single-node headroom, not the `3--4x` suggested by
comparing wall time directly with the theoretical peak floor.

To replace the range with an exact MFU, log the aggregate allowed PrefixLM
query-key pairs per optimizer step after packing, then combine that value with
the existing recurrence-aware formula. Hardware FLOP utilization from Nsight
Compute should be reported separately; it includes operations outside the
model-FLOP accounting used by MFU.

## Nsight Systems steady-state profile

On 2026-08-28, a checkpoint- and W&B-disabled XXL run resumed from
`checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_175000` and was profiled on
all eight B200s. The run used the production geometry above, including GAS 4,
BP 5, FSDP2 with FP32 parameters, BF16 forward/backward, no activation
checkpointing, `reshard_after_forward=false`, and `no_sync` accumulation. A
temporary metadata view selected the checkpoint's exact global row cursor so
startup did not replay 700,000 microbatches.

The steady 35-second report is at
`logs/profiling/dfm8_xxl_nsys_20260828_steady/steady.nsys-rep`; its SQLite
export is alongside it. No model checkpoint was written and W&B remained
disabled. The traced steady tail ran at about `3.7 s/step`, versus the
unprofiled `3.56 s/step` baseline, so the full CUDA/NCCL trace added roughly
4% wall-time overhead.

Nsight warned that some CUDA/NVTX events were not collected on three ranks.
The per-GPU conclusions below therefore use the five internally consistent
GPU traces (GPU 1 and GPUs 4--7), not the incomplete GPU 0, 2, and 3 traces.
Kernel-duration percentages are summed device time and may overlap across
streams; they are not additive wall-clock phase percentages.

| Kernel class | Summed kernel time |
|---|---:|
| GEMM (`nvjet`) | 34.7% |
| NCCL | 21.0% |
| Other kernels | 13.2% |
| Triton fused kernels | 11.2% |
| Index/gather/scatter | 10.2% |
| FlashAttention 4 | 9.7% |

The complete GPU traces were kernel-active for only 74.9--76.8% of the
35-second capture span. NCCL occupied 4.5--7.6 seconds of summed time per GPU,
but 62.9--66.5% of that communication overlapped non-NCCL kernels. The
remaining exposed communication is important, but it does not support making
a different FSDP implementation the first optimization target. All-gather was
the largest individual kernel family; communication topology and wrapping
remain useful second-stage experiments after fixing host synchronization and
launch fragmentation.

The strongest finding is extreme scalar synchronization and kernel
fragmentation:

- each GPU performed about 91,300 device-to-host copies in 35 seconds;
- those copies moved only about 375 KB total per GPU, or approximately 4.1
  bytes each;
- this is about 10,400 scalar copies per optimizer step;
- a complete trace contained about 1.42 million kernels per GPU, approximately
  40,600 launches/second or 162,000 kernels per optimizer step;
- 71.6% of kernels ran for less than 10 microseconds and 92.0% for less than
  50 microseconds; the sub-50-microsecond kernels still consumed 32.5% of
  summed kernel time.

**Superseded on 2026-08-28 after tracing the batch construction:** the five
scalar metadata tensors consumed by `prefixlm_seq_info_from_tensors()` are
deliberately wrapped CPU tensors, not CUDA tensors, so their `.item()` calls do
not cause device-to-host synchronization. The FA4 causal path did contain two
genuine synchronizing reductions, `active_causal_lens.max().item()` and
`active_total_lens.max().item()`, on every attention invocation.

The performance branch now reuses the data loader's existing
`max_seqlen_causal` and `max_seqlen_all` values for those FA4 launch arguments.
FlashAttention accepts these as upper bounds, and this matches the pre-existing
FA3 implementation. The equivalent ROCm path was fixed at the same time. The
change does not alter sequence masks, cumulative lengths, output placement, or
checkpoint state. Focused tests cover the important conservative-bound case in
which a prefix-only sequence makes the batch key-length maximum larger than
the exact maximum among causal sequences.

This removes two CUDA-to-Python synchronizations per causal PrefixLM attention
call, but it does not by itself explain all approximately 10,400 four-byte D2H
copies per optimizer step in the baseline profile. Reprofile before claiming a
specific end-to-end speedup or assigning the remaining copies to another
source.

### PrefixLM bound A/B benchmark

The fix was benchmarked on 2026-08-28 with three checkpoint- and W&B-disabled
30-step XXL resumes from the same step-175000 checkpoint and exact row cursor.
All runs used the production geometry described above. The committed baseline
ran before and after the patched run to control for cache and run-order effects.

| Run | Median step | Mean step | Minimum step |
|---|---:|---:|---:|
| Baseline 1 | 3.5159 s | 3.7864 s | 3.4189 s |
| Patched | 3.4420 s | 3.7224 s | 3.3603 s |
| Baseline 2 | 3.5117 s | 3.7993 s | 3.4291 s |

Relative to the mean of the two baseline medians, the patch improved median
step time by **2.04%**. Relative to the mean of the baseline means, it improved
mean step time by **1.86%**. Each run had one approximately 9.6-second late
compilation outlier, so median is the more representative result. The logs are
under `/tmp/hrm_prefixlm_ab/{baseline,patched,baseline_repeat}/train.log`.
No checkpoints or W&B records were produced.

The result shows that any additional FA4 scheduling work from occasionally
conservative maximum-length bounds is smaller than the synchronization cost it
replaces for this workload. It does not establish the isolated kernel-level
cost or account for all remaining D2H copies.

### PrefixLM routing reuse

On 2026-08-28, PrefixLM routing construction was moved from every recurrent
attention invocation to batch preparation. The data loader's packed metadata
now produces prefix, causal, and active-key indices plus cumulative sequence
lengths once per microbatch. FA4 and ROCm consume those tensors directly;
their public fallback path still computes routing internally for callers that
do not supply it. SM90, dense, and MPS attention retain their previous paths.

The routing tensors have data-dependent lengths. Marking their leading
dimensions dynamic before they enter the compiled train step is required: an
initial implementation specialized the graph for each packed shape and
eventually exhausted GPU memory with compiled variants. The dynamic-marked
implementation completed production-shaped compiled XXL runs without a
recompilation warning.

Disabled resume tracing no longer evaluates the three diagnostic `.item()`
calls around supervised-count reduction and loss scaling. The three `.item()`
calls remaining in each FA4 invocation read deliberately wrapped CPU launch
metadata; they do not synchronize CUDA. A real B200 FA4 comparison between
fallback and precomputed routing produced bit-identical outputs and `dq`,
`dk`, and `dv`. Focused mocked-backend tests cover both FA4 and ROCm routing
and launch parity.

Fresh-initialization, W&B-disabled production-geometry XXL runs gave:

| Implementation | Median step | Mean step |
|---|---:|---:|
| Bound-only predecessor (`27f55a4`) | 3.5452 s | 3.5975 s |
| Routing reuse, run 1 | 3.1068 s | 3.2791 s |
| Routing reuse, run 2 | 3.1372 s | 3.2455 s |

This is an **11.5--12.4% median-step improvement** over the controlled
predecessor. Final short-run loss varied naturally across repeated optimized
runs by more than the predecessor-versus-optimized difference, so aggregate
short-run loss is not a bitwise parity test; the direct FA4 forward/backward
comparison is.

The 45-second optimized Nsight trace is at
`logs/profiling/dfm8_xxl_prefixlm_precompute_20260828/steady.nsys-rep`, with
its SQLite export alongside it. Nsight again produced incomplete CUDA traces
on some ranks, so comparisons use complete GPU traces. Relative to the earlier
steady profile:

- D2H copies fell from about `2,609/GPU/s` to `8.8/GPU/s`, a **99.66%**
  reduction; the optimized trace contains only 395 four-byte D2H copies per
  GPU over 45 seconds;
- kernel launch rate fell from about `40,500/GPU/s` to `29,700/GPU/s`, a
  **26.7%** reduction;
- index/gather/scatter kernels excluding radix-sort machinery fell from about
  `10.2%` to `8.3%` of summed kernel time;
- kernels shorter than 10 microseconds fell from `71.6%` to about `50.1%` of
  launches, while kernels shorter than 50 microseconds fell from `92.0%` to
  about `85.1%`.

The next target should be selected from this new profile. Exposed NCCL is now
more prominent in relative terms, while repeated indexing and short-kernel
launches remain material. FA4 itself remains below 10% of summed kernel time
and is not the leading bottleneck.
