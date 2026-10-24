#!/usr/bin/env python3
"""A4 gate: UT-C1, then the ASSISTments DKT checkpoint by context table.

Does not train. Missing prediction files make A4 fail. Fold 2 and fold 3
share one learner partition and are not two inferential samples.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.calibration_eval import compute_ece  # noqa: E402
from src.ece_uncertainty import ece0_bound  # noqa: E402
from tests.test_protocol_v2 import (  # noqa: E402
    test_ut_c1_best_valid_restores_max_validation_epoch,
)

PRED_DIR = ROOT / "results" / "predictions"
MANIFEST = ROOT / "runs" / "manifest.csv"
OUT = ROOT / "results" / "A4_dkt_2x2.csv"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
CELLS = (
    ("final", "full"),
    ("final", "chunk"),
    ("best_valid", "full"),
    ("best_valid", "chunk"),
    ("best_valid", "slide"),
)
UNIQUE = {0: "P0", 1: "P1", 2: "P2", 3: "P2", 4: "P4"}
LOG_COLUMNS = ["epoch", "train_loss", "valid_auc", "valid_nll", "valid_ece"]
OUT_COLUMNS = [
    "partition",
    "init_seed",
    "select_rule",
    "eval_context",
    "selected_epoch",
    "auc",
    "acc",
    "ece_dense",
    "ece_sparse",
    "delta_ece",
    "delta_ece_star",
    "n_dense",
    "n_sparse",
    "n_no_history",
]


def pred_path(select: str, mode: str, fold: int, seed: int) -> Path:
    return PRED_DIR / f"pred_assist2012_dkt_{select}x{mode}_fold{fold}_{seed}.csv.gz"


def log_path(fold: int, seed: int, select: str) -> Path:
    return ROOT / "runs" / "a_dkt" / f"assist2012_fold{fold}_seed{seed}_{select}" / "train_log.csv"


def epoch_from_log(path: Path, select: str) -> int:
    log = pd.read_csv(path)
    if list(log.columns) != LOG_COLUMNS:
        raise SystemExit(f"train log columns {list(log.columns)} != {LOG_COLUMNS}: {path}")
    if select == "final":
        return int(log["epoch"].iloc[-1])
    return int(log["epoch"].iloc[int(np.argmax(log["valid_auc"].to_numpy()))])


def manifest_epoch(manifest: pd.DataFrame, fold: int, seed: int, select: str, mode: str) -> int:
    protocol = f"{select}x{mode}"
    seed_ok = pd.to_numeric(manifest["init_seed"], errors="coerce") == seed
    hit = manifest[
        (manifest["model"] == "dkt")
        & (manifest["partition_id"] == f"fold{fold}")
        & seed_ok
        & (manifest["protocol"] == protocol)
        & (manifest["status"] == "OK")
    ]
    if len(hit) != 1:
        raise SystemExit(f"manifest rows for {protocol} fold{fold} seed {seed}: {len(hit)}")
    return int(float(hit["selected_epoch"].iloc[0]))


def metrics(path: Path) -> dict:
    frame = pd.read_csv(path, usecols=["y", "p", "group", "no_history"])
    primary = frame[frame["no_history"] == 0]
    y = primary["y"].to_numpy()
    p = primary["p"].to_numpy(dtype=float)
    dense = primary[primary["group"] == "dense"]
    sparse = primary[primary["group"] == "sparse"]
    ece_dense = float(compute_ece(dense["y"].to_numpy(), dense["p"].to_numpy(dtype=float))[0])
    ece_sparse = float(compute_ece(sparse["y"].to_numpy(), sparse["p"].to_numpy(dtype=float))[0])
    delta = ece_sparse - ece_dense
    n_sparse = int(len(sparse))
    return {
        "auc": float(roc_auc_score(y, p)),
        "acc": float(np.mean((p >= 0.5).astype(int) == y)),
        "ece_dense": ece_dense,
        "ece_sparse": ece_sparse,
        "delta_ece": float(delta),
        "delta_ece_star": float(delta - ece0_bound(n_sparse)),
        "n_dense": int(len(dense)),
        "n_sparse": n_sparse,
        "n_no_history": int((frame["no_history"] == 1).sum()),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        test_ut_c1_best_valid_restores_max_validation_epoch()
    except Exception as exc:
        print("UT-C1 = FAIL")
        print(exc)
        raise SystemExit(1)
    print("UT-C1 = PASS")

    missing = [
        pred_path(select, mode, fold, seed)
        for fold, seed in PAIRS
        for select, mode in CELLS
        if not pred_path(select, mode, fold, seed).is_file()
    ]
    missing_logs = [
        log_path(fold, seed, select)
        for fold, seed in PAIRS
        for select in ("final", "best_valid")
        if not log_path(fold, seed, select).is_file()
    ]
    if missing or missing_logs:
        print("A4 = FAIL")
        for path in missing + missing_logs:
            print(f"MISSING {path.relative_to(ROOT)}")
        raise SystemExit(1)

    manifest = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    if "selected_epoch" not in manifest.columns:
        print("A4 = FAIL")
        print("MISSING selected_epoch in runs/manifest.csv")
        raise SystemExit(1)

    rows = []
    for fold, seed in PAIRS:
        for select, mode in CELLS:
            logged = epoch_from_log(log_path(fold, seed, select), select)
            recorded = manifest_epoch(manifest, fold, seed, select, mode)
            if logged != recorded:
                print("A4 = FAIL")
                print(
                    f"selected_epoch mismatch fold{fold} seed {seed} {select}x{mode}: "
                    f"log {logged} manifest {recorded}"
                )
                raise SystemExit(1)
            row = {
                "partition": f"fold{fold}",
                "init_seed": seed,
                "select_rule": select,
                "eval_context": mode,
                "selected_epoch": logged,
                "unique_partition": UNIQUE[fold],
            }
            row.update(metrics(pred_path(select, mode, fold, seed)))
            rows.append(row)

    table = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.loc[:, OUT_COLUMNS].to_csv(OUT, index=False)

    primary = table[(table["select_rule"] == "best_valid") & (table["eval_context"] == "chunk")]
    collapsed = (
        primary.groupby("unique_partition", sort=True)[["delta_ece", "delta_ece_star", "auc", "ece_dense", "ece_sparse"]]
        .mean()
    )
    print(f"rows {len(table)}")
    print(f"unique_partitions {sorted(primary['unique_partition'].unique())}")
    print("primary_cell best_valid x chunk")
    print(
        "four_partition_mean_delta_ece "
        f"{float(collapsed['delta_ece'].mean()):.6f} "
        f"sd {float(collapsed['delta_ece'].std(ddof=1)):.6f}"
    )
    print("fold2 and fold3 are one learner partition (P2) and were averaged before that SD")
    print("A4 = PASS")


if __name__ == "__main__":
    main()
