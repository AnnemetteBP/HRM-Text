---
type: Technical Reference
title: DFM8 XXL MFU Baseline
description: Recurrence-aware model-FLOP utilization estimate for the single-node DFM8 XXL production geometry.
tags: [dfm8, xxl, training, performance, mfu, b200]
status: stable
last_updated: 2026-08-29
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

### Post-commit optimization profile

A second post-commit capture on 2026-08-28 used the exact `e91d719` tree and a
shorter 20-second steady-state window to reduce event loss. The report and
SQLite export are under
`logs/profiling/dfm8_xxl_prefixlm_postcommit_20260828/`. Nsight terminated the
benchmark process when the requested capture duration ended; this is expected,
and no checkpoint or W&B run was produced. GPUs 0, 3, 5, and 7 had complete
and mutually consistent CUDA traces.

| Observation | Post-commit result |
|---|---:|
| Kernel-active wall time | 95.3--96.1% |
| Kernel launches | 29.3--29.7 K/GPU/s |
| D2H copies | 197/GPU/20 s (9.85/s) |
| NCCL overlap with non-NCCL kernels | 64.7--71.5% |
| NCCL-only wall time | 9.1--11.9% |
| GEMM summed kernel time | 32.5% |
| NCCL summed kernel time | 29.2% |
| FA4 summed kernel time | 10.0% |
| Triton summed kernel time | 10.5% |
| Index/gather/scatter summed kernel time | 8.2% |
| Radix-sort summed kernel time | 2.2% |

The top individual kernel family is FSDP all-gather. Each complete GPU launched
about 4,464 all-gather kernels in 20 seconds. PrefixLM indexing is the other
large fragmented family: index/gather/scatter plus radix sort accounts for
about 10.4% of summed kernel time and hundreds of thousands of launches per
GPU in the capture. The host also issued about 3.39 million
`cudaLaunchKernel` calls across ranks during the window. High GPU-active time
means host launch optimization has a smaller ceiling than these percentages
alone suggest, but dependency-chain launch latency can still affect step time.

Recommended experiments, in order:

1. **Prototype an FA4 `seqused_q`/`seqused_k` PrefixLM path.** The installed
   FA4 API supports these arguments, as the existing FA3 implementation does.
   Running the prefix and causal passes over the original packed Q/K/V storage
   could remove repeated Q/K/V gathers, output index-put, indexing backward,
   and much of the radix-sort work. Start with the public FA4 API, require
   bit-exact or tolerance-defined forward/backward parity, and measure extra
   output-buffer memory. The profile supports a plausible 4--8% wall-time
   improvement, with about 10% as a hard kernel-time ceiling.
2. **Benchmark recurrence-aware FSDP wrapping.** The current configuration
   wraps every Transformer block and the root model. Test wrapping H and L
   recurrent levels as larger FSDP units while retaining
   `reshard_after_forward=false`. The production run has roughly 19--22 GiB of
   memory headroom, so retaining one level's unsharded parameters may fit. Use
   checkpoint-load and optimizer-step parity tests before adoption. NCCL-only
   time provides a 9--12% hard ceiling; a 3--8% gain is a reasonable initial
   target.
3. **Benchmark compile/autotuning modes after the two structural changes.** A
   `max-autotune` comparison may improve the GEMM-heavy 32.5% portion without
   changing numerics beyond normal kernel selection. CUDA graphs or
   `reduce-overhead` should come later because dynamic packed shapes, FSDP
   collectives, and the compiler-disabled FA4 call complicate capture, while
   measured GPU-active time already exceeds 95%.
4. **Do not prioritize BF16 persistent FSDP parameters as a neutral speed
   optimization.** They would reduce communication volume, but previous runs
   showed materially different training behavior. Activation checkpointing
   likewise saves memory at a substantial measured speed cost and is not a
   per-step optimization for the current 4K run.

Performance-to-MFU backlog status:

- [x] Benchmark `max-autotune` and `max-autotune-no-cudagraphs` against the
  unchanged default compile mode. The no-graph mode was neutral and is not the
  production default; graph-enabled mode exposed an output-lifetime error.
