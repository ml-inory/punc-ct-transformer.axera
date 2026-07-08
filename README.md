# Sherpa Punctuation CT-Transformer for AX650

中文文本自动添加标点符号模型。CT-Transformer 架构，6 类标点预测：`，` `。` `？` `、` `_` `<unk>`。

**目标芯片**: AX650 (NPU3)  
**原始来源**: [sherpa-onnx pretrained models](https://k2-fsa.github.io/sherpa/onnx/punctuation/pretrained_models.html#id4) — ct-transformer-zh-en-vocab272727-2024-04-12

## 模型规格

| 属性 | 值 |
|------|-----|
| 输入 | int32 [1, 64]，token IDs |
| 输出 | float32 [1, 64, 6]，6 类 logits |
| 词表 | 272,727 tokens (CharTokenizer) |
| ONNX 大小 | ~281 MB |
| AXMODEL 大小 | ~270 MB |

### 标点类别

| ID | 标点 |
|----|------|
| 0 | <unk> |
| 1 | _ (无标点) |
| 2 | ， |
| 3 | 。 |
| 4 | ？ |
| 5 | 、 |

## 目录说明

| 目录 | 用途 |
|------|------|
| `models/` | AXMODEL、模型元信息、词表 |
| `python/` | Python SDK（pyaxengine NPU 推理） |
| `cpp/` | C++ SDK（AX_ENGINE 原生 API 交叉编译） |
| `model_convert/` | ONNX 导出 + Pulsar2 编译（复现用） |
| `reports/` | 导出、编译、仿真、精度、上板报告 |

## 板端环境要求

| 组件 | 说明 |
|------|------|
| AX650 芯片 | NPU 驱动已加载 |
| libax_engine.so | 位于 `/soc/lib/`（系统自带） |
| ldconfig | 缓存 `/soc/lib` 以便 `ctypes.util.find_library` 工作 |

**如果 `python3 -c "import ctypes.util; print(ctypes.util.find_library('ax_engine'))"` 返回 `None`**：
```bash
echo "/soc/lib" >> /etc/ld.so.conf && ldconfig
```

## 下载模型文件

`models/model.axmodel` 为占位文件，需要替换为实际编译产物。

### 方式一：直接获取已编译的 AXMODEL

从项目 GitHub Releases 下载（如有发布），或联系项目维护者获取。

### 方式二：从 ONNX 自行编译

详见 `model_convert/README.md`。

```bash
# 1. 下载 ONNX 模型（~281MB）
wget https://huggingface.co/csukuangfj/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12/resolve/main/model.onnx -O model_convert/model.onnx

# 2. 使用 Pulsar2 编译为 AXMODEL
cd model_convert && ./compile_pulsar2.sh

# 3. 复制产物
cp compile/model.axmodel ../models/model.axmodel
```

## 快速开始

### Python SDK

```bash
# 0. 板端要求 Python 3.11+
python3 --version
# 如未安装：curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.11

# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
# 国内板端推荐使用清华镜像加速 pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy onnxruntime

# 2. 安装 pyaxengine（AX650 NPU 推理后端）
# 若板端无法访问 GitHub，在 PC 下载 wheel 后 scp 传到板端再安装：
#   wget https://github.com/AXERA-TECH/pyaxengine/releases/download/0.1.3.rc2/axengine-0.1.3-py3-none-any.whl
#   scp axengine-0.1.3-py3-none-any.whl root@<board>:/tmp/
pip install /tmp/axengine-0.1.3-py3-none-any.whl

# 3. 运行（需设置 PYTHONPATH 以导入 sherpa_punct_sdk 包）
PYTHONPATH=python python python/sherpa_punct_sdk/example.py
PYTHONPATH=python python python/sherpa_punct_sdk/example.py "今天天气真好我们出去散步吧"
```

### C++ SDK（交叉编译 → 上板）

```bash
# 1. 准备交叉编译器
#    下载 aarch64-none-linux-gnu-g++ 工具链，例如：
#    https://developer.arm.com/downloads/-/gnu-a

# 2. 从板端拉取 NPU 头文件和运行时库（交叉链接需要）
mkdir -p ax_libs ax_headers
scp -r root@<board>:/soc/lib/ ax_libs/
scp -r root@<board>:/soc/include/ ax_headers/

# 3. 交叉编译
cd cpp
<CROSS_COMPILE_PREFIX>g++ -std=c++17 \
    -Iinclude -I../ax_headers/include -L../ax_libs/lib \
    -Wl,-rpath-link,../ax_libs/lib \
    -o demo src/punctuation_runner.cpp examples/demo.cpp \
    -lax_engine -lax_sys -lpthread -ldl

# <CROSS_COMPILE_PREFIX> 示例：
#   ~/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-

# 4. 推送 demo 到板端并运行（模型文件已提前放在板端）
scp demo root@<board>:/tmp/
ssh root@<board> "cd /tmp && LD_LIBRARY_PATH=/soc/lib ./demo /path/to/model.axmodel /path/to/tokens.json"
```

### 从零复现模型转换

详见 `model_convert/README.md`。

## 精度

| 指标 | 值 |
|------|-----|
| Cosine Similarity | 0.9998 |
| MAE | 0.157 |

## 上板性能

| SDK | 引擎 | 延迟 |
|-----|------|------|
| C++ | AX_ENGINE_RunSync 原生 API | avg 0.254ms |
| Python | pyaxengine AxEngineExecutionProvider | ~同 |

## 已知限制

- 输入长度固定为 64 tokens，长文本需分段处理
- Buildroot 板端需额外配置 ldconfig 使 pyaxengine 的 `ctypes.util.find_library` 正常工作
- C++ 交叉编译需从板端拉取 aarch64 .so 和头文件用于链接
- `uv venv` 在 musl libc（Buildroot）上不工作，请使用 `python3 -m venv`
