#!/usr/bin/env python3
"""15-bin ECE for official simpleKT on ASSISTments learner-based folds.

Does not overwrite T-KT locks 0.1136/0.2280. Four-partition mean averages
seeds 2025/2026 first. Main cuts: sparse 20<=f<100, dense f>=500.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.calibration_eval import compute_ece  # noqa: E402

SEEDS = (42, 2024, 2025, 2026, 2027)
T0, T1, T2 = 20, 100, 500


def four_part(vals: list[float]) -> float:
    return float(np.mean([vals[0], vals[1], 0.5 * (vals[2] + vals[3]), vals[4]]))


def four_sd(vals: list[float]) -> float:
    parts = [vals[0], vals[1], 0.5 * (vals[2] + vals[3]), vals[4]]
    return float(np.std(parts, ddof=1))


def bucket(freq: float) -> str:
    if freq == 0:
        return "cold"
    if freq < T0:
        return "very_sparse"
    if freq < T1:
        return "sparse"
    if freq < T2:
        return "medium"
    return "dense"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    freq = {}
    for fold in range(5):
        tr = pd.read_csv(
            ROOT / f"data/processed/assist2012/splits/learner_based/fold_{fold}/train.csv",
            usecols=["kc_id"],
        )
        freq[fold] = tr["kc_id"].value_counts()

    overall_auc, overall_acc = [], []
    by_b = {b: {"ece": [], "n": [], "auc": []} for b in ("dense", "medium", "sparse")}

    for seed in SEEDS:
        fold = SEEDS.index(seed)
        p = ROOT / "results/predictions" / (
            f"assist2012_learner_based_simplekt_official_seed{seed}.csv"
        )
        df = pd.read_csv(p, usecols=["kc_id", "y_true", "p_pred"])
        df["freq"] = df["kc_id"].map(freq[fold]).fillna(0)
        df["bucket"] = [bucket(f) for f in df["freq"]]
        y, pr = df["y_true"].to_numpy(), df["p_pred"].to_numpy()
        overall_auc.append(float(roc_auc_score(y, pr)))
        overall_acc.append(float(accuracy_score(y, (pr >= 0.5).astype(int))))
        for b in by_b:
            sl = df[df["bucket"] == b]
            ece, *_ = compute_ece(sl["y_true"].to_numpy(), sl["p_pred"].to_numpy(), n_bins=15)
            by_b[b]["ece"].append(float(ece))
            by_b[b]["n"].append(int(len(sl)))
            if sl["y_true"].nunique() == 2:
                by_b[b]["auc"].append(float(roc_auc_score(sl["y_true"], sl["p_pred"])))
            else:
                by_b[b]["auc"].append(float("nan"))

    out = {
        "model": "simplekt_official",
        "dataset": "assist2012",
        "auc_4part": four_part(overall_auc),
        "auc_4part_sd": four_sd(overall_auc),
        "acc_4part": four_part(overall_acc),
        "acc_4part_sd": four_sd(overall_acc),
        "per_seed_auc": dict(zip(SEEDS, overall_auc)),
        "strata": {},
        "delta_ece_sparse_minus_dense": None,
        "positive_dense_to_sparse": None,
        "tkt_lock_untouched": {"ece_dense": 0.1136, "ece_sparse": 0.2280},
    }
    for b, d in by_b.items():
        out["strata"][b] = {
            "ece": four_part(d["ece"]),
            "ece_sd": four_sd(d["ece"]),
            "n": four_part(d["n"]),
            "auc": four_part(d["auc"]),
            "per_seed_ece": dict(zip(SEEDS, d["ece"])),
        }
    delta = out["strata"]["sparse"]["ece"] - out["strata"]["dense"]["ece"]
    out["delta_ece_sparse_minus_dense"] = delta
    out["positive_dense_to_sparse"] = bool(delta > 0)

    path = ROOT / "results/reports/p0_official_simplekt_assist_ece.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2), flush=True)
    print(
        "DECISION",
        "ADD_TO_PAPER" if out["positive_dense_to_sparse"] else "DO_NOT_ADD_AUC_ONLY",
        flush=True,
    )


if __name__ == "__main__":
    main()
