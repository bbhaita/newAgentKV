"""Download the small smoke-test model from ModelScope, verifying every SHA256."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
REPO = "Qwen/Qwen3-0.6B"
DEST = ROOT / "models" / "Qwen3-0.6B"
API = f"https://modelscope.cn/api/v1/models/{REPO}/repo"
PREFERRED_SOURCE = "modelscope"


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(entry):
    name = entry["Path"]
    target = DEST / name
    if target.is_file() and checksum(target) == entry["Sha256"]:
        print(f"Verified cached {name}", flush=True)
        return
    query = urllib.parse.urlencode({"Revision": entry["Revision"], "FilePath": name})
    url = API + "?" + query
    if PREFERRED_SOURCE == "huggingface":
        url = f"https://huggingface.co/{REPO}/resolve/main/{urllib.parse.quote(name)}?download=true"
    elif PREFERRED_SOURCE == "modelscope-web":
        url = f"https://www.modelscope.cn/models/{REPO}/resolve/master/{urllib.parse.quote(name)}"
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(3):
        try:
            print(f"Downloading {name} ({entry['Size'] / 1024**2:.1f} MiB)", flush=True)
            with urllib.request.urlopen(url, timeout=90) as response:
                with partial.open("wb") as stream:
                    count = 0
                    last_report = time.monotonic()
                    while chunk := response.read(4 * 1024**2):
                        stream.write(chunk)
                        count += len(chunk)
                        if time.monotonic() - last_report >= 20:
                            print(f"  {name}: {count / 1024**2:.0f} MiB", flush=True)
                            last_report = time.monotonic()
            if partial.stat().st_size != entry["Size"] or checksum(partial) != entry["Sha256"]:
                raise ValueError(f"Size/SHA256 mismatch: {name}")
            partial.replace(target)
            print(f"Verified {name}", flush=True)
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def main():
    global PREFERRED_SOURCE
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["modelscope", "modelscope-web", "huggingface"], default="modelscope-web")
    PREFERRED_SOURCE = parser.parse_args().source
    DEST.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(API + "/files?Revision=master&Recursive=true", timeout=30) as response:
        manifest = json.load(response)
    if not manifest.get("Success"):
        raise RuntimeError(manifest)
    entries = [item for item in manifest["Data"]["Files"] if item["Type"] == "blob"]
    # This repository has only top-level model/tokenizer/license files.
    for item in entries:
        if Path(item["Path"]).name != item["Path"]:
            raise ValueError(f"Unexpected model path: {item['Path']}")
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(download, entries))
    (ROOT / "reproduction-model.json").write_text(
        json.dumps({"repo": REPO, "manifest_source": "modelscope", "download_source": PREFERRED_SOURCE, "files": entries}, indent=2) + "\n"
    )
    print(f"Model ready: {DEST}", flush=True)


if __name__ == "__main__":
    main()
