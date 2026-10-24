#!/usr/bin/env python3
"""B2: retrain DKT on Junyi Academy at best_valid x chunk.

Five runs, four learner partitions. Fold 2 and fold 3 share one partition.
Does not overwrite archived Junyi predictions. The medium-dense contrast
is computed later from these files; this script does not edit the manuscript.
"""
from __future__ import annotations

import argparse
import gc
import subprocess
import sys
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
from src.baseline_runner import DKT, KTDataset, collate_fn, train_torch_model  # noqa: E402
from src.kc_strata import get_bucket  # noqa: E402
from src.protocol_v2 import score_windowed  # noqa: E402

PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
PLAN_COMMIT = "46e0208"
COLS = ["user_id", "item_id", "kc_id", "timestamp", "correct"]


def code_commit() -> str:
    try:
        raw = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT.parent),
            text=True,
        )
        return raw.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def pred_path(fold: int, seed: int) -> Path:
    name = prediction_name("junyi", "dkt", "best_validxchunk", f"fold{fold}", seed)
    return ROOT / "results" / "predictions" / name


def run_one(fold: int, seed: int, epochs: int) -> None:
    dest = pred_path(fold, seed)
    if dest.is_file():
        print(f"SKIP fold={fold} seed={seed}", flush=True)
        return
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    split = ROOT / "data" / "processed" / "junyi" / "splits" / "learner_based" / f"fold_{fold}"
    print(f"LOAD fold={fold} seed={seed}", flush=True)
    train_df = pd.read_csv(split / "train.csv", usecols=COLS)
    valid_df = pd.read_csv(split / "valid.csv", usecols=COLS)
    test_df = pd.read_csv(split / "test.csv", usecols=COLS)
    print(
        f"ROWS train={len(train_df)} valid={len(valid_df)} test={len(test_df)}",
        flush=True,
    )
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    kc_map = {kc: i for i, kc in enumerate(all_kcs)}
    counts = train_df["kc_id"].value_counts().to_dict()
    print(f"N_KCS {len(all_kcs)}", flush=True)

    run_dir = ROOT / "runs" / "b2_dkt_junyi" / f"junyi_fold{fold}_seed{seed}_best_valid"
    run_dir.mkdir(parents=True, exist_ok=True)
    ckpt = run_dir / "model.pt"
    log_path = run_dir / "train_log.csv"

    torch.manual_seed(seed)
    np.random.seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = DKT(len(all_kcs)).to(device)
    if ckpt.is_file():
        blob = torch.load(ckpt, map_location=device, weights_only=False)
        model.load_state_dict(blob["state"])
        model.selected_epoch = blob.get("selected_epoch")
        print(f"LOAD {ckpt}", flush=True)
        del train_df, valid_df
        gc.collect()
    else:
        generator = torch.Generator()
        generator.manual_seed(seed)
        print("BUILD datasets", flush=True)
        train_loader = DataLoader(
            KTDataset(train_df, kc_map),
            batch_size=64,
            shuffle=True,
            collate_fn=collate_fn,
            generator=generator,
        )
        valid_loader = DataLoader(
            KTDataset(valid_df, kc_map),
            batch_size=64,
            shuffle=False,
            collate_fn=collate_fn,
        )
        del train_df, valid_df
        gc.collect()
        print(f"TRAIN fold={fold} seed={seed} select=best_valid device={device}", flush=True)
        model = train_torch_model(
            model,
            train_loader,
            valid_loader,
            device,
            n_epochs=epochs,
            select="best_valid",
            patience=8,
            log_path=log_path,
        )
        torch.save(
            {
                "state": model.state_dict(),
                "n_kcs": len(all_kcs),
                "selected_epoch": int(model.selected_epoch),
                "select": "best_valid",
                "fold": fold,
                "seed": seed,
                "model": "dkt",
                "dataset": "junyi",
            },
            ckpt,
        )
        del train_loader, valid_loader
        gc.collect()

    print(f"SCORE fold={fold} seed={seed} mode=chunk", flush=True)
    rows = score_windowed(model, test_df, kc_map, device, window=200, mode="chunk")
    frame = pd.DataFrame(
        rows,
        columns=["row_index", "user_id", "seq_pos", "history_len", "no_history", "p"],
    )
    base = test_df.reset_index().rename(columns={"index": "row_index"})
    frame = frame.merge(base[["row_index", "item_id", "kc_id", "correct"]], on="row_index", how="left")
    del test_df, rows, base
    gc.collect()
    run_id = f"b2-dkt-best_valid-chunk-fold{fold}-seed{seed}"
    frame["dataset"] = "junyi"
    frame["split"] = "learner_based"
    frame["partition_id"] = f"fold{fold}"
    frame["init_seed"] = seed
    frame["model"] = "dkt"
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
            "dataset": "junyi",
            "partition_id": f"fold{fold}",
            "init_seed": seed,
            "model": "dkt",
            "protocol": "best_validxchunk",
            "code_commit": code_commit(),
            "analysis_plan_commit": PLAN_COMMIT,
            "config_path": "configs/junyi.yaml",
            "checkpoint_path": str(ckpt.relative_to(ROOT)).replace("\\", "/"),
            "selected_epoch": int(model.selected_epoch),
            "train_log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "pred_file": str(dest.relative_to(ROOT)).replace("\\", "/"),
            "pred_sha256": sha256(dest),
            "n_rows": len(frame),
            "status": "OK",
            "notes": "Junyi DKT best_valid x chunk. Contrast is medium-dense. Archived final x full numbers stay in place.",
        }
    )
    print(f"WROTE {dest.name} rows={len(frame)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=50)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    for fold, seed in PAIRS:
        run_one(fold, seed, args.epochs)
    print("B2 QUEUE DONE", flush=True)


if __name__ == "__main__":
    main()
