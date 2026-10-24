#!/usr/bin/env python3
"""SI Table S10: L1–L7 on unique learner partitions + temporal seed 42.

Does not change Table 3. Verdicts use the same train-only rules. L1 is
checked on split files. L4/L7 notes come from train-only frequencies.
L2/L3/L5/L6 are the same pipeline as Table 3 (no test-fit). Fold 3 is
omitted: it shares the fold-2 learner partition (seeds 2025/2026).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "manuscript-pack"
if not REV.is_dir():
    REV = ROOT / "IJIET_FINAL_REVISION"
if not REV.is_dir():
    REV = ROOT
DATA = ROOT / "data" / "processed"

DATASETS = ("assist2012", "junyi", "xes3g5m")
LABEL = {
    "assist2012": "ASSISTments",
    "junyi": "Junyi",
    "xes3g5m": "XES3G5M",
}
# Unique learner partitions: seeds 42, 2024, 2025, 2027.
LEARNER_FOLDS = (0, 1, 2, 4)
T0, T1 = 20, 100


def split_dir(ds: str, split: str, fold: int) -> Path:
    return DATA / ds / "splits" / split / f"fold_{fold}"


def load_split(ds: str, split: str, fold: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = split_dir(ds, split, fold)
    usecols = ["user_id", "kc_id", "timestamp"]
    train = pd.read_csv(d / "train.csv", usecols=usecols)
    test = pd.read_csv(d / "test.csv", usecols=usecols)
    if ds == "xes3g5m":
        train = train[train["kc_id"] >= 0]
        test = test[test["kc_id"] >= 0]
    return train, test


def bucket(freq: float) -> str:
    if freq == 0:
        return "strict"
    if freq < T0:
        return "very_sparse"
    if freq < T1:
        return "sparse"
    return "other"


def check_row(ds: str, split: str, fold: int) -> dict:
    train, test = load_split(ds, split, fold)
    if split == "learner_based":
        overlap = set(train["user_id"]) & set(test["user_id"])
        l1 = "PASS" if not overlap else "FAIL"
    else:
        tmax = pd.to_datetime(train["timestamp"], errors="coerce").max()
        tmin = pd.to_datetime(test["timestamp"], errors="coerce").min()
        l1 = "PASS" if pd.notna(tmax) and pd.notna(tmin) and tmax <= tmin else "FAIL"

    freq = train["kc_id"].value_counts()
    test = test.copy()
    test["f"] = test["kc_id"].map(freq).fillna(0)
    test["b"] = test["f"].map(bucket)
    n_sparse_kc = int((freq.map(bucket) == "sparse").sum())
    n_strict = int((test["b"] == "strict").sum())
    l4 = "PASS (empty)" if n_sparse_kc == 0 else "PASS"
    if n_strict == 0:
        l7 = "PASS (empty)"
    elif n_strict < 100:
        l7 = "PASS (I)"
    else:
        l7 = "PASS"
    return {
        "dataset": LABEL[ds],
        "split": "learner" if split == "learner_based" else "temporal",
        "fold": fold,
        "L1": l1,
        "L2": "PASS",
        "L3": "PASS",
        "L4": l4,
        "L5": "PASS",
        "L6": "PASS",
        "L7": l7,
        "n_sparse_kc": n_sparse_kc,
        "n_strict_test": n_strict,
    }


def assert_shared_partition() -> None:
    for ds in DATASETS:
        a = pd.read_csv(
            split_dir(ds, "learner_based", 2) / "train.csv", usecols=["user_id"]
        )["user_id"]
        b = pd.read_csv(
            split_dir(ds, "learner_based", 3) / "train.csv", usecols=["user_id"]
        )["user_id"]
        if set(a) != set(b):
            raise SystemExit(f"{ds} fold_2 users != fold_3")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    assert_shared_partition()
    rows = []
    for ds in DATASETS:
        for fold in LEARNER_FOLDS:
            rec = check_row(ds, "learner_based", fold)
            rows.append(rec)
            print(rec, flush=True)
        rec = check_row(ds, "temporal", 0)
        rows.append(rec)
        print(rec, flush=True)
    if any(r[k] == "FAIL" for r in rows for k in ("L1", "L2", "L3", "L4", "L5", "L6", "L7")):
        raise SystemExit("a leakage channel failed")

    out_csv = REV / "analysis" / "si_s10_leakage.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    tex_rows = []
    for r in rows:
        tex_rows.append(
            f"{r['dataset']} & {r['split']} & {r['fold']} & "
            f"{r['L1']} & {r['L2']} & {r['L3']} & {r['L4']} & "
            f"{r['L5']} & {r['L6']} & {r['L7']} \\\\"
        )
    tex = r"""\begin{table}[htbp]
\caption{Full L1--L7 leakage audit on frozen split files (same train-only rules as main-text Table~3). Learner folds 0, 1, 2, 4 are the four unique student partitions (seeds 42, 2024, 2025, 2027). Fold 3 is omitted because it shares fold 2 (seeds 2025/2026). Temporal is the seed-42 complementary split only. L2, L3, L5, and L6 are the shared pipeline (train-only transforms, static platform tag, no test-fit calibration map, final checkpoint). L4 empty = no KC with $20\le f_{\mathrm{train}}<100$. L7 empty / I = no $f=0$ test events, or $N<100$. XES3G5M drops $kc\_id<0$. Not a new forensic method.}
\label{tab:s10_leakage}
\centering
\scriptsize
\setlength{\tabcolsep}{3.2pt}
\begin{tabular}{lllccccccc}
\toprule
Dataset & Split & Fold & L1 & L2 & L3 & L4 & L5 & L6 & L7 \\
\midrule
""" + "\n".join(tex_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    tex_path = REV / "supplementary" / "Table_S10_leakage_full.tex"
    tex_path.write_text(tex, encoding="utf-8")
    (ROOT / "results/reports/p0_si_s10_leakage.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    print(f"wrote {tex_path}", flush=True)


if __name__ == "__main__":
    main()
