#!/usr/bin/env python3
"""C1: fold-5 identity, selected epochs, and group AUC/ECE.

One new ASSISTments learner partition. Init seed 42. Protocol
best_valid x chunk. Cluster bootstrap stays on fold 0 only.
Fold 2 and fold 3 remain one partition and are not averaged with fold 5.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.export_predictions import prediction_name  # noqa: E402
from scripts.p0_a5_dkt_assist import aligned_users  # noqa: E402
from src.ece_uncertainty import ece, ece0_bound, size_matched_contrast  # noqa: E402

PLAN_SEED = 20261021
GROUPS = ("strict_cold_start", "very_sparse", "sparse", "medium", "dense")
MODELS = ("dkt", "tktc", "simplekt")
LOGS = {
    "dkt": ROOT / "runs" / "c1_dkt" / "assist2012_fold5_seed42_best_valid" / "train_log.csv",
    "tktc": ROOT / "runs" / "b1_tktc" / "assist2012_fold5_seed42_best_valid" / "train_log.csv",
    "simplekt": ROOT / "runs" / "b3_simplekt" / "assist2012_fold5_seed42_best_valid" / "train_log.csv",
}
SPLIT = ROOT / "data" / "processed" / "assist2012" / "splits" / "learner_based"
MANIFEST = ROOT / "runs" / "manifest.csv"
OUT = ROOT / "results" / "C1_fold5_group_metrics.csv"


def test_users(fold: int) -> set:
    path = SPLIT / f"fold_{fold}" / "test.csv"
    return set(pd.read_csv(path, usecols=["user_id"])["user_id"])


def first_max_epoch(path: Path) -> tuple[int, float, int]:
    log = pd.read_csv(path)
    values = log["valid_auc"].to_numpy(dtype=float)
    idx = int(np.argmax(values))
    return int(log.iloc[idx]["epoch"]), float(values[idx]), int(log.iloc[-1]["epoch"])


def manifest_epoch(model: str) -> int:
    table = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    rows = table[
        (table["dataset"] == "assist2012")
        & (table["partition_id"] == "fold5")
        & (table["init_seed"] == "42")
        & (table["model"] == model)
        & (table["protocol"] == "best_validxchunk")
        & (table["status"] == "OK")
    ]
    if rows.empty:
        raise SystemExit(f"MISSING manifest row {model}")
    return int(rows.iloc[-1]["selected_epoch"])


def auc_of(y, p) -> float:
    y = np.asarray(y)
    if len(y) < 2 or len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, np.asarray(p, dtype=float)))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sets = {fold: test_users(fold) for fold in range(6)}
    if sets[2] != sets[3]:
        raise SystemExit("fold 2 and fold 3 test users differ")
    print("fold2_eq_fold3 = 1", flush=True)
    print(f"old fold identity [0, 1, 2, 2, 4] sizes {[len(sets[k]) for k in range(5)]}", flush=True)
    for fold in (0, 1, 2, 4):
        if sets[5] == sets[fold]:
            raise SystemExit(f"fold 5 test users equal fold {fold}")
        print(f"overlap fold{fold} {len(sets[5] & sets[fold])}", flush=True)
    print("C1_SPLIT = PASS", flush=True)

    rng = np.random.default_rng(PLAN_SEED)
    rows = []
    for model in MODELS:
        path = ROOT / "results" / "predictions" / prediction_name(
            "assist2012", model, "best_validxchunk", "fold5", 42
        )
        if not path.is_file():
            raise SystemExit(f"MISSING {path}")
        log_epoch, log_auc, last_epoch = first_max_epoch(LOGS[model])
        recorded = manifest_epoch(model)
        if recorded != log_epoch:
            raise SystemExit(f"{model} selected_epoch {recorded} is not log epoch {log_epoch}")
        frame = pd.read_csv(path)
        kept = frame[frame["no_history"] == 0]
        print(
            f"MODEL {model} rows={len(frame)} no_history={int((frame['no_history'] == 1).sum())} "
            f"selected_epoch={recorded} valid_auc={log_auc:.6f} last_epoch={last_epoch}",
            flush=True,
        )
        for group in GROUPS:
            part = kept[kept["group"] == group]
            y = part["y"].to_numpy()
            p = part["p"].to_numpy(dtype=float)
            value_auc = auc_of(y, p)
            value_ece = float("nan") if len(y) == 0 else ece(y, p)
            print(
                f"  {group} n={len(part)} learners={part['user_id'].nunique()} "
                f"kcs={part['kc_id'].nunique()} auc={value_auc:.6f} ece={value_ece:.6f}",
                flush=True,
            )
            rows.append(
                {
                    "model": model,
                    "group": group,
                    "n": int(len(part)),
                    "learners": int(part["user_id"].nunique()),
                    "kcs": int(part["kc_id"].nunique()),
                    "auc": value_auc,
                    "ece": value_ece,
                    "selected_epoch": recorded,
                    "valid_auc": log_auc,
                }
            )
        sparse = kept[kept["group"] == "sparse"]
        dense = kept[kept["group"] == "dense"]
        sy, sp = sparse["y"].to_numpy(), sparse["p"].to_numpy(dtype=float)
        dy, dp = dense["y"].to_numpy(), dense["p"].to_numpy(dtype=float)
        delta = ece(sy, sp) - ece(dy, dp)
        star = delta - ece0_bound(len(sparse))
        _, _, user_d = aligned_users(frame)
        clusters = [pair for pair in user_d if len(pair[0])]
        matched = size_matched_contrast(sy, sp, clusters, rng, n_draws=2000)
        overall = auc_of(kept["y"], kept["p"])
        print(
            f"  overall_auc={overall:.6f} DeltaECE={delta:.6f} DeltaECE_star={star:.6f} "
            f"matched_gap={matched['size_matched_diff']:.6f} "
            f"matched_dense_median={matched['ece_dense_at_n_median']:.6f} "
            f"tail={matched['exceedance_rate']:.6f} invalid={matched['n_invalid']}",
            flush=True,
        )
        rows.append(
            {
                "model": model,
                "group": "contrast_sparse_minus_dense",
                "n": int(len(sparse)),
                "learners": int(sparse["user_id"].nunique()),
                "kcs": int(sparse["kc_id"].nunique()),
                "auc": overall,
                "ece": delta,
                "selected_epoch": recorded,
                "valid_auc": log_auc,
                "DeltaECE_star": star,
                "matched_gap": matched["size_matched_diff"],
                "matched_dense_median": matched["ece_dense_at_n_median"],
                "matched_tail": matched["exceedance_rate"],
                "matched_invalid": matched["n_invalid"],
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"WROTE {OUT}", flush=True)
    print("C1_FILES = PASS", flush=True)


if __name__ == "__main__":
    main()
