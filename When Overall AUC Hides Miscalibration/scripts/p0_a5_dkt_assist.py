#!/usr/bin/env python3
"""A3–A5 tables for DKT on ASSISTments, read only from prediction files.

Does not train and does not edit the manuscript. Missing protocols are
skipped. The confidence interval is computed only for best_valid x chunk
on fold 0. Four learner partitions are summarized after averaging the two
initializations that share one split. They are not one pooled interval.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ece_uncertainty import (  # noqa: E402
    cluster_bootstrap_diff,
    ece,
    ece0_bound,
    ece_equal_mass,
    ece_sweep,
    kumar_squared_ce,
    rows_at_n,
    size_matched_contrast,
)

PLAN_SEED = 20261021
PRED_DIR = ROOT / "results" / "predictions"
OUT_DIR = ROOT / "results" / "tables"
PRIMARY = "best_validxchunk"
# fold 2 and fold 3 are one learner partition with two initializations.
PARTITION_OF_FOLD = {0: "P0", 1: "P1", 2: "P2", 3: "P2", 4: "P4"}


def _arrays(frame: pd.DataFrame, keep_no_history: bool):
    if keep_no_history:
        y = frame["y"].to_numpy()
        p = frame["p"].to_numpy(dtype=float)
        flag = frame["no_history"].to_numpy()
        p = np.where(flag == 1, 0.5, p)
        return y, p
    kept = frame[frame["no_history"] == 0]
    return kept["y"].to_numpy(), kept["p"].to_numpy(dtype=float)


def _group_frame(frame: pd.DataFrame, group: str, keep_no_history: bool) -> pd.DataFrame:
    part = frame[frame["group"] == group]
    if keep_no_history:
        return part
    return part[part["no_history"] == 0]


def metrics_for(frame: pd.DataFrame) -> dict:
    primary = frame[frame["no_history"] == 0]
    row = {
        "protocol": str(frame["protocol"].iloc[0]),
        "partition_id": str(frame["partition_id"].iloc[0]),
        "init_seed": int(frame["init_seed"].iloc[0]),
        "n_rows_file": int(len(frame)),
        "n_no_history": int((frame["no_history"] == 1).sum()),
    }
    fold = int(str(row["partition_id"]).replace("fold", ""))
    row["fold"] = fold
    row["unique_partition"] = PARTITION_OF_FOLD[fold]
    for group in ("dense", "medium", "sparse"):
        part = _group_frame(frame, group, keep_no_history=False)
        y, p = part["y"].to_numpy(), part["p"].to_numpy(dtype=float)
        row[f"n_{group}"] = int(len(part))
        row[f"n_users_{group}"] = int(part["user_id"].nunique()) if len(part) else 0
        row[f"n_kcs_{group}"] = int(part["kc_id"].nunique()) if len(part) else 0
        row[f"ece_{group}"] = ece(y, p) if len(part) else float("nan")
        dropped = frame[(frame["group"] == group) & (frame["no_history"] == 1)]
        row[f"n_dropped_{group}"] = int(len(dropped))
    row["delta_ece"] = row["ece_sparse"] - row["ece_dense"]
    row["ece0_sparse"] = ece0_bound(row["n_sparse"])
    row["delta_ece_star"] = row["delta_ece"] - row["ece0_sparse"]
    y_s, p_s = _arrays(_group_frame(frame, "sparse", True), True)
    y_d, p_d = _arrays(_group_frame(frame, "dense", True), True)
    row["ece_sparse_with_half"] = ece(y_s, p_s) if len(y_s) else float("nan")
    row["ece_dense_with_half"] = ece(y_d, p_d) if len(y_d) else float("nan")
    row["delta_ece_with_half"] = row["ece_sparse_with_half"] - row["ece_dense_with_half"]
    row["n_primary"] = int(len(primary))
    return row


def aligned_users(frame: pd.DataFrame):
    kept = frame[frame["no_history"] == 0]
    users = kept["user_id"].drop_duplicates().tolist()
    sparse, dense = [], []
    grouped = {uid: g for uid, g in kept.groupby("user_id", sort=False)}
    for uid in users:
        g = grouped[uid]
        def take(group):
            part = g[g["group"] == group]
            return part["y"].to_numpy(), part["p"].to_numpy(dtype=float)
        sparse.append(take("sparse"))
        dense.append(take("dense"))
    return users, sparse, dense


def row_matched(sparse_y, sparse_p, dense_y, dense_p, rng, n_draws, n_bins=15):
    n = len(sparse_y)
    ece_s = ece(sparse_y, sparse_p, n_bins=n_bins)
    draws = []
    invalid = 0
    for _ in range(n_draws):
        got = rows_at_n(dense_y, dense_p, n, rng)
        if got is None:
            invalid += 1
            continue
        draws.append(ece(got[0], got[1], n_bins=n_bins))
    if not draws:
        return float("nan"), float("nan"), invalid
    return float(ece_s - np.median(draws)), float(np.mean(np.asarray(draws) >= ece_s)), invalid


def uncertainty_row(frame: pd.DataFrame, rng, n_boot: int, n_inner: int, n_draws: int) -> dict:
    kept = frame[frame["no_history"] == 0]
    sparse = kept[kept["group"] == "sparse"]
    dense = kept[kept["group"] == "dense"]
    sy, sp = sparse["y"].to_numpy(), sparse["p"].to_numpy(dtype=float)
    dy, dp = dense["y"].to_numpy(), dense["p"].to_numpy(dtype=float)
    _, user_s, user_d = aligned_users(frame)
    clusters = [pair for pair in user_d if len(pair[0])]
    matched = size_matched_contrast(sy, sp, clusters, rng, n_draws=n_draws)
    row_gap, row_rate, row_invalid = row_matched(sy, sp, dy, dp, rng, n_draws)
    boot = cluster_bootstrap_diff(user_s, user_d, rng, n_boot=n_boot, n_inner=n_inner)
    sweep_s, bins_s = ece_sweep(sy, sp)
    sweep_d, bins_d = ece_sweep(dy, dp)
    sq_s = kumar_squared_ce(sy, sp)
    sq_d = kumar_squared_ce(dy, dp)
    sens = {}
    for n_bins in (10, 15, 20):
        sens[f"delta_ew_{n_bins}"] = ece(sy, sp, n_bins=n_bins) - ece(dy, dp, n_bins=n_bins)
        sens[f"delta_em_{n_bins}"] = ece_equal_mass(sy, sp, n_bins) - ece_equal_mass(dy, dp, n_bins)
    out = {
        "protocol": PRIMARY,
        "partition_id": str(frame["partition_id"].iloc[0]),
        "init_seed": int(frame["init_seed"].iloc[0]),
        "n_sparse": int(len(sparse)),
        "n_dense": int(len(dense)),
        "n_users_sparse": int(sparse["user_id"].nunique()),
        "n_kcs_sparse": int(sparse["kc_id"].nunique()),
        "ci_unstable_flag": int(sparse["user_id"].nunique() < 30),
        "delta_ece": float(ece(sy, sp) - ece(dy, dp)),
        "ece0_sparse": ece0_bound(len(sparse)),
        "delta_ece_star": float(ece(sy, sp) - ece(dy, dp) - ece0_bound(len(sparse))),
        "size_matched_diff": matched["size_matched_diff"],
        "ece_dense_at_n_median": matched["ece_dense_at_n_median"],
        "exceedance_rate": matched["exceedance_rate"],
        "n_draws": n_draws,
        "n_draws_invalid": matched["n_invalid"],
        "row_matched_diff": row_gap,
        "row_exceedance_rate": row_rate,
        "row_draws_invalid": row_invalid,
        "matched_ci95_low": boot["ci95_low"] if str(frame["partition_id"].iloc[0]) == "fold0" else float("nan"),
        "matched_ci95_high": boot["ci95_high"] if str(frame["partition_id"].iloc[0]) == "fold0" else float("nan"),
        "raw_ci95_low": boot["raw_ci95_low"] if str(frame["partition_id"].iloc[0]) == "fold0" else float("nan"),
        "raw_ci95_high": boot["raw_ci95_high"] if str(frame["partition_id"].iloc[0]) == "fold0" else float("nan"),
        "n_boot": n_boot if str(frame["partition_id"].iloc[0]) == "fold0" else 0,
        "n_inner": n_inner if str(frame["partition_id"].iloc[0]) == "fold0" else 0,
        "n_boot_empty_or_invalid": boot["n_empty_or_invalid"] if str(frame["partition_id"].iloc[0]) == "fold0" else 0,
        "ece_sweep_sparse": sweep_s,
        "ece_sweep_dense": sweep_d,
        "ece_sweep_bins_sparse": bins_s,
        "ece_sweep_bins_dense": bins_d,
        "delta_ece_sweep": sweep_s - sweep_d,
        "kumar_sq_sparse": sq_s,
        "kumar_sq_dense": sq_d,
        "delta_kumar_sq": sq_s - sq_d,
        "rng_seed": PLAN_SEED,
    }
    out.update(sens)
    if str(frame["partition_id"].iloc[0]) != "fold0":
        # Size-matched point estimates are required on every partition.
        # The interval stays on fold 0 only, so do not spend the bootstrap here.
        out["n_boot_empty_or_invalid"] = 0
    return out


def four_partition_summary(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for protocol, block in detail.groupby("protocol"):
        part_rows = []
        for partition, sub in block.groupby("unique_partition"):
            part_rows.append({
                "unique_partition": partition,
                "ece_dense": sub["ece_dense"].mean(),
                "ece_medium": sub["ece_medium"].mean(),
                "ece_sparse": sub["ece_sparse"].mean(),
                "delta_ece": sub["delta_ece"].mean(),
                "delta_ece_star": sub["delta_ece_star"].mean(),
                "n_sparse": sub["n_sparse"].mean(),
                "n_runs": len(sub),
            })
        parts = pd.DataFrame(part_rows)
        rows.append({
            "protocol": protocol,
            "n_unique_partitions": len(parts),
            "ece_dense_mean": parts["ece_dense"].mean(),
            "ece_dense_sd": parts["ece_dense"].std(ddof=1) if len(parts) > 1 else float("nan"),
            "ece_sparse_mean": parts["ece_sparse"].mean(),
            "ece_sparse_sd": parts["ece_sparse"].std(ddof=1) if len(parts) > 1 else float("nan"),
            "delta_ece_mean": parts["delta_ece"].mean(),
            "delta_ece_sd": parts["delta_ece"].std(ddof=1) if len(parts) > 1 else float("nan"),
            "delta_ece_star_mean": parts["delta_ece_star"].mean(),
            "n_sparse_mean": parts["n_sparse"].mean(),
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--n-inner", type=int, default=200)
    parser.add_argument("--n-draws", type=int, default=2000)
    parser.add_argument("--skip-uncertainty", action="store_true")
    args = parser.parse_args()
    files = sorted(PRED_DIR.glob("pred_assist2012_dkt_*x*_fold*_*.csv.gz"))
    if not files:
        raise SystemExit(f"no DKT protocol predictions in {PRED_DIR}")
    detail_rows = []
    frames = {}
    for path in files:
        frame = pd.read_csv(path)
        detail_rows.append(metrics_for(frame))
        frames[path.name] = frame
        print(f"READ {path.name} delta={detail_rows[-1]['delta_ece']:.4f}", flush=True)
    detail = pd.DataFrame(detail_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    detail_path = OUT_DIR / "p0_a3a4_dkt_by_run.csv"
    summary_path = OUT_DIR / "p0_a3a4_dkt_four_partition.csv"
    detail.to_csv(detail_path, index=False)
    four_partition_summary(detail).to_csv(summary_path, index=False)
    print(f"WROTE {detail_path}", flush=True)
    print(f"WROTE {summary_path}", flush=True)
    if args.skip_uncertainty:
        return
    primary = detail[detail["protocol"] == PRIMARY]
    if primary.empty:
        print("PRIMARY best_validxchunk not scored yet; uncertainty table skipped", flush=True)
        return
    rng = np.random.default_rng(PLAN_SEED)
    unc_rows = []
    for _, info in primary.iterrows():
        name = (
            f"pred_assist2012_dkt_{PRIMARY}_{info['partition_id']}_{int(info['init_seed'])}.csv.gz"
        )
        frame = frames[name]
        do_boot = info["partition_id"] == "fold0"
        print(f"UNCERTAINTY {name} boot={do_boot}", flush=True)
        # Non-fold-0 rows still need the size-matched point estimate.
        # cluster_bootstrap_diff is skipped by passing n_boot=0 only on fold 0's complement.
        if do_boot:
            unc_rows.append(uncertainty_row(frame, rng, args.n_boot, args.n_inner, args.n_draws))
        else:
            unc_rows.append(uncertainty_row(frame, rng, n_boot=1, n_inner=1, n_draws=args.n_draws))
            unc_rows[-1]["matched_ci95_low"] = float("nan")
            unc_rows[-1]["matched_ci95_high"] = float("nan")
            unc_rows[-1]["raw_ci95_low"] = float("nan")
            unc_rows[-1]["raw_ci95_high"] = float("nan")
            unc_rows[-1]["n_boot"] = 0
            unc_rows[-1]["n_inner"] = 0
            unc_rows[-1]["n_boot_empty_or_invalid"] = 0
    unc_path = OUT_DIR / "p0_a5_dkt_uncertainty.csv"
    pd.DataFrame(unc_rows).to_csv(unc_path, index=False)
    print(f"WROTE {unc_path}", flush=True)


if __name__ == "__main__":
    main()
