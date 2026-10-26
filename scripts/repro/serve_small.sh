#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
exec python -m minisgl \
  --model-path "$AGENTKV_ROOT/models/Qwen3-0.6B" \
  --host 127.0.0.1 --port "${PORT:-30000}" \
  --attention-backend fi --dtype float16 \
  --max-running-requests 1 --cuda-graph-max-bs 1 --cuda-graph-bs 1 \
  --max-seq-len-override 2048 --max-extend-length 1024 \
  --num-pages 4096 --page-size 1 \
  --eviction-plan "${EVICTION_PLAN:-agentkv-128}" \
  --compact-interval 32 --compact-after-prefill --compact-before-park \
  "$@"
