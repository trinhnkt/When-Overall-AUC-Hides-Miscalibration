"""B2: one definition of the primary protocol, fold labels, integer counts. --check runs the blind-file checker."""
from __future__ import annotations

import re
import sys
import zipfile

from lxml import etree

from msedit import PATHS, W, apply, count, fill_table, sub, table_rows, text_of

PROTOCOL_DEF = (
    "Test sequences are scored in non-overlapping windows of at most 200. We call this setting the primary protocol "
    "(internal ID P0-BV200-15EW): the validation-AUC checkpoint, non-overlapping test windows of at most 200 responses, and "
    "M = 15 equal-width bins (Section III.E)."
)
SUBS = [
    ("The study addresses three research questions.", "under protocol P0-BV200-15EW,", "under the primary protocol (Section III.C),"),
    ("Table 2 lists the runs", "Test sequences are scored in non-overlapping windows of at most 200.", PROTOCOL_DEF),
    ("Table 2. Configuration", "under P0-BV200-15EW", "under the primary protocol"),
    ("Table 4. Overall AUC", "N is that mean count.", "N is the mean count, rounded."),
    ("Table 4. Overall AUC", " Protocol P0-BV200-15EW.", " All rows use the primary protocol."),
    ("On ASSISTments 2012, under protocol", "under protocol P0-BV200-15EW,", "under the primary protocol,"),
    ("On ASSISTments 2012, under", "ΔECE* is positive only on P1.", "ΔECE* is positive only on fold 1."),
    ("On ASSISTments 2012, under", "positive on P1 and P4 and negative on P0 and P2.",
     "positive on fold 1 and fold 4 and negative on fold 0 and folds 2–3."),
    ("Junyi Academy has no sparse group. Its DKT", "mean N medium = 3676.75", "mean count N medium = 3,677"),
    ("Table A3. Threshold analysis", "under protocol P0-BV200-15EW", "under the primary protocol"),
    ("Table A4. ΔFAR", "under protocol P0-BV200-15EW", "under the primary protocol"),
    ("Table A4. ΔFAR", "N, Nadv, and Ninc are sparse-group means.", "N, Nadv, and Ninc are sparse-group mean counts, rounded."),
    ("Table 5. Calibration by frequency group", "N is the mean count)", "N is the mean count, rounded)"),
]


def num(s: str) -> float:
    return float(s.replace(",", ""))


def edit(body, path) -> None:
    for prefix, old, new in SUBS:
        sub(body, prefix, old, new)
    t4 = table_rows(body, "Table 4. Overall AUC")
    rows = [r[:4] + [count(num(r[4])) if r[4][0].isdigit() else r[4]] for r in t4[1:]]
    fill_table(body, "Table 4. Overall AUC", None, t4[0][:5], rows, weights=[1.4, 1.6, 1.3, 1.3, 1.0])
    t5 = table_rows(body, "Table 5. Calibration")
    fill_table(body, "Table 5. Calibration", None, None, [r[:3] + [count(num(r[3]))] + r[4:] for r in t5[1:]])
    a2 = table_rows(body, "Table A2.")
    fill_table(body, "Table A2.", None, None, [r[:6] + [count(num(r[6]))] + r[7:] for r in a2[1:]])
    a4 = table_rows(body, "Table A4.")
    fill_table(body, "Table A4.", None, None, [r[:5] + [count(num(x)) for x in r[5:8]] for r in a4[1:]])


def check() -> int:
    bad = 0
    for path in PATHS:
        with zipfile.ZipFile(path) as z:
            body = etree.fromstring(z.read("word/document.xml")).find(W + "body")
        text = "\n".join(text_of(p) for p in body.iter(W + "p"))
        n_id = text.count("P0-BV200")
        labels = re.findall(r"(?<![\w-])P[0-5](?![\w-])", text)
        dot0 = re.findall(r"\b[1-9][\d,]*\.0000\b", text)
        halfcounts = re.findall(r"\b\d{3,}\.(?:5|25|75|3)\b(?!\d)", text)
        for label, ok, detail in (
            ("P0-BV200 occurrences <= 1", n_id <= 1, n_id),
            ("no standalone P0-P5 partition labels", not labels, labels),
            ("no count ending .0000", not dot0, dot0),
            ("no fractional mean counts", not halfcounts, halfcounts),
        ):
            print(f"{'PASS' if ok else 'FAIL'} {path.name[-30:]}: {label} ({detail})")
            bad += not ok
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        raise SystemExit(1 if check() else 0)
    apply(edit, "--write" in sys.argv)
