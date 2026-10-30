#!/usr/bin/env python3
"""A3: purge legacy and invalid results from the manuscript and insert the recomputed FAR and Brier tables.

Already applied. Running it again would fail on missing anchors.
"""
from __future__ import annotations

import copy
import os
import sys
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd
from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
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
    if s in ("−0." + "0" * digits,):
        s = s[1:]
    return s


def thousands(x: float, digits: int = 0) -> str:
    q = Decimal(1).scaleb(-digits) if digits else Decimal(1)
    v = Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP)
    return f"{v:,}"


def text_of(el) -> str:
    return "".join(t.text or "" for t in el.iter(W + "t"))


def find_para(body, prefix: str):
    hits = [p for p in body.iter(W + "p") if text_of(p).strip().startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"anchor {prefix!r} matched {len(hits)}")
    return hits[0]


def sub(body, prefix: str, old: str, new: str) -> None:
    para = find_para(body, prefix)
    for node in para.iter(W + "t"):
        if node.text and old in node.text:
            node.text = node.text.replace(old, new, 1)
            if node.text != node.text.strip():
                node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            return
    full = text_of(para)
    if old not in full:
        raise SystemExit(f"text not found under {prefix!r}: {old[:60]!r}")
    set_text(para, full.replace(old, new, 1))
    LOG.append(f"flattened runs in paragraph starting {prefix!r}")


