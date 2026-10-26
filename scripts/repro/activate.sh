#!/usr/bin/env bash
# Source this file from an existing WSL/Linux shell.
AGENTKV_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "$AGENTKV_ROOT" == *' '* ]]; then
  if [[ -f /mnt/agentkv-newAgentKV/reproduction-source.json && "$AGENTKV_ROOT" -ef /mnt/agentkv-newAgentKV ]]; then
    AGENTKV_ROOT=/mnt/agentkv-newAgentKV
  else
    echo 'Use scripts/repro/wsl.ps1 to create the path without spaces required by CUDA JIT.' >&2
    return 1
  fi
fi
export AGENTKV_SYSTEM_CUDA_HOME="${AGENTKV_SYSTEM_CUDA_HOME:-${CUDA_HOME:-/usr/local/cuda}}"
export CUDA_HOME="$AGENTKV_SYSTEM_CUDA_HOME"
if [[ -f "$AGENTKV_ROOT/.cache/cuda-compat/agentkv-compat.json" ]]; then
  export CUDA_HOME="$AGENTKV_ROOT/.cache/cuda-compat"
fi
export PATH="$CUDA_HOME/bin:$PATH"
if [[ -x /usr/bin/gcc-14 && -x /usr/bin/g++-14 ]]; then
  export CC="${CC:-/usr/bin/gcc-14}"
  export CXX="${CXX:-/usr/bin/g++-14}"
  export NVCC_CCBIN="${NVCC_CCBIN:-/usr/bin/g++-14}"
fi
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
export UV_CACHE_DIR="$AGENTKV_ROOT/.cache/uv"
export HF_HOME="$AGENTKV_ROOT/.cache/huggingface"
export MODELSCOPE_CACHE="$AGENTKV_ROOT/.cache/modelscope"
export TVM_FFI_CACHE_DIR="$AGENTKV_ROOT/.cache/tvm-ffi"
export FLASHINFER_WORKSPACE_BASE="$AGENTKV_ROOT/.cache/flashinfer"
export TRITON_CACHE_DIR="$AGENTKV_ROOT/.cache/triton"
export CUDA_CACHE_PATH="$AGENTKV_ROOT/.cache/cuda"
export TORCH_EXTENSIONS_DIR="$AGENTKV_ROOT/.cache/torch-extensions"
export TAU2_DATA_DIR="$AGENTKV_ROOT/tau2-bench/data"
export MAX_JOBS="${MAX_JOBS:-2}"
export TOKENIZERS_PARALLELISM=false
export LITELLM_LOCAL_MODEL_COST_MAP=True
source "$AGENTKV_ROOT/.venv-linux/bin/activate"
# uv's activation file embeds the original path; use the bind mount for JIT includes too.
export VIRTUAL_ENV="$AGENTKV_ROOT/.venv-linux"
export PATH="$VIRTUAL_ENV/bin:$PATH"
cd "$AGENTKV_ROOT"
