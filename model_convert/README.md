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

运行 `generate_calib_data.py` 使用 `models/tokens.json` 词表将 10 组中文文本转为 token ID 数组：

```bash
python generate_calib_data.py
```

如需自定义校准文本，编辑 `generate_calib_data.py` 中的 `DEFAULT_TEXTS` 列表即可。

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
