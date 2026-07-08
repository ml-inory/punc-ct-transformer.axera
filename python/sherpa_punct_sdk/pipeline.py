# Sherpa Onnx Punctuation Pipeline
#
# End-to-end pipeline: text → tokens → inference → punctuation-annotated text.

import json
import os
from typing import List

import numpy as np

from .preprocess import CharTokenizer
from .inference import PunctInference
from .postprocess import decode_punctuation


PUNCT_MARKS = ["", "", "，", "。", "？", "、"]
INPUT_LENGTH = 64


class PunctuationPipeline:
    """End-to-end punctuation prediction pipeline.

    Usage:
        pipeline = PunctuationPipeline("model.axmodel", "tokens.json")
        result = pipeline("你好吗how are you我很好谢谢")
        print(result)  # 你好吗，how are you，我很好谢谢。
    """

    def __init__(
        self,
        model_path: str,
        tokens_path: str,
        provider: str = "AxEngineExecutionProvider",
    ):
        self.tokenizer = CharTokenizer(tokens_path)
        if not hasattr(self.tokenizer, "id2token") or not self.tokenizer.id2token:
            raise RuntimeError("Failed to load tokens.json")
        self.id2token = self.tokenizer.id2token
        self.inference = PunctInference(
            model_path, tokens_path, provider
        )

    def __call__(self, text: str) -> str:
        """Add punctuation to input text.

        Args:
            text: Raw Chinese text (may include English words).

        Returns:
            Punctuation-annotated text.
        """
        # Tokenize and pad
        input_array, orig_len = self.tokenizer.encode(text, INPUT_LENGTH)
        token_ids = self.tokenizer.tokenize(text)

        # Inference
        logits = self.inference(input_array)

        # Decode
        result = decode_punctuation(
            logits,
            token_ids,
            self.id2token,
            min(orig_len, len(token_ids)),
        )
        return result
