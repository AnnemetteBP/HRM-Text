---
type: Technical Reference
title: Conda-Local CUDA Compiler Toolchain
description: 'Part of FlashAttention on B200: Conda-Local CUDA Compiler Toolchain.'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200.md
---
# Conda-Local CUDA Compiler Toolchain

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Update, 2026-08-10. Confidence: high for the NVIDIA package availability and
local Conda layout; the installation command has not yet been executed in this
environment.

The host NVIDIA driver must remain system-provided, but `nvcc`, CUDA headers,
and development libraries can be installed inside the `hrm` environment.

Superseded later on 2026-08-10: the initial recommendation used the complete
`cuda-toolkit` metapackage. A solver dry-run against `hrm` showed that the
headless `cuda-compiler=13.2.2` metapackage installs 45 compiler/runtime
development packages, including `nvcc`, CCCL, CUDA runtime development files,
driver stubs, NVVM, and a C/C++ host compiler, without any Xorg or audio
packages. It is the better fit for FlashInfer/vLLM JIT compilation:

```bash
/home/ucloud/miniforge3/bin/mamba install -n hrm -c nvidia cuda-compiler=13.2.2
```

After activation, `$CONDA_PREFIX/bin` is already on `PATH`. Set `CUDA_HOME`
explicitly for build systems that do not infer the environment prefix:

```bash
conda activate hrm
export CUDA_HOME="$CONDA_PREFIX"
export PATH="$CUDA_HOME/bin:$PATH"
nvcc --version
```

This can coexist with a system/runfile toolkit. Whichever location is selected
by `CUDA_HOME` and `PATH` supplies the compiler and headers; GPU execution still
uses the host kernel driver. The still-narrower `nvidia::cuda-nvcc` package
exists, but by itself may omit headers or link-time development files needed by
a later JIT extension. Add `cuda-libraries-dev=13.2.2` only if future custom
extensions require the broader CUDA math-library development set; it is not
needed for the presently observed FlashInfer sampler JIT failure.