- [x] Prototype FA4 PrefixLM using `seqused_q`/`seqused_k` and verify complete
  forward/backward parity. The implementation remains opt-in pending a clean
  bracketed control and a longer resumed-checkpoint stability run.
- [ ] Benchmark H/L-level recurrence-aware FSDP wrapping and checkpoint-resume
  compatibility.
- [ ] Evaluate CUDA graph capture only after dynamic routing and FSDP boundaries
  are stabilized.
- [ ] Evaluate custom Triton fusion for residual routing, masking, output
  combination, or optimizer fragments that remain after the FA4 seqused path;
  do not replace efficient FA4/GEMM kernels with Triton merely for uniformity.

#### Compile-mode benchmark

The production-shaped XXL compile-mode comparison used fresh initialization,
W&B disabled, no checkpoint writes, GAS 4, BP 5, and 40 optimizer steps. The
default remains unchanged.

| Mode | Median step | Mean step | Result |
|---|---:|---:|---|
| Default control | 2.9873 s | 3.0621 s | Baseline |
| Max autotune, no CUDA graphs | 2.9820 s | 3.1528 s | Neutral median; worse outlier-sensitive mean |
| Max autotune, no CUDA graphs, cached repeat | 2.9859 s | 3.0948 s | Neutral |

The controlled median difference is below 0.2% and therefore noise at this
run length. Autotuning also adds substantial first-run compilation work, with
some generated Triton GEMM candidates rejected for exceeding the SM100
per-block resource limit. Valid candidates remained, and training completed.
This mode is retained only as an explicit diagnostic and should not replace
`default` for the current XXL geometry.

PyTorch's graph-enabled `max-autotune` was also tested. It failed before the
first completed optimizer step because a CUDA-graph replay overwrote a logits
tensor still needed by cross-entropy across recurrent/microbatch calls. Rather
than adding a local clone or step marker without validating the full lifetime
and FSDP/NCCL contract, graph-enabled modes are excluded from the supported
configuration until the dedicated CUDA-graph backlog item is implemented.

#### FA4 `seqused` PrefixLM prototype

An opt-in SM100 implementation now runs both PrefixLM attention passes over
the original fixed packed Q/K/V storage. It supplies `seqused_q` and
`seqused_k` for the prefix pass, and shifted query cumulative lengths plus
`seqused_q` for the causal pass. This removes the forward Q/K/V gathers and
output index-put operations used by the existing implementation. Enable it
with `+arch.prefixlm_fa4_impl=seqused`; the architecture default remains
`gather`, and all non-SM100 backends retain their previous behavior.

FA4 returns correct active output and gradient rows for this layout but leaves
storage rows excluded by `seqused` undefined in backward. Production packed
batches also use fixed 8192-token Q/K/V storage even when the real packed token
count is slightly smaller. The implementation therefore precomputes distinct
prefix and causal masks once per microbatch, masks undefined gradients at the
FA4 autograd boundary, and zeroes output padding. Causal K/V must use the union
of both masks: masking causal Q alone produced a fast but invalid 40-step run
whose final loss was NaN.

Direct B200 tests compare the opt-in implementation with the existing gather
path using separate cloned inputs. Mixed prefix/causal batches, prefix-only
sequences, and trailing packed-storage padding all produced bit-identical BF16
outputs and `dq`, `dk`, and `dv`. Focused CPU/mocked-backend tests cover
prepared metadata, original-storage launches, padding zeroing, and gradient
mask semantics. The relevant regression set passes 24 tests.

The corrected fresh-initialization XXL run used the same production geometry
as the compile-mode benchmark and completed 40 optimizer steps with finite
loss and accuracy:

| Path | Median step | Mean step | Peak observed GPU memory | Final loss |
|---|---:|---:|---:|---:|
| Gather, clean same-tree control | 2.9784 s | 3.0345 s | 161524 MiB | 9.7407 |
| FA4 `seqused`, corrected | 2.8654 s | 2.9107 s | 154148 MiB | 9.7411 |

