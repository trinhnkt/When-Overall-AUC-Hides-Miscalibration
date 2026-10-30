#!/usr/bin/env python3
"""Recompute the supported cells of Tables 4, 5, A1, A2, A3, A4, and the G column of A5 from prediction exports.

Run from an extracted artifact_v4 directory:

    py -3 rebuild/reproduce_tables.py

No training. No path outside this directory. Exit 0 means every checked
manuscript digit matched. Exit 1 means a digit did not match.
"""
from __future__ import annotations

import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from far_brier import brier_decomposition, far_bootstrap, far_stats  # noqa: E402
from published_gap import (  # noqa: E402
    aligned_users,
    cluster_bootstrap_diff,
    ece,
    ece0_bound,
    row_matched,
    size_matched_contrast,
)

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "predictions"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
SEED = 20261021
USECOLS = ["y", "p", "group", "no_history", "user_id"]


def show(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def four(values: dict[str, float]) -> tuple[float, float]:
    units = np.array(
        [
            values["fold0"],
            values["fold1"],
            0.5 * (values["fold2"] + values["fold3"]),
            values["fold4"],
        ],
        dtype=float,
    )
    return float(units.mean()), float(units.std(ddof=1))


def load(name: str) -> pd.DataFrame:
    path = PRED / name
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    return pd.read_csv(path, usecols=USECOLS)


def pred_name(dataset: str, model: str, select: str, context: str, fold: int, seed: int) -> str:
    return f"pred_{dataset}_{model}_{select}x{context}_fold{fold}_{seed}.csv.gz"


def overall(frame: pd.DataFrame) -> tuple[float, float, int]:
    kept = frame[frame["no_history"] == 0]
    y = kept["y"].to_numpy()
    p = kept["p"].to_numpy(dtype=float)
    mask = ~np.isnan(p)
    y, p = y[mask], p[mask]
    auc = float(roc_auc_score(y, p))
    acc = float(accuracy_score(y, (p >= 0.5).astype(int)))
    return auc, acc, int(len(kept))


def groups(frame: pd.DataFrame, focal: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, int]:
    kept = frame[frame["no_history"] == 0]
    focal_rows = kept[kept["group"] == focal]
    dense = kept[kept["group"] == "dense"]
    return (
        focal_rows["y"].to_numpy(),
        focal_rows["p"].to_numpy(dtype=float),
        dense["y"].to_numpy(),
        dense["p"].to_numpy(dtype=float),
        int(len(focal_rows)),
        int(len(dense)),
    )


def uncertainty(frame: pd.DataFrame, focal: str, rng: np.random.Generator, bootstrap: bool) -> dict:
    fy, fp, dy, dp, n_f, n_d = groups(frame, focal)
    ece_f = ece(fy, fp)
    ece_d = ece(dy, dp)
    delta = ece_f - ece_d
    user_f, user_d = aligned_users(frame, focal)
    clusters = [pair for pair in user_d if len(pair[0])]
    matched = size_matched_contrast(fy, fp, clusters, rng, n_draws=2000)
    row_matched(fy, fp, dy, dp, rng, 2000)
    out = {
        "ece_focal": ece_f,
        "ece_dense": ece_d,
        "delta": delta,
        "star": delta - ece0_bound(n_f),
        "gap": matched["size_matched_diff"],
        "n_focal": n_f,
        "n_dense": n_d,
        "n_invalid_draws": matched["n_invalid"],
        "ci_low": float("nan"),
        "ci_high": float("nan"),
        "n_empty_sparse": 0,
    }
    if bootstrap:
        boot = cluster_bootstrap_diff(user_f, user_d, rng, n_boot=2000, n_inner=200)
        out["ci_low"] = boot["ci95_low"]
        out["ci_high"] = boot["ci95_high"]
        out["n_empty_sparse"] = boot["n_empty_sparse"]
    return out


class Check:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.rows: list[dict] = []

    def eq(self, label: str, got: float, printed: str) -> None:
        shown = show(got)
        status = "PASS" if shown == printed else "FAIL"
        self.rows.append({"label": label, "got": got, "shown": shown, "manuscript": printed, "status": status})
        print(f"{status} {label}: recomputed {shown} manuscript {printed}", flush=True)
        if status == "FAIL":
            self.failures.append(label)

    def cnt(self, label: str, got: float, printed: str) -> None:
        shown = f"{Decimal(repr(float(got))).quantize(Decimal(1), rounding=ROUND_HALF_UP):,}"
        status = "PASS" if shown == printed else "FAIL"
        self.rows.append({"label": label, "got": got, "shown": shown, "manuscript": printed, "status": status})
        print(f"{status} {label}: recomputed {shown} manuscript {printed}", flush=True)
        if status == "FAIL":
            self.failures.append(label)

    def near(self, label: str, got: float, expected: float, tol: float = 1e-6) -> None:
        status = "PASS" if abs(got - expected) <= tol else "FAIL"
        self.rows.append({"label": label, "got": got, "shown": str(got), "manuscript": str(expected), "status": status})
        print(f"{status} {label}: recomputed {got} manuscript {expected}", flush=True)
        if status == "FAIL":
            self.failures.append(label)


def series(rows: list[dict], key: str) -> dict[str, float]:
    return {row["partition"]: float(row[key]) for row in rows}


def run_model(dataset: str, model: str, focal: str, check: Check, prefix: str, expect: dict) -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    aucs, accs, ns = {}, {}, {}
    for fold, seed in PAIRS:
        name = pred_name(dataset, model, "best_valid", "chunk", fold, seed)
        print(f"LOAD {name}", flush=True)
        frame = load(name)
        auc, acc, n = overall(frame)
        part = f"fold{fold}"
        aucs[part] = auc
        accs[part] = acc
        ns[part] = n
        stats = uncertainty(frame, focal, rng, bootstrap=(fold == 0))
        stats["partition"] = part
        rows.append(stats)
        print(
            f"  {part} AUC={auc:.4f} gap={stats['gap']:.4f} delta={stats['delta']:.4f}",
            flush=True,
        )
    auc_m, auc_s = four(aucs)
    acc_m, acc_s = four(accs)
    n_m, _ = four({k: float(v) for k, v in ns.items()})
    check.eq(f"{prefix} AUC", auc_m, expect["auc"])
    check.eq(f"{prefix} AUC SD", auc_s, expect["auc_sd"])
    check.eq(f"{prefix} ACC", acc_m, expect["acc"])
    check.eq(f"{prefix} ACC SD", acc_s, expect["acc_sd"])
    check.near(f"{prefix} N", n_m, expect["n"])
    check.cnt(f"{prefix} N printed (Table 4)", n_m, expect["n_print"])
    for key, label, digits_key in (
        ("ece_focal", "focal ECE", "ece"),
        ("ece_dense", "dense ECE", "ece_dense"),
        ("delta", "DeltaECE", "delta"),
        ("star", "DeltaECE*", "star"),
        ("gap", "matched gap", "gap"),
    ):
        mean, sd = four(series(rows, key))
        check.eq(f"{prefix} {label}", mean, expect[digits_key])
        check.eq(f"{prefix} {label} SD", sd, expect[digits_key + "_sd"])
        mean_n, _ = four(series(rows, "n_focal" if key == "ece_focal" else "n_dense"))
        if key == "ece_focal":
            check.near(f"{prefix} focal N", mean_n, expect["n_focal"])
            check.cnt(f"{prefix} focal N printed (Table 5)", mean_n, expect["n_focal_print"])
        if key == "ece_dense":
            check.near(f"{prefix} dense N", mean_n, expect["n_dense"])
            check.cnt(f"{prefix} dense N printed (Table 5)", mean_n, expect["n_dense_print"])
    gaps = series(rows, "gap")
    for part, value, printed in zip(
        ("fold 0", "fold 1", "folds 2-3", "fold 4"),
        (gaps["fold0"], gaps["fold1"], 0.5 * (gaps["fold2"] + gaps["fold3"]), gaps["fold4"]),
        expect.get("partition_gaps", ()),
    ):
        check.eq(f"Table A5 {prefix} {part} G", value, printed)
    fold0 = rows[0]
    check.eq(f"{prefix} fold-0 matched gap", fold0["gap"], expect["gap0"])
    check.eq(f"{prefix} fold-0 interval low", fold0["ci_low"], expect["ci_low"])
    check.eq(f"{prefix} fold-0 interval high", fold0["ci_high"], expect["ci_high"])
    check.near(f"{prefix} fold-0 empty sparse replicates", float(fold0["n_empty_sparse"]), 0.0)
    check.near(f"{prefix} fold-0 invalid draws", float(fold0["n_invalid_draws"]), 0.0)


def table_a2(check: Check) -> None:
    cells = {
        ("final", "full"): "final/full",
        ("final", "chunk"): "final/200",
        ("best_valid", "full"): "best/full",
        ("best_valid", "chunk"): "best/200",
    }
    expected = {
        "fold0": {"final/full": "0.1689", "final/200": "0.1620", "best/full": "0.0977", "best/200": "0.0846", "star": "-0.0088", "n": 430},
        "fold1": {"final/full": "0.1746", "final/200": "0.1732", "best/full": "0.1017", "best/200": "0.1016", "star": "0.0074", "n": 423},
        "fold2": {"final/full": "0.1086", "final/200": "0.1084", "best/full": "0.0905", "best/200": "0.0867", "star": "-0.0118", "n": 386},
        "fold3": {"final/full": "0.1354", "final/200": "0.1316", "best/full": "0.0867", "best/200": "0.0935", "star": "-0.0050", "n": 386},
        "fold4": {"final/full": "0.1319", "final/200": "0.1335", "best/full": "0.0822", "best/200": "0.0808", "star": "-0.0224", "n": 352},
    }
    for fold, seed in PAIRS:
        part = f"fold{fold}"
        for (select, context), label in cells.items():
            name = pred_name("assist2012", "dkt", select, context, fold, seed)
            print(f"LOAD {name}", flush=True)
            fy, fp, dy, dp, n_f, _ = groups(load(name), "sparse")
            delta = ece(fy, fp) - ece(dy, dp)
            check.eq(f"Table A2 {part} {label}", delta, expected[part][label])
            if select == "best_valid" and context == "chunk":
                check.eq(f"Table A2 {part} DeltaECE*", delta - ece0_bound(n_f), expected[part]["star"])
                check.near(f"Table A2 {part} N sparse", float(n_f), float(expected[part]["n"]))
                check.cnt(f"Table A2 {part} N sparse printed", float(n_f), f"{expected[part]['n']:,}")


def simplekt_auc(check: Check) -> None:
    aucs, accs, ns = {}, {}, {}
    for fold, seed in PAIRS:
        name = pred_name("assist2012", "simplekt", "best_valid", "chunk", fold, seed)
        print(f"LOAD {name}", flush=True)
        auc, acc, n = overall(load(name))
        part = f"fold{fold}"
        aucs[part], accs[part], ns[part] = auc, acc, n
    auc_m, auc_s = four(aucs)
    acc_m, acc_s = four(accs)
    n_m, _ = four({k: float(v) for k, v in ns.items()})
    check.eq("Table 4 simpleKT AUC", auc_m, "0.7711")
    check.eq("Table 4 simpleKT AUC SD", auc_s, "0.0013")
    check.eq("Table 4 simpleKT ACC", acc_m, "0.7533")
    check.eq("Table 4 simpleKT ACC SD", acc_s, "0.0014")
    check.near("Table 4 simpleKT N", n_m, 523611.5)
    check.cnt("Table 4 simpleKT N printed", n_m, "523,612")


def far_brier_tables(check: Check) -> None:
    a3 = {
        ("DKT", "sparse"): (430, 200, 195, "0.215", "0.138", "0.304", "0.142", "0.073", "0.221"),
        ("DKT", "dense"): (521348, 300610, 156258, "0.179", "0.170", "0.187", "0.178", "0.001", "0.344"),
        ("T-KT masked", "sparse"): (430, 198, 195, "0.232", "0.163", "0.320", "0.119", "0.113", "0.236"),
        ("T-KT masked", "dense"): (521348, 298201, 156258, "0.182", "0.173", "0.191", "0.176", "0.006", "0.347"),
    }
    a3_delta = {"DKT": ("0.036", "-0.041", "0.125"), "T-KT masked": ("0.051", "-0.019", "0.141")}
    a4 = {
        "DKT": ("0.021", "0.019", "-0.001", "0.038", 3, 397.75, 190.625, 156.5),
        "T-KT masked": ("0.036", "0.038", "-0.007", "0.081", 3, 397.75, 191.875, 156.5),
    }
    a4_printed = {"DKT": ("398", "191", "157"), "T-KT masked": ("398", "192", "157")}

    def half_up(x, digits):
        q = Decimal(1).scaleb(-digits)
        s = str(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))
        return "0." + "0" * digits if s == "-0." + "0" * digits else s

    def show3(x):
        return half_up(x, 3)

    def show(x):
        return half_up(x, 4)

    def eq3(label, got, printed):
        shown = show3(got)
        status = "PASS" if shown == printed else "FAIL"
        check.rows.append({"label": label, "got": got, "shown": shown, "manuscript": printed, "status": status})
        print(f"{status} {label}: recomputed {shown} manuscript {printed}", flush=True)
        if status == "FAIL":
            check.failures.append(label)

    for model, label in (("dkt", "DKT"), ("tktc", "T-KT masked")):
        per_fold = {}
        for fold, seed in PAIRS:
            name = pred_name("assist2012", model, "best_valid", "chunk", fold, seed)
            print(f"LOAD {name}", flush=True)
            frame = pd.read_csv(PRED / name, usecols=["y", "p", "group", "no_history", "kc_id"])
            frame = frame[(frame["no_history"] == 0) & frame["group"].isin(["sparse", "dense"])]
            frame = frame[~frame["p"].isna()]
            sides = {}
            for g in ("sparse", "dense"):
                part = frame[frame["group"] == g]
                y = part["y"].to_numpy()
                p = part["p"].to_numpy(dtype=float)
                sides[g] = (part["kc_id"].to_numpy(), y, p)
            stats = {g: far_stats(sides[g][1], sides[g][2]) for g in ("sparse", "dense")}
            per_fold[f"fold{fold}"] = stats
            if fold == 0:
                boot = far_bootstrap(sides["sparse"], sides["dense"])
                for g in ("sparse", "dense"):
                    exp = a3[(label, g)]
                    s = stats[g]
                    check.near(f"Table A3 {label} {g} N", float(s["N"]), float(exp[0]))
                    check.near(f"Table A3 {label} {g} Nadv", float(s["N_adv"]), float(exp[1]))
                    check.near(f"Table A3 {label} {g} Ninc", float(s["N_inc"]), float(exp[2]))
                    eq3(f"Table A3 {label} {g} FAR", s["FAR"], exp[3])
                    eq3(f"Table A3 {label} {g} FAR CI low", boot[g][0], exp[4])
                    eq3(f"Table A3 {label} {g} FAR CI high", boot[g][1], exp[5])
                    eq3(f"Table A3 {label} {g} E[FAR]", s["E_FAR"], exp[6])
                    eq3(f"Table A3 {label} {g} excess", s["excess"], exp[7])
                    eq3(f"Table A3 {label} {g} FPR", s["FPR"], exp[8])
                d = a3_delta[label]
                eq3(f"Table A3 {label} DeltaFAR", stats["sparse"]["FAR"] - stats["dense"]["FAR"], d[0])
                eq3(f"Table A3 {label} DeltaFAR CI low", boot["delta"][0], d[1])
                eq3(f"Table A3 {label} DeltaFAR CI high", boot["delta"][1], d[2])
                check.near(f"Table A3 {label} invalid bootstrap replicates", float(boot["invalid"]), 0.0)
        delta = {k: v["sparse"]["FAR"] - v["dense"]["FAR"] for k, v in per_fold.items()}
        units = np.array([delta["fold0"], delta["fold1"], 0.5 * (delta["fold2"] + delta["fold3"]), delta["fold4"]])
        exp = a4[label]
        eq3(f"Table A4 {label} mean DeltaFAR", float(units.mean()), exp[0])
        eq3(f"Table A4 {label} SD DeltaFAR", float(units.std(ddof=1)), exp[1])
        eq3(f"Table A4 {label} min DeltaFAR", float(units.min()), exp[2])
        eq3(f"Table A4 {label} max DeltaFAR", float(units.max()), exp[3])
        check.near(f"Table A4 {label} partitions positive", float((units > 0).sum()), float(exp[4]))
        for (key, idx, target), printed in zip(
            (("N", "N", exp[5]), ("Nadv", "N_adv", exp[6]), ("Ninc", "N_inc", exp[7])), a4_printed[label]
        ):
            mean, _ = four({k: float(v["sparse"][idx]) for k, v in per_fold.items()})
            check.near(f"Table A4 {label} mean {key}", mean, target)
            check.cnt(f"Table A4 {label} mean {key} printed", mean, printed)


