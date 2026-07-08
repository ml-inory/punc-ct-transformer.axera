# Sherpa Punctuation C++ SDK

中文文本标点预测 C++ SDK，基于 AX650 NPU 推理。

## 环境要求

**本机构建**（仅验证编译，不可推理）：
- CMake ≥ 3.14
- GCC ≥ 7 或 Clang ≥ 8

**交叉编译**（产物可上板运行）：
- AX650 BSP SDK V3.10.2
  下载：https://hf-mirror.com/AXERA-TECH/AX650-Community-Hub/resolve/main/sdk/edge-computing-AX650_SDK_V3.10.2/02.%20SDK/AX650_SDK_V3.10.2/AX650_SDK_V3.10.2_20260513151335.tgz

## 构建步骤

### 本机构建

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

> 本地二进制无法执行 NPU 推理，仅用于验证代码可编译。

### 交叉编译（上板运行）

```bash
# 1. 下载并解压 BSP SDK
wget <AX650_BSP_URL> -O ax650_sdk.tgz
tar xzf ax650_sdk.tgz

# 2. 编译
mkdir build_arm && cd build_arm
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE=../toolchain-aarch64.cmake \
    -DBSP_ROOT=/path/to/AX650_SDK \
    -DAX_RUNTIME_ROOT=/path/to/AX650_SDK/ax_engine \
    -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

产物：`build_arm/demo`

## 上板运行

```bash
# 传输文件
scp build_arm/demo user@board:/tmp/
scp models/model.axmodel models/tokens.json user@board:/tmp/

# SSH 到板端执行
ssh user@board
cd /tmp
export LD_LIBRARY_PATH=/lib/ax_engine:$LD_LIBRARY_PATH
./demo model.axmodel tokens.json "今天天气真好我们出去散步吧"
```

## API 说明

### PunctuationRunner

```cpp
PunctuationRunner runner;
runner.LoadVocab("tokens.json");          // 加载词表
runner.Init("model.axmodel");             // 初始化 AX 引擎
std::string result = runner.Run("你好吗"); // 推理
```

#### 方法

| 方法 | 说明 |
|------|------|
| `Init(model_path)` | 加载 AXMODEL，初始化推理引擎 |
| `LoadVocab(vocab_path)` | 加载 tokens.json 词表 |
| `Run(text)` | 输入原始文本，返回带标点文本 |
| `VocabSize()` | 返回词表大小 |

#### 输入输出格式

- **输入**：int32 `[1, 64]`，token IDs（不足 64 补零）
- **输出**：float32 `[1, 64, 6]`，6 类标点 logits
