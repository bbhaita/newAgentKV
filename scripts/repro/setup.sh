#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
if [[ "$(uname -s)" != Linux ]]; then
  echo 'Run this script inside Linux or WSL2 Ubuntu.' >&2
  exit 1
fi
export UV_CACHE_DIR="$PWD/.cache/uv"
export UV_LINK_MODE=copy
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { echo 'uv is required: https://docs.astral.sh/uv/' >&2; exit 1; }
if [[ ! -x .venv-linux/bin/python ]]; then
  uv venv --python 3.12 .venv-linux
fi
source scripts/repro/activate.sh
python scripts/repro/prepare_cuda_compat.py
source scripts/repro/activate.sh
nvcc --version
uv pip install --python "$VIRTUAL_ENV/bin/python" \
  --constraint scripts/repro/constraints.txt \
  --torch-backend cu128 \
  -e engine pytest pytest-cov ninja torch-c-dlpack-ext
if [[ "${1:-}" == --benchmarks ]]; then
  uv pip install --python "$VIRTUAL_ENV/bin/python" \
    --constraint scripts/repro/constraints.txt \
    -e gorilla/berkeley-function-call-leaderboard -e tau2-bench soundfile
fi
uv pip check --python "$VIRTUAL_ENV/bin/python"
uv pip freeze --python "$VIRTUAL_ENV/bin/python" > reproduction-environment.txt
if [[ ! -f .env ]]; then cp .env.example .env; fi
