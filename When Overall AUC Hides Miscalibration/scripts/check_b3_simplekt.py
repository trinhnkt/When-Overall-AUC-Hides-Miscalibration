#!/usr/bin/env python3
"""B3 gate: logs, checkpoints, ban-I ECE comparison, and the A5 table.

The 0.005 comparison uses every scored row, matching
results/reports/p0_official_simplekt_assist_ece.json.
The A5 table drops no_history = 1. Seed 20261021. Fold 0 only for the
cluster interval. Fold 2 and fold 3 stay one learner partition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_a5_uncertainty import COLUMNS, one_partition  # noqa: E402
from scripts.p0_official_simplekt_ece import four_part  # noqa: E402
from src.calibration_eval import compute_ece  # noqa: E402

PLAN_SEED = 20261021
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
ARCHIVED = ROOT / "results" / "reports" / "p0_official_simplekt_assist_ece.json"
OUT = ROOT / "results" / "B3_simplekt_uncertainty.csv"
SECONDARY = ROOT / "results" / "B3_simplekt_secondary.csv"
TOLERANCE = 0.005


def new_frame(fold: int, seed: int) -> pd.DataFrame:
    path = (
        ROOT
        / "results"
        / "predictions"
        / f"pred_assist2012_simplekt_best_validxchunk_fold{fold}_{seed}.csv.gz"
    )
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    return pd.read_csv(path)


def files_ok() -> None:
    manifest = pd.read_csv(ROOT / "runs" / "manifest.csv", dtype=str)
    for fold, seed in PAIRS:
        log_path = (
            ROOT
            / "runs"
            / "b3_simplekt"
            / f"assist2012_fold{fold}_seed{seed}_best_valid"
            / "train_log.csv"
        )
        ckpt = log_path.with_name("model.pt")
        if not log_path.is_file() or not ckpt.is_file():
            raise SystemExit(f"MISSING log or checkpoint fold {fold}")
        log = pd.read_csv(log_path)
        selected = int(log.loc[log["valid_auc"].idxmax(), "epoch"])
        row = manifest[
            (manifest["model"] == "simplekt")
            & (manifest["partition_id"] == f"fold{fold}")
            & (manifest["init_seed"] == str(seed))
        ]
        if row.empty or int(float(row.iloc[-1]["selected_epoch"])) != selected:
            raise SystemExit(f"manifest epoch mismatch fold {fold}")
        print(f"fold{fold} selected_epoch={selected} log_rows={len(log)}")


def archived_gap(frames: list[pd.DataFrame]) -> None:
    archived = json.loads(ARCHIVED.read_text(encoding="utf-8"))
    for stratum in ("dense", "sparse"):
        per_seed = []
        for frame in frames:
            sl = frame[frame["group"] == stratum]
            per_seed.append(float(compute_ece(sl["y"].to_numpy(), sl["p"].to_numpy(), n_bins=15)[0]))
        mean = four_part(per_seed)
        old = float(archived["strata"][stratum]["ece"])
        delta = mean - old
        print(
            f"ALL_ROWS {stratum} new={mean:.6f} archived={old:.6f} delta={delta:.6f}",
            flush=True,
        )
        for (fold, seed), value in zip(PAIRS, per_seed):
            old_seed = float(archived["strata"][stratum]["per_seed_ece"][str(seed)])
            print(
                f"  fold{fold} new={value:.6f} archived={old_seed:.6f} delta={value - old_seed:.6f}",
                flush=True,
            )
        if abs(delta) > TOLERANCE:
            print(f"B3_REPRO {stratum} DIFFERS", flush=True)
        else:
            print(f"B3_REPRO {stratum} WITHIN_0.005", flush=True)


def four_partition(frame: pd.DataFrame, column: str) -> tuple[float, float]:
    values = frame.set_index("partition")[column]
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


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    files_ok()
    frames = [new_frame(fold, seed) for fold, seed in PAIRS]
    archived_gap(frames)
    rng = np.random.default_rng(PLAN_SEED)
    primary_rows, secondary_rows = [], []
    print(f"seed {PLAN_SEED}", flush=True)
    for (fold, seed), frame in zip(PAIRS, frames):
        print(f"PARTITION fold{fold} seed={seed}", flush=True)
        kept = frame[["y", "p", "group", "no_history", "user_id", "kc_id"]]
        primary, secondary = one_partition(kept, fold, rng)
        primary_rows.append(primary)
        secondary_rows.append(secondary)
        print(
            f"  DeltaECE={primary['DeltaECE']:.4f} matched_gap={primary['matched_gap']:.4f} "
            f"DeltaECE_star={primary['DeltaECE_star']:.4f}",
            flush=True,
        )
    primary = pd.DataFrame(primary_rows, columns=COLUMNS)
    secondary = pd.DataFrame(secondary_rows)
    primary.to_csv(OUT, index=False)
    secondary.to_csv(SECONDARY, index=False)
    for column in ("DeltaECE", "DeltaECE_star", "matched_gap", "ECE_sparse", "ECE_dense"):
        mean, sd = four_partition(primary, column)
        print(f"FOUR {column} mean={mean:.6f} sd={sd:.6f}", flush=True)
    print(f"WROTE {OUT}", flush=True)
    print(f"WROTE {SECONDARY}", flush=True)
    print("B3_FILES = PASS", flush=True)


if __name__ == "__main__":
    main()
