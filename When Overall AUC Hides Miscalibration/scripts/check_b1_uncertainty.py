#!/usr/bin/env python3
"""B1: same A5 estimand for T-KT-c on ASSISTments.

Primary rows are best_valid x chunk and no_history = 0. Seed 20261021.
Fold 2 and fold 3 stay two rows of one learner partition.
The cluster interval is computed only for fold 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_a5_uncertainty import COLUMNS, one_partition  # noqa: E402

PLAN_SEED = 20261021
PRED = ROOT / "results" / "predictions"
OUT = ROOT / "results" / "B1_tktc_uncertainty.csv"
SECONDARY = ROOT / "results" / "B1_tktc_secondary.csv"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))


def load(fold: int, seed: int) -> pd.DataFrame:
    path = PRED / f"pred_assist2012_tktc_best_validxchunk_fold{fold}_{seed}.csv.gz"
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    return pd.read_csv(path, usecols=["y", "p", "group", "no_history", "user_id", "kc_id"])


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


def build(seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    primary_rows, secondary_rows = [], []
    for fold, init_seed in PAIRS:
        print(f"PARTITION fold{fold} seed={init_seed}", flush=True)
        primary, secondary = one_partition(load(fold, init_seed), fold, rng)
        primary_rows.append(primary)
        secondary_rows.append(secondary)
        print(
            f"  DeltaECE={primary['DeltaECE']:.4f} matched_gap={primary['matched_gap']:.4f} "
            f"DeltaECE_star={primary['DeltaECE_star']:.4f}",
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
    for column in ("DeltaECE", "DeltaECE_star", "matched_gap", "ECE_sparse", "ECE_dense"):
        mean, sd = four_partition(primary, column)
        print(f"FOUR {column} mean={mean:.6f} sd={sd:.6f}", flush=True)
    print(f"WROTE {OUT}", flush=True)
    print(f"WROTE {SECONDARY}", flush=True)


if __name__ == "__main__":
    main()