def set_text(para, value: str) -> None:
    nodes = list(para.iter(W + "t"))
    if not nodes:
        raise SystemExit("paragraph without text")
    nodes[0].text = value
    nodes[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for node in nodes[1:]:
        node.text = ""


def rewrite(body, prefix: str, value: str) -> None:
    set_text(find_para(body, prefix), value)


def delete(body, prefix: str) -> None:
    para = find_para(body, prefix)
    para.getparent().remove(para)


def fill_table(body, caption_prefix: str, caption: str, rows: list[list[str]]) -> None:
    cap = find_para(body, caption_prefix)
    set_text(cap, caption)
    tbl = cap.getnext()
    while tbl is not None and tbl.tag != W + "tbl":
        tbl = tbl.getnext()
    if tbl is None:
        raise SystemExit(f"no table after {caption_prefix!r}")
    trs = tbl.findall(W + "tr")
    template = trs[1]
    width = len(template.findall(W + "tc"))
    for tr in trs[1:]:
        tbl.remove(tr)
    for values in rows:
        if len(values) != width:
            raise SystemExit(f"row width {len(values)} != {width} in {caption_prefix!r}")
        tr = copy.deepcopy(template)
        for tc, value in zip(tr.findall(W + "tc"), values):
            paras = tc.findall(W + "p")
            for extra in paras[1:]:
                tc.remove(extra)
            para = paras[0]
            nodes = list(para.iter(W + "t"))
            if nodes:
                nodes[0].text = value
                for node in nodes[1:]:
                    node.text = ""
            else:
                run = etree.SubElement(para, W + "r")
                etree.SubElement(run, W + "t").text = value
        tbl.append(tr)


def texts() -> dict:
    far0 = pd.read_csv(RES / "A3_far_fold0.csv")
    far4 = pd.read_csv(RES / "A3_far_four_partition.csv")
    brier = pd.read_csv(RES / "A3_brier_four_partition.csv")

    def f0(model, group):
        return far0[(far0["model"] == model) & (far0["group"] == group)].iloc[0]

    d_s, d_d = f0("DKT", "sparse"), f0("DKT", "dense")
    t_s, t_d = f0("T-KT masked", "sparse"), f0("T-KT masked", "dense")
    d4 = far4[far4["model"] == "DKT"].iloc[0]
    t4 = far4[far4["model"] == "T-KT masked"].iloc[0]

    def b(model, group):
        return brier[(brier["model"] == model) & (brier["group"] == group)].iloc[0]

    db_s, db_d = b("DKT", "sparse"), b("DKT", "dense")
    tb_s, tb_d = b("T-KT masked", "sparse"), b("T-KT masked", "dense")

    def pm(row, col):
        return f"{fmt(row[col + '_mean'], 4)} ± {fmt(row[col + '_sd'], 4)}"

    brier_para = (
        "Table A1 gives the Brier decomposition (4) for the two primary models under the same protocol. "
        f"For DKT, REL is {pm(db_s, 'REL')} on sparse and {pm(db_d, 'REL')} on dense components, "
        f"and RES is {pm(db_s, 'RES')} and {pm(db_d, 'RES')}. "
        f"For T-KT masked, REL is {pm(tb_s, 'REL')} and {pm(tb_d, 'REL')}, "
        f"and RES is {pm(tb_s, 'RES')} and {pm(tb_d, 'RES')}. "
        "The sparse groups therefore carry both a larger reliability term and nonzero resolution. "
        "REL is binned like ECE and is also biased upward in small groups, so it is not a separate test of the sparse–dense difference."
    )

    def ci(lo, hi):
        return f"{fmt(lo, 3)} to {fmt(hi, 3)}"

    far_para = (
        f"At τ = 0.7 on fold 0 (Table A3), DKT advanced {int(d_s['N_adv'])} of {int(d_s['N'])} sparse responses "
        f"and {thousands(d_d['N_adv'])} of {thousands(d_d['N'])} dense responses. "
        f"FAR was {fmt(d_s['FAR'], 3)} on sparse and {fmt(d_d['FAR'], 3)} on dense components, "
        f"so ΔFAR = {fmt(d_s['DeltaFAR'], 3)}, with a KC-clustered 95% interval of {ci(d_s['DeltaFAR_ci_low'], d_s['DeltaFAR_ci_high'])}. "
        f"For T-KT masked, FAR was {fmt(t_s['FAR'], 3)} and {fmt(t_d['FAR'], 3)}, and ΔFAR = {fmt(t_s['DeltaFAR'], 3)} "
        f"({ci(t_s['DeltaFAR_ci_low'], t_s['DeltaFAR_ci_high'])}). Both fold-0 intervals for ΔFAR include 0. "
        f"Observed FAR exceeded the model’s own expected FAR on sparse components by {fmt(d_s['excess'], 3)} for DKT "
        f"and {fmt(t_s['excess'], 3)} for T-KT masked, against {fmt(d_d['excess'], 3)} and {fmt(t_d['excess'], 3)} on dense components. "
        f"Across the four unique partitions (Table A4), mean ΔFAR was {fmt(d4['mean_DeltaFAR'], 3)} ± {fmt(d4['sd_DeltaFAR'], 3)} for DKT "
        f"and {fmt(t4['mean_DeltaFAR'], 3)} ± {fmt(t4['sd_DeltaFAR'], 3)} for T-KT masked, "
        f"and it was positive in {int(d4['units_positive'])} of the 4 partitions for DKT and {int(t4['units_positive'])} of the 4 for T-KT masked. "
        "The sparse advance sets are small, so these figures describe one threshold on these partitions. "
        "They are not evidence that sparse advances fail more often in general."
    )

    flag = {"sparse": "L", "dense": "R"}
    a1_rows = []
    for model, s_row, d_row in (("DKT", db_s, db_d), ("T-KT masked", tb_s, tb_d)):
        for group, row in (("sparse", s_row), ("dense", d_row)):
            n = row["mean_N"]
            n_txt = f"{n:,.2f}".rstrip("0").rstrip(".")
            a1_rows.append(
                [
                    "ASSISTments 2012",
                    model,
                    group,
                    n_txt,
                    flag[group],
                    *[f"{fmt(row[c + '_mean'], 4)}±{fmt(row[c + '_sd'], 4)}" for c in ("Brier", "UNC", "REL", "RES")],
                ]
            )

    a3_rows = []
    for model, s, d in (("DKT", d_s, d_d), ("T-KT masked", t_s, t_d)):
        for group, row in (("sparse", s), ("dense", d)):
            a3_rows.append(
                [
                    model,
                    group,
                    thousands(row["N"]),
                    thousands(row["N_adv"]),
                    thousands(row["N_inc"]),
                    f"{fmt(row['FAR'], 3)} [{fmt(row['FAR_ci_low'], 3)}–{fmt(row['FAR_ci_high'], 3)}]",
                    fmt(row["E_FAR"], 3),
                    fmt(row["excess"], 3),
                    fmt(row["FPR"], 3),
                ]
            )

    def two(x):
        v = Decimal(repr(float(x))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{v}"

    a4_rows = []
    for model, row in (("DKT", d4), ("T-KT masked", t4)):
        a4_rows.append(
            [
                model,
                fmt(row["mean_DeltaFAR"], 3),
                fmt(row["sd_DeltaFAR"], 3),
                f"{fmt(row['min_DeltaFAR'], 3)} to {fmt(row['max_DeltaFAR'], 3)}",
                f"{int(row['units_positive'])}/4",
                two(row["mean_N_sparse"]),
                two(row["mean_Nadv_sparse"]),
                two(row["mean_Ninc_sparse"]),
            ]
        )

    a3_caption = (
        "Table A3. Threshold analysis at τ = 0.7 under protocol P0-BV200-15EW (ASSISTments 2012, fold 0, nonempty windows). "
        "FAR intervals are KC-clustered percentile bootstrap intervals (B = 2,000; seed 20261021). "
        f"ΔFAR is {fmt(d_s['DeltaFAR'], 3)} [{fmt(d_s['DeltaFAR_ci_low'], 3)}, {fmt(d_s['DeltaFAR_ci_high'], 3)}] for DKT "
        f"and {fmt(t_s['DeltaFAR'], 3)} [{fmt(t_s['DeltaFAR_ci_low'], 3)}, {fmt(t_s['DeltaFAR_ci_high'], 3)}] for T-KT masked. "
        "Excess is FAR minus E[FAR]."
    )
    a4_caption = (
        "Table A4. ΔFAR at τ = 0.7 across four unique partitions under protocol P0-BV200-15EW (ASSISTments 2012; "
        "fold 2 and fold 3 averaged first; the SD is descriptive). N, Nadv, and Ninc are sparse-group means."
    )
    a1_caption = (
        "Table A1. Brier decomposition under protocol P0-BV200-15EW (ASSISTments 2012; mean ± SD across four unique partitions; "
        "15 equal-width bins; nonempty windows). N is the mean count. REL and RES are binned and are biased in small groups."
    )
    return {
        "brier_para": brier_para,
        "far_para": far_para,
        "a1": (a1_caption, a1_rows),
        "a3": (a3_caption, a3_rows),
        "a4": (a4_caption, a4_rows),
    }


def edit(path: Path, t: dict) -> None:
    with zipfile.ZipFile(path) as archive:
        original = archive.read("word/document.xml")
        others = [(i, archive.read(i.filename)) for i in archive.infolist() if i.filename != "word/document.xml"]
    root = etree.fromstring(original)
    body = root.find(W + "body")

    sub(
        body,
        "Deep models were trained with seeds",
        "The Junyi Academy runs of the Transformer model (T-KT, Section III.C) were aligned differently: seeds 42 and 2024 were two initializations on fold 0, averaged first, and seeds 2025, 2026, and 2027 were run on folds 1, 2, and 4, so these labels are initialization seeds rather than split seeds. ",
        "",
    )
    sub(body, "Deep models were trained with seeds", "On every dataset, seeds", "On ASSISTments 2012 and Junyi Academy, seeds")
    sub(
        body,
        "Table 2 lists the runs",
        " The one-parameter IRT fit returns the training base rate for unseen learners, so its AUC is 0.5000 by construction and it is not a ranking model.",
        "",
    )
    sub(body, "Table 2. Configuration", " The base-rate reference is not a neural model and is omitted here.", "")
    sub(
        body,
        "The primary checkpoint is the validation-AUC",
        "The final epoch and the full test history remain in the sensitivity grid (Table A2).",
        "The final epoch and the full test history appear only as sensitivity cells in Table A2.",
    )
    sub(
        body,
        "The primary checkpoint is the validation-AUC",
        " The original weights behind the archived final-checkpoint pairs were not recovered. Those pairs are not results of this protocol.",
        "",
    )
    sub(
        body,
        "Two secondary analyses complement",
        " A test-response-weighted regression relates T-KT’s KC-level ECE to log(1 + ftrain) and the four descriptors, and a within-KC sparsification check reduces the training data of originally dense KCs.",
        " These descriptors use no model output.",
    )
    sub(
        body,
        "The second is a simulated threshold analysis",
        "on the saved predictions.",
        "on the primary-protocol predictions of ASSISTments DKT and T-KT masked.",
    )
    p87 = "that is, the proportion of advance decisions"
    sub(body, p87, "probabilities, E[1", "probabilities, E[FAR] = E[1")
    sub(body, p87, "FAR in (8) is computed", "FAR in (10) is computed")
    sub(
        body,
        p87,
        "Where prediction-level files exist, 95% intervals come from a KC-clustered percentile bootstrap (B = 2,000, with KCs resampled within the sparse and dense groups).",
        "Only rows with a nonempty test window enter. On fold 0, 95% intervals for FAR and ΔFAR come from a KC-clustered percentile bootstrap: each of B = 2,000 replicates resamples KCs with replacement within the sparse group and within the dense group, with a fresh NumPy Generator seeded with 20261021 for each model. A replicate with no advance in either group would be left out; none occurred. Across partitions, ΔFAR is summarized over the four unique partitions, with fold 2 and fold 3 averaged first.",
    )
    rewrite(body, "The base-rate reference shows why", t["brier_para"])
    rewrite(body, "D. Robustness to frequency cut points", "D. Checkpoint and test-window sensitivity")
    sub(
        body,
        "Table A2 is the ASSISTments DKT grid",
        " The alternative frequency grids of the archived final-checkpoint analysis were not repeated here and are not a current result.",
        " Alternative frequency cut points were not evaluated under this protocol.",
    )
    delete(body, "E. KC-level associations and controlled sparsification")
    delete(body, "A test-response-weighted regression of T-KT")
    delete(body, "Reducing the training data of originally dense KCs")
    rewrite(body, "F. Threshold analysis", "E. Threshold analysis")
    rewrite(body, "A threshold probe of false advances", t["far_para"])
    sub(
        body,
        "Several limits qualify",
        " The archived full-history pairs are not this protocol, and their weights were not recovered.",
        "",
    )
    sub(
        body,
        "Several limits qualify",
        "FAR was not recomputed.",
        "FAR uses one threshold, and its interval covers fold 0 only.",
    )
    fill_table(body, "Table A1. Archived", *t["a1"])
    fill_table(body, "Table A3. Archived threshold probe.", *t["a3"])
    fill_table(body, "Table A4. Archived threshold probe across", *t["a4"])

    xml = etree.tostring(root, xml_declaration=False, encoding="UTF-8")
    if b"w:document" not in xml[:1500]:
        raise SystemExit("prefix lost")
    tmp = path.with_suffix(".docx.a3")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for info, payload in others:
            archive.writestr(info, payload)
        archive.writestr("word/document.xml", xml)
    os.replace(tmp, path)
    print(f"UPDATED {path.name}", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    t = texts()
    print(t["brier_para"])
    print(t["far_para"])
    for key in ("a1", "a3", "a4"):
        print(t[key][0])
        for row in t[key][1]:
            print("  | " + " | ".join(row))
    if "--write" not in sys.argv:
        print("DRY RUN")
        return
    for path in PATHS:
        edit(path, t)
    for line in LOG:
        print("NOTE", line)


if __name__ == "__main__":
    main()
