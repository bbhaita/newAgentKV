#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
python scripts/repro/prepare_cuda_compat.py "$@"
if [[ "${1:-}" == --inspect ]]; then exit; fi
source scripts/repro/activate.sh
printf '#include <cuda_runtime.h>\n#include <cmath>\n__global__ void probe(float *x) { x[threadIdx.x] += 1.0f; }\n' > .cache/cuda-compat-probe.cu
for standard in c++17 c++20; do
  "$CUDA_HOME/bin/nvcc" -ccbin "$CC" -std="$standard" -arch=sm_86 \
    -isystem "$CUDA_HOME/include" --compiler-options=-fPIC \
    -c .cache/cuda-compat-probe.cu -o ".cache/cuda-compat-probe-$standard.o"
done
echo 'CUDA C++17/C++20 probes with FlashInfer include flags passed.'
