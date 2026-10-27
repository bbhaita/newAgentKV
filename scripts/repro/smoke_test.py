"""Run real inference and require a committed AgentKV compaction event."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def request(url, payload=None, timeout=15):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="agentkv-128")
    parser.add_argument("--port", type=int, default=30000)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", args.port)) == 0:
            raise RuntimeError(f"Port {args.port} is already in use")
    run = args.output_dir or ROOT / "reproduction-logs" / f"smoke-{args.plan}-{time.strftime('%Y%m%d_%H%M%S')}"
    run = run.resolve()
    run.mkdir(parents=True, exist_ok=True)
    compact = run / "compact"
    events_file = compact / "compact_events.jsonl"
    if events_file.exists():
        raise RuntimeError(f"Choose a fresh output directory; existing events: {events_file}")
    model = str(ROOT / "models" / "Qwen3-0.6B")
    base = f"http://127.0.0.1:{args.port}/v1"
    env = dict(os.environ, EVICTION_PLAN=args.plan, PORT=str(args.port))
    command = ["bash", "scripts/repro/serve_small.sh", "--compact-debug-jsonl", "--compact-debug-dir", str(compact)]
    result = {"plan": args.plan, "model": model, "passed": False}
    start = time.monotonic()
    with (run / "server.log").open("w") as log:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 900
            while True:
                if proc.poll() is not None:
                    raise RuntimeError(f"Server exited ({proc.returncode}); see {run / 'server.log'}")
                log_path = run / "server.log"
                with log_path.open("rb") as startup_log:
                    startup_log.seek(max(0, log_path.stat().st_size - 65536))
                    if b"Traceback (most recent call last):" in startup_log.read():
                        raise RuntimeError(f"Server worker failed during startup; see {log_path}")
                try:
                    models = request(base + "/models")
                    if any(row["id"] == model for row in models["data"]):
                        break
                except (OSError, ValueError):
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError("Server did not become ready in 900 seconds")
                time.sleep(2)
            print(f"Ready: {base}, plan={args.plan}", flush=True)
            prompt = "Here are some observations from an agent's tool: " + "The sky is blue. " * 80
            response = request(base + "/chat/completions", {
                "model": model,
                "messages": [{"role": "user", "content": prompt + "\nWhat color is the sky? Answer briefly. /no_think"}],
                "session_id": "agentkv-reproduction-smoke",
                "temperature": 0, "max_tokens": 48,
            }, timeout=300)
            result["response"] = response
            if not response.get("choices"):
                raise AssertionError(f"No generated choices: {response}")
            message = response["choices"][0]["message"]
            text = message.get("raw_content") or message.get("content")
            if not isinstance(text, str) or not text.strip():
                raise AssertionError(f"Empty generated text: {response}")
            # This upstream API fills usage with zeros. Measure actual returned
            # text with the local model tokenizer instead of trusting placeholders.
            from tokenizers import Tokenizer

            tokenizer = Tokenizer.from_file(str(Path(model) / "tokenizer.json"))
            generated_tokens = len(tokenizer.encode(text, add_special_tokens=False).ids)
            if generated_tokens <= 0:
                raise AssertionError(f"Returned text has no tokens: {response}")
            result["generated_tokens_local_tokenizer"] = generated_tokens
            request(base + "/chat/completions", {
                "model": model, "messages": [{"role": "user", "content": ""}],
                "session_id": "agentkv-reproduction-smoke", "close_session": True, "max_tokens": 1,
            }, timeout=30)
            events = [json.loads(line) for line in events_file.read_text().splitlines()] if events_file.exists() else []
            committed = [event for event in events if event.get("status") == "committed"]
            result["compaction_events"] = len(events)
            result["committed_compactions"] = len(committed)
            if args.plan != "none" and not committed:
                raise AssertionError("No committed KV compaction was observed")
            result["passed"] = True
        except BaseException as exc:
            result["error"] = repr(exc)
            raise
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=10)
            result["elapsed_seconds"] = round(time.monotonic() - start, 2)
            (run / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
