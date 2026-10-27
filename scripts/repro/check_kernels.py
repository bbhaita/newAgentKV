"""Exercise the FlashInfer kernel that exposed the CUDA/glibc header conflict."""
import json
from pathlib import Path

import torch
from flashinfer import rmsnorm

torch.manual_seed(0)
x = torch.randn(4, 128, device="cuda", dtype=torch.float16)
weight = torch.ones(128, device="cuda", dtype=torch.float16)
eps = 1e-6
actual = rmsnorm(x, weight, eps)
reference = (x.float() * torch.rsqrt(x.float().square().mean(-1, keepdim=True) + eps)).half()
torch.cuda.synchronize()
torch.testing.assert_close(actual, reference, rtol=5e-3, atol=5e-3)
report = {
    "flashinfer_rmsnorm_passed": True,
    "dtype": "float16",
    "shape": list(x.shape),
    "max_absolute_error": (actual - reference).abs().max().item(),
}
root = Path(__file__).resolve().parents[2]
(root / "reproduction-kernel-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
