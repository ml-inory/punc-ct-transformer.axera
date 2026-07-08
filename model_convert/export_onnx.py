#!/usr/bin/env python3
"""ONNX export / staticization script for sherpa-punct-ct-transformer.

This model comes as a pre-exported ONNX from the sherpa-onnx project.
The original source is: ModelScope iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch

This script performs staticization and validation required for Pulsar2 compilation.

Inputs:
  - inputs:   int32 [1, 64]  (token IDs, padded)
  - text_lengths: converted to graph constant (value=64)

Output:
  - logits: float32 [1, 64, 6]  (6-class punctuation logits)

Usage:
  python export_onnx.py --input model.onnx --output model_static.onnx
"""

import argparse
import numpy as np
import onnx
import onnxruntime as ort
from onnx.tools import update_model_dims
from onnxsim import simplify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="model.onnx", help="Input ONNX path")
    parser.add_argument("--output", default="model_static.onnx", help="Output ONNX path")
    args = parser.parse_args()

    print(f"Loading {args.input}...")
    m = onnx.load(args.input)

    # Print original inputs
    for inp in m.graph.input:
        dims = [d.dim_value or d.dim_param for d in inp.type.tensor_type.shape.dim]
        print(f"  Input: {inp.name}, shape: {dims}")

    # Step 1: Staticize dynamic dims
    feats_length = 64
    update_model_dims.update_inputs_outputs_dims(
        m,
        {"inputs": [1, feats_length], "text_lengths": [1]},
        {"logits": [1, feats_length, 6]},
    )
    onnx.checker.check_model(m)
    print("Staticization: PASS")

    # Step 2: Convert text_lengths to constant (Pulsar2 compat)
    const = onnx.helper.make_tensor(
        name="text_lengths",
        data_type=onnx.TensorProto.INT32,
        dims=[1],
        vals=np.array([feats_length], dtype=np.int32).tobytes(),
    )
    m.graph.initializer.append(const)
    m.graph.input.pop()  # remove text_lengths from inputs
    onnx.checker.check_model(m)
    print("Constant fold: PASS")

    # Step 3: onnxsim with real inputs
    feed = {"inputs": np.random.randint(0, 272727, (1, 64), dtype=np.int32)}
    m_simp, check = simplify(m, input_data=feed, perform_optimization=True)
    print(f"onnxsim: check={check}")
    onnx.checker.check_model(m_simp)

    # Step 4: Verify ORT inference
    sess = ort.InferenceSession(
        m_simp.SerializeToString(), providers=["CPUExecutionProvider"]
    )
    test_input = np.random.randint(0, 272727, (1, 64), dtype=np.int32)
    out = sess.run(None, {"inputs": test_input})
    print(f"ORT verify: output shape={out[0].shape}")

    # Save
    onnx.save(m_simp, args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
