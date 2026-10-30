"""Recompute every value of Table 6 (RQ2 evidence status) and Table 7 (counts and descriptors).

Train-derived values use learner-based fold 0 training rows. Test-row counts are means over the
four unique partitions (folds 0, 1, mean(2, 3), 4) of the split files. The average sparse N under
the primary protocol comes from results/B5_STRATIFIED_METRICS.csv (nonempty windows).
Run with --check to assert the printed manuscript values.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
INNER = HERE.parents[1]
SPLITS = INNER / "data" / "processed"
RES = HERE.parent / "results"
DATASETS = ("assist2012", "junyi", "xes3g5m")


def group_of(f: int) -> str:
    if f == 0:
        return "strict_cold_start"
    if f < 20:
        return "very_sparse"
    if f < 100:
        return "sparse"
    if f < 500:
        return "medium"
    return "dense"


def kc_key(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\.0$", "", regex=True)


def read(dataset: str, fold: int, part: str, cols: list[str]) -> pd.DataFrame:
    df = pd.read_csv(SPLITS / dataset / "splits" / "learner_based" / f"fold_{fold}" / f"{part}.csv", usecols=cols)
    df["kc"] = kc_key(df["kc_id"])
    return df[df["kc"] != "-1"]


def test_counts(dataset: str, fold: int) -> tuple[dict, set]:
    train = read(dataset, fold, "train", ["kc_id"])
    freq = train["kc"].value_counts().to_dict()
    test = read(dataset, fold, "test", ["user_id", "kc_id"])
    groups = test["kc"].map(lambda k: group_of(int(freq.get(k, 0))))
    return groups.value_counts().to_dict(), set(test["user_id"].unique())


def descriptors(dataset: str) -> dict:
    train = read(dataset, 0, "train", ["user_id", "item_id", "kc_id", "timestamp", "correct"])
    test = read(dataset, 0, "test", ["kc_id"])
    train["timestamp"] = pd.to_datetime(train["timestamp"], errors="coerce")
    train = train.sort_values(["user_id", "timestamp"], kind="stable")
    rank = train.groupby("user_id").cumcount()
    length = rank.groupby(train["user_id"]).transform("max").replace(0, 1)
    train["pos"] = rank / length
    kc = train.groupby("kc").agg(f=("correct", "size"), acc=("correct", "mean"),
                                 items=("item_id", "nunique"), pos=("pos", "median"))
    kc["group"] = kc["f"].map(group_of)
    test_kcs = set(test["kc"].unique())
    out = {
        "n_kc_train": int(len(kc)),
        "pct_kc_lt100": float((kc["f"] < 100).mean() * 100),
        "n_kc_very_sparse": int((kc["group"] == "very_sparse").sum()),
        "n_kc_sparse": int((kc["group"] == "sparse").sum()),
        "n_kc_medium": int((kc["group"] == "medium").sum()),
        "n_kc_dense": int((kc["group"] == "dense").sum()),
        "n_kc_strict_cold_start_fold0": int(len(test_kcs - set(kc.index))),
        "median_f_train": float(kc["f"].median()),
    }
    for scope, sel in (("test", kc[kc.index.isin(test_kcs)]), ("train", kc)):
        logf = np.log1p(sel["f"])
        out[f"rho_freq_difficulty_{scope}"] = float(spearmanr(logf, 1 - sel["acc"]).statistic)
        out[f"rho_freq_position_{scope}"] = float(spearmanr(logf, sel["pos"]).statistic)
        out[f"median_items_{scope}"] = float(sel["items"].median())
        for g in ("dense", "sparse"):
            part = sel[sel["group"] == g]["items"]
            out[f"median_items_{g}_{scope}"] = float(part.median()) if len(part) else float("nan")
    return out


def compute() -> dict:
    result = {}
    for ds in DATASETS:
        per_fold, users = {}, {}
        for fold in range(5):
            per_fold[fold], users[fold] = test_counts(ds, fold)
            print(f"{ds} fold{fold} {per_fold[fold]}", flush=True)
        shared = users[2] == users[3]
        row = descriptors(ds)
        row["folds_2_3_share_learners"] = bool(shared)
        for g in ("strict_cold_start", "very_sparse", "sparse", "medium", "dense"):
            v = {f: per_fold[f].get(g, 0) for f in range(5)}
            units = [v[0], v[1], 0.5 * (v[2] + v[3]), v[4]] if shared else [v[f] for f in range(5)]
            row[f"test_rows_{g}_mean"] = float(np.mean(units))
            row[f"test_rows_{g}_partitions_nonempty"] = int(sum(u > 0 for u in units))
        result[ds] = row
        print(json.dumps({ds: row}, indent=1), flush=True)
    b5 = pd.read_csv(RES / "B5_STRATIFIED_METRICS.csv")
    b5 = b5[(b5["fold"] == "four-partition") & (b5["model"] == "DKT") & (b5["group"] == "sparse")]
    result["assist2012"]["primary_sparse_N"] = float(b5[b5["dataset"] == "assist2012"]["N"].iloc[0])
    (RES / "TABLE6_7_CONTEXT.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def support(n: float) -> str:
    if n <= 0:
        return "empty"
    return "R" if n >= 1000 else ("L" if n >= 100 else "I")


def _r(x: float, d: int = 3) -> str:
    sys.path.insert(0, str(HERE))
    from msedit import fmt

    s = fmt(x, d)
    return ("+" + s) if x > 0 and d == 3 else s


def _n(x: float) -> str:
    from msedit import count

    return count(x)


def _rows_of(ctx: dict, ds: str) -> dict:
    c = ctx[ds]
    groups = f"{_n(c['n_kc_very_sparse'])} / {_n(c['n_kc_sparse'])} / {_n(c['n_kc_medium'])} / {_n(c['n_kc_dense'])}"
    sp = c["test_rows_sparse_mean"]
    vs = c["test_rows_very_sparse_mean"]
    cs = c["test_rows_strict_cold_start_mean"]
    cs_txt = "empty" if cs == 0 else f"{_n(cs)} ({support(cs)}; nonempty in {c['test_rows_strict_cold_start_partitions_nonempty']} of 4)"
    items_s = c["median_items_sparse_train"]
    items = f"{_n(c['median_items_train'])} (dense {_n(c['median_items_dense_train'])}; sparse {'–' if items_s != items_s else _n(items_s)})"
    if ds == "assist2012":
        primary = f"{_n(c['primary_sparse_N'])} ({support(c['primary_sparse_N'])})"
    elif ds == "junyi":
        primary = "No sparse group"
    else:
        primary = "Not evaluated (descriptive only)"
    return {
        "KCs present in training": _n(c["n_kc_train"]),
        "KCs with ftrain < 100 (E1)": f"{fmt1(c['pct_kc_lt100'])}%",
        "KCs very sparse / sparse / medium / dense": groups,
        "Strict cold-start KCs in fold-0 test": _n(c["n_kc_strict_cold_start_fold0"]),
        "Median ftrain per KC": _n(c["median_f_train"]),
        "Sparse-group test rows (E2)": "empty" if sp == 0 else f"{_n(sp)} ({support(sp)})",
        "Very-sparse test rows": "empty" if vs == 0 else f"{_n(vs)} ({support(vs)})",
        "Strict cold-start test rows": cs_txt,
        "Mean sparse N, primary protocol": primary,
        "Frequency–difficulty ρ": _r(c["rho_freq_difficulty_train"]),
        "Median item support": items,
        "Frequency–position ρ": _r(c["rho_freq_position_train"]),
    }


def fmt1(x: float) -> str:
    from msedit import fmt

    return fmt(x, 1)


SECTIONS = {
    "Train-derived (fold 0)": ["KCs present in training", "KCs with ftrain < 100 (E1)", "KCs very sparse / sparse / medium / dense",
                                "Strict cold-start KCs in fold-0 test", "Median ftrain per KC"],
    "Test-derived (mean over four partitions)": ["Sparse-group test rows (E2)", "Very-sparse test rows", "Strict cold-start test rows",
                                                 "Mean sparse N, primary protocol"],
    "Structural descriptors (fold-0 training)": ["Frequency–difficulty ρ", "Median item support", "Frequency–position ρ"],
}


def table7_rows(ctx: dict) -> list[list[str]]:
    per = {ds: _rows_of(ctx, ds) for ds in DATASETS}
    rows = []
    for section, keys in SECTIONS.items():
        rows.append([section, "", "", ""])
        for k in keys:
            rows.append([k] + [per[ds][k] for ds in DATASETS])
    return rows


def table6_rows(table5: list[list[str]], c1: pd.DataFrame) -> list[list[str]]:
    t5 = {(r[0], r[1], r[2].split(" ")[0]): r for r in table5[1:]}
    j = t5[("Junyi (post-hoc)", "DKT", "medium")]
    lows = c1[c1["partition"].isin(["fold 0", "fold 1", "folds 2–3", "fold 4"])]["ci_low"]
    all_exclude = bool((lows > 0).all())
    unc_a = "Fold-0 learner-cluster interval of G excludes 0 (primary); per-partition intervals in Table A5" + (
        " also exclude 0" if all_exclude else "")
    return [
        ["Sparse group present?", "Yes (Limited)", "No", "KC-level tail only"],
        ["L1–L8 PASS?", "L1–L7 PASS; L8 not applicable (one row per response)",
         "L1–L7 PASS; L8 not applicable (one row per response)", "L1–L7 PASS; L8 FAIL"],
        ["Eligible model contrast?", "Yes: DKT and T-KT masked", "Post-hoc medium versus dense (DKT)", "No"],
        ["Direction", "Mean ΔECE and G positive for both models; G positive in every partition; ΔECE* mixed in sign",
         f"Mean ΔECE {j[5].split('±')[0].strip()} and G {j[7].split('±')[0].strip()} positive; ΔECE* {j[6].split('±')[0].strip()}",
         "Not evaluated"],
        ["Uncertainty", unc_a, f"Fold-0 interval of G {j[8].replace('to', ' to ').replace('  ', ' ')}; post-hoc", "Not evaluated"],
        ["Protocol/evidence status", "Primary protocol; primary evidence", "Primary-protocol rules; post-hoc, not pre-specified",
         "Descriptive only"],
    ]


def check() -> None:
    import zipfile

    from lxml import etree

    from msedit import PATHS, W, table_rows

    ctx = json.loads((RES / "TABLE6_7_CONTEXT.json").read_text(encoding="utf-8"))
    c1 = pd.read_csv(RES / "C1_PARTITION_INTERVALS.csv")
    bad = 0
    for path in PATHS:
        with zipfile.ZipFile(path) as z:
            body = etree.fromstring(z.read("word/document.xml")).find(W + "body")
        t5 = table_rows(body, "Table 5.")
        for label, want, got in (("Table 6", table6_rows(t5, c1), table_rows(body, "Table 6.")[1:]),
                                 ("Table 7", table7_rows(ctx), table_rows(body, "Table 7.")[1:])):
            if len(want) != len(got):
                print(f"FAIL {path.name} {label}: {len(got)} rows, expected {len(want)}")
                bad += 1
                continue
            for w, g in zip(want, got):
                if [x.strip() for x in w] != [x.strip() for x in g]:
                    print(f"FAIL {path.name} {label} row {w[0]!r}: printed {g} expected {w}")
                    bad += 1
    print("All values match" if not bad else f"{bad} mismatches")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--check" in sys.argv:
        check()
    else:
        compute()
