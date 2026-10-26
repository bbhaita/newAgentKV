"""Record the actual Linux/CUDA environment and verify a GPU matrix product."""
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import torch

root = Path(__file__).resolve().parents[2]
if not torch.cuda.is_available():
    raise RuntimeError("PyTorch cannot access a CUDA GPU")
x = torch.arange(16, dtype=torch.float32, device="cuda").reshape(4, 4)
product = x @ x.T
torch.cuda.synchronize()
torch.testing.assert_close(product.cpu(), x.cpu() @ x.cpu().T)
packages = {}
for name in ["torch", "transformers", "flashinfer-python", "sgl-kernel", "apache-tvm-ffi", "triton", "quack-kernels", "minisgl", "bfcl_eval", "tau2"]:
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = None
info = {
    "python": sys.version,
    "python_prefix": sys.prefix,
    "python_executable": sys.executable,
    "platform": platform.platform(),
    "torch_cuda": torch.version.cuda,
    "gpu": torch.cuda.get_device_name(),
    "compute_capability": list(torch.cuda.get_device_capability()),
    "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
    "cuda_matrix_product_passed": True,
    "packages": packages,
    "nvcc": subprocess.check_output(["nvcc", "--version"], text=True).strip(),
    "compiler": subprocess.check_output(["g++-14", "--version"], text=True).splitlines()[0],
}
(root / "reproduction-system.json").write_text(json.dumps(info, indent=2) + "\n")
print(json.dumps(info, indent=2))
