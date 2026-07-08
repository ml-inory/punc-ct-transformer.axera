# Compile Report: sherpa-punct-ct-transformer

## 编译概要
- Pulsar2 版本: 6.0 (commit 48520c11)
- 目标硬件: AX650, NPU3
- 编译时间: N/A s
- 状态: SUCCESS

## 文件大小
- ONNX: 294,387,490 bytes (280.75 MB)
- AXMODEL: 283,103,944 bytes (269.99 MB)
- 压缩比: 1.04x

## 输入输出
- Input: inputs (int32, [1, 64])
- Output: logits (float32, [1, 64, 6])
- Note: text_lengths converted to graph constant (value=64)

## 量化配置
- 方法: MinMax
- 校准数据: 10 组中文句子, int32 token IDs, padded to 64
