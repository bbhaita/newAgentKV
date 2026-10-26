#!/usr/bin/env bash
# A bind mount gives Ninja a path without spaces while all files stay in the workspace.
set -euo pipefail
if [[ $EUID != 0 ]]; then
  echo 'This script only mounts the workspace and must run as WSL root.' >&2
  exit 1
fi
source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
target_dir=/mnt/agentkv-newAgentKV
test -f "$source_dir/reproduction-source.json"
mkdir -p "$target_dir"
if mountpoint -q "$target_dir"; then
  if [[ "$(stat -c '%d:%i' "$source_dir")" != "$(stat -c '%d:%i' "$target_dir")" ]]; then
    echo "$target_dir is already mounted from another workspace" >&2
    exit 1
  fi
else
  if [[ -n "$(ls -A "$target_dir")" ]]; then
    echo "Refusing to hide files in nonempty $target_dir" >&2
    exit 1
  fi
  mount --bind "$source_dir" "$target_dir"
fi
echo "Workspace available at $target_dir"
