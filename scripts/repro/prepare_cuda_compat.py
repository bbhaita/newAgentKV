"""Build a project-local CUDA 12.8 header overlay for glibc >= 2.41.

No files in the system toolkit are changed. See NVIDIA's first-hand report:
https://forums.developer.nvidia.com/t/323591
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(os.environ.get("AGENTKV_SYSTEM_CUDA_HOME", "/usr/local/cuda")).resolve()
COMPAT = ROOT / ".cache" / "cuda-compat"
NAMES = r"(?:rsqrtf?|sinpif?|cospif?)"


def main():
    include = (SYSTEM / "include").resolve()
    if "--inspect" in sys.argv:
        for name in ["math_functions.h", "math_functions.hpp"]:
            path = include / "crt" / name
            print(path)
            for line in path.read_text().splitlines():
                if re.search(rf"\b{NAMES}\(", line) and ("extern" in line or "__func__" in line):
                    print(line)
        return
    version = subprocess.check_output([str(SYSTEM / "bin" / "nvcc"), "--version"], text=True)
    libc = tuple(map(int, platform.libc_ver()[1].split(".")[:2]))
    marker = COMPAT / "agentkv-compat.json"
    if "release 12.8," not in version or libc < (2, 41):
        marker.unlink(missing_ok=True)
        print("CUDA/glibc header overlay is not needed for this configuration.")
        return
    original = include / "crt" / "math_functions.h"
    fingerprint = hashlib.sha256(original.read_bytes()).hexdigest()
    if marker.is_file() and json.loads(marker.read_text()).get("source_sha256") == fingerprint:
        print(f"CUDA header overlay ready: {COMPAT}")
        return
    (COMPAT / "include").mkdir(parents=True, exist_ok=True)
    (COMPAT / "bin").mkdir(exist_ok=True)
    for item in include.iterdir():
        target = COMPAT / "include" / item.name
        if item.name == "crt":
            shutil.copytree(item, target, dirs_exist_ok=True)
        elif item.name == "cuda_runtime.h":
            # Keep quoted crt/* includes relative to this overlay.
            shutil.copy2(item, target)
        elif not target.exists():
            target.symlink_to(item, target_is_directory=item.is_dir())
    changes = {}
    for name in ["math_functions.h", "math_functions.hpp"]:
        path = COMPAT / "include" / "crt" / name
        text = path.read_text()
        text, extern_count = re.subn(
            rf"(extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__\s+(?:double|float)\s+{NAMES}\((?:double|float) x\));",
            r"\1 noexcept (true);", text,
        )
        text, inline_count = re.subn(
            rf"(__func__\((?:double|float)\s+{NAMES}\((?:double|float)\s+\w+\))\)",
            r"\1 noexcept (true))", text,
        )
        path.write_text(text)
        changes[name] = {"extern": extern_count, "inline": inline_count}
    if changes["math_functions.h"]["extern"] != 6:
        raise RuntimeError(f"Unexpected CUDA header layout: {changes}")
    for item in (SYSTEM / "bin").iterdir():
        if item.name == "nvcc":
            continue
        target = COMPAT / "bin" / item.name
        if not target.exists():
            target.symlink_to(item)
    for name in ["lib64", "nvvm"]:
        target = COMPAT / name
        if not target.exists():
            target.symlink_to((SYSTEM / name).resolve(), target_is_directory=True)
    wrapper = COMPAT / "bin" / "nvcc"
    # Workspace is accessed through its path without spaces.
    wrapper.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\n'
        f'exec "{SYSTEM / "bin" / "nvcc"}" -I"{COMPAT / "include"}" "$@"\n'
    )
    wrapper.chmod(0o755)
    marker.write_text(json.dumps({"system_cuda": str(SYSTEM), "source_sha256": fingerprint, "changes": changes}, indent=2) + "\n")
    print(json.dumps({"overlay": str(COMPAT), "changes": changes}, indent=2))


if __name__ == "__main__":
    main()
