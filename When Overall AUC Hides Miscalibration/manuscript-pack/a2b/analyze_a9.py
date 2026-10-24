#!/usr/bin/env python3
"""A2B: A9 ΔECE on selected XES KCs only."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from paths import ANALYSIS, DS, N_BINS, PRED  # noqa: E402
from src.recalculate_diagnostics import calculate_metrics, compute_brier_decomposition, compute_ece  # noqa: E402

N_BOOT = 10000
BOOT_SEED = 2029
LEVELS = ["full", "t500", "t100", "t50"]
MODELS = ["dkt", "simplekt"]


def kc_key(s) -> str:
    return str(s).replace(".0", "")


def metrics_block(y, p) -> dict:
    y = np.asarray(y).astype(int)
    p = np.clip(np.asarray(p).astype(float), 1e-15, 1 - 1e-15)
    auc, acc, nll, rmse = calculate_metrics(y, p)
    ece = compute_ece(y, p)
    brier, unc, rel, res = compute_brier_decomposition(y, p)
    return dict(AUC=auc, ACC=acc, NLL=nll, RMSE=rmse, ECE=ece, Brier=brier, REL=rel, RES=res, n_events=int(len(y)))


def eval_file(path: Path, selected: set[str]):
    df = pd.read_csv(path, usecols=["kc_id", "y_true", "p_pred"])
    df["kc_id"] = df["kc_id"].map(kc_key)
    df = df[df["kc_id"].isin(selected)].dropna(subset=["y_true", "p_pred"])
    pooled = metrics_block(df["y_true"], df["p_pred"])
    rows = []
    for kc, g in df.groupby("kc_id"):
        m = metrics_block(g["y_true"], g["p_pred"])
        m["kc_id"] = kc
        rows.append(m)
    return pooled, pd.DataFrame(rows)


def main() -> None:
    a9 = ANALYSIS / "a9"
    sel = pd.read_csv(a9 / "selected_kcs.csv")
    selected = set(sel["kc_id"].map(kc_key))
    pooled_rows, kc_rows = [], []
    for model in MODELS:
        pfull = PRED / f"{DS}_learner_based_{model}_seed42_predictions_rerun.csv"
        if not pfull.exists():
            continue
        pooled, per_kc = eval_file(pfull, selected)
        pooled.update(dataset=DS, model=model, level="full", seed=42)
        pooled_rows.append(pooled)
        per_kc["dataset"] = DS
        per_kc["model"] = model
        per_kc["level"] = "full"
        per_kc["seed"] = 42
        kc_rows.append(per_kc)
        for level in ("t500", "t100", "t50"):
            p = PRED / f"a9_{DS}_learner_based_{model}_{level}_seed42.csv"
            if not p.exists():
                continue
            pooled, per_kc = eval_file(p, selected)
            pooled.update(dataset=DS, model=model, level=level, seed=42)
            pooled_rows.append(pooled)
            per_kc["dataset"] = DS
            per_kc["model"] = model
            per_kc["level"] = level
            per_kc["seed"] = 42
            kc_rows.append(per_kc)
    if not kc_rows:
        print("no a9 files", flush=True)
        return
    kc_m = pd.concat(kc_rows, ignore_index=True)
    pd.DataFrame(pooled_rows).to_csv(a9 / "pooled_selected_kc_metrics.csv", index=False)
    kc_m.to_csv(a9 / "kc_metrics.csv", index=False)
    rng = np.random.default_rng(BOOT_SEED)
    stats = []
    for (model, level), g in kc_m.groupby(["model", "level"]):
        if level == "full":
            continue
        full = kc_m[(kc_m["model"] == model) & (kc_m["level"] == "full") & (kc_m["seed"] == 42)]
        merged = g.merge(full[["kc_id", "ECE", "REL"]], on="kc_id", suffixes=("", "_full"))
        d_ece = merged["ECE"] - merged["ECE_full"]
        d_rel = merged["REL"] - merged["REL_full"]
        def boot_ci(vals):
            vals = np.asarray(vals, dtype=float)
            means = [vals[rng.integers(0, len(vals), len(vals))].mean() for _ in range(N_BOOT)]
            lo, hi = np.quantile(means, [0.025, 0.975])
            return float(vals.mean()), float(lo), float(hi)
        e_m, e_lo, e_hi = boot_ci(d_ece)
        r_m, r_lo, r_hi = boot_ci(d_rel)
        stats.append(
            dict(
                dataset=DS, model=model, level=level, n_kcs=int(len(merged)),
                delta_ECE_mean=e_m, delta_ECE_ci95_lo=e_lo, delta_ECE_ci95_hi=e_hi,
                delta_REL_mean=r_m, delta_REL_ci95_lo=r_lo, delta_REL_ci95_hi=r_hi,
                frac_kcs_ece_worse=float((d_ece > 0).mean()),
            )
        )
    pd.DataFrame(stats).to_csv(a9 / "statistical_summary.csv", index=False)
    print(pd.DataFrame(stats).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
