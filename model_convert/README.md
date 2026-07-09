# Model Convert: sherpa-punct-ct-transformer

从 ONNX 导出到 AX650 AXMODEL 编译的完整流程。

目标芯片：AX650，NPU3
模型：CT-Transformer 中文标点预测，6 类
输入：int32 [1, 64]，token IDs
输出：float32 [1, 64, 6]，标点 logits

## 前置条件

- Python ≥ 3.8
- Docker（用于 Pulsar2 编译）
- 磁盘空间 ≥ 2GB
- pulsar2:6.0 Docker 镜像（脚本自动拉取）

## 环境准备

### Python 环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

验证：

```bash
python --version
pip list | grep onnx
```

输出应包含 `onnx`, `onnx-simplifier`, `onnxruntime`。

### Pulsar2 环境

Pulsar2 通过 Docker 镜像提供。从 HuggingFace 下载镜像 tar.gz，用 `docker load` 导入：

```bash
# 下载 Pulsar2 Docker 镜像（~5GB）
wget https://hf-mirror.com/AXERA-TECH/Pulsar2/resolve/main/pulsar2_6.0.tar.gz

# 导入镜像
docker load -i pulsar2_6.0.tar.gz
```

> 镜像仓库：https://hf-mirror.com/AXERA-TECH/Pulsar2

验证：

```bash
docker run --rm pulsar2:6.0 pulsar2 version
```

## ONNX 导出与静态化

此模型的 ONNX 由 sherpa-onnx 项目预导出。
`export_onnx.py` 负责静态化和验证，产物位于 `export/model.onnx`：

```bash
mkdir -p export
python export_onnx.py --input model.onnx --output export/model.onnx
```

验证：

```bash
python -c "import onnx; onnx.checker.check_model('export/model.onnx'); print('OK')"
```

## 校准数据准备

校准数据需要手动生成。在 `model_convert/` 目录下运行以下脚本，使用 `models/tokens.json` 词表将中文文本转为 token ID 数组：

```bash
mkdir -p export
python3 << 'EOF'
import json, os, tarfile, numpy as np

with open("../models/tokens.json") as f:
    tokens = json.load(f)
token_to_id = {t: i for i, t in enumerate(tokens)}

def encode(text):
    ids = []
    for ch in text:
        ids.append(token_to_id.get(ch, token_to_id.get("<unk>", 0)))
    if len(ids) < 64:
        ids += [0] * (64 - len(ids))
    else:
        ids = ids[:64]
    return np.array([ids], dtype=np.int32)  # shape (1, 64)

texts = [
    "今天天气真好我们出去散步吧",
    "你好吗我很好谢谢你的关心",
    "这个方案有三个优点第一成本低第二效率高第三维护简单",
    "请确认以下事项一合同已签署二款项已到账三交付日期已确定",
    "人工智能技术正在改变我们的生活方式",
    "明天下午三点在公司会议室开会请准时参加",
    "他是一名优秀的工程师工作认真负责",
    "北京是中国的首都拥有悠久的历史文化",
    "随着科技的发展人们的生活越来越便利",
    "学习新知识需要耐心和毅力坚持下去就会有收获",
]

for i, text in enumerate(texts):
    ids = encode(text)
    np.save(f"export/input_{i}.npy", ids)

with tarfile.open("export/calib_data.tar.gz", "w:gz") as tar:
    for i in range(len(texts)):
        tar.add(f"export/input_{i}.npy", arcname=f"input_{i}.npy")
EOF
```

如需自定义校准文本：

```python
import numpy as np, tarfile

# texts: list of Chinese strings
# tokenizer: CharTokenizer from tokens.json

inputs = []
for text in texts:
    ids = tokenizer.encode(text)[0]  # (1, 64) int32
    inputs.append(ids)

# Save as tar.gz
with tarfile.open('calib_data.tar.gz', 'w:gz') as tar:
    for i, arr in enumerate(inputs):
        np.save(f'input_{i}.npy', arr)
    tar.add('.')
```

## Pulsar2 编译

```bash
./compile_pulsar2.sh
```

编译配置 `pulsar2_config.json` 关键参数：

| 参数 | 值 | 说明 |
|------|-----|------|
| target_hardware | AX650 | 目标芯片 |
| npu_mode | NPU3 | NPU 模式 |
| input_shapes | inputs:1x64 | 输入 shape |
| calibration_method | MinMax | 量化校准方法 |
| precision_analysis | true | 逐层精度分析 |

预期编译时间：约 3-5 分钟。
产物：`compile/model.axmodel`

## 产物检查

| 文件 | 用途 | 预期大小 |
|------|------|----------|
| model.onnx | 浮点模型 | ~281 MB |
| compile/model.axmodel | 芯片可部署模型 | ~270 MB |
| compile/compile.log | 编译日志 | - |

## 常见问题

### 编译失败：Docker permission denied

```bash
sudo usermod -aG docker $USER
# 重新登录后生效
```

### 编译失败：ONNX 模型包含动态 shape

Pulsar2 仅支持静态 shape。运行 `export_onnx.py` 重新静态化。

### 编译失败：OOM

Docker 可能需要更多内存，确保至少分配 8GB。
