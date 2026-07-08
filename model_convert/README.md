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

Pulsar2 通过 Docker 镜像提供：

```bash
# 从 HuggingFace 镜像站拉取
docker pull pulsar2:6.0
```

> 镜像地址：https://hf-mirror.com/AXERA-TECH/Pulsar2

验证：

```bash
docker run --rm pulsar2:6.0 -c "pulsar2 --version"
```

## ONNX 导出与静态化

此模型的 ONNX 由 sherpa-onnx 项目预导出。
`export_onnx.py` 负责静态化和验证：

```bash
python export_onnx.py --input model.onnx --output model_static.onnx
```

验证：

```bash
python -c "import onnx; onnx.checker.check_model('model_static.onnx'); print('OK')"
```

## 校准数据准备

校准数据已随包提供：`calib_data.tar.gz`，包含 10 组中文文本样本的 token ID 数组。

如需重新生成：

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
