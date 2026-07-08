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

## 快速开始

### Python SDK

```bash
# 1. 安装 Python 3.11+（如板端无 Python，推荐 uv 安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.11

# 2. 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate
uv pip install numpy onnxruntime
# 安装 pyaxengine（AX650 NPU 推理后端）
uv pip install https://github.com/AXERA-TECH/pyaxengine/releases/download/0.1.3.rc2/axengine-0.1.3-py3-none-any.whl

# 3. 运行
cd python
python sherpa_punct_sdk/example.py
python sherpa_punct_sdk/example.py "今天天气真好我们出去散步吧"
```

### C++ SDK（交叉编译 → 上板）

```bash
# 1. 获取 AX650 BSP SDK（含交叉编译器 + 头文件）
wget https://hf-mirror.com/AXERA-TECH/AX650-Community-Hub/resolve/main/sdk/edge-computing-AX650_SDK_V3.10.2/02.%20SDK/AX650_SDK_V3.10.2/AX650_SDK_V3.10.2_20260513151335.tgz
tar xzf AX650_SDK_V3.10.2_20260513151335.tgz

# 2. 从板端拉取 aarch64 运行时库（交叉链接需要）
scp root@<board>:/soc/lib/libax_engine.so ./ax_libs/
scp root@<board>:/soc/lib/libax_sys.so ./ax_libs/

# 3. 交叉编译
cd cpp
aarch64-none-linux-gnu-g++ -std=c++17 \
    -I<BSP>/msp/out/include -Iinclude -L./ax_libs \
    -o demo src/punctuation_runner.cpp examples/demo.cpp \
    -lax_engine -lax_sys -lpthread -ldl

# 4. 推送并运行
scp demo models/model.axmodel models/tokens.json root@<board>:/tmp/
ssh root@<board> "cd /tmp && LD_LIBRARY_PATH=/soc/lib ./demo model.axmodel tokens.json"
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
- C++ 交叉编译需从板端拉取 aarch64 .so 用于链接
