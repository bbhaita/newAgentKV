#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
mkdir -p reproduction-logs
python -m pytest -q -o addopts='' engine/tests/core \
  --junitxml=reproduction-logs/core-tests.xml 2>&1 | tee reproduction-logs/core-tests.log
