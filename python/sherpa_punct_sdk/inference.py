# Sherpa Onnx Punctuation Inference Engine
#
# Uses pyaxengine's AxEngineExecutionProvider to run the compiled AXMODEL.
# Falls back to onnxruntime CPUExecutionProvider if AX Engine is unavailable.

import os
import sys
from typing import Optional

import numpy as np


class PunctInference:
    """Inference wrapper for sherpa punct CT Transformer AXMODEL."""

    def __init__(
        self,
        model_path: str,
        tokens_path: str,
        provider: Optional[str] = None,
    ):
        """Initialize the inference engine.

        Args:
            model_path: Path to compiled model.axmodel (or .onnx for dev).
            tokens_path: Path to tokens.json vocabulary file.
            provider: Execution provider override.
                      Defaults to AxEngineExecutionProvider if available,
                      else falls back to CPUExecutionProvider.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model_path = model_path
        self.tokens_path = tokens_path
        self.provider = provider
        self._session = None

    def _create_session(self):
        """Create inference session with the configured provider."""
        session = None

        if self.provider == "AxEngineExecutionProvider" or self.provider is None:
            try:
                import axengine

                available = axengine.get_available_providers()
                if "AxEngineExecutionProvider" in available:
                    session = axengine.InferenceSession(
                        self.model_path,
                        providers=["AxEngineExecutionProvider"],
                    )
                else:
                    session = axengine.InferenceSession(
                        self.model_path,
                        providers=available,
                    )
            except (ImportError, Exception) as e:
                pass

        if session is None:
            try:
                import onnxruntime as ort
            except ImportError:
                raise RuntimeError(
                    "No inference backend available. "
                    "Install pyaxengine for NPU or onnxruntime for CPU fallback."
                )

            session = ort.InferenceSession(
                self.model_path,
                providers=["CPUExecutionProvider"],
            )

        return session

    def __call__(self, inputs: np.ndarray) -> np.ndarray:
        """Run inference.

        Args:
            inputs: (1, 64) int32 numpy array of token IDs.

        Returns:
            logits: (1, 64, 6) float32 numpy array.
        """
        if self._session is None:
            self._session = self._create_session()

        # Build input feed for all model inputs
        feed = {}
        for inp in self._session.get_inputs():
            name = inp.name
            shape = inp.shape
            if name == "inputs":
                feed[name] = inputs
            elif name == "text_lengths":
                # text_lengths: int32 scalar with sequence length
                feed[name] = np.array([inputs.shape[1]], dtype=np.int32)
            else:
                # Unknown input: pass zeros of expected shape
                dshape = [d if isinstance(d, int) else 1 for d in shape]
                feed[name] = np.zeros(dshape, dtype=np.float32)

        results = self._session.run(None, feed)
        return results[0]
