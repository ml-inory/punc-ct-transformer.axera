#!/usr/bin/env python3
"""Example: Sherpa Onnx Punctuation Prediction on AX650 NPU.

Usage:
    python example.py                                    # demo texts
    python example.py "今天天气真好我们出去散步吧"         # custom text
"""

import os
import sys


def main():
    from sherpa_punct_sdk import PunctuationPipeline

    # Paths relative to project root (script is at python/sherpa_punct_sdk/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "..", "..", "models", "model.axmodel")
    tokens_path = os.path.join(base_dir, "..", "..", "models", "tokens.json")

    # On-device fallback: compiled artifacts via model_convert/
    if not os.path.exists(model_path):
        model_path = os.path.join(base_dir, "..", "..", "model_convert", "compile", "model.axmodel")
    if not os.path.exists(tokens_path):
        tokens_path = os.path.join(base_dir, "..", "..", "model_convert", "export", "tokens.json")
    if not os.path.exists(model_path):
        # Use ONNX for local testing (CPU only)
        model_path = os.path.join(base_dir, "..", "..", "model_convert", "model.onnx")
        print("NOTE: Using ONNX model (CPU). For NPU, ensure model.axmodel is present.")
        provider = "CPUExecutionProvider"
    else:
        provider = "AxEngineExecutionProvider"

    print(f"Model: {model_path}")
    print(f"Tokens: {tokens_path}")
    print(f"Provider: {provider}")

    pipeline = PunctuationPipeline(model_path, tokens_path, provider)

    texts = []
    if len(sys.argv) > 1:
        texts = [" ".join(sys.argv[1:])]
    else:
        texts = [
            "你好吗how are you我很好谢谢",
            "今天天气真不错我们出去走走吧",
            "这个方案有三个优点第一成本低第二效率高第三维护简单",
            "请确认以下事项一合同已签署二款项已到账三交付日期已确定",
            # Long text (>64 tokens): auto-sliding-window test
            "人工智能技术正在改变我们的生活方式"
            "明天下午三点在公司会议室开会请准时参加"
            "他是一名优秀的工程师工作认真负责"
            "北京是中国的首都拥有悠久的历史文化"
            "随着科技的发展人们的生活越来越便利",
        ]

    for text in texts:
        result = pipeline(text)
        print(f"\nInput:  {text}")
        print(f"Output: {result}")


if __name__ == "__main__":
    main()
