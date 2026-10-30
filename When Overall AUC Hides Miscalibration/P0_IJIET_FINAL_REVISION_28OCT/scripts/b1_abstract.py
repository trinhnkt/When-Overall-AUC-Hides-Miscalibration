"""B1: rewrite the Abstract body. Checks word count, acronym definitions, and that every number traces to Table 5 or Table A2.

Dry run by default; --write saves the three copies; --check verifies the saved copies only.
"""
from __future__ import annotations

import csv
import re
import sys
import zipfile

from lxml import etree

from msedit import PATHS, RES, W, XML_SPACE, apply, find_para, mark_red, table_rows, text_of

PREFIX = "Abstract—"
BODY = (
    "Knowledge tracing (KT) models are usually ranked by the area under the receiver operating characteristic curve (AUC) "
    "over all responses, which can hide poor calibration on knowledge components (KCs) that learners rarely practice. "
    "We fix one protocol on ASSISTments 2012: the validation-AUC checkpoint, non-overlapping test windows of at most 200 "
    "responses, 15 equal-width bins, frequency groups, and four unique learner partitions. "
    "For deep knowledge tracing (DKT), the mean expected calibration error (ECE) was 0.0982 on sparse KCs and 0.0089 on "
    "dense KCs, a difference of 0.0893. When dense rows were subsampled to the sparse sample size, the gap was 0.0400, and "
    "its learner-cluster 95% interval on one partition was 0.0170 to 0.0821, although the conservative small-sample bias "
    "reference averaged −0.0081. A causally masked Transformer showed the same "
    "direction (difference 0.1041). In a DKT checkpoint-by-window grid, the validation-AUC checkpoint was "
    "associated with a sparse–dense difference lower by 0.0181 to 0.0774 than the final checkpoint, whereas changing the "
    "test window shifted it by −0.0131 to +0.0068. The evidence comes from one dataset with a mean of 398 sparse responses "
    "per partition; Junyi Academy had no sparse group. Reports should give frequency-stratified calibration, group "
    "sizes, and the checkpoint rule alongside overall AUC."
)
ACRONYMS = {
    "KT": "Knowledge tracing (KT)",
    "KC": "knowledge components (KCs)",
    "AUC": "receiver operating characteristic curve (AUC)",
    "ECE": "expected calibration error (ECE)",
    "DKT": "deep knowledge tracing (DKT)",
}
FORBIDDEN = ("fold-0", "fold 0", "DeltaECE", "ΔECE", "audit", "P0-BV200")
PROTOCOL_NUMBERS = {"2012", "200", "15", "95"}


def numbers(text: str) -> list[str]:
    return re.findall(r"[−+]?\d[\d,]*(?:\.\d+)?", text)


def allowed_values(body) -> set[str]:
    vals: set[str] = set()
    for row in table_rows(body, "Table 5. Calibration")[1:]:
        for cell in row:
            vals.update(n.lstrip("+") for n in numbers(cell))
    with (RES / "B3_TABLE_A2_EFFECTS.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for k, v in row.items():
                vals.update(n.lstrip("+") for n in numbers(str(v).replace("-", "−")))
                if k.startswith("ckpt_"):
                    vals.add(f"{abs(float(v)):.4f}")
    return vals


def verify(text: str, body) -> list[str]:
    errors = []
    words = len(text.split())
    print(f"words = {words}")
    if not 180 <= words <= 200:
        errors.append(f"word count {words}")
    for short, long in ACRONYMS.items():
        first_def = text.find(long)
        first_use = re.search(rf"\b{short}s?\b", text)
        ok = first_def >= 0 and first_use is not None and first_use.start() >= first_def
        print(f"{'PASS' if ok else 'FAIL'} acronym {short} defined at first use")
        if not ok:
            errors.append(f"acronym {short}")
    for bad in FORBIDDEN:
        if bad in text:
            errors.append(f"forbidden {bad}")
    vals = allowed_values(body)
    for n in numbers(text):
        key = n.lstrip("+")
        ok = key in PROTOCOL_NUMBERS or key in vals or key == "4"
        print(f"{'PASS' if ok else 'FAIL'} number {n} {'protocol setting' if key in PROTOCOL_NUMBERS else 'in Table 5 / Table A2 effects'}")
        if not ok:
            errors.append(f"number {n}")
    return errors


def edit(body, path) -> None:
    para = find_para(body, PREFIX)
    nodes = list(para.iter(W + "t"))
    head = next(i for i, n in enumerate(nodes) if n.text and PREFIX in n.text)
    lead, rest = nodes[head].text.split(PREFIX, 1)
    nodes[head].text = lead + PREFIX
    target = nodes[head + 1] if head + 1 < len(nodes) else None
    if target is None:
        run = etree.SubElement(para, W + "r")
        target = etree.SubElement(run, W + "t")
    target.text = BODY
    target.set(XML_SPACE, "preserve")
    for n in nodes[head + 2:]:
        n.text = ""
    mark_red(target.getparent())
    errors = verify(text_of(para)[len(PREFIX):], body)
    if errors:
        raise SystemExit(f"B1 FAIL {path.name}: {errors}")


def check() -> int:
    bad = 0
    for path in PATHS:
        with zipfile.ZipFile(path) as z:
            body = etree.fromstring(z.read("word/document.xml")).find(W + "body")
        text = text_of(find_para(body, PREFIX))[len(PREFIX):]
        same = text == BODY
        errs = verify(text, body)
        print(f"{'PASS' if same and not errs else 'FAIL'} {path.name[-30:]}")
        bad += (not same) or bool(errs)
    return bad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--check" in sys.argv:
        raise SystemExit(1 if check() else 0)
    apply(edit, "--write" in sys.argv)
