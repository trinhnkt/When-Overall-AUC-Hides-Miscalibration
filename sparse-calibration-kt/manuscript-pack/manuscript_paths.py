"""Canonical paper filenames = manuscript title."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER_TITLE = (
    "Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing"
)
NAMED_STEM = PAPER_TITLE
BLIND_STEM = f"{PAPER_TITLE}_blind"

FULL_DOCX = HERE / "manuscript" / f"{NAMED_STEM}.docx"
FULL_DOC = HERE / "manuscript" / f"{NAMED_STEM}.doc"
BLIND_DOCX = HERE / "manuscript" / f"{BLIND_STEM}.docx"
BLIND_DOC = HERE / "manuscript" / f"{BLIND_STEM}.doc"
FULL_PDF = HERE / "output" / f"{NAMED_STEM}.pdf"
BLIND_PDF = HERE / "output" / f"{BLIND_STEM}.pdf"