TABLE_A1 = {
    ("assist2012", "dkt", "sparse"): ("398", "0.7670±0.0188", "0.7318±0.0132", "0.1904±0.0088", "0.2356±0.0119", "0.0137±0.0026", "0.0589±0.0090"),
    ("assist2012", "dkt", "medium"): ("5,867", "0.8131±0.0125", "0.7342±0.0132", "0.1758±0.0069", "0.2484±0.0013", "0.0013±0.0005", "0.0733±0.0055"),
    ("assist2012", "dkt", "dense"): ("517,330", "0.7285±0.0004", "0.7354±0.0010", "0.1797±0.0004", "0.2100±0.0003", "0.0001±0.0000", "0.0301±0.0001"),
    ("assist2012", "tktc", "sparse"): ("398", "0.7476±0.0344", "0.7198±0.0201", "0.2039±0.0187", "0.2356±0.0119", "0.0215±0.0076", "0.0530±0.0125"),
    ("assist2012", "tktc", "medium"): ("5,867", "0.8042±0.0114", "0.7243±0.0104", "0.1820±0.0059", "0.2484±0.0013", "0.0036±0.0005", "0.0695±0.0046"),
    ("assist2012", "tktc", "dense"): ("517,330", "0.7227±0.0006", "0.7315±0.0007", "0.1817±0.0004", "0.2100±0.0003", "0.0004±0.0001", "0.0284±0.0001"),
    ("assist2012", "base_rate", "sparse"): ("398", "0.5000", "0.6101±0.0556", "0.2453±0.0218", "0.2356±0.0119", "0.0097±0.0100", "0.0000±0.0000"),
    ("assist2012", "base_rate", "medium"): ("5,867", "0.5000", "0.5363±0.0198", "0.2742±0.0078", "0.2484±0.0013", "0.0258±0.0065", "0.0000±0.0000"),
    ("assist2012", "base_rate", "dense"): ("517,330", "0.5000", "0.6999±0.0007", "0.2100±0.0003", "0.2100±0.0003", "0.0000±0.0000", "0.0000±0.0000"),
    ("assist2012", "simplekt", "sparse"): ("398", "0.7850±0.0362", "0.7363±0.0180", "0.1798±0.0112", "0.2356±0.0119", "0.0128±0.0032", "0.0682±0.0152"),
    ("assist2012", "simplekt", "medium"): ("5,867", "0.8262±0.0106", "0.7461±0.0117", "0.1700±0.0060", "0.2484±0.0013", "0.0013±0.0004", "0.0793±0.0045"),
    ("assist2012", "simplekt", "dense"): ("517,330", "0.7698±0.0014", "0.7534±0.0015", "0.1686±0.0006", "0.2100±0.0003", "0.0009±0.0002", "0.0420±0.0004"),
    ("junyi", "dkt", "medium"): ("3,677", "0.6998±0.0167", "0.6564±0.0147", "0.2152±0.0035", "0.2432±0.0013", "0.0020±0.0009", "0.0299±0.0043"),
    ("junyi", "dkt", "dense"): ("3,200,666", "0.7554±0.0012", "0.7470±0.0013", "0.1714±0.0006", "0.2078±0.0007", "0.0000±0.0000", "0.0360±0.0004"),
    ("junyi", "base_rate", "medium"): ("3,677", "0.5000", "0.5822±0.0082", "0.2578±0.0033", "0.2432±0.0013", "0.0146±0.0020", "0.0000±0.0000"),
    ("junyi", "base_rate", "dense"): ("3,200,666", "0.5000", "0.7055±0.0018", "0.2078±0.0007", "0.2078±0.0007", "0.0000±0.0000", "0.0000±0.0000"),
}


