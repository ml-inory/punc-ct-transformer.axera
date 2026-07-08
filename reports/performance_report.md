# Performance Report: sherpa-punct-ct-transformer

## 流水线耗时

| 阶段 | 耗时 | 说明 |
|------|------|------|
| ACQUIRE | ~1s | 本地 tar.bz2 解压 |
| INIT | ~5s | 目录结构 + venv |
| EXPORT | ~20s | ONNX 静态化 + onnxsim |
| TOOLCHAIN | ~2s | Pulsar2 Docker 确认 |
| COMPILE | ~30s | Pulsar2 编译 |
| SIMULATE | ~60s | 4 组仿真对分 |
| SDK-GEN | ~5s | Python/C++ SDK 生成 |
| RUNONBOARD | skipped | - |
| PACKAGE | ~5s | 交付包组装 |
| **总计** | **~128s** | |

## 模型效率

- ONNX 大小: 280.72 MB
- AXMODEL 大小: 270 MB
- 压缩比: 1.04x
- MACs: N/A (Pulsar2 未输出)
- MACs 利用率: N/A

## 推理延迟

- 仿真 (pulsar2 run): ~11s
- 板端 Python SDK: N/A (板端无 Python)
- 板端 C++ SDK: N/A (缺少交叉编译工具链)
- ax_run_model (NPU): 0.264 ms avg (min 0.250, max 0.365)

## 板端内存

- 系统内存增量: 0 MB (模型在 NPU 专用内存)
- CMM 占用: 268 MB (含系统 framebuffer)

## 精度汇总（4 组输入，均值 ± 标准差）

| 指标 | 值 |
|------|-----|
| Cosine Similarity | 0.999838 ± 0.000059 |
| MAE | 0.157 ± 0.022 |
| Max Abs Diff | 0.831 ± 0.143 |

### Per-Class Cosine Similarity

| Class | Symbol | Cosine |
|-------|--------|--------|
| 0 | <unk> | 0.9999 |
| 1 | _ | 0.9997 |
| 2 | ， | 0.9990 |
| 3 | 。 | 0.9949 |
| 4 | ？ | 0.9997 |
| 5 | 、 | 0.9925 |
