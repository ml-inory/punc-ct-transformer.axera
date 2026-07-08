# Export Report: sherpa-punct-ct-transformer

## 模型信息
- 模型名称: sherpa-punct-ct-transformer
- 架构: CT-Transformer (SAN-M encoder)
- 原始来源: ModelScope iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch
- ONNX 已由 sherpa 社区预先导出

## ONNX 属性
- Opset: 14
- IR version: 7
- Producer: PyTorch
- 文件大小: 294,372,519 bytes (~281 MB, float32)

## 输入
| 名称 | Shape | Dtype |
|------|-------|-------|
| inputs | [batch_size, feats_length] | int32 |
| text_lengths | [batch_size] | int32 |

## 输出
| 名称 | Shape | Dtype | 语义 |
|------|-------|-------|------|
| logits | [batch_size, logits_length, 6] | float32 | 6类标点logits |

## 标点类别
0: <unk>, 1: _, 2: ，, 3: 。, 4: ？, 5: 、

## 验证
- ONNX checker: PASS
- ONNX Runtime 推理: PASS
- Tokenizer: CharTokenizer, vocab 272727

## 校准数据
- 10 组中文测试句子
- 输入为 int32 token IDs
- 长度范围: 8-20 tokens

## 静态化

Pulsar2 仅支持静态 ONNX。已将模型从动态 shape 静态化：

- `inputs`: [batch_size, feats_length] → [1, 64]
- `text_lengths`: [batch_size] → [1]
- `logits`: [batch_size, logits_length, 6] → [1, 64, 6]

方法: `onnx.tools.update_model_dims.update_inputs_outputs_dims()`  
ONNX checker: PASS  
ORT 推理: PASS

校准数据已更新为 pad-64, text_lengths=64。
