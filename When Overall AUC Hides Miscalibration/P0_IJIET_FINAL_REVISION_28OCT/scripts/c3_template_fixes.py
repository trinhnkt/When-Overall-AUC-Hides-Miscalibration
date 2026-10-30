"""C3 supplement from IJIET_template.doc:
 1. the template's copyright / CC BY line, copied verbatim, as a FigureCaption paragraph after the last reference;
 2. 'Define abbreviations and acronyms the first time they are used in the text, even after they have been defined in the
    abstract': ECE, DKT, T-KT masked, LSTM, UKT, SD, CI, UT-A1..A7, and the Brier components UNC, RES, REL.
Changed runs are red for review. Dry run unless --write.
"""
from __future__ import annotations

import sys

from lxml import etree

from msedit import W, XML_SPACE, apply, find_para, mark_red, sub, text_of

COPYRIGHT = ("Copyright © 2026 by the authors. This is an open access article distributed under the Creative Commons "
             "Attribution License which permits unrestricted use, distribution, and reproduction in any medium, provided the "
             "original work is properly cited (CC BY 4.0).")
LAST_REF = "J. Platt, “Probabilistic Outputs"

SUBS = [
    ("RQ1:", "how does ECE differ", "how does expected calibration error (ECE) differ", True),
    ("RQ3:", "how does the DKT contrast", "how does the deep knowledge tracing (DKT) contrast", True),
    ("The paper makes three contributions.", "DKT and T-KT masked under that protocol",
     "DKT and the causally masked Transformer (T-KT masked) under that protocol", True),
    ("Table 2 lists the runs", "DKT is an LSTM over", "DKT is a long short-term memory (LSTM) network over", True),
    ("KT models a learner", "such as UKT", "such as Uncertainty-Aware Knowledge Tracing (UKT)", True),
    ("Table 4 reports overall AUC", "The mean and SD use", "The mean and standard deviation (SD) use", True),
    ("Table 5. Calibration by frequency group", "the 95% CI is", "the 95% confidence interval (CI) is", True),
    ("Artifact v4 contains", "log for UT-A1 through UT-A7", "log for unit tests UT-A1 through UT-A7", True),
]

BRIER = [("with UNC = ", "with uncertainty UNC = "), ("), RES = (1/", "), resolution RES = (1/"),
         (", and REL = (1/", ", and reliability REL = (1/")]


def brier_names(body) -> None:
    p = find_para(body, "with UNC")
    for r in p.iter(W + "r"):
        ts = r.findall(W + "t")
        if len(ts) != 1:
            continue
        for old, new in BRIER:
            if ts[0].text == old:
                ts[0].text = new
                mark_red(r)


def add_copyright(body) -> None:
    for p in body.iter(W + "p"):
        if text_of(p).startswith("Copyright ©"):
            return
    last = find_para(body, LAST_REF)
    new = etree.Element(W + "p")
    ppr = etree.SubElement(new, W + "pPr")
    etree.SubElement(ppr, W + "pStyle").set(W + "val", "FigureCaption")
    etree.SubElement(ppr, W + "overflowPunct").set(W + "val", "0")
    run = etree.SubElement(new, W + "r")
    t = etree.SubElement(run, W + "t")
    t.text = COPYRIGHT
    t.set(XML_SPACE, "preserve")
    mark_red(run)
    last.addnext(new)


def edit(body, path) -> None:
    for prefix, old, new, flatten in SUBS:
        sub(body, prefix, old, new, allow_flatten=flatten)
    brier_names(body)
    add_copyright(body)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
