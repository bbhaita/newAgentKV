# AgentKV 本地复现

本目录包含 [LiuTaowen-Tony/agentkv](https://github.com/LiuTaowen-Tony/agentkv) 的源码快照及三个子模块的完整源码。
原有 `origin` 和 Git 历史保留，原先删除的 `x.py` 保持删除状态。子模块源码以普通目录存放，后续提交本目录时可一起保存；无需再次运行 `git submodule update`。

## 源码版本

| 组件 | 固定提交 |
| --- | --- |
| agentkv | `b5280b7c42bd90962712c19f8e0047c89ca40d6d` |
| engine | `254c57bc84e4a7895159ba1062bd46c83626f511` |
| gorilla / BFCL | `c1c222ed87e1cf2ad721e332bdb8ae977ba9cc31` |
| tau2-bench | `b761585177de694ad6ac83eff70f1f0cf7af4600` |

版本信息见 `reproduction-source.json`。`reproduction-source-check.json` 记录初次导入时与上游工作树的逐文件比较结果；比较忽略 CRLF/LF 差异，根目录 `.gitignore` 增加了本机环境排除项。

## 本机运行环境

- Windows + 已安装的 Ubuntu WSL2，推理和评测使用 WSL 中的 Python。
- NVIDIA RTX 3060 Laptop，6GB 显存，计算能力 8.6。
- WSL 内 CUDA Toolkit 12.8、Python 3.12.15，独立环境 `.venv-linux/`。
- CUDA 编译使用现有 GCC/G++ 14，避免默认 GCC 15 与 CUDA 12.8 不兼容。
- 模型、Python 包和编译缓存保存在本目录的 `models/`、`.cache/`，均被 Git 忽略。

当前 Windows 路径含空格，FlashInfer 0.5.3 的 Ninja 生成器不能直接处理该路径。`scripts/repro/wsl.ps1` 在 WSL 中创建 `/mnt/agentkv-newAgentKV` 的临时 bind mount，并通过该无空格路径运行。代码、环境和缓存仍是当前文件夹中的同一份文件，没有搬移。WSL 重启后，该入口会重新建立映射。它以 WSL root 仅执行挂载准备，安装和推理仍使用普通用户。

本机 Ubuntu 26.04 的 glibc 2.43 与 CUDA 12.8 的数学函数异常声明存在兼容冲突。安装脚本会在 `.cache/cuda-compat/` 创建局部头文件及 nvcc 驱动副本，为冲突函数补齐 `noexcept`；系统 CUDA 文件不受修改。此处理参考 [NVIDIA 开发者论坛中的问题与修复记录](https://forums.developer.nvidia.com/t/error-exception-specification-is-incompatible-for-cospi-sinpi-cospif-sinpif-with-glibc-2-41/323591)。可单独执行以下命令，使用 FlashInfer 相同的 include 选项，实际编译 CUDA C++17/C++20 内核来验证兼容层：

```powershell
.\scripts\repro\wsl.ps1 prepare_cuda.sh
```

上游实验入口默认只注册 Qwen3-8B 和 Qwen3-32B。仅 FP16/BF16 权重就约需 16GB/64GB，另需 KV 缓存和运行空间，因此本机采用 Qwen3-0.6B 做运行验证。小模型验证不等于复现原始模型的 BFCL/tau2 分数或吞吐量。

## 已完成的本机验证（2026-10-27）

完整记录见 [reproduction-report.json](reproduction-report.json)。

| 检查 | 结果 |
| --- | --- |
| 上游引擎核心测试 | 67 项通过，含 GPU Triton KV 压缩测试 |
| BFCL / tau2 | 命令入口、实验 runner 参数入口、tau2 数据检查通过 |
| CUDA / FlashInfer | C++17/C++20 编译通过；RMSNorm GPU 小样本与 PyTorch 参考结果一致 |
| Windows 本地访问 | `http://127.0.0.1:30000/v1/models` 访问通过 |
| 无压缩基线 | 真实 Qwen3-0.6B 生成通过，返回 `The sky is blue.`，本地分词统计为 9 个输出 token |
| AgentKV-128 | 返回相同答案，记录到 2 次已提交的 Triton KV 压缩 |

AgentKV 首次压缩把该请求的物理 KV 缓存长度从 **432 token 降到 128 token**；结束前再次从 137 降到 128。原始记录保存在 `reproduction-logs/agentkv-128/compact/compact_events.jsonl`。这些是功能验证数据，固定 KV 内存池、首次 JIT 编译和初始化时间均不能据此换算为显存节省或吞吐量提升。

成功的两次推理结果分别位于 `reproduction-logs/baseline-none-final/result.json` 和 `reproduction-logs/agentkv-128/result.json`。验证脚本完成后会自动停止测试服务；需要使用接口时执行下文的常驻启动命令。首次加载依赖、权重与编译内核可能需要数分钟。

## 安装与验证

在 PowerShell 中切换到本目录后执行：

```powershell
.\scripts\repro\wsl.ps1 setup.sh --benchmarks
.\scripts\repro\wsl.ps1 test_core.sh
.\scripts\repro\wsl.ps1 check_install.sh
.\scripts\repro\wsl.ps1 check_kernels.sh
```

通过上述 PowerShell 入口建立映射后，也可以在 Ubuntu 终端中执行：

```bash
cd /mnt/agentkv-newAgentKV
bash scripts/repro/setup.sh --benchmarks
source scripts/repro/activate.sh
```

`setup.sh` 默认安装引擎和测试依赖，`--benchmarks` 另安装 BFCL、tau2 及 qwen-agent 漏声明的 `soundfile`。核心版本约束位于 `scripts/repro/constraints.txt`；成功安装后实际版本写入 `reproduction-environment.txt`。

下载用于验证的小模型：

```powershell
python scripts/repro/download_model.py
```

默认使用 ModelScope 网页入口，也可显式选择 Hugging Face 或 ModelScope API：

```bash
python scripts/repro/download_model.py --source huggingface
python scripts/repro/download_model.py --source modelscope
```

模型约 1.5GB。下载器校验 ModelScope 清单中的文件大小与 SHA256，完成后写出 `reproduction-model.json`。如果网络阻断 CDN，配置文件下载成功并不表示权重已下载完成。

运行真实模型推理与压缩验证（WSL）：

```bash
bash scripts/repro/smoke_test.sh --plan none
bash scripts/repro/smoke_test.sh --plan agentkv-128
```

脚本使用本地模型、单并发、2048 上下文，用本地 tokenizer 检查实际返回文本的 token；AgentKV 验证还要求日志出现已提交的 KV 压缩事件。当前上游 API 的 `usage` 字段固定填零，因此它不能用于判断是否生成或计算吞吐量。服务在验证后自动退出，结果保存在带时间戳的 `reproduction-logs/smoke-*/`。也可用 `--output-dir` 指定新的结果目录。

常驻启动：

```powershell
.\scripts\repro\wsl.ps1 serve_small.sh
```

或在已建立映射的 WSL 终端中：

```bash
bash scripts/repro/serve_small.sh
# 基线：
EVICTION_PLAN=none bash scripts/repro/serve_small.sh
```

接口地址 `http://127.0.0.1:30000/v1`。此分支的聊天请求需要 `session_id`，例如：

```bash
curl http://127.0.0.1:30000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"What is 2+2? /no_think"}],"session_id":"demo-1","max_tokens":32,"temperature":0}'
```

## 在大显存 Linux 机器上运行原始实验

在目标机器安装合适的 NVIDIA 驱动、CUDA Toolkit 和 uv，然后执行 `bash scripts/repro/setup.sh --benchmarks`，激活环境。
`.env` 已从 `.env.example` 创建，当前为空密钥模板。BFCL `multi_turn_base` 不需要外部 API；`web_search_base` 需要对应搜索服务配置。

```bash
source scripts/repro/activate.sh
MODEL=qwen3-8b EVICTION_PLAN=none TASK=multi_turn_base \
  bash experiment/scripts/run_bfcl.sh
MODEL=qwen3-8b EVICTION_PLAN=agentkv-2048 TASK=multi_turn_base \
  bash experiment/scripts/run_bfcl.sh
```

tau2 的用户模拟器默认使用外部模型，需要在 `.env` 中配置有效的 `OPENAI_API_KEY`：

```bash
MODEL=qwen3-8b DOMAINS=airline EVICTION_PLAN=agentkv-512 \
  bash experiment/scripts/run_tau2.sh --num-tasks 1
```

注意：当前固定版本的 `experiment/runners/tau2.py` 会检查该密钥，且只给 agent 配置本地 `api_base`；它没有为用户模拟器配置本地地址。因此只修改 `--user-llm` 并不能切换为完全本地评测。上游脚本注释对此描述不完整，本次保留其源码，在这里明确记录实际行为。

正式比较需要保持模型、任务、预算、并发和提示长度一致。`triattn` 还需额外校准统计，见 `engine/python/minisgl/eviction/triattention_stats/README.md`。
