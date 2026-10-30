"""B5: group-level N, AUC, ACC, Brier, UNC, REL, RES under the primary protocol.

Rows: primary exports pred_{dataset}_{model}_best_validxchunk, no_history = 0, p not NaN.
Base-rate reference: the constant training base rate of the IRT rerun for the same seed,
applied to the DKT primary row set of that partition (same learners checked).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
INNER = HERE.parents[1]
PRED = INNER / "results" / "predictions"
OUT = HERE.parent / "results"
sys.path.insert(0, str(HERE))
from a5_far_brier import brier_decomposition  # noqa: E402

PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
GROUPS = ("sparse", "medium", "dense")
RUNS = (
    ("assist2012", "dkt", "DKT", "primary"),
    ("assist2012", "tktc", "T-KT masked", "primary"),
    ("assist2012", "base_rate", "Base-rate reference", "reference"),
    ("assist2012", "simplekt", "simpleKT", "sensitivity"),
    ("junyi", "dkt", "DKT", "post-hoc"),
    ("junyi", "base_rate", "Base-rate reference", "reference"),
)


def load(dataset: str, model: str, fold: int, seed: int) -> pd.DataFrame:
    source = "dkt" if model == "base_rate" else model
    name = f"pred_{dataset}_{source}_best_validxchunk_fold{fold}_{seed}.csv.gz"
    frame = pd.read_csv(PRED / name, usecols=["user_id", "no_history", "group", "y", "p"])
    frame = frame[(frame["no_history"] == 0) & frame["p"].notna()].copy()
    if model == "base_rate":
        irt_name = f"{dataset}_learner_based_irt_1pl_seed{seed}_predictions_rerun.csv"
        irt = pd.read_csv(PRED / irt_name, usecols=["user_id", "p_pred"])
        rate = irt["p_pred"].unique()
        if np.ptp(rate) > 1e-12:
            raise SystemExit(f"{irt_name}: prediction is not constant")
        if set(irt["user_id"].unique()) != set(pd.read_csv(PRED / name, usecols=["user_id"])["user_id"].unique()):
            raise SystemExit(f"{irt_name}: test learners differ from {name}")
        frame["p"] = float(rate[0])
        return frame, irt_name
    return frame, name


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    auc = roc_auc_score(y, p) if len(np.unique(y)) == 2 else float("nan")
    brier, unc, rel, res = brier_decomposition(y, p)
    return {
        "N": len(y),
        "AUC": auc,
        "ACC": float(np.mean((p >= 0.5) == (y == 1))),
        "Brier": brier,
        "UNC": unc,
        "REL": rel,
        "RES": res,
    }


def main() -> None:
    rows = []
    for dataset, model, label, role in RUNS:
        for fold, seed in PAIRS:
            frame, source = load(dataset, model, fold, seed)
            y_all = frame["y"].to_numpy()
            p_all = frame["p"].to_numpy(dtype=float)
            parts = [("overall", y_all, p_all)]
            for g in GROUPS:
                sub = frame[frame["group"] == g]
                if len(sub):
                    parts.append((g, sub["y"].to_numpy(), sub["p"].to_numpy(dtype=float)))
            for g, y, p in parts:
                rows.append({"dataset": dataset, "model": label, "role": role, "fold": fold, "seed": seed,
                             "group": g, "source": source, **metrics(y, p)})
            print(f"DONE {dataset} {label} fold{fold}", flush=True)
    per = pd.DataFrame(rows)
    keys = ["dataset", "model", "role", "group"]
    summary = []
    for key, sub in per.groupby(keys, sort=False):
        sub = sub.set_index("fold")
        out = dict(zip(keys, key))
        out["fold"] = "four-partition"
        out["seed"] = ""
        out["source"] = "mean and SD over folds 0, 1, mean(2, 3), 4"
        for col in ("N", "AUC", "ACC", "Brier", "UNC", "REL", "RES"):
            v = sub[col]
            units = np.array([v[0], v[1], 0.5 * (v[2] + v[3]), v[4]], dtype=float)
            out[col] = units.mean()
            out[col + "_SD"] = units.std(ddof=1)
        summary.append(out)
    table = pd.concat([per, pd.DataFrame(summary)], ignore_index=True)
    OUT.mkdir(exist_ok=True)
    table.to_csv(OUT / "B5_STRATIFIED_METRICS.csv", index=False)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(summary)[keys + ["N", "AUC", "AUC_SD", "ACC", "Brier", "Brier_SD", "UNC", "REL", "REL_SD", "RES", "RES_SD"]].round(4).to_string())


if __name__ == "__main__":
    main()
