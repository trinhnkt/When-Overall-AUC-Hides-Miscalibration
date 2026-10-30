"""B2 follow-up: the remaining paraphrases of the protocol name, and the Limitations sentence after Table A5 (C1)."""
import sys

from msedit import apply, sub

SUBS = [
    ("RQ1:", "Under the locked protocol,", "Under the primary protocol,"),
    ("Table A2 is the ASSISTments DKT grid", "cut points were not evaluated under this protocol",
     "cut points were not evaluated under the primary protocol"),
    ("Overall AUC can hide frequency-stratified calibration differences. The observed magnitude",
     "under the locked validation-AUC and window-200 protocol,", "under the primary protocol,"),
    ("Several limits qualify these findings.", "The matched interval covers fold 0 only.",
     "The primary matched interval covers fold 0 only; the Table A5 intervals for the other partitions are supplementary."),
]


def edit(body, path) -> None:
    for prefix, old, new in SUBS:
        sub(body, prefix, old, new)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
