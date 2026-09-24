#!/usr/bin/env python3
"""A2B: train IRT / DKT / local SimpleKT on the masked XES3G5M tree.

Settings match TABLE_S1 / baseline_runner.py: batch 64, 50 epochs, Adam 1e-3,
best validation AUC. IRT: lr 0.01, reg 0.01, 10 epochs, batch 512.
Writes only under IJIET_FINAL_REVISION/a2b/.
"""
from __future__ import annotations

import argparse
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

from paths import (  # noqa: E402
    BATCH_SIZE,
    CKPT,
    DS,
    EPOCHS,
    LOG,
    MODELS,
    PRED,
    SEEDS,
    SPLITS,
)
from src.baseline_runner import (  # noqa: E402
    DKT,
    KTDataset,
    SimpleKT,
    collate_fn,
    predict_sequential,
    train_torch_model,
)
from src.models.irt_baseline import IRT1PL  # noqa: E402


def job_list(only_model: str | None, only_split: str | None, only_seed: int | None):
    jobs = []
    for split in ("learner_based", "temporal"):
        if only_split and split != only_split:
            continue
        for model in MODELS:
            if only_model and model != only_model:
                continue
            for i, seed in enumerate(SEEDS):
                if only_seed is not None and seed != only_seed:
                    continue
                fold = i if split == "learner_based" else 0
                jobs.append({"split": split, "fold": fold, "model": model, "seed": seed})
    return jobs


def pred_path(split: str, model: str, seed: int) -> Path:
    PRED.mkdir(parents=True, exist_ok=True)
    return PRED / f"{DS}_{split}_{model}_seed{seed}_predictions_rerun.csv"


def ckpt_path(split: str, model: str, seed: int) -> Path:
    CKPT.mkdir(parents=True, exist_ok=True)
    return CKPT / f"{DS}_{split}_{model}_seed{seed}.pt"


def load_split(split: str, fold: int):
    base = SPLITS / split / f"fold_{fold}"
    train = pd.read_csv(base / "train.csv")
    valid = pd.read_csv(base / "valid.csv")
    test = pd.read_csv(base / "test.csv")
    for d in (train, valid, test):
        bad = d["kc_id"].astype(str).str.replace(r"\.0$", "", regex=True).isin(["-1", "nan"])
        if bad.any():
            raise SystemExit(f"padding leaked into {base}: {int(bad.sum())} rows")
    return train, valid, test


def write_pred(test_df, p_pred, split, model, seed, path: Path):
    out = test_df.copy()
    out["dataset"] = DS
    out["split_mode"] = split
    out["model"] = model
    out["seed"] = seed
    out["p_pred"] = p_pred
    out["y_true"] = test_df["correct"].values
    cols = ["dataset", "split_mode", "model", "seed", "user_id", "item_id", "kc_id", "timestamp", "y_true", "p_pred"]
    out[cols].to_csv(path, index=False)


def run_job(job: dict, overwrite: bool) -> str:
    split, fold, model, seed = job["split"], job["fold"], job["model"], job["seed"]
    out = pred_path(split, model, seed)
    tag = f"{split}/{model}/seed{seed}/fold_{fold}"
    if out.exists() and not overwrite:
        print(f"[SKIP] {tag} {out.name}", flush=True)
        return "skip"
    print(f"[RUN] {tag}", flush=True)
    t0 = time.time()
    print(f"  loading splits {split}/fold_{fold}", flush=True)
    train_df, valid_df, test_df = load_split(split, fold)
    print(f"  loaded train={len(train_df)} valid={len(valid_df)} test={len(test_df)}", flush=True)
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    if any(str(k).replace(".0", "") == "-1" for k in all_kcs):
        raise SystemExit("kc_map would include -1")
    kc_map = {kc: i for i, kc in enumerate(all_kcs)}
    n_kcs = len(all_kcs)

    if model == "irt_1pl":
        irt = IRT1PL(seed=seed)
        irt.fit(train_df, verbose=True)
        p_pred = irt.predict(test_df)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        print(f"  n_kcs={n_kcs} building KTDataset", flush=True)
        train_ds = KTDataset(train_df, kc_map)
        valid_ds = KTDataset(valid_df, kc_map)
        print(f"  n_seq train={len(train_ds)} valid={len(valid_ds)}", flush=True)
        train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
        valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
        net = DKT(n_kcs).to(device) if model == "dkt" else SimpleKT(n_kcs).to(device)
        print(f"  training {model} on {device} epochs={EPOCHS} batch={BATCH_SIZE}", flush=True)
        net = train_torch_model(net, train_loader, valid_loader, device, n_epochs=EPOCHS)
        print(f"  trained, running predict_sequential n_test={len(test_df)}", flush=True)
        ck = ckpt_path(split, model, seed)
        torch.save(
            {
                "state_dict": {k: v.detach().cpu() for k, v in net.state_dict().items()},
                "n_kcs": n_kcs,
                "kc_map": kc_map,
                "model": model,
                "seed": seed,
            },
            ck,
        )
        p_pred = predict_sequential(net, test_df, kc_map, device)

    write_pred(test_df, p_pred, split, model, seed, out)
    dt = (time.time() - t0) / 60.0
    print(f"[OK] {tag} {dt:.2f} min -> {out.name}", flush=True)
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG / "train_log.tsv").open("a", encoding="utf-8") as f:
        f.write(f"{tag}\t{dt:.3f}\t{out.name}\n")
    return "ok"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=list(MODELS) + ["all"], default="all")
    p.add_argument("--split", choices=["learner_based", "temporal", "all"], default="all")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    jobs = job_list(
        None if args.model == "all" else args.model,
        None if args.split == "all" else args.split,
        args.seed,
    )
    print(f"{len(jobs)} jobs device={'cuda' if torch.cuda.is_available() else 'cpu'}", flush=True)
    for job in jobs:
        run_job(job, args.overwrite)


if __name__ == "__main__":
    main()
