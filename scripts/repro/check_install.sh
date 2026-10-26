#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
python scripts/repro/doctor.py
python scripts/repro/check_install.py
