#!/usr/bin/env python3
"""C3: medium-minus-dense uncertainty for official simpleKT on Junyi.

Same functions as the Junyi DKT check. The focal group is medium.
Seed 20261021. The cluster interval is fold 0 only. Fold 2 and fold 3
stay two rows of one learner partition. Archived DKT 0.0389/0.2513 is
not a simpleKT result and is not replaced.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_a5_uncertainty import COLUMNS, one_partition  # noqa: E402
from scripts.check_b2_junyi import (  # noqa: E402
    RENAME,
    SECONDARY_RENAME,
    four_partition,
)

PLAN_SEED = 20261021
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
OUT = ROOT / "results" / "C3_junyi_simplekt_uncertainty.csv"
SECONDARY = ROOT / "results" / "C3_junyi_simplekt_secondary.csv"


def load(fold: int, seed: int) -> pd.DataFrame:
    path = (
        ROOT
        / "results"
        / "predictions"
        / f"pred_junyi_simplekt_best_validxchunk_fold{fold}_{seed}.csv.gz"
    )
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    frame = pd.read_csv(path, usecols=["y", "p", "group", "no_history", "user_id", "kc_id"])
    frame["group"] = frame["group"].replace({"medium": "sparse"})
    return frame


def files_ok() -> None:
    manifest = pd.read_csv(ROOT / "runs" / "manifest.csv", dtype=str)
    for fold, seed in PAIRS:
        log_path = (
            ROOT
            / "runs"
            / "c3_simplekt_junyi"
            / f"junyi_fold{fold}_seed{seed}_best_valid"
            / "train_log.csv"
        )
        ckpt = log_path.with_name("model.pt")
        if not log_path.is_file() or not ckpt.is_file():
            raise SystemExit(f"MISSING log or checkpoint fold {fold}")
        log = pd.read_csv(log_path)
        selected = int(log.loc[log["valid_auc"].idxmax(), "epoch"])
        row = manifest[
            (manifest["dataset"] == "junyi")
            & (manifest["model"] == "simplekt")
            & (manifest["protocol"] == "best_validxchunk")
            & (manifest["partition_id"] == f"fold{fold}")
            & (manifest["init_seed"] == str(seed))
        ]
        if row.empty or int(float(row.iloc[-1]["selected_epoch"])) != selected:
            raise SystemExit(f"manifest epoch mismatch fold {fold}")
        print(f"fold{fold} selected_epoch={selected} log_rows={len(log)}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    files_ok()
    rng = np.random.default_rng(PLAN_SEED)
    primary_rows, secondary_rows = [], []
    print(f"seed {PLAN_SEED}", flush=True)
    print("contrast medium-dense", flush=True)
    for fold, seed in PAIRS:
        print(f"PARTITION fold{fold} seed={seed}", flush=True)
        primary, secondary = one_partition(load(fold, seed), fold, rng)
        primary_rows.append(primary)
        secondary_rows.append(secondary)
        print(
            f"  DeltaECE={primary['DeltaECE']:.4f} matched_gap={primary['matched_gap']:.4f} "
            f"DeltaECE_star={primary['DeltaECE_star']:.4f}",
            flush=True,
        )
    primary = pd.DataFrame(primary_rows, columns=COLUMNS).rename(columns=RENAME)
    secondary = pd.DataFrame(secondary_rows).rename(columns=SECONDARY_RENAME)
    primary.to_csv(OUT, index=False)
    secondary.to_csv(SECONDARY, index=False)
    for column in ("DeltaECE", "DeltaECE_star", "matched_gap", "ECE_medium", "ECE_dense"):
        mean, sd = four_partition(primary, column)
        print(f"FOUR {column} mean={mean:.6f} sd={sd:.6f}", flush=True)
    print(f"WROTE {OUT}", flush=True)
    print(f"WROTE {SECONDARY}", flush=True)
    print("C3_FILES = PASS", flush=True)


if __name__ == "__main__":
    main()
