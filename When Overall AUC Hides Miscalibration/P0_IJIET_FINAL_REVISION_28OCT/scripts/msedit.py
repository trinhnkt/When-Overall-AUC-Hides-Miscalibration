"""Shared helpers for editing the three manuscript copies through word/document.xml."""
from __future__ import annotations

import copy
import os
import sys
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
INNER = Path(__file__).resolve().parents[2]
RES = INNER / "P0_IJIET_FINAL_REVISION_28OCT" / "results"
NAME = "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components"
PATHS = [
    INNER / "manuscript-pack" / "manuscript" / f"{NAME}.docx",
    INNER / "manuscript-pack" / "manuscript" / f"{NAME}_blind.docx",
    INNER / "P0_IJIET_FINAL_CORRECTION_2026" / "artifact_final" / "07_submission" / f"{NAME}_blind.docx",
]
LOG: list[str] = []


def fmt(x: float, digits: int) -> str:
    q = Decimal(1).scaleb(-digits)
    s = str(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))
    if s.startswith("-"):
        s = "−" + s[1:]
    if s == "−0." + "0" * digits:
        s = s[1:]
    return s


def pm(mean: float, sd: float, digits: int = 4) -> str:
    return f"{fmt(mean, digits)} ± {fmt(sd, digits)}"


def count(x: float) -> str:
    v = Decimal(repr(float(x))).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return f"{v:,}"


def text_of(el) -> str:
    return "".join(t.text or "" for t in el.iter(W + "t"))


def paragraphs(body):
    return list(body.iter(W + "p"))


def find_para(body, prefix: str):
    hits = [p for p in body.iter(W + "p") if text_of(p).strip().startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"anchor {prefix!r} matched {len(hits)}")
    return hits[0]


def mark_red(run) -> None:
    pr = run.find(W + "rPr")
    if pr is None:
        pr = etree.Element(W + "rPr")
        run.insert(0, pr)
    color = pr.find(W + "color")
    if color is None:
        color = etree.SubElement(pr, W + "color")
    color.set(W + "val", "FF0000")


def set_text(para, value: str, red: bool = True) -> None:
    nodes = list(para.iter(W + "t"))
    if not nodes:
        raise SystemExit("paragraph without text")
    nodes[0].text = value
    nodes[0].set(XML_SPACE, "preserve")
    for node in nodes[1:]:
        node.text = ""
    if red:
        mark_red(nodes[0].getparent())


def sub(body, prefix: str, old: str, new: str, allow_flatten: bool = True) -> None:
    para = find_para(body, prefix)
    for node in para.iter(W + "t"):
        if node.text and old in node.text:
            node.text = node.text.replace(old, new, 1)
            node.set(XML_SPACE, "preserve")
            if new:
                mark_red(node.getparent())
            return
    full = text_of(para)
    if old not in full:
        raise SystemExit(f"text not found under {prefix!r}: {old[:70]!r}")
    if not allow_flatten:
        raise SystemExit(f"text spans runs under {prefix!r}: {old[:70]!r}")
    set_text(para, full.replace(old, new, 1))
    LOG.append(f"flattened runs in paragraph starting {prefix!r}")


def rewrite(body, prefix: str, value: str) -> None:
    set_text(find_para(body, prefix), value)


def delete(body, prefix: str) -> None:
    para = find_para(body, prefix)
    para.getparent().remove(para)


def table_after(body, caption_prefix: str):
    cap = find_para(body, caption_prefix)
    tbl = cap.getnext()
    while tbl is not None and tbl.tag != W + "tbl":
        tbl = tbl.getnext()
    if tbl is None:
        raise SystemExit(f"no table after {caption_prefix!r}")
    return cap, tbl


def _set_cell(tc, value: str) -> None:
    paras = tc.findall(W + "p")
    for extra in paras[1:]:
        tc.remove(extra)
    para = paras[0]
    nodes = list(para.iter(W + "t"))
    if nodes:
        nodes[0].text = value
        nodes[0].set(XML_SPACE, "preserve")
        for node in nodes[1:]:
            node.text = ""
    else:
        run = etree.SubElement(para, W + "r")
        t = etree.SubElement(run, W + "t")
        t.text = value
        t.set(XML_SPACE, "preserve")


