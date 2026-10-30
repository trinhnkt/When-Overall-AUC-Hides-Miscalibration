"""Print manuscript paragraphs and appendix tables by unique prefixes."""
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
PREFIXES = (
    "KT models, however",
    "For RQ1, DKT",
    "The paper makes three",
    "KT models a learner",
    "Deep models were trained",
    "Two secondary analyses",
    "FAR =",
    "that is, the proportion of advance",
    "The base-rate reference",
    "Table A2 is the ASSISTments",
    "E. KC-level",
    "A test-response-weighted",
    "Reducing the training data",
    "A threshold probe",
    "The results support a limited",
    "For platforms that use",
    "Several limits qualify",
    "Table A1.",
    "Table A3.",
    "Table A4.",
)
root = etree.fromstring(zipfile.ZipFile(PATH).read("word/document.xml"))


def ptext(el) -> str:
    return "".join(node.text or "" for node in el.iter(W + "t")).strip()


for para in root.iter(W + "p"):
    text = ptext(para)
    if any(text.startswith(prefix) for prefix in PREFIXES):
        print("\n=====")
        print(text)
        print("=====")

body = root.find(W + "body")
children = list(body)
for i, child in enumerate(children):
    if child.tag != W + "p":
        continue
    text = ptext(child)
    if text.startswith("Table A1.") or text.startswith("Table A3.") or text.startswith("Table A4."):
        print("\nTABLE AFTER", text[:80])
        for nxt in children[i + 1 : i + 5]:
            if nxt.tag == W + "tbl":
                for tr in nxt.findall(W + "tr"):
                    cells = []
                    for tc in tr.findall(W + "tc"):
                        cells.append(" | ".join(ptext(pp) for pp in tc.findall(W + "p")))
                    print(" || ".join(cells))
                break