The clean same-tree control ran after confirming that all eight GPUs were free
and retained exactly eight training processes throughout. Relative to that
control, `seqused` is **3.79% faster by median and 4.08% faster by mean**. Peak
observed allocation was 7,376 MiB lower, a 4.57% reduction relative to gather.
Final loss differed by 0.0004 and final token accuracy by approximately 0.0001.

An earlier same-tree gather attempt remains invalid because unrelated vLLM
servers materialized concurrently on every GPU and caused OOM. Before changing
the default, run a longer resume from identical model/optimizer state; a second
bracketing control is optional if machine conditions change. The healthy logs
are `/tmp/hrm_fa4_gather_control_clean/train.log` and
`/tmp/hrm_fa4_seqused_prod3/train.log`; the NaN diagnostic run is
`/tmp/hrm_fa4_seqused_prod2/train.log`.

#### RMSNorm fusion status

The active XXL configuration is pre-norm, not post-norm. Each transformer block
applies RMSNorm before attention and before the MLP, plus a final RMSNorm at the
end of each pre-norm transformer. In the post-routing Nsight trace these appear
as separate Triton reduction kernels named
`triton_red_fused__fused_rms_norm_0` and
`triton_red_fused__fused_rms_norm_add_0`; backward has corresponding separate
Triton reductions. The `_add_0` variants fuse RMSNorm with residual/addition
pointwise work, but none is fused into the following `nvjet` matrix
multiplication. RMSNorm-related kernels account for 2.895 seconds out of
132.266 seconds of summed device-kernel time, about 2.19%, in that pre-seqused
trace. A custom RMSNorm-GEMM prologue therefore has a small hard ceiling and
risks replacing highly tuned nvJet GEMMs; it is not the next low-risk target.

Because the `seqused` path directly removes work that represented roughly 10%
of the preceding profile, take a short steady-state Nsight Systems trace before
choosing the next implementation. Use it to verify the expected collapse in
index/radix kernels and then choose between recurrence-aware FSDP wrapping if
exposed all-gather dominates, or remaining attention/output glue if short
pointwise and masking kernels remain prominent.

#### Post-`seqused` Nsight profile

The recommended follow-up capture ran on 2026-08-28 with the corrected opt-in
`seqused` implementation, the production XXL geometry, W&B and checkpoints
disabled, an 80-second startup delay, and a 20-second steady-state trace. The
report and SQLite export are under
`logs/profiling/dfm8_xxl_fa4_seqused_20260828/`. Nsight intentionally
terminated the benchmark after capture. GPUs 1, 2, and 4--7 have complete and
consistent traces; GPUs 0 and 3 dropped events and are excluded below.

| Observation | Pre-`seqused` | Post-`seqused` |
|---|---:|---:|
| Kernel launches per complete GPU/s | 29.3--29.7K | 20.2--20.5K |
| D2H copies per complete GPU/s | 9.85 | about 9.93 |
| Index plus radix summed kernel time | 11.01% | 0.70% |
| Radix-sort kernels | 2.17% | none observed |
| GEMM summed kernel time | 32.50% | 35.34% |
| NCCL summed kernel time | 29.18% | 28.08% |
| FA4 summed kernel time | 10.02% | 10.87% |
| Triton summed kernel time | 10.49% | 11.51% |
| RMSNorm summed kernel time | 2.19% | 2.01% |

Kernel launch rate fell approximately 31%, while index/radix launch rate fell
approximately 97.6%. This verifies that `seqused` removed the targeted gather,
scatter, indexing-backward, and radix-sort machinery. D2H behavior remained
unchanged and negligible.

**Corrected on 2026-08-28 after the Triton follow-up profile:** the original
attribution below grouped gradient `masked_fill` and output `where` kernels
together. The dimensions correctly identified the affected attention glue, but
the launch count was not exclusively six gradient masks per FA4 invocation.

The replacement bottleneck appeared as generic CUDA `elementwise_kernel`
families with grid
`(28672, 1, 1)` and block `(128, 1, 1)`: 354,849 launches across the six
complete traces consumed 12.577 seconds, or 8.22% of summed kernel time. The
grid covers one full 8192-by-14-by-128 BF16 Q/K/V tensor at four values per
thread. This was sufficient to define the isolated fusion experiment, but the
later name-resolved query showed that the count included both `masked_fill`
and `where` operations.

