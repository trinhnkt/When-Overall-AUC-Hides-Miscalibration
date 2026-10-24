#!/usr/bin/env python3
"""Fig. 2: 2x2 reliability diagrams (DKT/T-KT x ASSISTments/Junyi), seed 42."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRED = ROOT / "results" / "predictions"
STRATA = ROOT / "results" / "tables" / "kc_strata.csv"
OUT = HERE / "fig2_reliability_p0.png"

SPECS = [
    ("assist2012", "dkt", "ASSISTments 2012 / DKT"),
    ("assist2012", "simplekt", "ASSISTments 2012 / T-KT"),
    ("junyi", "dkt", "Junyi / DKT"),
    ("junyi", "simplekt", "Junyi / T-KT"),
]


def bucket(f: float, dataset: str) -> str | None:
    if pd.isna(f):
        return None
    if f >= 500:
        return "dense"
    if 100 <= f < 500:
        return "medium"
    if 20 <= f < 100:
        return "sparse"
    return None


def reliability(y: np.ndarray, p: np.ndarray, m: int = 15):
    edges = np.linspace(0.0, 1.0, m + 1)
    conf = acc = n = []
    conf, acc, n = [], [], []
    for i in range(m):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi) if i < m - 1 else (p >= lo) & (p <= hi)
        if not mask.any():
            continue
        conf.append(float(p[mask].mean()))
        acc.append(float(y[mask].mean()))
        n.append(int(mask.sum()))
    return np.array(conf), np.array(acc), np.array(n)


def ece(y: np.ndarray, p: np.ndarray, m: int = 15) -> float:
    edges = np.linspace(0.0, 1.0, m + 1)
    tot = 0.0
    n = len(y)
    for i in range(m):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi) if i < m - 1 else (p >= lo) & (p <= hi)
        if not mask.any():
            continue
        tot += (mask.sum() / n) * abs(y[mask].mean() - p[mask].mean())
    return tot


def main() -> None:
    strata = pd.read_csv(STRATA)
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4), sharex=True, sharey=True)
    axes = axes.ravel()
    colors = {"dense": "#1f4e79", "medium": "#2e7d32", "sparse": "#c0392b"}
    for ax, (ds, model, title) in zip(axes, SPECS):
        pred_path = PRED / f"{ds}_learner_based_{model}_seed42_predictions_rerun.csv"
        pred = pd.read_csv(pred_path, usecols=["kc_id", "y_true", "p_pred"])
        pred["kc_id"] = pred["kc_id"].astype(str)
        st = strata[(strata["dataset"] == ds) & (strata["split"] == "learner_based")]
        if "fold" in st.columns:
            st = st[st["fold"] == 0]
        freq_col = "train_freq" if "train_freq" in st.columns else "f_train"
        st = st[["kc_id", freq_col]].drop_duplicates("kc_id")
        st["kc_id"] = st["kc_id"].astype(str)
        merged = pred.merge(st, on="kc_id", how="left")
        merged["bucket"] = merged[freq_col].map(lambda x: bucket(x, ds))
        want = ("dense", "sparse") if ds == "assist2012" else ("dense", "medium")
        ax.plot([0, 1], [0, 1], ls="--", c="0.55", lw=0.8)
        for b in want:
            sub = merged[merged["bucket"] == b]
            if sub.empty:
                continue
            y = sub["y_true"].to_numpy(float)
            p = sub["p_pred"].to_numpy(float)
            c, a, _ = reliability(y, p)
            ax.plot(
                c,
                a,
                marker="o",
                ms=3,
                lw=1.1,
                color=colors[b],
                label=f"{b} ECE={ece(y, p):.3f} N={len(y):,}",
            )
        ax.set_title(title, fontsize=8)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6, loc="upper left", frameon=False)
        ax.grid(alpha=0.25, lw=0.4)
    axes[2].set_xlabel("Confidence", fontsize=8)
    axes[3].set_xlabel("Confidence", fontsize=8)
    axes[0].set_ylabel("Accuracy", fontsize=8)
    axes[2].set_ylabel("Accuracy", fontsize=8)
    fig.suptitle(
        "Reliability by train-only stratum (seed 42, 15 equal-width bins)",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(OUT, dpi=300)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
