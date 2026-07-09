#!/usr/bin/env python3
"""Sherpa Punctuation Prediction on AX650 NPU.

Usage:
    python example.py                                    # run demo texts
    python example.py "今天天气真好我们出去散步吧"         # custom text
    python example.py -m /path/to/model.axmodel          # specify model
"""

import argparse
import os
import sys

from sherpa_punct_sdk import PunctuationPipeline


DEMO_TEXTS = [
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


def find_file(*candidates):
    """Return the first existing file from candidates."""
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def resolve_paths(args):
    """Resolve model and tokens paths with smart defaults."""
    base = os.path.dirname(os.path.abspath(__file__))
    project = os.path.dirname(base)

    model = args.model or find_file(
        os.path.join(project, "models", "model.axmodel"),
        os.path.join(project, "model_convert", "compile", "model.axmodel"),
    )
    tokens = args.tokens or find_file(
        os.path.join(project, "models", "tokens.json"),
        os.path.join(project, "model_convert", "export", "tokens.json"),
    )

    if not model:
        print("ERROR: model.axmodel not found. Use -m to specify path.")
        sys.exit(1)
    if not tokens:
        print("ERROR: tokens.json not found. Use -t to specify path.")
        sys.exit(1)

    return model, tokens


def main():
    parser = argparse.ArgumentParser(
        description="Sherpa Punctuation Prediction on AX650 NPU",
    )
    parser.add_argument(
        "text", nargs="*",
        help="Text to punctuate. If omitted, runs demo texts.",
    )
    parser.add_argument(
        "-m", "--model",
        help="Path to model.axmodel (default: auto-detect)",
    )
    parser.add_argument(
        "-t", "--tokens",
        help="Path to tokens.json (default: auto-detect)",
    )
    args = parser.parse_args()

    model_path, tokens_path = resolve_paths(args)

    print(f"Model:  {model_path}")
    print(f"Tokens: {tokens_path}")

    pipeline = PunctuationPipeline(model_path, tokens_path)

    texts = args.text if args.text else DEMO_TEXTS

    for text in texts:
        result = pipeline(text)
        print(f"\nInput:  {text}")
        print(f"Output: {result}")


if __name__ == "__main__":
    main()
