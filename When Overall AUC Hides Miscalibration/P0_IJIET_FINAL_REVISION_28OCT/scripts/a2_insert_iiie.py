"""Already applied to Section III.E.

Do not run this module. A second run would duplicate the inserted paragraphs.
The live manuscript numbers the retained dense ECE as (8), G as (9), and FAR as (10).
"""
from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ROOT = Path(__file__).resolve().parents[2]

PATHS = [
    ROOT
    / "manuscript-pack"
    / "manuscript"
    / "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.docx",
    ROOT
    / "manuscript-pack"
    / "manuscript"
    / "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components_blind.docx",
    ROOT
    / "P0_IJIET_FINAL_CORRECTION_2026"
    / "artifact_final"
    / "07_submission"
    / "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components_blind.docx",
]

BODY = [
    (
        "The size-matched gap is computed on the rows with a nonempty test history. "
        "On one partition, N_sparse is the number of sparse rows and ECE_sparse is their ECE under (2). "
        "The dense reference uses the learners who have at least one dense row in that same row set, "
        "in order of first appearance in the scored predictions. "
        "Draw r permutes those learners without replacement and appends their dense rows until the concatenated length is at least N_sparse. "
        "A draw with fewer than N_sparse dense rows is invalid and is omitted from the median. "
        "Otherwise a second sample, also without replacement, retains exactly N_sparse rows, so a learner whose rows cross N_sparse need not contribute every row. "
        "The ECE of the retained rows, again under (2), is the dense value of draw r. "
        "The point estimate uses R = 2000 draws. In the published fold-0 run, all 2000 draws were valid. "
        "The first of the 15 equal-width bins in (2) contains predicted probabilities on [0, 1/15]; each later bin contains probabilities on (left, right]."
    ),
    (
        "Matching equalizes sample size only. It does not equalize ECE bin occupancy, "
        "the predicted-probability distribution, or the dependence structure."
    ),
    (
        "The 95% interval is the fold-0 learner-cluster bootstrap. "
        "It describes fold 0. "
        "The stream is a NumPy Generator seeded with 20261021. "
        "Fold 0 is the first partition, so that seed is the start of the stream. "
        "The stream then has three stages. "
        "Stage 1 is the R = 2000 draws that define G. "
        "Stage 2 draws 2000 subsets of exactly N_sparse dense rows without regard to learner identity. "
        "Stage 2 is excluded from G and from the interval; a replay of the interval still has to execute it, because it advances the same stream. "
        "Stage 3 resamples, with replacement, every test learner who has a nonempty history, B = 2000 times, drawing as many learners as that list contains. "
        "A learner drawn more than once is kept as a separate cluster, and the sparse and dense rows are rebuilt from those copies. "
        "A replicate with no sparse rows is invalid: it is counted, it is excluded from the percentiles, and its gap is not imputed. "
        "A replicate whose dense rows are all empty is excluded in the same way. "
        "The published fold-0 run had 0 empty sparse replicates and 0 other invalid replicates, so the percentiles use all 2000 values. "
        "For each valid replicate the parent stream draws one integer on the half-open interval [0, 2^31 - 1), and that integer seeds an inner generator. "
        "The inner generator repeats the size-matched draw 200 times, and the replicate stores its own G. "
        "The interval is the 2.5th and 97.5th percentiles of those values, using NumPy’s linear percentile."
    ),
]


def text_of(paragraph) -> str:
    return "".join(node.text or "" for node in paragraph.iter(W + "t"))


def body_paragraph(template, content: str):
    paragraph = etree.Element(W + "p")
    source = template.find(W + "pPr")
    if source is not None:
        paragraph.append(etree.fromstring(etree.tostring(source)))
    run = etree.SubElement(paragraph, W + "r")
    node = etree.SubElement(run, W + "t")
    if content.startswith(" ") or content.endswith(" "):
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    node.text = content
    return paragraph


def equation_paragraph(template):
    paragraph = etree.Element(W + "p")
    source = template.find(W + "pPr")
    if source is not None:
        paragraph.append(etree.fromstring(etree.tostring(source)))

    def add(text, subscript=False):
        run = etree.SubElement(paragraph, W + "r")
        if subscript:
            props = etree.SubElement(run, W + "rPr")
            align = etree.SubElement(props, W + "vertAlign")
            align.set(W + "val", "subscript")
        node = etree.SubElement(run, W + "t")
        if text.startswith(" ") or text.endswith(" "):
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        node.text = text

    add("\t")
    add("G = ECE")
    add("sparse", subscript=True)
    add(" − median")
    add("r", subscript=True)
    add("(ECE")
    add("dense,r", subscript=True)
    add("@N")
    add("sparse", subscript=True)
    add(")")
    add("\t")
    add("(8)")
    return paragraph


def edit(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        original = archive.read("word/document.xml")
        others = [(info, archive.read(info.filename)) for info in archive.infolist() if info.filename != "word/document.xml"]
    root = etree.fromstring(original)
    body = root.find(W + "body")
    heading = None
    equation_style = None
    body_style = None
    far = None
    for child in list(body):
        if child.tag != W + "p":
            continue
        content = text_of(child).strip()
        if content.startswith("Within a group") and body_style is None:
            body_style = child
        if content.endswith("(5)") and content.startswith("ΔECE"):
            equation_style = child
        if content.startswith("F. Leakage checks") and heading is None:
            heading = child
        if content.startswith("FAR ="):
            far = child
    if heading is None or equation_style is None or body_style is None or far is None:
        raise SystemExit(f"anchors missing in {path.name}")
    far_text = text_of(far)
    if not far_text.endswith("(8)"):
        raise SystemExit(f"FAR equation is not labeled (8) in {path.name}: {far_text[-20:]}")
    blocks = [
        body_paragraph(body_style, BODY[0]),
        equation_paragraph(equation_style),
        body_paragraph(body_style, BODY[1]),
        body_paragraph(body_style, BODY[2]),
    ]
    for block in blocks:
        heading.addprevious(block)
    changed = False
    for node in far.iter(W + "t"):
        if node.text and "(8)" in node.text:
            node.text = node.text.replace("(8)", "(9)")
            changed = True
    if not changed or not text_of(far).endswith("(9)"):
        raise SystemExit(f"FAR label was not renumbered in {path.name}")
    xml = etree.tostring(root, xml_declaration=False, encoding="UTF-8")
    if b"w:document" not in xml[:1500]:
        raise SystemExit(f"document prefix lost in {path.name}")
    if b"G = ECE" not in xml or b"(9)" not in xml:
        raise SystemExit(f"inserted text missing in {path.name}")
    temporary = path.with_suffix(".docx.a2tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for info, payload in others:
            archive.writestr(info, payload)
        archive.writestr("word/document.xml", xml)
    os.replace(temporary, path)
    print(f"UPDATED {path.name}")


def main() -> None:
    raise SystemExit(
        "Already applied. Running this script again would duplicate Section III.E. "
        "The live text numbers the dense-draw ECE as (8), G as (9), and FAR as (10)."
    )


if __name__ == "__main__":
    main()
