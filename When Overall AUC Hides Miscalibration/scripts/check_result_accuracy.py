#!/usr/bin/env python3
"""Recompute stored ECE from prediction files and check the locked formulas.

Does not retrain and does not rerun the bootstrap. A mismatch prints FAIL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.p0_official_simplekt_ece import four_part  # noqa: E402
from src.calibration_eval import compute_ece  # noqa: E402

PRED = ROOT / "results" / "predictions"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
ATOL = 1e-8
FAILURES = []


def fail(message: str) -> None:
    FAILURES.append(message)
    print(f"FAIL {message}", flush=True)


def ece(y, p) -> float:
    return float(compute_ece(np.asarray(y), np.asarray(p, dtype=float), n_bins=15)[0])


def bound(n: int) -> float:
    return float(0.5 * np.sqrt(15 / n))


def four_mean_sd(values: pd.Series) -> tuple[float, float]:
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


def load_pred(name: str) -> pd.DataFrame:
    path = PRED / name
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    return pd.read_csv(path, usecols=["y", "p", "group", "no_history"])


def group_ece(frame: pd.DataFrame, group: str, drop_empty: bool) -> tuple[float, int]:
    kept = frame[frame["no_history"] == 0] if drop_empty else frame
    part = kept[kept["group"] == group]
    if len(part) == 0:
        raise SystemExit(f"empty group {group}")
    return ece(part["y"], part["p"]), int(len(part))


def check_close(label: str, got: float, expected: float) -> None:
    if not np.isclose(got, expected, rtol=0, atol=ATOL):
        fail(f"{label} recomputed {got:.12f} stored {expected:.12f}")


def check_primary(path: Path, focal: str, focal_col: str, n_col: str) -> None:
    table = pd.read_csv(path)
    for _, row in table.iterrows():
        label = f"{path.name} {row['partition']}"
        delta = float(row[focal_col] - row["ECE_dense"])
        check_close(f"{label} DeltaECE", delta, float(row["DeltaECE"]))
        star = delta - bound(int(row[n_col]))
        check_close(f"{label} DeltaECE_star", star, float(row["DeltaECE_star"]))
        gap = float(row[focal_col] - row["matched_dense_median"])
        check_close(f"{label} matched_gap", gap, float(row["matched_gap"]))
        if int(row["invalid_bootstraps"]) != 0:
            fail(f"{label} invalid_bootstraps {row['invalid_bootstraps']}")
        if int(row["matched_R"]) != 2000:
            fail(f"{label} matched_R {row['matched_R']}")
        if row["partition"] == "fold0":
            if int(row["bootstrap_B"]) != 2000:
                fail(f"{label} bootstrap_B {row['bootstrap_B']}")
            for low, high, point in (
                ("cluster_CI_raw_low", "cluster_CI_raw_high", "DeltaECE"),
                ("cluster_CI_matched_low", "cluster_CI_matched_high", "matched_gap"),
            ):
                if not (float(row[low]) < float(row[point]) < float(row[high])):
                    fail(f"{label} {point} is outside {low}/{high}")
        if int(row["n_sparse_events" if n_col == "n_sparse_events" else n_col]) != int(row[n_col]):
            fail(f"{label} n column")
    n2 = int(table.loc[table["partition"] == "fold2", n_col].iloc[0])
    n3 = int(table.loc[table["partition"] == "fold3", n_col].iloc[0])
    if n2 != n3:
        fail(f"{path.name} fold2 N {n2} differs from fold3 N {n3}")
    indexed = table.set_index("partition")
    for column in (focal_col, "ECE_dense", "DeltaECE", "DeltaECE_star", "matched_gap"):
        mean, sd = four_mean_sd(indexed[column])
        print(f"FOUR {path.name} {column} mean={mean:.6f} sd={sd:.6f}", flush=True)


def check_predictions() -> None:
    jobs = [
        ("A5_uncertainty_dkt_assist.csv", "assist2012", "dkt", "sparse", "ECE_sparse", "n_sparse_events", True),
        ("B1_tktc_uncertainty.csv", "assist2012", "tktc", "sparse", "ECE_sparse", "n_sparse_events", True),
        ("B3_simplekt_uncertainty.csv", "assist2012", "simplekt", "sparse", "ECE_sparse", "n_sparse_events", True),
        ("B2_junyi_dkt_uncertainty.csv", "junyi", "dkt", "medium", "ECE_medium", "n_medium_events", True),
        ("C3_junyi_simplekt_uncertainty.csv", "junyi", "simplekt", "medium", "ECE_medium", "n_medium_events", True),
    ]
    for filename, dataset, model, group, focal_col, n_col, drop_empty in jobs:
        table = pd.read_csv(ROOT / "results" / filename).set_index("partition")
        for fold, seed in PAIRS:
            frame = load_pred(f"pred_{dataset}_{model}_best_validxchunk_fold{fold}_{seed}.csv.gz")
            got, n_got = group_ece(frame, group, drop_empty)
            dense, n_dense = group_ece(frame, "dense", drop_empty)
            label = f"{model} {dataset} fold{fold}"
            check_close(f"{label} {group}", got, float(table.loc[f"fold{fold}", focal_col]))
            check_close(f"{label} dense", dense, float(table.loc[f"fold{fold}", "ECE_dense"]))
            stored_n = int(table.loc[f"fold{fold}", n_col])
            stored_dense = int(table.loc[f"fold{fold}", "n_dense_events"])
            if n_got != stored_n or n_dense != stored_dense:
                fail(f"{label} N recomputed {n_got}/{n_dense} stored {stored_n}/{stored_dense}")
            print(f"ECE {label} {group}={got:.6f} dense={dense:.6f} n={n_got}", flush=True)
            del frame


def check_c1_c2() -> None:
    table = pd.read_csv(ROOT / "results" / "C1_fold5_group_metrics.csv")
    for model in ("dkt", "tktc", "simplekt"):
        frame = load_pred(f"pred_assist2012_{model}_best_validxchunk_fold5_42.csv.gz")
        kept = frame[frame["no_history"] == 0]
        rows = table[table["model"] == model]
        for _, row in rows.iterrows():
            group = row["group"]
            if group == "contrast_sparse_minus_dense":
                sparse = float(rows.loc[rows["group"] == "sparse", "ece"].iloc[0])
                dense = float(rows.loc[rows["group"] == "dense", "ece"].iloc[0])
                check_close(f"C1 {model} delta", sparse - dense, float(row["ece"]))
                check_close(f"C1 {model} star", sparse - dense - bound(int(row["n"])), float(row["DeltaECE_star"]))
                continue
            part = kept[kept["group"] == group]
            if int(row["n"]) == 0:
                continue
            check_close(f"C1 {model} {group}", ece(part["y"], part["p"]), float(row["ece"]))
            if len(part) != int(row["n"]):
                fail(f"C1 {model} {group} N {len(part)} stored {int(row['n'])}")
        print(f"ECE C1 {model} fold5 checked", flush=True)
        del frame
    both = pd.read_csv(ROOT / "results" / "C2_tktpe_vs_tktc_fold0.csv")
    b1 = pd.read_csv(ROOT / "results" / "B1_tktc_uncertainty.csv")
    b1_fold0 = b1[b1["partition"] == "fold0"].iloc[0]
    tktc = both[(both["model"] == "tktc") & (both["group"] == "sparse")].iloc[0]
    tktc_dense = both[(both["model"] == "tktc") & (both["group"] == "dense")].iloc[0]
    check_close("C2 tktc sparse equals B1", float(tktc["ece"]), float(b1_fold0["ECE_sparse"]))
    check_close("C2 tktc dense equals B1", float(tktc_dense["ece"]), float(b1_fold0["ECE_dense"]))
    frame = load_pred("pred_assist2012_tkt_pe_best_validxchunk_fold0_42.csv.gz")
    kept = frame[frame["no_history"] == 0]
    for group in ("very_sparse", "sparse", "medium", "dense"):
        stored = both[(both["model"] == "tkt_pe") & (both["group"] == group)].iloc[0]
        part = kept[kept["group"] == group]
        check_close(f"C2 tkt_pe {group}", ece(part["y"], part["p"]), float(stored["ece"]))
        if len(part) != int(stored["n"]):
            fail(f"C2 tkt_pe {group} N")
    print("ECE C2 tkt_pe fold0 checked", flush=True)


def check_simplekt_all_rows() -> None:
    archived = json.loads(
        (ROOT / "results" / "reports" / "p0_official_simplekt_assist_ece.json").read_text(encoding="utf-8")
    )
    for stratum in ("dense", "sparse"):
        seeds = [float(archived["strata"][stratum]["per_seed_ece"][str(seed)]) for _, seed in PAIRS]
        stored = float(archived["strata"][stratum]["ece"])
        check_close(f"archived {stratum} four-part", four_part(seeds), stored)
    fresh = {stratum: [] for stratum in ("dense", "sparse")}
    for fold, seed in PAIRS:
        frame = load_pred(f"pred_assist2012_simplekt_best_validxchunk_fold{fold}_{seed}.csv.gz")
        for stratum in ("dense", "sparse"):
            value, _ = group_ece(frame, stratum, drop_empty=False)
            fresh[stratum].append(value)
        del frame
    for stratum in ("dense", "sparse"):
        mean = four_part(fresh[stratum])
        old = float(archived["strata"][stratum]["ece"])
        print(
            f"ALL_ROWS simplekt {stratum} new={mean:.6f} archived={old:.6f} delta={mean - old:.6f}",
            flush=True,
        )
        if abs(mean - old) > 0.005:
            fail(f"all-rows {stratum} moved by more than 0.005")


def check_reported_four() -> None:
    expected = {
        "B1_tktc_uncertainty.csv": {
            "DeltaECE": (0.104112, 0.021516),
            "DeltaECE_star": (0.006782, 0.020703),
            "matched_gap": (0.058075, 0.022980),
            "ECE_sparse": (0.119936, 0.024683),
            "ECE_dense": (0.015823, 0.003233),
        },
        "B3_simplekt_uncertainty.csv": {
            "DeltaECE": (0.059438, 0.017676),
            "DeltaECE_star": (-0.037892, 0.016711),
            "matched_gap": (0.021479, 0.015661),
            "ECE_sparse": (0.084597, 0.014952),
            "ECE_dense": (0.025159, 0.004284),
        },
        "B2_junyi_dkt_uncertainty.csv": {
            "DeltaECE": (0.030231, 0.006892),
            "DeltaECE_star": (-0.003150, 0.006714),
            "matched_gap": (0.011521, 0.007328),
            "ECE_medium": (0.034502, 0.008012),
            "ECE_dense": (0.004271, 0.002144),
        },
        "C3_junyi_simplekt_uncertainty.csv": {
            "DeltaECE": (0.040292, 0.009049),
            "DeltaECE_star": (0.006910, 0.013632),
            "matched_gap": (0.026267, 0.012693),
            "ECE_medium": (0.049340, 0.012754),
            "ECE_dense": (0.009048, 0.005077),
        },
    }
    for filename, columns in expected.items():
        table = pd.read_csv(ROOT / "results" / filename).set_index("partition")
        for column, (want_mean, want_sd) in columns.items():
            mean, sd = four_mean_sd(table[column])
            if round(mean, 6) != want_mean or round(sd, 6) != want_sd:
                fail(f"report {filename} {column} {mean:.6f}/{sd:.6f} != {want_mean}/{want_sd}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    for filename, focal_col, n_col in (
        ("A5_uncertainty_dkt_assist.csv", "ECE_sparse", "n_sparse_events"),
        ("B1_tktc_uncertainty.csv", "ECE_sparse", "n_sparse_events"),
        ("B3_simplekt_uncertainty.csv", "ECE_sparse", "n_sparse_events"),
        ("B2_junyi_dkt_uncertainty.csv", "ECE_medium", "n_medium_events"),
        ("C3_junyi_simplekt_uncertainty.csv", "ECE_medium", "n_medium_events"),
    ):
        check_primary(ROOT / "results" / filename, focal_col, focal_col, n_col)
    check_reported_four()
    check_c1_c2()
    check_predictions()
    check_simplekt_all_rows()
    if FAILURES:
        print(f"ACCURACY = FAIL count={len(FAILURES)}", flush=True)
        raise SystemExit(1)
    print("ACCURACY = PASS", flush=True)


if __name__ == "__main__":
    main()
