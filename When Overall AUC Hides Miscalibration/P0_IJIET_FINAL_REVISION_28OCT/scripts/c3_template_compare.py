"""C3: compare the living blind manuscript with IJIET_template.doc (converted to .docx by Word into %TEMP%).

Prints page setup per section, heading list, caption alignment, front matter, tail, reference style hits, and abbreviation checks.
Read-only.
"""
import os
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

from msedit import PATHS, W, dump, text_of

TEMPLATE = Path(os.environ["TEMP"]) / "ijiet_template_copy.docx"


def root_of(path):
    with zipfile.ZipFile(path) as z:
        return etree.fromstring(z.read("word/document.xml")), z.read("word/styles.xml")


def sections(root):
    out = []
    for sp in root.iter(W + "sectPr"):
        pg = sp.find(W + "pgSz")
        mar = sp.find(W + "pgMar")
        cols = sp.find(W + "cols")
        out.append({
            "size": (pg.get(W + "w"), pg.get(W + "h")) if pg is not None else None,
            "margins": {k: mar.get(W + k) for k in ("top", "bottom", "left", "right")} if mar is not None else None,
            "cols": (cols.get(W + "num"), cols.get(W + "space")) if cols is not None else None,
        })
    return out


def align_of(p):
    j = p.find(f"{W}pPr/{W}jc")
    style = p.find(f"{W}pPr/{W}pStyle")
    return (j.get(W + "val") if j is not None else None, style.get(W + "val") if style is not None else None)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t_root, _ = root_of(TEMPLATE)
    m_root, _ = root_of(PATHS[1])
    print("TEMPLATE sections", sections(t_root))
    print("MANUSCRIPT sections", sections(m_root))
    print("\nHeadings (style names) in manuscript:")
    body = m_root.find(W + "body")
    for p in body.iter(W + "p"):
        al, st = align_of(p)
        txt = text_of(p).strip()
        if st and ("eading" in st or "Title" in st.title()) and txt:
            print(f"  [{st}] {txt[:80]}")
    print("\nTemplate paragraph styles of first 40 non-empty paragraphs:")
    n = 0
    for p in t_root.find(W + "body").iter(W + "p"):
        txt = text_of(p).strip()
        if txt:
            print(f"  {align_of(p)} {txt[:70]}")
            n += 1
            if n >= 40:
                break
    print("\nManuscript captions (alignment, style):")
    for p in body.iter(W + "p"):
        txt = text_of(p).strip()
        if re.match(r"(Fig\. \d|Table (A?\d))", txt):
            print(f"  {align_of(p)} {txt[:60]}")
    lines = dump(PATHS[1])
    print("\nFront matter:")
    for l in lines[:12]:
        print("  ", l[:140])
    print("\nTail (last 12 non-empty lines before references and after):")
    tail = [l for l in lines if l.startswith("[P") and len(l) > 8]
    for l in tail[-6:]:
        print("  ", l[:160])
    print("\nSection headings present (Funding / Acknowledg / Conflict / Author Contributions):")
    for l in lines:
        if re.search(r"\] (Funding|Acknowledg|Conflict of Interest|Author Contributions|Ethical Statement|Data and Code|AI|Declaration)", l):
            print("  ", l[:120])
    print("\nReferences with a URL:")
    for l in lines:
        if "http" in l and re.match(r"\[P\d+\] [A-Z]\. ", l):
            print("  ", l[:200])
    print("\nFirst-use acronym check in text after the Abstract (template: define again after the abstract):")
    text = " ".join(l for l in lines if l.startswith("[P"))
    intro = text[text.find("I. INTRODUCTION"):]
    for short, long in (("KT", "knowledge tracing (KT)"), ("AUC", "(AUC)"), ("KC", "(KCs)"), ("ECE", "expected calibration error (ECE)"),
                        ("DKT", "deep knowledge tracing (DKT)"), ("FAR", "false-advance rate (FAR)")):
        first_use = re.search(rf"\b{short}s?\b", intro)
        defined = intro.find(long)
        print(f"  {short}: first use at {first_use.start() if first_use else None}, defined at {defined}")


if __name__ == "__main__":
    main()