GPU-active time remains 94.8--96.4%. NCCL-only wall time is 5.3--6.5% on five
of the six complete traces; GPU 1 is lower at 2.5%. All-gather remains the
largest individual kernel family but is substantially overlapped. Therefore,
the next target should be reducing the six gradient-mask launches, initially
with a conservative multi-tensor mask/combine boundary or pre-zeroed FA4
backward buffers. Reprofile that change before attempting recurrence-aware
FSDP wrapping. A lower-level custom backward may remove more memory traffic but
couples the project to FA4 internals and carries higher maintenance risk.

#### Multi-tensor `seqused` gradient masking

On 2026-08-28, the conservative follow-up was implemented behind the separate
`+arch.prefixlm_fa4_grad_mask_impl=triton` option. The existing eager masks
remain the default, and the architecture-wide FA4 path itself remains
`gather` by default. The Triton option combines Q/K/V masking into one launch
for the prefix FA4 pass and one launch for the causal pass. It conditionally
loads only rows that FA4 defined, rather than multiplying undefined values by
zero, and therefore preserves the NaN-safety requirement discovered during
the original `seqused` experiment. Non-CUDA and non-contiguous gradients use
the unchanged eager operation as a defensive fallback.

Direct B200 comparison of gather, eager-mask `seqused`, and Triton-mask
`seqused` produced bit-identical BF16 output and `dq`, `dk`, and `dv` for mixed
prefix/causal batches, prefix-only sequences, and padded fixed storage. A
separate CUDA test verified exact masking with different Q and K/V head counts.
The focused regression suite passes 26 tests, including a CUDA test with
different Q and K/V head counts and NaNs in excluded rows.

For two full-shape FA4 passes over 8192-by-14-by-128 gradients, three repeated
CUDA-event measurements gave `0.253--0.260 ms` for the six eager masks and
`0.083--0.087 ms` for the two Triton launches. This is an isolated roughly 3x
mask-operation speedup, not an end-to-end training claim.

A reproducible 100-step, eight-B200 comparison is provided by
`scripts/benchmark_fa4_grad_mask_100step.sh`. It runs a detached `main`
worktree, performance-branch `seqused+eager`, and performance-branch
`seqused+triton` from identical fresh initialization and data order, with W&B
and checkpoint writes disabled. A second eager run measures nondeterministic
run-to-run spread. It records timing, final metrics, and
distributed model/optimizer/EMA fingerprints under
`/tmp/hrm_fa4_grad_mask_100step`.

| 100-step path | Median step | Mean step | Final loss |
|---|---:|---:|---:|
| `main` (`3c7ca80`) | 3.5253 s | 3.6091 s | 7.46164 |
| `seqused+eager` | 2.8612 s | 2.9258 s | 7.45494 |
| `seqused+eager`, repeat | 2.8614 s | 2.9177 s | 7.44713 |
| `seqused+triton` | 2.7617 s | 2.8620 s | 7.47232 |

The Triton mask reduces median step time by **3.48%** and mean step time by
**2.18%** relative to the first eager-mask control. Relative to `main`, the
complete performance branch plus Triton reduces median step time by **21.66%**
and mean step time by **20.70%**. The two eager medians differ by only 0.007%,
so the timing result is stable at this run length.

The 100-step runs are not bitwise reproducible: even the two eager controls
produce different final model, optimizer, and EMA fingerprints. Their final
losses differ by 0.00781; Triton differs from the first eager control by
0.01737. Several Triton fingerprint deltas fall within the corresponding
eager-to-eager spread, but not every aggregate does. Therefore the correct
claim is **direct-operation bit parity and short-run numerical training
parity**, not bitwise end-state parity. Before making Triton masking the
`seqused` default, run a longer identical-checkpoint A/B and compare smoothed
loss rather than a single final minibatch.

The follow-up Nsight report is
`logs/profiling/dfm8_xxl_fa4_triton_masks_20260828/steady.nsys-rep`, with its
SQLite export alongside it. GPUs 0--4 and 7 have complete traces; GPUs 5 and 6
dropped roughly half their events and are excluded. Relative to the eager-mask
profile:

