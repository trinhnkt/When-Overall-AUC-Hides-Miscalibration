"""Reference [26] (Junyi Kaggle dataset): follow the citation printed on the Kaggle dataset page (read 2026-10-30):
authors P. J. Chen, M. E. Hsieh, T. Y. Tsai; year 2020; title "Junyi Academy Online Learning Activity Dataset: A large-scale
public online learning activity dataset from elementary to senior high school students"; licence CC BY-NC-SA 4.0.
Authors, year and URL were already right; the title is completed and the access date set to the day it was read.
Red marking for review. Dry run unless --write.
"""
from __future__ import annotations

import sys

from msedit import apply, sub

PREFIX = "P. J. Chen, M. E. Hsieh"
SUBS = [
    ("“Junyi Academy Online Learning Activity Dataset,” Kaggle, 2020.",
     "“Junyi Academy Online Learning Activity Dataset: A large-scale public online learning activity dataset from "
     "elementary to senior high school students,” Kaggle, 2020."),
    ("Accessed: Sep. 20, 2026.", "Accessed: Oct. 30, 2026."),
]


def edit(body, path) -> None:
    for old, new in SUBS:
        sub(body, PREFIX, old, new, allow_flatten=True)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
