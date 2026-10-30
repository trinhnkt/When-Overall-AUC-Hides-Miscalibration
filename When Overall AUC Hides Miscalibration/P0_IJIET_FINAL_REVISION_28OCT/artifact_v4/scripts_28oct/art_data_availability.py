"""Data and Code Availability: describe the 29 Oct additions to artifact v4 (Table A1 base rate, Table A5, audits, Tables 6-7)."""
import sys

from msedit import apply, sub

PREFIX = "Artifact v4 contains the code snapshot"
SUBS = [
    ("ASSISTments simpleKT, and Junyi DKT. From an extracted copy",
     "ASSISTments simpleKT, and Junyi DKT, and the per-partition base-rate constants used in Table A1. From an extracted copy"),
    ("recomputes the supported cells of Tables 4, 5, A1, A2, A3, and A4, the size-matched gaps, and the fold-0 intervals from those exports without retraining.",
     "recomputes the supported cells of Tables 4, 5, A1, A2, A3, A4, and A5, the size-matched gaps, and the fold-0 intervals from those exports without retraining; a second command recomputes the supplementary intervals of Table A5."),
    ("keeps a prefix and does not reproduce that gap.",
     "keeps a prefix and does not reproduce that gap. The XES3G5M audit files cited in Sections III.A and IV.B are included."),
    ("The artifact does not contain the raw datasets, the model weights,",
     "The artifact does not contain the raw datasets or the processed split files (Tables 6 and 7 are included as recorded outputs), the model weights,"),
]


def edit(body, path) -> None:
    for old, new in SUBS:
        sub(body, PREFIX, old, new)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