- total kernel launch rate fell from `20.23--20.50K/GPU/s` to
  `18.23--18.26K/GPU/s`, a further reduction of roughly 9.8%;
- generic `masked_fill` launches fell from approximately 41,720 to 12,894 per
  complete GPU over 20 seconds;
- the new multi-tensor kernel launched approximately 9,917 times per complete
  GPU, giving the expected 3:1 replacement of the removed mask launches;
- `where` launches remained approximately 17,850 per GPU, confirming that the
  earlier aggregate had included output combination rather than only gradient
  masking;
- eager `masked_fill` consumed about 1.34 seconds/GPU, while residual
  `masked_fill` plus the custom kernel consumed about 0.79 seconds/GPU, a 41%
  reduction for these mask families.

The next low-risk attention-glue target is therefore the remaining
prefix/causal output `where` plus padding zeroing, not another Q/K/V gradient
mask. A fused custom-autograd combine could conditionally load only the defined
FA4 output for each row, write zero for storage padding, and route output
gradients in one boundary. Its hard ceiling is smaller than this experiment:
the current `where` family consumes about 0.77 seconds/GPU over the 20-second
capture, before accounting for overlap.

#### 1,000-step `main` versus `seqused+triton` resume

On 2026-08-29, `scripts/benchmark_fa4_long_ab.sh` completed the recommended
longer comparison. Both arms resumed the exact model, optimizer, EMA, and
global row cursor from
`checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_175000`, then trained through
step 176000 on the same eight B200 GPUs and production XXL geometry. The main
arm used commit `3c7ca80`; the optimized arm used commit `8cd7af1` with
`prefixlm_fa4_impl=seqused` and `prefixlm_fa4_grad_mask_impl=triton`. W&B and
checkpoint writes were disabled. Metrics were reduced and retained every five
steps, giving 200 aligned trajectory observations.

The source checkpoint's sidecar contains an exact global row cursor but marks
its legacy batch cursor exact. A read-only resume view copied that sidecar and
set only `batch_in_epoch_exact=false`, forcing both arms to seek directly to
row 141,196,506 instead of replaying 700,000 microbatches. The source
checkpoint was not modified.

| Path | Median step | Mean step | Mean loss | Mean token accuracy |
|---|---:|---:|---:|---:|
| `main` | 3.4980 s | 3.5850 s | 1.099601 | 0.749248 |
| `seqused+triton` | 2.9120 s | 2.9077 s | 1.094871 | 0.750004 |

The complete optimized path is **16.75% faster by median** and **18.89% faster
by mean** than main. This is a cumulative comparison of all performance-branch
PrefixLM work plus Triton masking, not the isolated contribution of the Triton
mask kernel.

Across the 200 aligned observations, optimized-minus-main mean loss was
`-0.004731`, mean token-accuracy delta was `+0.000756`, and mean exact-accuracy
delta was `+0.001440`. The final minibatch losses were 1.129384 and 1.129457, a
difference of only `0.000073`. Individual 100-step windows fluctuate in both
directions, with no sustained adverse trajectory. Distributed parameter,
optimizer, and EMA fingerprints differ, as expected from the previously
documented nondeterministic training behavior; direct FA4 operation parity
remains the relevant exactness test.

Artifacts are under `/tmp/hrm_fa4_long_ab_1000step`: `RESULTS.md` contains the
summary and 100-step windows, `comparison.json` contains machine-readable
deltas, and each arm has its own `summary.json` and `train.log`. No training or
benchmark process remained after completion.

One first optimized launch is invalid and excluded: eight unrelated E4B vLLM
servers appeared after the final idle poll but before the training process
established CUDA contexts, causing immediate OOM. The retry controller now
also detects pre-CUDA `VLLM::EngineCore` processes, preserves completed arms,
and rechecks immediately before launch. The clean retry used 154.6--156.9 GiB
per GPU, compared with approximately 162.9--165.7 GiB for main.

#### Default promotion and post-promotion profile

