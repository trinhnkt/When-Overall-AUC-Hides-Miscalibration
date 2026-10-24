"""Canonical paper title and filenames.

The title uses a hyphen. The on-disk stem is the same string.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER_TITLE = (
    "When Overall AUC Hides Miscalibration - "
    "Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components"
)
NAMED_STEM = PAPER_TITLE
BLIND_STEM = f"{NAMED_STEM}_blind"

FULL_DOCX = HERE / "manuscript" / f"{NAMED_STEM}.docx"
FULL_DOC = HERE / "manuscript" / f"{NAMED_STEM}.doc"
BLIND_DOCX = HERE / "manuscript" / f"{BLIND_STEM}.docx"
BLIND_DOC = HERE / "manuscript" / f"{BLIND_STEM}.doc"
FULL_PDF = HERE / "output" / f"{NAMED_STEM}.pdf"
BLIND_PDF = HERE / "output" / f"{BLIND_STEM}.pdf"
