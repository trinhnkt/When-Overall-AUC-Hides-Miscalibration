"""B6: replace claims that the presence of a calibration difference depends on the model."""
from __future__ import annotations

import sys

from msedit import apply, sub

EDITS = [
    (
        "The results support a limited claim.",
        "Overall AUC can hide frequency-stratified calibration differences, but the size and the sign of the extra summaries depend on the protocol, the checkpoint, the sample size, the model, and the dataset.",
        "Overall AUC can hide frequency-stratified calibration differences. Both primary models showed the difference; its observed magnitude differed between them and across partitions, checkpoints, and datasets. Where a sign varied, it was the sign of the bias reference ΔECE*, not the presence of the calibration difference.",
    ),
    (
        "The datasets differ first in whether",
        "The models differ as well.",
        "The two primary models showed the same direction with different observed magnitudes.",
    ),
    (
        "Overall AUC can hide frequency-stratified calibration differences, but their size and presence",
        "Overall AUC can hide frequency-stratified calibration differences, but their size and presence depend on the evaluation protocol, the checkpoint, the sample size, the model, and the dataset.",
        "Overall AUC can hide frequency-stratified calibration differences. The observed magnitude differed between the two primary models and across checkpoints, partitions, and datasets; these are descriptive differences, not designed comparisons.",
    ),
]


def edit(body, path) -> None:
    for prefix, old, new in EDITS:
        sub(body, prefix, old, new)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
