#!/usr/bin/env python3
"""A3–A4: retrain DKT on ASSISTments 2012 and score three windows.

Bản I checkpoints are not recovered, so final and best_valid are both
trained again. This script does not edit the manuscript and does not
invent an ECE value.
"""
from __future__ import annotations

import argparse
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
MODES = ("full", "chunk", "slide")
PLAN_COMMIT = "46e0208"
PRED_DIR = ROOT / "results" / "predictions"


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


def pred_path(select: str, mode: str, fold: int, seed: int) -> Path:
    protocol = f"{select}x{mode}"
    name = prediction_name("assist2012", "dkt", protocol, f"fold{fold}", seed)
    return PRED_DIR / name


def run_one(fold: int, seed: int, select: str, epochs: int) -> None:
    missing = [mode for mode in MODES if not pred_path(select, mode, fold, seed).is_file()]
    if not missing:
        print(f"SKIP fold={fold} seed={seed} select={select}", flush=True)
        return
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    split = ROOT / "data" / "processed" / "assist2012" / "splits" / "learner_based" / f"fold_{fold}"
    train_df = pd.read_csv(split / "train.csv")
    valid_df = pd.read_csv(split / "valid.csv")
    test_df = pd.read_csv(split / "test.csv")
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    kc_map = {kc: i for i, kc in enumerate(all_kcs)}
    counts = train_df["kc_id"].value_counts().to_dict()

    run_dir = ROOT / "runs" / "a_dkt" / f"assist2012_fold{fold}_seed{seed}_{select}"
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
    else:
        generator = torch.Generator()
        generator.manual_seed(seed)
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
        print(f"TRAIN fold={fold} seed={seed} select={select} device={device}", flush=True)
        model = train_torch_model(
            model,
            train_loader,
            valid_loader,
            device,
            n_epochs=epochs,
            select=select,
            patience=8,
            log_path=log_path,
        )
        torch.save(
            {
                "state": model.state_dict(),
                "n_kcs": len(all_kcs),
                "kc_map": kc_map,
                "selected_epoch": int(model.selected_epoch),
                "select": select,
                "fold": fold,
                "seed": seed,
            },
            ckpt,
        )

    scored = {}
    for mode in missing:
        print(f"SCORE fold={fold} seed={seed} select={select} mode={mode}", flush=True)
        scored[mode] = score_windowed(model, test_df, kc_map, device, window=200, mode=mode)

    commit = code_commit()
    for mode, rows in scored.items():
        frame = pd.DataFrame(
            rows,
            columns=["row_index", "user_id", "seq_pos", "history_len", "no_history", "p"],
        )
        base = test_df.reset_index().rename(columns={"index": "row_index"})
        keep = base[["row_index", "item_id", "kc_id", "correct"]]
        frame = frame.merge(keep, on="row_index", how="left")
        protocol = f"{select}x{mode}"
        run_id = f"a-dkt-{select}-{mode}-fold{fold}-seed{seed}"
        frame["dataset"] = "assist2012"
        frame["split"] = "learner_based"
        frame["partition_id"] = f"fold{fold}"
        frame["init_seed"] = seed
        frame["model"] = "dkt"
        frame["protocol"] = protocol
        frame["run_id"] = run_id
        frame["event_id"] = frame["row_index"]
        frame["item_id"] = frame["item_id"]
        frame["f_train"] = frame["kc_id"].map(lambda kc: int(counts.get(kc, 0)))
        frame["group"] = frame["f_train"].map(get_bucket)
        frame["y"] = frame["correct"].astype(int)
        dest = pred_path(select, mode, fold, seed)
        write_prediction(frame, dest)
        append_manifest(
            {
                "run_id": run_id,
                "dataset": "assist2012",
                "partition_id": f"fold{fold}",
                "init_seed": seed,
                "model": "dkt",
                "protocol": protocol,
                "code_commit": commit,
                "analysis_plan_commit": PLAN_COMMIT,
                "config_path": "configs/assist2012.yaml",
                "checkpoint_path": str(ckpt.relative_to(ROOT)).replace("\\", "/"),
                "selected_epoch": int(model.selected_epoch),
                "train_log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
                "pred_file": str(dest.relative_to(ROOT)).replace("\\", "/"),
                "pred_sha256": sha256(dest),
                "n_rows": len(frame),
                "status": "OK",
                "notes": (
                    "Retrained because ban I checkpoints are NOT RECOVERED. "
                    "final x full is a new training, not a rescore of 0.0602."
                ),
            }
        )
        print(f"WROTE {dest.name} rows={len(frame)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", action="store_true")
    parser.add_argument("--fold", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--select", choices=["final", "best_valid"])
    parser.add_argument("--epochs", type=int, default=50)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.queue:
        for fold, seed in PAIRS:
            for select in ("final", "best_valid"):
                run_one(fold, seed, select, args.epochs)
        print("QUEUE DONE", flush=True)
        return
    if args.fold is None or args.seed is None or args.select is None:
        raise SystemExit("pass --queue, or --fold --seed --select")
    run_one(args.fold, args.seed, args.select, args.epochs)


if __name__ == "__main__":
    main()