def _reshape_row(tr, ncols: int, widths: list[int]) -> None:
    cells = tr.findall(W + "tc")
    while len(cells) < ncols:
        clone = copy.deepcopy(cells[-1])
        cells[-1].addnext(clone)
        cells = tr.findall(W + "tc")
    for extra in cells[ncols:]:
        tr.remove(extra)
    for tc, w in zip(tr.findall(W + "tc"), widths):
        pr = tc.find(W + "tcPr")
        if pr is not None:
            tcw = pr.find(W + "tcW")
            if tcw is not None:
                tcw.set(W + "w", str(w))
                tcw.set(W + "type", "dxa")
            span = pr.find(W + "gridSpan")
            if span is not None:
                pr.remove(span)


def fill_table(body, caption_prefix: str, caption: str | None, header: list[str] | None,
               rows: list[list[str]], weights: list[float] | None = None) -> None:
    """Replace the data rows; optionally replace the header and change the column count."""
    cap, tbl = table_after(body, caption_prefix)
    if caption is not None:
        set_text(cap, caption)
    trs = tbl.findall(W + "tr")
    head, template = trs[0], copy.deepcopy(trs[1])
    ncols = len(rows[0]) if rows else len(header)
    if header is not None and len(header) != ncols:
        raise SystemExit("header width differs from rows")
    old = len(template.findall(W + "tc"))
    if ncols != old or weights is not None:
        grid = tbl.find(W + "tblGrid")
        cols = grid.findall(W + "gridCol")
        total = sum(int(c.get(W + "w", "0")) for c in cols) or 9000
        weights = weights or [1.0] * ncols
        widths = [int(total * w / sum(weights)) for w in weights]
        for c in cols:
            grid.remove(c)
        for w in widths:
            etree.SubElement(grid, W + "gridCol").set(W + "w", str(w))
        _reshape_row(head, ncols, widths)
        _reshape_row(template, ncols, widths)
    if header is not None:
        for tc, value in zip(head.findall(W + "tc"), header):
            _set_cell(tc, value)
    for tr in trs[1:]:
        tbl.remove(tr)
    for values in rows:
        if len(values) != ncols:
            raise SystemExit(f"row width {len(values)} != {ncols} in {caption_prefix!r}")
        tr = copy.deepcopy(template)
        for tc, value in zip(tr.findall(W + "tc"), values):
            _set_cell(tc, value)
        tbl.append(tr)


def table_rows(body, caption_prefix: str) -> list[list[str]]:
    _, tbl = table_after(body, caption_prefix)
    return [[text_of(tc) for tc in tr.findall(W + "tc")] for tr in tbl.findall(W + "tr")]


def apply(edit, write: bool) -> None:
    """Run edit(body, path) on each manuscript copy; save only with write=True."""
    sys.stdout.reconfigure(encoding="utf-8")
    for path in PATHS:
        with zipfile.ZipFile(path) as archive:
            original = archive.read("word/document.xml")
            others = [(i, archive.read(i.filename)) for i in archive.infolist() if i.filename != "word/document.xml"]
        root = etree.fromstring(original)
        edit(root.find(W + "body"), path)
        if not write:
            print(f"DRY {path.name}")
            continue
        xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        if b"w:document" not in xml[:1500]:
            raise SystemExit("prefix lost")
        tmp = path.with_suffix(".docx.tmp")
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for info, payload in others:
                archive.writestr(info, payload)
            archive.writestr("word/document.xml", xml)
        os.replace(tmp, path)
        print(f"UPDATED {path.name}")
    for line in sorted(set(LOG)):
        print("NOTE", line)
    LOG.clear()


def dump(path: Path | None = None) -> list[str]:
    path = path or PATHS[1]
    with zipfile.ZipFile(path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    out = []
    for i, el in enumerate(root.find(W + "body")):
        tag = etree.QName(el).localname
        if tag == "p":
            out.append(f"[P{i}] " + text_of(el))
        elif tag == "tbl":
            out.append(f"[T{i}] TABLE")
            for tr in el.iter(W + "tr"):
                out.append("   | " + " | ".join(text_of(tc) for tc in tr.findall(W + "tc")))
    return out
