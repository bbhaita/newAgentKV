"""Check benchmark entry points and packaged data without making model API calls."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
logs = root / "reproduction-logs"
logs.mkdir(exist_ok=True)
commands = {
    "bfcl_cli": [str(Path(sys.executable).with_name("bfcl")), "--help"],
    "tau2_data": [str(Path(sys.executable).with_name("tau2")), "check-data"],
    "bfcl_runner": [sys.executable, "-m", "experiment.runners.bfcl", "run", "--help"],
    "tau2_runner": [sys.executable, "-m", "experiment.runners.tau2", "run", "--help"],
}
results = {}
for name, command in commands.items():
    with (logs / f"{name}.log").open("w") as stream:
        try:
            result = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, timeout=300)
            results[name] = {"returncode": result.returncode, "passed": result.returncode == 0}
        except subprocess.TimeoutExpired:
            results[name] = {"passed": False, "error": "timeout after 300 seconds"}
    print(name, results[name], flush=True)
(root / "reproduction-install-check.json").write_text(json.dumps(results, indent=2) + "\n")
raise SystemExit(0 if all(row["passed"] for row in results.values()) else 1)
