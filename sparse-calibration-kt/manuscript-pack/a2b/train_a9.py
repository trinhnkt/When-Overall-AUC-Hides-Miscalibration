#!/usr/bin/env python3
"""A2B: retrain DKT/SimpleKT on XES A9 downsampled trains. Seed 42 only."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from paths import BATCH_SIZE, CKPT, DS, EPOCHS, LOG, PRED  # noqa: E402
from src.baseline_runner import DKT, KTDataset, SimpleKT, collate_fn, predict_sequential, train_torch_model  # noqa: E402

LEVELS = ("t500", "t100", "t50")
MODELS = ("dkt", "simplekt")
SEED = 42


def data_dir(level: str) -> Path:
    return HERE / "data" / "processed" / "a9" / DS / level / "learner_based" / "fold_0"


def run_one(level: str, model_name: str) -> None:
    out = PRED / f"a9_{DS}_learner_based_{model_name}_{level}_seed{SEED}.csv"
    if out.exists():
        print(f"[SKIP] {out.name}", flush=True)
        return
    base = data_dir(level)
    train_df = pd.read_csv(base / "train.csv")
    valid_df = pd.read_csv(base / "valid.csv")
    test_df = pd.read_csv(base / "test.csv")
    for d in (train_df, valid_df, test_df):
        bad = (d["kc_id"].astype(str).str.replace(r"\.0$", "", regex=True) == "-1").sum()
        if bad:
            print(f"WARNING {level} {model_name} still has {bad} pad rows", flush=True)
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    kc_map = {kc: i for i, kc in enumerate(all_kcs)}
    n_kcs = len(all_kcs)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
    print(f"[RUN] a9 {model_name} {level} n_kcs={n_kcs} train={len(train_df)}", flush=True)
    t0 = time.time()
    train_ds = KTDataset(train_df, kc_map)
    valid_ds = KTDataset(valid_df, kc_map)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    net = DKT(n_kcs).to(device) if model_name == "dkt" else SimpleKT(n_kcs).to(device)
    # Same selection rule as main baselines (best valid AUC, 50 epochs, no patience).
    net = train_torch_model(net, train_loader, valid_loader, device, n_epochs=EPOCHS)
    CKPT.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": {k: v.detach().cpu() for k, v in net.state_dict().items()}, "kc_map": kc_map, "n_kcs": n_kcs}, CKPT / f"a9_{model_name}_{level}.pt")
    p_pred = predict_sequential(net, test_df, kc_map, device)
    pred = test_df.copy()
    pred["dataset"] = DS
    pred["split_mode"] = "learner_based"
    pred["model"] = model_name
    pred["seed"] = SEED
    pred["p_pred"] = p_pred
    pred["y_true"] = test_df["correct"].values
    cols = ["dataset", "split_mode", "model", "seed", "user_id", "item_id", "kc_id", "timestamp", "y_true", "p_pred"]
    PRED.mkdir(parents=True, exist_ok=True)
    pred[cols].to_csv(out, index=False)
    print(f"[OK] {out.name} {(time.time()-t0)/60:.2f} min", flush=True)
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG / "train_log.tsv").open("a", encoding="utf-8") as f:
        f.write(f"a9/{model_name}/{level}\t{(time.time()-t0)/60:.3f}\t{out.name}\n")


def main() -> None:
    for model in MODELS:
        for level in LEVELS:
            run_one(level, model)


if __name__ == "__main__":
    main()
