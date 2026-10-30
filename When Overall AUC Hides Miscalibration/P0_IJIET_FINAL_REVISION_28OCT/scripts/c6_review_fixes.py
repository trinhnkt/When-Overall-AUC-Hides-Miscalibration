"""Wording and notation fixes from the 30/10 full-manuscript review (audit/MANUSCRIPT_REVIEW_30OCT.md), items 1, 2, 3, 5, 6.
No number is changed. Changed runs are red. Dry run unless --write.
 1. III.F and Table 3 caption: replace the undefined "three local models".
 2. III.E: literal N_sparse / ECE_sparse -> subscripts like the rest of the paper.
 3. Table A2: drop the leftover "reason missing" column.
 5. IV.A: replace the unclear last sentence.
 6. Table 1 caption: say why test events differ from N in Tables 4-5.
"""
from __future__ import annotations

import copy
import re
import sys

from lxml import etree

import msedit
from msedit import W, XML_SPACE, apply, find_para, fill_table, mark_red, sub, table_rows, text_of

SUBS = [
    ("Table 3 reports the outcomes",
     "The archived audit covers the three local models; simpleKT reads",
     "The archived audit covers the partition files and the training and scoring code of the locally implemented "
     "models (DKT and T-KT masked); simpleKT reads"),
    ("Table 3. Leakage checks",
     "(L1–L7 numbered as in the archived audit records of the local models)",
     "(L1–L7 numbered as in the archived audit records)"),
    ("Table 4 reports overall AUC",
     "These figures are not benchmark scores from a different split.",
     "These are discrimination scores under the primary protocol; they are not comparable with published "
     "benchmark scores that use other splits or window rules."),
    ("Table 1. Cohort statistics",
     "For XES3G5M, interactions and test events are KC-level rows (Section III.A).",
     "For XES3G5M, interactions and test events are KC-level rows (Section III.A). Test events are all test rows "
     "of fold 0; Tables 4, 5, and A1–A5 use only the rows with a nonempty test history."),
]

PAT = re.compile(r"(ECE|N)_(sparse|dense)")


def subscript_underscores(body) -> int:
    n = 0
    for run in list(body.iter(W + "r")):
        ts = run.findall(W + "t")
        if len(ts) != 1 or not ts[0].text or not PAT.search(ts[0].text):
            continue
        text = ts[0].text
        parent = run.getparent()
        idx = parent.index(run)
        pieces = []
        pos = 0
        for m in PAT.finditer(text):
            if m.start() > pos:
                pieces.append((text[pos:m.start()], False))
            pieces.append((m.group(1), False))
            pieces.append((m.group(2), True))
            pos = m.end()
            n += 1
        if pos < len(text):
            pieces.append((text[pos:], False))
        parent.remove(run)
        for k, (value, sub_) in enumerate(pieces):
            new = copy.deepcopy(run)
            t = new.find(W + "t")
            t.text = value
            t.set(XML_SPACE, "preserve")
            if sub_:
                pr = new.find(W + "rPr")
                if pr is None:
                    pr = etree.Element(W + "rPr")
                    new.insert(0, pr)
                va = pr.find(W + "vertAlign")
                if va is None:
                    va = etree.SubElement(pr, W + "vertAlign")
                va.set(W + "val", "subscript")
                mark_red(new)
            parent.insert(idx + k, new)
    return n


def drop_last_column(body) -> None:
    rows = table_rows(body, "Table A2.")
    if not rows[0][-1].strip().lower().startswith("reason missing"):
        raise SystemExit(f"last column of Table A2 is {rows[0][-1]!r}")
    if any(r[-1].strip() != "none" for r in rows[1:]):
        raise SystemExit("reason-missing column holds something other than 'none'")
    header = [c for c in rows[0][:-1]]
    data = [r[:-1] for r in rows[1:]]
    fill_table(body, "Table A2.", None, header, data)


def edit(body, path) -> None:
    for prefix, old, new in SUBS:
        sub(body, prefix, old, new, allow_flatten=True)
    print(f"  subscripted {subscript_underscores(body)} underscore tokens in {path.name[-30:]}")
    drop_last_column(body)
    left = sorted({m.group(0) for m in re.finditer(r"\b\w+_\w+\b", " ".join(text_of(p) for p in body.iter(W + 'p')))})
    print("  remaining underscore tokens:", left)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
