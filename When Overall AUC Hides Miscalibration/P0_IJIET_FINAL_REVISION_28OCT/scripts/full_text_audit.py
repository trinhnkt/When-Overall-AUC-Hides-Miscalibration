"""Line-by-line audit: every number in the manuscript prose and tables against its evidence.

1. Table cells: the printed value of each recomputed check (artifact reproduce_tables.py output CSV) must occur in the
   matching manuscript table (Tables 4, 5, A1, A2, A3, A4, A5).
2. Prose: every number in a body paragraph is classed as
   TABLE (also printed in a table), CONTEXT (in results/TABLE6_7_CONTEXT.json or the other results CSV/JSON files),
   CONST (protocol constant / identifier) or OPEN (needs a manual check, listed with its sentence).

    py -3 full_text_audit.py <recomputed_checks.csv> [manuscript.docx]
"""
from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

from msedit import W

R28 = Path(__file__).resolve().parents[1]
NUM = re.compile(r"[−\-+]?\d[\d,]*(?:\.\d+)?")
CONST = {"2012", "2013", "2015", "2016", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "200", "15",
         "2000", "20261021", "50", "8", "64", "128", "24", "256", "0.001", "0.7", "0.5", "100", "500", "1000", "20", "95",
         "2.5", "97.5", "0", "1", "2", "3", "4", "5", "6", "7", "9", "10", "30", "0.1", "1,000", "2,000", "31"}


def norm(token: str) -> str:
    return token.replace("−", "-").replace("+", "").replace(",", "").rstrip(".")


def text(el) -> str:
    return "".join(t.text or "" for t in el.iter(W + "t"))


def load(path: Path):
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    paras, tables = [], []
    cap = ""
    for el in body:
        tag = etree.QName(el).localname
        if tag == "p":
            s = text(el).strip()
            if s:
                paras.append(s)
                if re.match(r"Table (A?\d)\.", s):
                    cap = re.match(r"Table (A?\d)\.", s).group(1)
        elif tag == "tbl":
            rows = [[text(tc).strip() for tc in tr.findall(W + "tc")] for tr in el.iter(W + "tr")]
            tables.append((cap, rows))
    return paras, tables


def main() -> int:
    checks = Path(sys.argv[1])
    doc = Path(sys.argv[2]) if len(sys.argv) > 2 else R28 / "a6_clean" / "manuscript-pack_manuscript_blind_A6_clean.docx"
    paras, tables = load(doc)
    by_cap = {}
    for cap, rows in tables:
        by_cap.setdefault(cap, set()).update(norm(n) for r in rows for c in r for n in NUM.findall(c))
    all_table = set().union(*by_cap.values())
    print("tables found:", {k: len(v) for k, v in by_cap.items()})

    bad = 0
    n_checked = 0
    with checks.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            label, printed = row["label"], row["manuscript"]
            if row["status"] != "PASS":
                print("RECOMPUTE FAIL", label)
                bad += 1
                continue
            m = re.match(r"Table (A?\d)", label)
            caps = [m.group(1)] if m else []
            if label.startswith("Table 4/5"):
                caps = ["4", "5", "A5"]
            if label.startswith("Table A5"):
                caps = ["A5"]
            pool = set().union(*(by_cap.get(c, set()) for c in caps)) if caps else all_table
            try:
                float(printed)
            except ValueError:
                continue
            if label.endswith(("empty sparse replicates", "invalid draws")) or re.search(r" (focal |dense )?N$", label):
                continue
            key = norm(printed)
            alt = {key, key.lstrip("0") if key.startswith("0.") else key, str(float(key)) if key else key}
            n_checked += 1
            if not (alt & pool):
                print("NOT IN TABLE", label, printed, caps)
                bad += 1
    print(f"table-cell checks: {n_checked} printed values looked up, {bad} problems")

    ctx = set()
    ctx_path = R28 / "results" / "TABLE6_7_CONTEXT.json"
    blob = ctx_path.read_text(encoding="utf-8") if ctx_path.exists() else ""
    ctx |= {norm(n) for n in NUM.findall(blob)}
    for name in ("B5_STRATIFIED_METRICS.csv", "B3_TABLE_A2_EFFECTS.csv", "C1_PARTITION_INTERVALS.csv", "A3_far_fold0.csv",
                 "A3_far_four_partition.csv", "base_rate_constants.csv"):
        p = R28 / "results" / name
        if p.exists():
            ctx |= {norm(n) for n in NUM.findall(p.read_text(encoding="utf-8"))}

    start = next(i for i, p in enumerate(paras) if p.startswith("Abstract"))
    end = next(i for i, p in enumerate(paras) if p == "References")
    open_items = []
    counts = {"TABLE": 0, "CONTEXT": 0, "CONST": 0, "OPEN": 0}
    for p in paras[start:end]:
        if p.startswith("Table "):
            body = p
        else:
            body = p
        for sent in re.split(r"(?<=[.;])\s+(?=[A-Z(])", body):
            for tok in NUM.findall(sent):
                k = norm(tok)
                if not k or k in {"-", "+"}:
                    continue
                if re.fullmatch(r"\d{1,2}", k) and "." not in k:
                    counts["CONST"] += 1
                    continue
                if k in all_table:
                    counts["TABLE"] += 1
                elif k in ctx:
                    counts["CONTEXT"] += 1
                elif tok in CONST or k in {norm(c) for c in CONST}:
                    counts["CONST"] += 1
                else:
                    counts["OPEN"] += 1
                    open_items.append((tok, sent.strip()))
    print("prose numbers:", counts)
    seen = set()
    for tok, sent in open_items:
        key = (tok, sent[:60])
        if key in seen:
            continue
        seen.add(key)
        print(f"OPEN {tok} :: {sent[:230]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
