# Sherpa Punctuation Inference Engine
#
# Uses pyaxengine's AxEngineExecutionProvider to run the compiled AXMODEL
# on AX650 NPU.

import os
from typing import Optional

import numpy as np


class PunctInference:
    """Inference wrapper for sherpa punct CT Transformer AXMODEL."""

    def __init__(
        self,
        model_path: str,
        provider: Optional[str] = None,
    ):
        """Initialize the inference engine.

        Args:
            model_path: Path to compiled model.axmodel.
            provider: Execution provider (default: AxEngineExecutionProvider).
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model_path = model_path
        self.provider = provider or "AxEngineExecutionProvider"
        self._session = None

    def _create_session(self):
        """Create AX Engine inference session."""
        import axengine

        available = axengine.get_available_providers()
        if self.provider in available:
            return axengine.InferenceSession(
                self.model_path,
                providers=[self.provider],
            )
        return axengine.InferenceSession(
            self.model_path,
            providers=available,
        )

    def __call__(self, inputs: np.ndarray) -> np.ndarray:
        """Run inference.

        Args:
            inputs: (1, 64) int32 numpy array of token IDs.

        Returns:
            logits: (1, 64, 6) float32 numpy array.
        """
        if self._session is None:
            self._session = self._create_session()

        input_name = self._session.get_inputs()[0].name
        results = self._session.run(None, {input_name: inputs})
        return results[0]
