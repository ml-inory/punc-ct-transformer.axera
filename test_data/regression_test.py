#!/usr/bin/env python3
"""Regression test: compare SDK output against ONNX ground truth.

Usage (on AX650 board):
    cd python && source .venv/bin/activate
    python ../test_data/regression_test.py

Compares PunctuationPipeline output against ONNX-generated GT text.
"""

import os, sys, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
from sherpa_punct_sdk import PunctuationPipeline


def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project = os.path.dirname(test_dir)

    # Resolve model
    model_path = os.path.join(project, 'models', 'model.axmodel')
    if not os.path.exists(model_path):
        model_path = os.path.join(project, 'model_convert', 'compile', 'model.axmodel')
    tokens_path = os.path.join(project, 'models', 'tokens.json')

    # Load test cases
    cases_path = os.path.join(test_dir, 'cases.json')
    if not os.path.exists(cases_path):
        print("ERROR: cases.json not found")
        return 1

    with open(cases_path) as f:
        cases = json.load(f)

    print(f"Model:  {model_path}")
    print(f"Tokens: {tokens_path}")
    print(f"Cases:  {len(cases)}")

    pipeline = PunctuationPipeline(model_path, tokens_path)

    passed = 0
    failed = 0

    for case in cases:
        i = case['id']
        text = case['input']
        gt_path = os.path.join(test_dir, case['gt'])

        with open(gt_path) as f:
            gt = f.read().strip()

        result = pipeline(text)

        match = (result == gt)
        status = "PASS" if match else "FAIL"

        if match:
            passed += 1
        else:
            failed += 1

        print(f"  [{i}] {status}")
        if not match:
            print(f"       Input:  {text[:50]}")
            print(f"       GT:     {gt[:50]}")
            print(f"       Output: {result[:50]}")

    print(f"\nResults: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
