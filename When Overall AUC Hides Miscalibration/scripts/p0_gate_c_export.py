#!/usr/bin/env python3
"""Gate C export. Reads prediction files. Does not edit published result tables.

The random stream matches scripts/check_a5_uncertainty.py: seed 20261021,
size-matched learner draws, then event-level draws, then the fold-0
cluster bootstrap. Fold 2 and fold 3 stay one learner partition.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_a5_uncertainty import row_matched  # noqa: E402
from scripts.p0_a5_dkt_assist import aligned_users  # noqa: E402
from src.ece_uncertainty import (  # noqa: E402
    cluster_bootstrap_diff,
    ece,
    ece0_bound,
    ece_equal_mass,
    size_matched_contrast,
)

PLAN_SEED = 20261021
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
PARTITION = {0: "P0", 1: "P1", 2: "P2", 3: "P2", 4: "P4"}
OUT = ROOT / "P0_IJIET_FINAL_CORRECTION_2026"
PRED = ROOT / "results" / "predictions"

JOBS = (
    {
        "dataset": "assist2012",
        "model": "dkt",
        "focal": "sparse",
        "file": "pred_assist2012_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz",
        "published": ROOT / "results" / "A5_uncertainty_dkt_assist.csv",
        "published_secondary": ROOT / "results" / "A5_secondary_dkt_assist.csv",
        "role": "PRIMARY",
    },
    {
        "dataset": "assist2012",
        "model": "tktc",
        "focal": "sparse",
        "file": "pred_assist2012_tktc_best_validxchunk_fold{fold}_{seed}.csv.gz",
        "published": ROOT / "results" / "B1_tktc_uncertainty.csv",
        "published_secondary": ROOT / "results" / "B1_tktc_secondary.csv",
        "role": "PRIMARY",
    },
    {
        "dataset": "junyi",
        "model": "dkt",
        "focal": "medium",
        "file": "pred_junyi_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz",
        "published": ROOT / "results" / "B2_junyi_dkt_uncertainty.csv",
        "published_secondary": ROOT / "results" / "B2_junyi_dkt_secondary.csv",
        "role": "POSTHOC",
    },
)


def load_frame(job: dict, fold: int, seed: int) -> tuple[pd.DataFrame, str]:
    path = PRED / job["file"].format(fold=fold, seed=seed)
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    frame = pd.read_csv(path, usecols=["y", "p", "group", "no_history", "user_id", "kc_id"])
    if job["focal"] == "medium":
        frame["group"] = frame["group"].replace({"medium": "sparse"})
    return frame, str(path.relative_to(ROOT)).replace("\\", "/")


def overall_scores(frame: pd.DataFrame) -> dict:
    kept = frame[frame["no_history"] == 0]
    y = kept["y"].to_numpy()
    p = np.clip(kept["p"].to_numpy(dtype=float), 1e-6, 1 - 1e-6)
    return {
        "AUC": float(roc_auc_score(y, p)),
        "ACC": float(accuracy_score(y, (p >= 0.5).astype(int))),
        "Brier": float(np.mean((kept["p"].to_numpy(dtype=float) - y) ** 2)),
        "NLL": float(log_loss(y, p, labels=[0, 1])),
        "FAR": np.nan,
    }


def counts(frame: pd.DataFrame, group: str) -> dict:
    part = frame[(frame["no_history"] == 0) & (frame["group"] == group)]
    return {
        "n": int(len(part)),
        "kcs": int(part["kc_id"].nunique()) if len(part) else 0,
        "learners": int(part["user_id"].nunique()) if len(part) else 0,
    }


def bin_rows(frame: pd.DataFrame, dataset: str, model: str, fold: int) -> list[dict]:
    kept = frame[frame["no_history"] == 0]
    focal = kept[kept["group"] == "sparse"]
    dense = kept[kept["group"] == "dense"]
    sy, sp = focal["y"].to_numpy(), focal["p"].to_numpy(dtype=float)
    dy, dp = dense["y"].to_numpy(), dense["p"].to_numpy(dtype=float)
    rows = []
    for n_bins in (10, 15, 20):
        for scheme, fn in (
            ("equal-width", lambda yy, pp, m: ece(yy, pp, n_bins=m)),
            ("equal-mass", lambda yy, pp, m: ece_equal_mass(yy, pp, m)),
        ):
            delta = fn(sy, sp, n_bins) - fn(dy, dp, n_bins)
            if delta > 0:
                sign = "positive"
            elif delta < 0:
                sign = "negative"
            else:
                sign = "null"
            rows.append({
                "dataset": dataset,
                "model": model,
                "partition": f"fold{fold}",
                "unique_partition": PARTITION[fold],
                "M": n_bins,
                "scheme": scheme,
                "DeltaECE": delta,
                "sign": sign,
                "primary": int(n_bins == 15 and scheme == "equal-width"),
            })
    return rows


def replay(job: dict):
    rng = np.random.default_rng(PLAN_SEED)
    detail_rows = []
    draw_rows = []
    boot_rows = []
    binning = []
    checks = []
    for fold, seed in PAIRS:
        frame, source = load_frame(job, fold, seed)
        print(f"{job['dataset']} {job['model']} fold{fold}", flush=True)
        focal = counts(frame, "sparse")
        dense = counts(frame, "dense")
        scores = overall_scores(frame)
        draws = []
        kept = frame[frame["no_history"] == 0]
        sparse = kept[kept["group"] == "sparse"]
        dense_rows = kept[kept["group"] == "dense"]
        sy = sparse["y"].to_numpy()
        sp = sparse["p"].to_numpy(dtype=float)
        dy = dense_rows["y"].to_numpy()
        dp = dense_rows["p"].to_numpy(dtype=float)
        _, user_s, user_d = aligned_users(frame)
        clusters = [pair for pair in user_d if len(pair[0])]
        matched = size_matched_contrast(sy, sp, clusters, rng, n_draws=2000, draw_store=draws)
        row_matched(sy, sp, dy, dp, rng, 2000)
        ece_s = ece(sy, sp)
        ece_d = ece(dy, dp)
        delta = ece_s - ece_d
        ece0 = ece0_bound(len(sparse))
        ci_lo = ci_hi = np.nan
        if fold == 0:
            replicates = []
            boot = cluster_bootstrap_diff(
                user_s, user_d, rng, n_boot=2000, n_inner=200, replicate_store=replicates
            )
            ci_lo = boot["ci95_low"]
            ci_hi = boot["ci95_high"]
            for record in replicates:
                boot_rows.append({
                    "dataset": job["dataset"],
                    "model": job["model"],
                    "partition": "fold0",
                    "unique_partition": "P0",
                    "init_seed": seed,
                    "unit": "learner",
                    "B": 2000,
                    "inner_R": 200,
                    "rng_seed": PLAN_SEED,
                    **record,
                })
            checks.append(("ci_low", ci_lo))
            checks.append(("ci_high", ci_hi))
        for draw_id, value in enumerate(draws):
            draw_rows.append({
                "dataset": job["dataset"],
                "model": job["model"],
                "partition": f"fold{fold}",
                "unique_partition": PARTITION[fold],
                "init_seed": seed,
                "draw_id": draw_id,
                "ece_dense_at_n": value,
                "rng_seed": PLAN_SEED,
                "learner_sampling": "without_replacement",
                "row_sampling": "without_replacement",
                "n_target": int(len(sparse)),
            })
        detail_rows.append({
            "dataset": job["dataset"],
            "model": job["model"],
            "role": job["role"],
            "partition": f"fold{fold}",
            "unique_partition": PARTITION[fold],
            "init_seed": seed,
            "focal_group": job["focal"],
            "N_focal": focal["n"],
            "N_dense": dense["n"],
            "n_focal_KCs": focal["kcs"],
            "n_dense_KCs": dense["kcs"],
            "n_focal_learners": focal["learners"],
            "n_dense_learners": dense["learners"],
            "ECE_focal": ece_s,
            "ECE_dense": ece_d,
            "DeltaECE": delta,
            "ECE0": ece0,
            "DeltaECE_star": delta - ece0,
            "matched_gap": matched["size_matched_diff"],
            "matched_dense_median": matched["ece_dense_at_n_median"],
            "CI95_low": ci_lo,
            "CI95_high": ci_hi,
            "source_prediction_file": source,
            **scores,
        })
        binning.extend(bin_rows(frame, job["dataset"], job["model"], fold))
        print(
            f"  DeltaECE={delta:.6f} star={delta - ece0:.6f} gap={matched['size_matched_diff']:.6f}",
            flush=True,
        )
    return detail_rows, draw_rows, boot_rows, binning


def four_units(detail: pd.DataFrame, column: str) -> np.ndarray:
    values = detail.set_index("partition")[column]
    return np.array([
        values["fold0"],
        values["fold1"],
        0.5 * (values["fold2"] + values["fold3"]),
        values["fold4"],
    ], dtype=float)


def unique_rows(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, model), block in detail.groupby(["dataset", "model"], sort=False):
        for partition in ("P0", "P1", "P2", "P4"):
            sub = block[block["unique_partition"] == partition]
            focal_n = sub["N_focal"].to_numpy()
            dense_n = sub["N_dense"].to_numpy()
            if len(set(focal_n.tolist())) != 1 or len(set(dense_n.tolist())) != 1:
                raise SystemExit(f"{dataset} {model} {partition} has unequal N across seeds")
            for column in ("n_focal_KCs", "n_dense_KCs", "n_focal_learners", "n_dense_learners"):
                if sub[column].nunique() != 1:
                    raise SystemExit(f"{dataset} {model} {partition} {column} differs across seeds")
            ci = sub.loc[sub["partition"] == "fold0"]
            rows.append({
                "dataset": dataset,
                "model": model,
                "role": sub["role"].iloc[0],
                "partition_id": partition,
                "folds": ",".join(sub["partition"].tolist()),
                "init_seeds": ",".join(str(int(v)) for v in sub["init_seed"]),
                "focal_group": sub["focal_group"].iloc[0],
                "N_sparse": int(focal_n[0]),
                "N_dense": int(dense_n[0]),
                "n_sparse_KCs": int(sub["n_focal_KCs"].iloc[0]) if len(sub) == 1 else int(sub["n_focal_KCs"].mean()),
                "n_dense_KCs": int(sub["n_dense_KCs"].iloc[0]) if len(sub) == 1 else int(round(sub["n_dense_KCs"].mean())),
                "n_sparse_learners": int(sub["n_focal_learners"].iloc[0]),
                "n_dense_learners": int(sub["n_dense_learners"].iloc[0]),
                "ECE_sparse": float(sub["ECE_focal"].mean()),
                "ECE_dense": float(sub["ECE_dense"].mean()),
                "DeltaECE": float(sub["DeltaECE"].mean()),
                "ECE0_exact_for_partition": float(sub["ECE0"].iloc[0]),
                "DeltaECE_star": float(sub["DeltaECE_star"].mean()),
                "matched_gap": float(sub["matched_gap"].mean()),
                "CI95_low": float(ci["CI95_low"].iloc[0]) if len(ci) else np.nan,
                "CI95_high": float(ci["CI95_high"].iloc[0]) if len(ci) else np.nan,
                "AUC": float(sub["AUC"].mean()),
                "ACC": float(sub["ACC"].mean()),
                "Brier": float(sub["Brier"].mean()),
                "NLL": float(sub["NLL"].mean()),
                "FAR": np.nan,
                "n_seeds": int(len(sub)),
            })
    return pd.DataFrame(rows)


def compare_published(detail: pd.DataFrame, job: dict) -> list[str]:
    published = pd.read_csv(job["published"])
    focal_ece = "ECE_medium" if job["focal"] == "medium" else "ECE_sparse"
    focal_n = "n_medium_events" if job["focal"] == "medium" else "n_sparse_events"
    problems = []
    got = detail.set_index("partition")
    for _, row in published.iterrows():
        part = row["partition"]
        pairs = (
            ("ECE_focal", row[focal_ece]),
            ("ECE_dense", row["ECE_dense"]),
            ("DeltaECE", row["DeltaECE"]),
            ("DeltaECE_star", row["DeltaECE_star"]),
            ("matched_gap", row["matched_gap"]),
            ("N_focal", row[focal_n]),
        )
        for column, expected in pairs:
            value = float(got.loc[part, column])
            if abs(value - float(expected)) > 1e-10:
                problems.append(f"{job['model']} {part} {column} {value} != {expected}")
        if part == "fold0":
            for column, published_column in (
                ("CI95_low", "cluster_CI_matched_low"),
                ("CI95_high", "cluster_CI_matched_high"),
            ):
                value = float(got.loc[part, column])
                expected = float(row[published_column])
                if abs(value - expected) > 1e-10:
                    problems.append(f"{job['model']} {part} {column} {value} != {expected}")
    return problems


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    details, draws, boots, bins = [], [], [], []
    problems = []
    for job in JOBS:
        detail, draw, boot, binning = replay(job)
        frame = pd.DataFrame(detail)
        problems.extend(compare_published(frame, job))
        units = four_units(frame, "DeltaECE_star")
        print(
            f"FOUR {job['dataset']} {job['model']} DeltaECE_star "
            f"mean={units.mean():.10f} sd={units.std(ddof=1):.10f} round4={round(float(units.mean()), 4)}",
            flush=True,
        )
        details.extend(detail)
        draws.extend(draw)
        boots.extend(boot)
        bins.extend(binning)
    if problems:
        print("MISMATCH")
        for line in problems:
            print(line)
        raise SystemExit(1)
    detail = pd.DataFrame(details)
    unique = unique_rows(detail)
    result_dir = OUT / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    (OUT / "audit").mkdir(parents=True, exist_ok=True)
    detail.to_csv(result_dir / "C_partition_detail.csv", index=False)
    unique.to_csv(result_dir / "C_unique_partition_summary.csv", index=False)
    pd.DataFrame(draws).to_csv(result_dir / "C_size_match_draws.csv.gz", index=False)
    pd.DataFrame(boots).to_csv(result_dir / "C_bootstrap_replicates_fold0.csv.gz", index=False)
    pd.DataFrame(bins).to_csv(result_dir / "C_binning_sensitivity.csv", index=False)
    junyi = detail[(detail["dataset"] == "junyi") & (detail["model"] == "dkt")]
    trace = junyi.rename(columns={
        "N_focal": "N_medium",
        "ECE_focal": "ECE_medium",
    })[[
        "partition",
        "N_medium",
        "N_dense",
        "ECE_medium",
        "ECE_dense",
        "DeltaECE",
        "ECE0",
        "DeltaECE_star",
        "source_prediction_file",
    ]]
    trace.to_csv(OUT / "audit" / "JUNYI_DELTAECESTAR_TRACE.csv", index=False)
    units = four_units(junyi, "DeltaECE_star")
    delta_units = four_units(junyi, "DeltaECE")
    n_units = four_units(junyi, "N_focal")
    wrong_3706 = float(delta_units.mean() - 0.5 * np.sqrt(15 / 3706))
    wrong_mean_n = float(delta_units.mean() - 0.5 * np.sqrt(15 / n_units.mean()))
    print(f"JUNYI star mean {units.mean():.10f} round4 {round(float(units.mean()), 4)}")
    print(f"JUNYI wrong bound on 3706 {wrong_3706:.10f}")
    print(f"JUNYI wrong bound on mean N {n_units.mean():.4f} -> {wrong_mean_n:.10f}")
    print("GATE_C_EXPORT = PASS")


if __name__ == "__main__":
    main()
