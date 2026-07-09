#!/usr/bin/env python3
"""Generate Pulsar2 calibration data for punctuation CT-Transformer.

Uses models/tokens.json to encode 10 Chinese text samples into (1, 64)
int32 token ID arrays, then packs them into export/calib_data.tar.gz.

Usage:
    cd model_convert
    python generate_calib_data.py
"""

import json
import os
import tarfile
import numpy as np


# Default calibration texts — replace or extend as needed
DEFAULT_TEXTS = [
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


def load_vocab(vocab_path):
    """Load tokens.json and return token→id mapping."""
    with open(vocab_path) as f:
        tokens = json.load(f)
    return {t: i for i, t in enumerate(tokens)}


def encode(token_to_id, text, max_len=64):
    """Encode Chinese text to int32 token IDs, padded to max_len."""
    unk_id = token_to_id.get("<unk>", 0)
    ids = [token_to_id.get(ch, unk_id) for ch in text]
    # Pad or truncate
    if len(ids) < max_len:
        ids += [0] * (max_len - len(ids))
    else:
        ids = ids[:max_len]
    return np.array([ids], dtype=np.int32)  # shape (1, max_len)


def main():
    # Resolve paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    vocab_path = os.path.join(project_root, "models", "tokens.json")
    export_dir = os.path.join(script_dir, "export")

    if not os.path.exists(vocab_path):
        print(f"ERROR: tokens.json not found at {vocab_path}")
        exit(1)

    os.makedirs(export_dir, exist_ok=True)

    print(f"Loading vocabulary: {vocab_path}")
    token_to_id = load_vocab(vocab_path)
    print(f"  Vocabulary size: {len(token_to_id)}")

    print(f"\nEncoding {len(DEFAULT_TEXTS)} calibration samples...")
    for i, text in enumerate(DEFAULT_TEXTS):
        ids = encode(token_to_id, text)
        out_path = os.path.join(export_dir, f"input_{i}.npy")
        np.save(out_path, ids)
        print(f"  [{i}] {text[:20]:<20s} → shape={ids.shape}")

    # Pack into tar.gz
    tar_path = os.path.join(export_dir, "calib_data.tar.gz")
    print(f"\nPacking to {tar_path}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for i in range(len(DEFAULT_TEXTS)):
            npy_path = os.path.join(export_dir, f"input_{i}.npy")
            tar.add(npy_path, arcname=f"input_{i}.npy")

    size_kb = os.path.getsize(tar_path) / 1024
    print(f"  Done ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
