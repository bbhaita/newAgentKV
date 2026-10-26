"""Check download endpoints without printing proxy credentials."""
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import time


def probe(url):
    start = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            return f"{url}: HTTP {response.status}, {time.monotonic() - start:.1f}s"
    except Exception as exc:
        return f"{url}: {type(exc).__name__}: {exc}"


if __name__ == "__main__":
    urls = [
        "https://pypi.org/simple/torch/",
        "https://download.pytorch.org/whl/cu128/torch/",
        "https://modelscope.cn/api/v1/models/Qwen/Qwen3-0.6B/repo?Revision=master&FilePath=config.json",
        "https://huggingface.co/Qwen/Qwen3-0.6B/resolve/main/config.json",
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(probe, urls):
            print(result, flush=True)
