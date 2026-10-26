#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
python scripts/repro/prepare_cuda_compat.py "$@"
if [[ "${1:-}" == --inspect ]]; then exit; fi
source scripts/repro/activate.sh
printf '#include <cuda_runtime.h>\n__global__ void probe(float *x) { x[threadIdx.x] += 1.0f; }\n' > .cache/cuda-compat-probe.cu
"$CUDA_HOME/bin/nvcc" -ccbin "$CC" -std=c++20 -arch=sm_86 \
  -c .cache/cuda-compat-probe.cu -o .cache/cuda-compat-probe.o
echo 'CUDA C++20 compilation probe passed.'