On 2026-08-29, the validated FA4 defaults changed from `gather+eager` to
`seqused+triton` at every configuration and wrapper boundary. Both former paths
remain available through explicit `prefixlm_fa4_impl=gather` and
`prefixlm_fa4_grad_mask_impl=eager` overrides. A regression test verifies that
the Transformer config, Attention constructor, dispatch wrappers, and direct
FA4 entry point all select the same optimized defaults.

A 40-step checkpoint resume used no FA4 command-line override and completed
with finite loss. It recorded a 2.746-second median step and used
154.6--156.9 GiB per GPU. W&B and checkpoint writes were disabled. The summary
and log are under `/tmp/hrm_fa4_default_smoke`.

The subsequent 20-second default-path Nsight capture is at
`logs/profiling/dfm8_xxl_fa4_default_20260829/steady.nsys-rep`, with its SQLite
export alongside it. GPU 3 dropped roughly half its events and is excluded;
the other seven traces are complete and mutually consistent.

| Observation | Default-path result |
|---|---:|
| Kernel launches | 18.52--18.54 K/GPU/s |
| Kernel-active wall time | 96.0--96.7% |
| NCCL-only wall time | 3.5--6.9% |
| GEMM summed kernel time | 36.2--41.0% |
| NCCL summed kernel time | 16.1--29.2% |
| FA4 summed kernel time | 10.6--15.5% |
| Output `where` summed kernel time | 3.0--3.3% |
| Residual `masked_fill` summed kernel time | 1.7--1.9% |
| Triton gradient-mask summed kernel time | 1.4--1.6% |
| Index/sort summed kernel time | below 0.01% |

FSDP all-gather is the largest individual kernel family, but most communication
still overlaps compute. The output `where` family remains a smaller,
well-isolated low-risk target. The next experiment should fuse prefix/causal
output selection and storage-padding zeroing at one custom-autograd boundary;
its summed-kernel ceiling is about 3%, before overlap. Reprofile before moving
to recurrence-aware FSDP wrapping.

#### Fused FA4 output selection and padding

On 2026-08-29, the seqused FA4 path gained a custom-autograd Triton boundary
that selects the defined prefix or causal output and zeros storage padding in
one forward launch. Its backward launch routes each output gradient to exactly
one FA4 pass and writes zero for the other pass and padding. Masked loads are
part of the forward kernel, so undefined rows left by FA4 `seqused` are never
read. The previous `torch.where` plus `masked_fill` implementation remains
available through `prefixlm_fa4_output_combine_impl=eager`; the consistent
default is `triton`.

CUDA tests inject NaNs into every unused branch and verify bit-identical eager
and Triton outputs and gradients. A same-process test around the two real FA4
launches also found bit-identical output, `dq`, `dk`, and `dv` for repeated
eager and eager-versus-Triton calls. A production XXL compile smoke resumed
the exact row cursor at step 175000, completed five optimizer steps under FSDP
and `torch.compile`, and used 154--157 GiB per GPU.

The isolated 100-step A/B artifacts are under
`/tmp/hrm_fa4_output_combine_ab_1787978087`. Both arms resumed the same
checkpoint and row cursor, held all eight GPU locks for the full experiment,
and differed only in `prefixlm_fa4_output_combine_impl`.

| Output combine | Median step | Mean step | Final loss |
|---|---:|---:|---:|
| eager | 2.7415 s | 2.8644 s | 1.14599 |
| Triton | 2.6316 s | 2.7672 s | 1.16200 |
| eager repeat | 2.7545 s | 2.8762 s | 1.12975 |

Triton reduced median step time by **4.01%** and mean step time by **3.39%**
relative to the first eager arm. The eager repeat changed median and mean by
only 0.47% and 0.41%, respectively. Final-loss spread is not attributable to
the fused operator: eager-repeat minus eager was `-0.01624`, while Triton
minus eager was `+0.01602`, and the real-FA4 operation test is bit-exact.
This matches the already documented process-level training nondeterminism.

This experiment realizes the output-glue target from the post-promotion
profile. The next optimization investigation should reprofile this default,
then examine recurrence-aware FSDP wrapping; do not assume the remaining
residual masks are the next largest wall-time opportunity.
