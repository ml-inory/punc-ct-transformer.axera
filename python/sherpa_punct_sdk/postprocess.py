# Sherpa Onnx Punctuation Postprocessor
#
# Converts model logits output to punctuation-annotated text.
# 6 classes: <unk>(0), _(1), ，(2), 。(3), ？(4), 、(5)

import numpy as np
from typing import List


PUNCT_CLASSES = [0, 1, 2, 3, 4, 5]
PUNCT_MARKS = ["", "", "，", "。", "？", "、"]
IGNORE_ID = 1  # underscore class = no punctuation


def decode_punctuation(
    logits: np.ndarray,
    token_ids: List[int],
    id2token: List[str],
    original_length: int,
    dot_id: int = 3,
    comma_id: int = 2,
    quest_id: int = 4,
    pause_id: int = 5,
) -> str:
    """Decode the model output to punctuation-annotated text.

    Args:
        logits: (1, 64, 6) float32 array from model
        token_ids: list of original (unpadded) token IDs
        id2token: vocab list mapping ID → token string
        original_length: length before padding (<= 64)
        dot_id, comma_id, quest_id, pause_id: class IDs for punctuation

    Returns:
        Annotated text string with punctuation inserted
    """
    # Take only valid portion
    if original_length > logits.shape[1]:
        original_length = logits.shape[1]
    if original_length > len(token_ids):
        original_length = len(token_ids)

    logits = logits[0, :original_length, :]
    ids = token_ids[:original_length]

    # Argmax over classes
    out = np.argmax(logits, axis=-1).tolist()

    # Segment with sentence-boundary heuristics
    # (simplified from original sherpa code)
    max_len = 200
    segment_size = 20
    num_segments = (len(ids) + segment_size - 1) // segment_size

    punctuations = []
    last = -1
    for i in range(num_segments):
        this_start = i * segment_size
        this_end = min(this_start + segment_size, len(ids))
        if last != -1:
            this_start = last

        seg_out = out[this_start:this_end]

        dot_index = -1
        comma_index = -1
        for k in range(len(seg_out) - 1, 1, -1):
            if seg_out[k] in (dot_id, quest_id):
                dot_index = k
                break
            if comma_index == -1 and seg_out[k] == comma_id:
                comma_index = k

        if dot_index == -1 and len(ids) >= max_len and comma_index != -1:
            dot_index = comma_index
            seg_out[dot_index] = dot_id

        if dot_index == -1:
            if last == -1:
                last = this_start
            if i == num_segments - 1:
                dot_index = len(seg_out) - 1
        else:
            last = this_start + dot_index + 1

        if dot_index != -1:
            punctuations += seg_out[: dot_index + 1]

    # Build output
    ans = []
    for j, p in enumerate(punctuations):
        t = id2token[ids[j]] if ids[j] < len(id2token) else "<unk>"
        # Insert space before ASCII tokens
        if ans and len(ans[-1][0].encode()) == 1 and len(t[0].encode()) == 1:
            ans.append(" ")
        ans.append(t)
        if p != IGNORE_ID and p < len(PUNCT_MARKS):
            ans.append(PUNCT_MARKS[p])

    return "".join(ans)
