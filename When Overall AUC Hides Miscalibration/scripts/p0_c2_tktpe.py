#!/usr/bin/env python3
"""C2 ablation: TKT_PE on ASSISTments fold 0, best_valid x chunk.

Learned positional embeddings of length 200. T-KT-c itself is unchanged.
"""
from __future__ import annotations

import subprocess
import sys
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.export_predictions import (  # noqa: E402
    append_manifest,
    prediction_name,
    sha256,
    write_prediction,
)
from src.baseline_runner import KTDataset, train_torch_model  # noqa: E402
from src.kc_strata import get_bucket  # noqa: E402
from src.protocol_v2 import TKTPE, collate_tktc, score_windowed  # noqa: E402

PLAN_COMMIT = "46e0208"


def code_commit() -> str:
    try:
        raw = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT.parent), text=True
        )
        return raw.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    fold, seed, epochs = 0, 42, 50
    dest = ROOT / "results" / "predictions" / prediction_name(
        "assist2012", "tkt_pe", "best_validxchunk", f"fold{fold}", seed
    )
    if dest.is_file():
        print(f"SKIP {dest.name}", flush=True)
        return
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    split = ROOT / "data" / "processed" / "assist2012" / "splits" / "learner_based" / f"fold_{fold}"
    train_df = pd.read_csv(split / "train.csv")
    valid_df = pd.read_csv(split / "valid.csv")
    test_df = pd.read_csv(split / "test.csv")
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    kc_map = {kc: i for i, kc in enumerate(all_kcs)}
    counts = train_df["kc_id"].value_counts().to_dict()
    n_kcs = len(all_kcs)
    run_dir = ROOT / "runs" / "c2_tktpe" / f"assist2012_fold{fold}_seed{seed}_best_valid"
    run_dir.mkdir(parents=True, exist_ok=True)
    ckpt = run_dir / "model.pt"
    log_path = run_dir / "train_log.csv"
    torch.manual_seed(seed)
    np.random.seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    generator = torch.Generator()
    generator.manual_seed(seed)
    model = TKTPE(n_kcs).to(device)
    collate = partial(collate_tktc, n_kcs=n_kcs)
    train_loader = DataLoader(
        KTDataset(train_df, kc_map), batch_size=64, shuffle=True, collate_fn=collate, generator=generator
    )
    valid_loader = DataLoader(
        KTDataset(valid_df, kc_map), batch_size=64, shuffle=False, collate_fn=collate
    )
    print(f"TRAIN tkt_pe fold={fold} device={device}", flush=True)
    model = train_torch_model(
        model, train_loader, valid_loader, device, n_epochs=epochs, select="best_valid", patience=8, log_path=log_path
    )
    torch.save({"state": model.state_dict(), "selected_epoch": int(model.selected_epoch)}, ckpt)
    rows = score_windowed(model, test_df, kc_map, device, window=200, mode="chunk")
    frame = pd.DataFrame(rows, columns=["row_index", "user_id", "seq_pos", "history_len", "no_history", "p"])
    base = test_df.reset_index().rename(columns={"index": "row_index"})
    frame = frame.merge(base[["row_index", "item_id", "kc_id", "correct"]], on="row_index", how="left")
    run_id = f"c2-tktpe-best_valid-chunk-fold{fold}-seed{seed}"
    frame["dataset"] = "assist2012"
    frame["split"] = "learner_based"
    frame["partition_id"] = f"fold{fold}"
    frame["init_seed"] = seed
    frame["model"] = "tkt_pe"
    frame["protocol"] = "best_validxchunk"
    frame["run_id"] = run_id
    frame["event_id"] = frame["row_index"]
    frame["f_train"] = frame["kc_id"].map(lambda kc: int(counts.get(kc, 0)))
    frame["group"] = frame["f_train"].map(get_bucket)
    frame["y"] = frame["correct"].astype(int)
    write_prediction(frame, dest)
    append_manifest(
        {
            "run_id": run_id,
            "dataset": "assist2012",
            "partition_id": f"fold{fold}",
            "init_seed": seed,
            "model": "tkt_pe",
            "protocol": "best_validxchunk",
            "code_commit": code_commit(),
            "analysis_plan_commit": PLAN_COMMIT,
            "config_path": "src/protocol_v2.py",
            "checkpoint_path": str(ckpt.relative_to(ROOT)).replace("\\", "/"),
            "selected_epoch": int(model.selected_epoch),
            "train_log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "pred_file": str(dest.relative_to(ROOT)).replace("\\", "/"),
            "pred_sha256": sha256(dest),
            "n_rows": len(frame),
            "status": "OK",
            "notes": "C2 ablation TKT_PE. Not a replacement for T-KT-c.",
        }
    )
    print(f"WROTE {dest.name} rows={len(frame)}", flush=True)


if __name__ == "__main__":
    main()
