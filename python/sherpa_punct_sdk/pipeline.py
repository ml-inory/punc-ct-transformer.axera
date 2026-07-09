# Sherpa Onnx Punctuation Pipeline
#
# End-to-end pipeline: text → tokens → inference → punctuation-annotated text.
# Long text is automatically split into overlapping windows for the model's
# fixed 64-token input.

import numpy as np

from .preprocess import CharTokenizer
from .inference import PunctInference
from .postprocess import decode_punctuation


INPUT_LENGTH = 64
WINDOW_STRIDE = 60  # step size; overlap = INPUT_LENGTH - WINDOW_STRIDE = 4


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
        self.inference = PunctInference(model_path, provider)

    def _run_window(self, tokens: List[int]) -> np.ndarray:
        """Run inference on a single window, return logits for valid tokens."""
        n = len(tokens)
        padded = np.zeros((1, INPUT_LENGTH), dtype=np.int32)
        padded[0, :n] = tokens
        logits = self.inference(padded)  # (1, INPUT_LENGTH, 6)
        return logits[0, :n, :]  # only valid token positions

    def __call__(self, text: str) -> str:
        """Add punctuation to input text.

        Long text (>64 tokens) is processed in overlapping windows:
        window_size=64, stride=60, overlap=4.

        Args:
            text: Raw Chinese text (may include English words).

        Returns:
            Punctuation-annotated text.
        """
        token_ids = self.tokenizer.tokenize(text)
        if not token_ids:
            return text

        # Short text: single inference
        if len(token_ids) <= INPUT_LENGTH:
            logits = self._run_window(token_ids)
            return decode_punctuation(
                logits[np.newaxis], token_ids, self.id2token, len(token_ids),
            )

        # Long text: sliding window
        all_logits = []
        for start in range(0, len(token_ids), WINDOW_STRIDE):
            end = min(start + INPUT_LENGTH, len(token_ids))
            window_tokens = token_ids[start:end]

            logits = self._run_window(window_tokens)  # (end-start, 6)

            if start == 0:
                all_logits.append(logits)
            else:
                # Discard overlap: previous window already covered those tokens
                overlap = INPUT_LENGTH - WINDOW_STRIDE
                new_tokens_start = overlap
                all_logits.append(logits[new_tokens_start:])

        combined = np.concatenate(all_logits, axis=0)[:len(token_ids)]
        combined = combined[np.newaxis, :, :]  # (1, N, 6)

        return decode_punctuation(
            combined, token_ids, self.id2token, len(token_ids),
        )
