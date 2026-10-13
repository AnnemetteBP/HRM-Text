#!/bin/bash
# Test-only fault injection; all other operations use the real NVIDIA binary.
set -euo pipefail
if [[ " $* " == *" --action restore "* ]]; then
    echo "injected restore failure" >&2
    exit 42
fi
exec "${CUDA_CHECKPOINT_REAL:?Set the real NVIDIA binary for this test}" "$@"
