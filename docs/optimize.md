# Training Optimization Notes

Last updated: 2026-06-28

This file records low-risk ways to improve HRM-Text training throughput without
intentionally changing the optimization target or data mix. Treat every change
as a benchmarked experiment: compare tokens/sec, GPU utilization, peak memory,
loss over a short fixed window, and a small eval smoke before adopting it.

## Low-Risk Candidates

### Distributed Strategy

- Benchmark FSDP vs DDP from the same checkpoint and same data position.
- Keep FSDP as the conservative default unless DDP shows loss/eval parity.
- DDP can be faster on a single 8-GPU node because it avoids FSDP shard/gather
  overhead, but previous DDP work exposed precision and EMA pitfalls.

Suggested benchmark matrix:

```text
FSDP fp32 params, current settings
FSDP bf16 params, if memory/quality tradeoff is under investigation
DDP bf16 params, fixed mixed-precision and EMA path
DDP fp32 params, if it fits
```

Run each for a short controlled window, for example 500-1000 steps from the
same checkpoint.

### Batch Shape

- If gradient accumulation is greater than 1, increase per-GPU microbatch only
  if it reduces accumulation or loop overhead while keeping the same global
  batch.
- If `gradient_accumulation_steps=1`, increasing per-GPU batch changes the
  global batch and therefore training dynamics unless the learning-rate schedule
  is retuned. Do not treat that as a free speedup.

### Data Loading

- Keep sampled training data on the fastest filesystem available.
- Avoid heavy concurrent eval/tokenization/checkpoint jobs that create shared
  filesystem metadata pressure.
- Tune dataloader workers and prefetch only when GPU traces show input stalls.
- Cache or pre-warm small metadata/index files where possible.

### Kernel Path

- Confirm FlashAttention 4 is used in the actual attention hot path on B200.
- Check for fallback attention kernels in profiler output.
- Use `torch.compile` only after a controlled benchmark; HRM carry/control flow
  may reduce gains or increase startup overhead.

### Checkpointing

- Checkpoint writes can stall training on shared filesystems.
- Regular checkpoints must remain durable. Ephemeral checkpoints are useful for
  resumability, but a very small interval can cost throughput.
- Prefer writing a new ephemeral checkpoint fully before deleting older
  ephemeral checkpoints.
- Consider async or local-staged checkpoint writes only after measuring
  checkpoint stalls.

## Measurement Plan

For each candidate, record:

```text
tokens/sec
steps/sec
GPU utilization
peak GPU memory
data wait time if available
forward/backward time
optimizer time
checkpoint/write time
loss agreement over the benchmark window
small eval smoke result
```

Adopt a faster path only when loss agreement and smoke evals are consistent
with the baseline.
