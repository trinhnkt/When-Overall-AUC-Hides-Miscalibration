"""Fixes from the 30/10 review of the clean blind copy (abstract is handled by b1_abstract.py):
 1. III.C: cite the dated analysis plan behind "pre-specified" (README of artifact v4, commit 46e0208, 2026-10-21 16:02:55).
 2. III.C: define n in "padding id 2n" (code: pad_index(n_kcs) = 2 * n_kcs).
 3. Data and Code Availability: explain "fold 5" (an extra run the paper does not report) and say that the per-partition
    L1-L7 audit records are not shipped (only leakage_checklist_runner.py is).
Changed runs are red. Dry run unless --write.
"""
from __future__ import annotations

import sys

from msedit import apply, sub

SUBS = [
    ("The primary checkpoint is the validation-AUC checkpoint",
     "That grid was pre-specified for ASSISTments DKT.",
     "That grid was pre-specified for ASSISTments DKT in an analysis plan committed on 21 October 2026 "
     "(commit 46e0208, before the first supplementary run) and included in artifact v4."),
    ("Table 2 lists the runs", "padding id 2n.", "padding id 2n (n is the number of KCs)."),
    ("Artifact v4 contains", "the model weights, fold 5, the slide-window exports,",
     "the model weights, an additional run (fold 5) that this paper does not report, the slide-window exports,"),
    ("Artifact v4 contains", "(Tables 6 and 7 are included as recorded outputs),",
     "(Tables 6 and 7 are included as recorded outputs), the per-partition records of checks L1–L7 behind Table 3 "
     "(only the runner code is included),"),
]


def edit(body, path) -> None:
    for prefix, old, new in SUBS:
        sub(body, prefix, old, new, allow_flatten=True)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
