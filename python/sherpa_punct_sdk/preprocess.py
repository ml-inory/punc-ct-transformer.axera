# Sherpa Onnx Punctuation Preprocessor (CharTokenizer)
#
# Model: sherpa-onnx-punct-ct-transformer
# Tokenizer: character-level for Chinese, word-level for English
# Vocab: tokens.json (272727 entries)
# Padding: to 64 tokens

import json
import os
from typing import List, Tuple
import numpy as np


class CharTokenizer:
    """Character/word tokenizer for the sherpa punct CT Transformer model."""

    def __init__(self, tokens_path: str, unk_symbol: str = "<unk>"):
        if not os.path.exists(tokens_path):
            raise FileNotFoundError(f"tokens.json not found: {tokens_path}")
        with open(tokens_path, "r", encoding="utf-8") as f:
            id2token = json.load(f)
        self.id2token = id2token
        self.token2id = {tok: idx for idx, tok in enumerate(id2token)}
        self.unk_id = self.token2id.get(unk_symbol, 0)

    def tokenize(self, text: str) -> List[int]:
        """Split text into tokens and return token IDs.

        Chinese characters are segmented individually.
        English words are kept as whole tokens.
        """
        # Split on whitespace
        word_list = text.split()

        words = []
        for w in word_list:
            s = ""
            for c in w:
                if len(c.encode()) > 1:
                    # Multi-byte character (Chinese, Japanese, etc.)
                    if s == "":
                        s = c
                    elif len(s[-1].encode()) > 1:
                        s += c
                    else:
                        words.append(s)
                        s = c
                else:
                    # ASCII character
                    if s == "":
                        s = c
                    elif len(s[-1].encode()) > 1:
                        words.append(s)
                        s = c
                    else:
                        s += c
            if s:
                words.append(s)

        ids = []
        for w in words:
            if len(w[0].encode()) > 1:
                # Chinese phrase: tokenize each character
                for c in w:
                    ids.append(self.token2id.get(c, self.unk_id))
            else:
                ids.append(self.token2id.get(w, self.unk_id))
        return ids

    def encode(
        self, text: str, pad_length: int = 64
    ) -> Tuple[np.ndarray, int]:
        """Tokenize and pad to fixed length.

        Returns:
            input_array: (1, pad_length) int32 numpy array
            original_length: actual token count before padding
        """
        ids = self.tokenize(text)
        original_len = len(ids)

        # Truncate or pad to pad_length
        if len(ids) > pad_length:
            ids = ids[:pad_length]
            original_len = pad_length

        padded = np.zeros((1, pad_length), dtype=np.int32)
        padded[0, : len(ids)] = ids

        return padded, min(original_len, pad_length)
