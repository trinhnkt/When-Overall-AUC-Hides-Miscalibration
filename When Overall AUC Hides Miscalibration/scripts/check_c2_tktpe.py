#!/usr/bin/env python3
"""C2: compare the TKT_PE ablation with T-KT-c on the same fold.

ASSISTments fold 0, init seed 42, best_valid x chunk, no_history = 0.
TKT_PE is an ablation. It does not replace the T-KT-c table.
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
from src.ece_uncertainty import ece, ece0_bound  # noqa: E402

GROUPS = ("strict_cold_start", "very_sparse", "sparse", "medium", "dense")
OUT = ROOT / "results" / "C2_tktpe_vs_tktc_fold0.csv"
LOG = ROOT / "runs" / "c2_tktpe" / "assist2012_fold0_seed42_best_valid" / "train_log.csv"
MANIFEST = ROOT / "runs" / "manifest.csv"


def auc_of(y, p) -> float:
    y = np.asarray(y)
    if len(y) < 2 or len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, np.asarray(p, dtype=float)))


def load(model: str) -> pd.DataFrame:
    path = ROOT / "results" / "predictions" / prediction_name(
        "assist2012", model, "best_validxchunk", "fold0", 42
    )
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    return pd.read_csv(path, usecols=["y", "p", "group", "no_history", "user_id", "kc_id"])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    log = pd.read_csv(LOG)
    values = log["valid_auc"].to_numpy(dtype=float)
    idx = int(np.argmax(values))
    log_epoch = int(log.iloc[idx]["epoch"])
    table = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    rows = table[
        (table["model"] == "tkt_pe")
        & (table["partition_id"] == "fold0")
        & (table["init_seed"] == "42")
        & (table["status"] == "OK")
    ]
    if rows.empty:
        raise SystemExit("MISSING manifest row tkt_pe")
    recorded = int(rows.iloc[-1]["selected_epoch"])
    if recorded != log_epoch:
        raise SystemExit(f"selected_epoch {recorded} is not log epoch {log_epoch}")
    print(
        f"MODEL tkt_pe selected_epoch={recorded} valid_auc={float(values[idx]):.6f} "
        f"last_epoch={int(log.iloc[-1]['epoch'])}",
        flush=True,
    )

    frames = {"tkt_pe": load("tkt_pe"), "tktc": load("tktc")}
    out_rows = []
    for model, frame in frames.items():
        kept = frame[frame["no_history"] == 0]
        print(f"MODEL {model} rows={len(frame)} no_history={int((frame['no_history'] == 1).sum())}", flush=True)
        for group in GROUPS:
            part = kept[kept["group"] == group]
            y = part["y"].to_numpy()
            p = part["p"].to_numpy(dtype=float)
            value_auc = auc_of(y, p)
            value_ece = float("nan") if len(y) == 0 else ece(y, p)
            print(
                f"  {group} n={len(part)} auc={value_auc:.6f} ece={value_ece:.6f}",
                flush=True,
            )
            out_rows.append(
                {
                    "model": model,
                    "group": group,
                    "n": int(len(part)),
                    "auc": value_auc,
                    "ece": value_ece,
                }
            )
        sparse = kept[kept["group"] == "sparse"]
        dense = kept[kept["group"] == "dense"]
        delta = ece(sparse["y"], sparse["p"]) - ece(dense["y"], dense["p"])
        star = delta - ece0_bound(len(sparse))
        overall = auc_of(kept["y"], kept["p"])
        print(
            f"  overall_auc={overall:.6f} DeltaECE={delta:.6f} DeltaECE_star={star:.6f}",
            flush=True,
        )
        out_rows.append(
            {
                "model": model,
                "group": "contrast_sparse_minus_dense",
                "n": int(len(sparse)),
                "auc": overall,
                "ece": delta,
                "DeltaECE_star": star,
            }
        )
    pe_n = frames["tkt_pe"].groupby(["no_history", "group"]).size()
    tc_n = frames["tktc"].groupby(["no_history", "group"]).size()
    if not pe_n.equals(tc_n):
        raise SystemExit("group counts differ between TKT_PE and T-KT-c")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(out_rows).to_csv(OUT, index=False)
    print(f"WROTE {OUT}", flush=True)
    print("C2_FILES = PASS", flush=True)
    print("ablation only; T-KT-c numbers are unchanged", flush=True)


if __name__ == "__main__":
    main()
