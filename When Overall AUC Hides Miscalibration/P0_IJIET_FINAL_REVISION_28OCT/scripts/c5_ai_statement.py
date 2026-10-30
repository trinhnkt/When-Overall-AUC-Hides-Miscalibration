"""Generative AI Statement: the first author confirmed on 2026-10-30 that Claude Sonnet 5.5 was also used.
 - adds Claude Sonnet 5.5 (inside Cursor) and its role in the final revision (scripts that recompute the tables from the
   prediction files, text edits);
 - replaces 'No AI tool was used to generate or alter experimental results' with a statement that matches what happened:
   models were trained and scored by the authors' pipeline; AI-assisted scripts only recomputed tables from prediction files.
Red marking for review. Dry run unless --write.
"""
from __future__ import annotations

import sys

from msedit import apply, sub

PREFIX = "During manuscript preparation"
SUBS = [
    ("Claude (Anthropic; Claude Opus 5.5) to review the manuscript and the analysis code and to draft structural and "
     "language revisions.",
     "Claude (Anthropic; Claude Opus 5.5, and Claude Sonnet 5.5 inside Cursor) to review the manuscript and the analysis "
     "code, to draft structural and language revisions, and, in the final revision, to write and run scripts that recompute "
     "the reported tables from the prediction files."),
    ("No AI tool was used to generate or alter experimental results.",
     "No AI tool trained a model or changed a prediction file."),
    ("The authors checked every AI-assisted passage and code finding against the underlying code and results,",
     "The authors checked every AI-assisted passage, script, and recomputed value against the underlying code and "
     "prediction files,"),
]


def edit(body, path) -> None:
    for old, new in SUBS:
        sub(body, PREFIX, old, new, allow_flatten=True)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
