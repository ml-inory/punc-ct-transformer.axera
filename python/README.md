# Sherpa Punctuation Python SDK

将中文文本自动添加标点符号（逗号、句号、问号、顿号）。

## 环境要求

- Python ≥ 3.8
- numpy, onnxruntime (CPU 回退)
- pyaxengine (AX650 NPU 推理，可选)

## 安装

```bash
cd sdk/python
pip install -r requirements.txt

# 如需 NPU 推理，额外安装 pyaxengine：
git clone https://github.com/AXERA-TECH/pyaxengine.git
cd pyaxengine && pip install .
```

## 快速运行

```bash
# 使用示例文本
python sherpa_punct_sdk/example.py

# 自定义文本
python sherpa_punct_sdk/example.py "今天天气真好我们出去散步吧"
```

## API 说明

### PunctuationPipeline

```python
from sherpa_punct_sdk import PunctuationPipeline

pipeline = PunctuationPipeline(
    model_path="models/model.axmodel",
    tokens_path="models/tokens.json",
    provider="AxEngineExecutionProvider",  # or "CPUExecutionProvider"
)
result = pipeline("你好吗我很好谢谢")
print(result)  # 你好吗？我很好，谢谢。
```

#### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `model_path` | str | AXMODEL 或 ONNX 模型路径 |
| `tokens_path` | str | tokens.json 词表路径 |
| `provider` | str | AxEngineExecutionProvider (NPU) 或 CPUExecutionProvider |

#### 推理方法
`pipeline(text: str) -> str`：输入原始文本，返回添加标点后的文本。

## 输入预处理

- 中文按字符切分，英文按单词切分
- Token IDs 填充至 64 长度（0 填充）
- 输入 dtype: int32, shape: [1, 64]
