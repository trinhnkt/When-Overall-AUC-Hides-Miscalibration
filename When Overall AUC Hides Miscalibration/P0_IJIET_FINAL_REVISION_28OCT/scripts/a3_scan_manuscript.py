"""List manuscript paragraphs that mention legacy or FAR terms."""
from __future__ import annotations

import sys
import zipfile
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PATH = (
    r"manuscript-pack\manuscript\When Overall AUC Hides Miscalibration - "
    r"Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.docx"
)
KEYS = (
    "unmasked",
    "t-kt",
    "table a1",
    "table a3",
    "table a4",
    "sparsification",
    "regression",
    "far",
    "archived",
    "final checkpoint",
    "full history",
    "base rate",
    "base-rate",
    "brier",
    "not evaluated",
)
root = etree.fromstring(zipfile.ZipFile(PATH).read("word/document.xml"))
texts = []
for para in root.iter(W + "p"):
    text = "".join(node.text or "" for node in para.iter(W + "t")).strip()
    if text:
        texts.append(text)
print("NPARAS", len(texts))
for index, text in enumerate(texts):
    low = text.lower()
    hit = [key for key in KEYS if key in low]
    if hit:
        print(f"[{index}] {', '.join(hit)}")
        print(text[:500])
        print("---")