def table_a1(check: Check) -> None:
    """Group-level N, AUC, ACC, and 15-bin Brier decomposition. The base-rate rows apply the constant
    in predictions/base_rate_constants.csv to the DKT primary rows of the same partition."""
    rates = pd.read_csv(PRED / "base_rate_constants.csv").set_index(["dataset", "fold"])["p_base"]

    def half_up(x: float) -> str:
        s = str(Decimal(repr(float(x))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        return "0.0000" if s == "-0.0000" else s

    for dataset, model in dict.fromkeys((d, m) for d, m, _ in TABLE_A1):
        groups_here = [g for d, m, g in TABLE_A1 if (d, m) == (dataset, model)]
        per = {g: {} for g in groups_here}
        for fold, seed in PAIRS:
            name = pred_name(dataset, "dkt" if model == "base_rate" else model, "best_valid", "chunk", fold, seed)
            print(f"LOAD {name}{' (base rate)' if model == 'base_rate' else ''}", flush=True)
            frame = pd.read_csv(PRED / name, usecols=["y", "p", "group", "no_history"])
            frame = frame[(frame["no_history"] == 0) & frame["p"].notna()]
            if model == "base_rate":
                frame = frame.assign(p=float(rates.loc[(dataset, fold)]))
            for g in groups_here:
                part = frame[frame["group"] == g]
                y = part["y"].to_numpy()
                p = part["p"].to_numpy(dtype=float)
                auc = roc_auc_score(y, p) if len(np.unique(y)) == 2 else float("nan")
                acc = float(np.mean((p >= 0.5) == (y == 1)))
                per[g][f"fold{fold}"] = (float(len(y)), auc, acc, *brier_decomposition(y, p))
        for g in groups_here:
            expected = TABLE_A1[(dataset, model, g)]
            tag = f"Table A1 {dataset} {model} {g}"
            n_mean, _ = four({f: v[0] for f, v in per[g].items()})
            check.cnt(f"{tag} N", n_mean, expected[0])
            for k, col in enumerate(("AUC", "ACC", "Brier", "UNC", "REL", "RES"), start=1):
                mean, sd = four({f: v[k] for f, v in per[g].items()})
                shown = half_up(mean) if expected[k].count("±") == 0 else f"{half_up(mean)}±{half_up(sd)}"
                status = "PASS" if shown == expected[k] else "FAIL"
                check.rows.append({"label": f"{tag} {col}", "got": mean, "shown": shown, "manuscript": expected[k], "status": status})
                print(f"{status} {tag} {col}: recomputed {shown} manuscript {expected[k]}", flush=True)
                if status == "FAIL":
                    check.failures.append(f"{tag} {col}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    check = Check()
    print("coverage: folds 0-4 recomputed from prediction exports", flush=True)
    print("not in this command: fold 5, slide window, XES3G5M, Junyi simpleKT, retraining", flush=True)
    run_model(
        "assist2012",
        "dkt",
        "sparse",
        check,
        "Table 4/5 ASSISTments DKT",
        {
            "auc": "0.7303",
            "auc_sd": "0.0005",
            "acc": "0.7354",
            "acc_sd": "0.0008",
            "n": 523611.5,
            "ece": "0.0982",
            "ece_sd": "0.0093",
            "ece_dense": "0.0089",
            "ece_dense_sd": "0.0013",
            "delta": "0.0893",
            "delta_sd": "0.0091",
            "star": "-0.0081",
            "star_sd": "0.0122",
            "gap": "0.0400",
            "gap_sd": "0.0107",
            "n_focal": 397.75,
            "n_dense": 517329.5,
            "n_print": "523,612",
            "n_focal_print": "398",
            "n_dense_print": "517,330",
            "partition_gaps": ("0.0351", "0.0546", "0.0406", "0.0295"),
            "gap0": "0.0351",
            "ci_low": "0.0170",
            "ci_high": "0.0821",
        },
    )
    run_model(
        "assist2012",
        "tktc",
        "sparse",
        check,
        "Table 4/5 T-KT masked",
        {
            "auc": "0.7244",
            "auc_sd": "0.0007",
            "acc": "0.7314",
            "acc_sd": "0.0006",
            "n": 523611.5,
            "ece": "0.1199",
            "ece_sd": "0.0247",
            "ece_dense": "0.0158",
            "ece_dense_sd": "0.0032",
            "delta": "0.1041",
            "delta_sd": "0.0215",
            "star": "0.0068",
            "star_sd": "0.0207",
            "gap": "0.0581",
            "gap_sd": "0.0230",
            "n_focal": 397.75,
            "n_dense": 517329.5,
            "n_print": "523,612",
            "n_focal_print": "398",
            "n_dense_print": "517,330",
            "partition_gaps": ("0.0365", "0.0834", "0.0408", "0.0715"),
            "gap0": "0.0365",
            "ci_low": "0.0233",
            "ci_high": "0.0878",
        },
    )
    run_model(
        "junyi",
        "dkt",
        "medium",
        check,
        "Table 4/5 Junyi DKT",
        {
            "auc": "0.7554",
            "auc_sd": "0.0012",
            "acc": "0.7469",
            "acc_sd": "0.0013",
            "n": 3204343.0,
            "ece": "0.0345",
            "ece_sd": "0.0080",
            "ece_dense": "0.0043",
            "ece_dense_sd": "0.0021",
            "delta": "0.0302",
            "delta_sd": "0.0069",
            "star": "-0.0032",
            "star_sd": "0.0067",
            "gap": "0.0115",
            "gap_sd": "0.0073",
            "n_focal": 3676.75,
            "n_dense": 3200666.25,
            "n_print": "3,204,343",
            "n_focal_print": "3,677",
            "n_dense_print": "3,200,666",
            "gap0": "0.0085",
            "ci_low": "0.0010",
            "ci_high": "0.0434",
        },
    )
    simplekt_auc(check)
    table_a2(check)
    far_brier_tables(check)
    table_a1(check)
    out = ROOT / "statistics" / "recomputed_checks.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(check.rows).to_csv(out, index=False)
    print(f"WROTE {out}", flush=True)
    if check.failures:
        print(f"FAIL {len(check.failures)} checks", flush=True)
        raise SystemExit(1)
    print("PASS all supported table checks", flush=True)


if __name__ == "__main__":
    main()
