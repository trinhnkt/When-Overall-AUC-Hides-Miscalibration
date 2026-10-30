"""B5: rebuild Table A1 with group AUC/ACC and the Brier decomposition; rewrite its IV.B paragraph."""
from __future__ import annotations

import sys

import pandas as pd

from msedit import RES, apply, count, fill_table, fmt, pm, rewrite, table_rows

S = pd.read_csv(RES / "B5_STRATIFIED_METRICS.csv")
S = S[S["fold"] == "four-partition"].set_index(["dataset", "model", "group"])


def v(dataset, model, group, col):
    return S.loc[(dataset, model, group), col]


def cell(dataset, model, group, col):
    if model == "Base-rate reference" and col == "AUC":
        return "0.5000"
    return f"{fmt(v(dataset, model, group, col), 4)}±{fmt(v(dataset, model, group, col + '_SD'), 4)}"


ORDER = [
    ("assist2012", "ASSISTments 2012", "DKT", "DKT", ("sparse", "medium", "dense")),
    ("assist2012", "ASSISTments 2012", "T-KT masked", "T-KT masked", ("sparse", "medium", "dense")),
    ("assist2012", "ASSISTments 2012", "Base-rate reference", "Base rate", ("sparse", "medium", "dense")),
    ("assist2012", "ASSISTments 2012", "simpleKT", "simpleKT (sensitivity)", ("sparse", "medium", "dense")),
    ("junyi", "Junyi (post-hoc)", "DKT", "DKT", ("medium", "dense")),
    ("junyi", "Junyi (post-hoc)", "Base-rate reference", "Base rate", ("medium", "dense")),
]
HEADER = ["Dataset", "Model", "Group", "N", "AUC", "ACC", "Brier", "UNC", "REL", "RES"]
ROWS = [
    [ds_label, m_label, g, count(v(ds, m, g, "N"))] + [cell(ds, m, g, c) for c in ("AUC", "ACC", "Brier", "UNC", "REL", "RES")]
    for ds, ds_label, m, m_label, groups in ORDER
    for g in groups
]

CAPTION = (
    "Table A1. Group-level discrimination and Brier decomposition under the primary protocol (mean ± SD across four "
    "unique partitions; 15 equal-width bins; nonempty windows). N is the mean count, rounded. The base-rate reference "
    "predicts each partition’s training proportion correct, so its AUC is 0.5000 and its RES is 0 by construction. "
    "simpleKT is sensitivity; Junyi is post-hoc and has no sparse group. REL and RES are binned and biased upward in small groups."
)


def paragraph() -> str:
    a = ("assist2012",)
    d_rel = pm(v(*a, "DKT", "sparse", "REL"), v(*a, "DKT", "sparse", "REL_SD"))
    d_rel_dense = pm(v(*a, "DKT", "dense", "REL"), v(*a, "DKT", "dense", "REL_SD"))
    t_rel = pm(v(*a, "T-KT masked", "sparse", "REL"), v(*a, "T-KT masked", "sparse", "REL_SD"))
    t_rel_dense = pm(v(*a, "T-KT masked", "dense", "REL"), v(*a, "T-KT masked", "dense", "REL_SD"))
    d_auc = pm(v(*a, "DKT", "sparse", "AUC"), v(*a, "DKT", "sparse", "AUC_SD"))
    t_auc = pm(v(*a, "T-KT masked", "sparse", "AUC"), v(*a, "T-KT masked", "sparse", "AUC_SD"))
    d_all = fmt(v(*a, "DKT", "overall", "AUC"), 4)
    t_all = fmt(v(*a, "T-KT masked", "overall", "AUC"), 4)
    return (
        f"Table A1 adds group-level AUC and the Brier decomposition (4) under the same protocol. REL was larger on sparse "
        f"than on dense components: {d_rel} versus {d_rel_dense} for DKT and {t_rel} versus {t_rel_dense} for T-KT masked. "
        f"Sparse-group AUC was {d_auc} for DKT and {t_auc} for T-KT masked, against overall AUC of {d_all} and {t_all} "
        f"(Table 4). For DKT, sparse-group AUC exceeded overall AUC in every run; for T-KT masked it was lower in folds 1 and 4. "
        f"Sparse responses were thus ranked about as well as responses overall while their reliability term was larger, "
        f"which a pooled AUC does not show. REL is binned like ECE and is biased upward in small groups, so it is not a "
        f"separate test of the sparse–dense difference."
    )


def check_table5(body) -> None:
    rows = table_rows(body, "Table 5. Calibration")
    printed = {(r[0], r[1], r[2].split(" ")[0]): r[3] for r in rows[1:]}
    expect = {
        ("ASSISTments", "DKT", "sparse"): v("assist2012", "DKT", "sparse", "N"),
        ("ASSISTments", "DKT", "dense"): v("assist2012", "DKT", "dense", "N"),
        ("ASSISTments", "T-KT masked", "sparse"): v("assist2012", "T-KT masked", "sparse", "N"),
        ("ASSISTments", "T-KT masked", "dense"): v("assist2012", "T-KT masked", "dense", "N"),
        ("Junyi (post-hoc)", "DKT", "medium"): v("junyi", "DKT", "medium", "N"),
        ("Junyi (post-hoc)", "DKT", "dense"): v("junyi", "DKT", "dense", "N"),
    }
    for key, n in expect.items():
        shown = float(printed[key].replace(",", ""))
        ok = abs(shown - n) <= 0.05 or count(n) == printed[key]
        print(f"{'PASS' if ok else 'FAIL'} Table 5 N {key}: printed {printed[key]} recomputed {n}")
        if not ok:
            raise SystemExit("Table 5 N mismatch")


def edit(body, path) -> None:
    check_table5(body)
    fill_table(body, "Table A1.", CAPTION, HEADER, ROWS, weights=[1.5, 1.6, 1.0, 1.1, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3])
    rewrite(body, "Table A1 gives the Brier decomposition", paragraph())


if __name__ == "__main__":
    print(CAPTION)
    for r in ROWS:
        print(" | ".join(r))
    print(paragraph())
    apply(edit, "--write" in sys.argv)
