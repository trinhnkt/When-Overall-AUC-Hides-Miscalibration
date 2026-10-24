#!/usr/bin/env python3
"""A5: size-matched ECE and the fold-0 learner-cluster interval.

Primary rows are best_valid x chunk and no_history = 0. The registered
seed is 20261021. Fold 2 and fold 3 stay two rows of one learner partition.
The cluster interval is computed only for fold 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.p0_a5_dkt_assist import aligned_users, row_matched  # noqa: E402
from src.ece_uncertainty import (  # noqa: E402
    cluster_bootstrap_diff,
    ece,
    ece0_bound,
    ece_equal_mass,
    ece_sweep,
    kumar_squared_ce,
    size_matched_contrast,
)

PLAN_SEED = 20261021
PRED = ROOT / "results" / "predictions"
OUT = ROOT / "results" / "A5_uncertainty_dkt_assist.csv"
SECONDARY = ROOT / "results" / "A5_secondary_dkt_assist.csv"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
COLUMNS = [
    "partition",
    "ECE_sparse",
    "ECE_dense",
    "DeltaECE",
    "DeltaECE_star",
    "matched_dense_median",
    "matched_gap",
    "matched_tail_probability",
    "cluster_CI_raw_low",
    "cluster_CI_raw_high",
    "cluster_CI_matched_low",
    "cluster_CI_matched_high",
    "ECE_sweep_sparse",
    "ECE_sweep_dense",
    "n_sparse_events",
    "n_dense_events",
    "n_sparse_learners",
    "n_sparse_kcs",
    "bootstrap_B",
    "matched_R",
    "invalid_bootstraps",
]


def load(fold: int, seed: int) -> pd.DataFrame:
    path = PRED / f"pred_assist2012_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz"
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    return pd.read_csv(path, usecols=["y", "p", "group", "no_history", "user_id", "kc_id"])


def one_partition(frame: pd.DataFrame, fold: int, rng: np.random.Generator) -> tuple[dict, dict]:
    kept = frame[frame["no_history"] == 0]
    sparse = kept[kept["group"] == "sparse"]
    dense = kept[kept["group"] == "dense"]
    sy = sparse["y"].to_numpy()
    sp = sparse["p"].to_numpy(dtype=float)
    dy = dense["y"].to_numpy()
    dp = dense["p"].to_numpy(dtype=float)
    ece_s = ece(sy, sp)
    ece_d = ece(dy, dp)
    delta = ece_s - ece_d
    _, user_s, user_d = aligned_users(frame)
    clusters = [pair for pair in user_d if len(pair[0])]
    matched = size_matched_contrast(sy, sp, clusters, rng, n_draws=2000)
    row_gap, row_rate, row_invalid = row_matched(sy, sp, dy, dp, rng, 2000)
    sweep_s, bins_s = ece_sweep(sy, sp)
    sweep_d, bins_d = ece_sweep(dy, dp)
    primary = {
        "partition": f"fold{fold}",
        "ECE_sparse": ece_s,
        "ECE_dense": ece_d,
        "DeltaECE": delta,
        "DeltaECE_star": delta - ece0_bound(len(sparse)),
        "matched_dense_median": matched["ece_dense_at_n_median"],
        "matched_gap": matched["size_matched_diff"],
        "matched_tail_probability": matched["exceedance_rate"],
        "cluster_CI_raw_low": np.nan,
        "cluster_CI_raw_high": np.nan,
        "cluster_CI_matched_low": np.nan,
        "cluster_CI_matched_high": np.nan,
        "ECE_sweep_sparse": sweep_s,
        "ECE_sweep_dense": sweep_d,
        "n_sparse_events": int(len(sparse)),
        "n_dense_events": int(len(dense)),
        "n_sparse_learners": int(sparse["user_id"].nunique()),
        "n_sparse_kcs": int(sparse["kc_id"].nunique()),
        "bootstrap_B": 0,
        "matched_R": 2000,
        "invalid_bootstraps": 0,
    }
    secondary = {
        "partition": f"fold{fold}",
        "row_matched_gap": row_gap,
        "row_matched_tail_probability": row_rate,
        "row_matched_invalid": row_invalid,
        "kumar_sparse": kumar_squared_ce(sy, sp),
        "kumar_dense": kumar_squared_ce(dy, dp),
        "ece_sweep_bins_sparse": bins_s,
        "ece_sweep_bins_dense": bins_d,
        "matched_draws_invalid": matched["n_invalid"],
    }
    for n_bins in (10, 15, 20):
        secondary[f"delta_equal_width_{n_bins}"] = ece(sy, sp, n_bins=n_bins) - ece(dy, dp, n_bins=n_bins)
        secondary[f"delta_equal_mass_{n_bins}"] = ece_equal_mass(sy, sp, n_bins) - ece_equal_mass(dy, dp, n_bins)
    if fold == 0:
        boot = cluster_bootstrap_diff(user_s, user_d, rng, n_boot=2000, n_inner=200)
        primary["cluster_CI_raw_low"] = boot["raw_ci95_low"]
        primary["cluster_CI_raw_high"] = boot["raw_ci95_high"]
        primary["cluster_CI_matched_low"] = boot["ci95_low"]
        primary["cluster_CI_matched_high"] = boot["ci95_high"]
        primary["bootstrap_B"] = 2000
        primary["invalid_bootstraps"] = int(boot["n_empty_sparse"])
        secondary["bootstrap_excluded"] = int(boot["n_empty_or_invalid"])
        secondary["bootstrap_empty_sparse"] = int(boot["n_empty_sparse"])
        secondary["bootstrap_matched_used"] = int(boot["n_used"])
    return primary, secondary


def build(seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    primary_rows, secondary_rows = [], []
    for fold, init_seed in PAIRS:
        print(f"PARTITION fold{fold} seed={init_seed}", flush=True)
        primary, secondary = one_partition(load(fold, init_seed), fold, rng)
        primary_rows.append(primary)
        secondary_rows.append(secondary)
        print(
            f"  DeltaECE={primary['DeltaECE']:.4f} matched_gap={primary['matched_gap']:.4f}",
            flush=True,
        )
    return pd.DataFrame(primary_rows, columns=COLUMNS), pd.DataFrame(secondary_rows)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"seed {PLAN_SEED}", flush=True)
    primary, secondary = build(PLAN_SEED)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    primary.to_csv(OUT, index=False)
    secondary.to_csv(SECONDARY, index=False)
    print(f"WROTE {OUT}", flush=True)
    print(f"WROTE {SECONDARY}", flush=True)


if __name__ == "__main__":
    main()
