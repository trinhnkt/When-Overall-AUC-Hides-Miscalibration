#!/usr/bin/env python3
"""C3: official pyKT simpleKT on Junyi, best_valid x chunk.

Same config as scripts/p0_retrain_official_simplekt.py. Does not change
the ASSISTments simpleKT script. Does not train XES. The Junyi contrast
used later is medium-dense. Archived DKT 0.0389/0.2513 is a different
protocol and is not replaced here.
"""
from __future__ import annotations

import argparse
import gc
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
from scripts.p0_b3_simplekt_assist import code_commit, valid_metrics  # noqa: E402
from scripts.p0_retrain_official_simplekt import (  # noqa: E402
    OFFICIAL,
    SimpleKTSeqs,
    collate,
    predict_test,
    simplekt_no_history,
    train_epoch,
)
from src.kc_strata import get_bucket  # noqa: E402

PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
PLAN_COMMIT = "46e0208"
DATASET = "junyi"


def pred_path(fold: int, seed: int) -> Path:
    name = prediction_name(DATASET, "simplekt", "best_validxchunk", f"fold{fold}", seed)
    return ROOT / "results" / "predictions" / name


def run_one(fold: int, seed: int, epochs: int, patience: int, batch_size: int, lr: float) -> None:
    dest = pred_path(fold, seed)
    if dest.is_file():
        print(f"SKIP fold={fold} seed={seed}", flush=True)
        return
    run_dir = ROOT / "runs" / "c3_simplekt_junyi" / f"junyi_fold{fold}_seed{seed}_best_valid"
    run_dir.mkdir(parents=True, exist_ok=True)
    ckpt = run_dir / "model.pt"
    log_path = run_dir / "train_log.csv"

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cols = ["user_id", "item_id", "kc_id", "timestamp", "correct"]
    base = ROOT / "data" / "processed" / DATASET / "splits" / "learner_based" / f"fold_{fold}"
    print(f"LOAD fold={fold} seed={seed}", flush=True)
    train_df = pd.read_csv(base / "train.csv", usecols=cols)
    valid_df = pd.read_csv(base / "valid.csv", usecols=cols)
    test_df = pd.read_csv(base / "test.csv", usecols=cols)
    print(
        f"ROWS train={len(train_df)} valid={len(valid_df)} test={len(test_df)}",
        flush=True,
    )
    counts = train_df["kc_id"].value_counts().to_dict()
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    all_qs = sorted(pd.concat([train_df["item_id"], valid_df["item_id"], test_df["item_id"]]).unique())
    kc_map = {k: i + 1 for i, k in enumerate(all_kcs)}
    q_map = {q: i + 1 for i, q in enumerate(all_qs)}
    num_c = len(kc_map) + 1
    num_q = len(q_map)
    seq_len = OFFICIAL["seq_len"]
    print(
        f"TRAIN fold={fold} seed={seed} num_c={num_c} num_q={num_q} device={device}",
        flush=True,
    )

    train_ds = SimpleKTSeqs(train_df, kc_map, q_map, seq_len)
    valid_ds = SimpleKTSeqs(valid_df, kc_map, q_map, seq_len)
    del train_df, valid_df
    gc.collect()

    from pykt.models.simplekt import simpleKT

    cfg = dict(OFFICIAL)
    model = simpleKT(
        num_c,
        num_q,
        d_model=cfg["d_model"],
        n_blocks=cfg["n_blocks"],
        dropout=cfg["dropout"],
        d_ff=cfg["d_ff"],
        num_attn_heads=cfg["num_attn_heads"],
        final_fc_dim=cfg["final_fc_dim"],
        final_fc_dim2=cfg["final_fc_dim2"],
        seq_len=cfg["seq_len"],
        kq_same=cfg["kq_same"],
        l2=cfg["l2"],
        emb_type=cfg["emb_type"],
        emb_path="",
    ).to(device)
    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate, num_workers=0
    )
    valid_loader = DataLoader(
        valid_ds, batch_size=batch_size, shuffle=False, collate_fn=collate, num_workers=0
    )
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    best_auc, bad, best_state, selected_epoch = -1.0, 0, None, None
    log_rows = []
    for epoch in range(1, epochs + 1):
        tr_loss = train_epoch(model, train_loader, opt, device)
        va_auc, va_nll, va_ece = valid_metrics(model, valid_loader, device)
        log_rows.append(
            {
                "epoch": epoch,
                "train_loss": tr_loss,
                "valid_auc": va_auc,
                "valid_nll": va_nll,
                "valid_ece": va_ece,
            }
        )
        pd.DataFrame(log_rows).to_csv(log_path, index=False)
        print(
            f"epoch {epoch:02d} loss={tr_loss:.4f} valid_auc={va_auc:.4f} "
            f"valid_nll={va_nll:.4f} valid_ece={va_ece:.4f}",
            flush=True,
        )
        if va_auc > best_auc:
            best_auc, bad = va_auc, 0
            selected_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                print("early stop", flush=True)
                break

    if best_state is None or selected_epoch is None:
        raise SystemExit(f"no validation AUC for fold {fold}")
    model.load_state_dict(best_state)
    model.to(device)
    torch.save(
        {
            "state": best_state,
            "cfg": cfg,
            "best_valid_auc": best_auc,
            "selected_epoch": int(selected_epoch),
            "fold": fold,
            "seed": seed,
            "model": "simplekt",
            "implementation": "pykt.models.simplekt.simpleKT",
        },
        ckpt,
    )

    print(f"SCORE fold={fold} seed={seed}", flush=True)
    flags = simplekt_no_history(test_df, seq_len)
    probs = predict_test(model, test_df, kc_map, q_map, device, seq_len)
    ordered = test_df.sort_values(["user_id", "timestamp"])
    seq_pos = pd.Series(0, index=test_df.index, dtype=int)
    history_len = pd.Series(0, index=test_df.index, dtype=int)
    for _, group in ordered.groupby("user_id", sort=False):
        for local, idx in enumerate(group.index.tolist()):
            seq_pos.loc[idx] = local
            history_len.loc[idx] = local % seq_len
    expected = (history_len.to_numpy() == 0).astype(int)
    if not np.array_equal(flags.to_numpy().astype(int), expected):
        raise SystemExit("simpleKT no_history flags do not match chunk starts")

    frame = test_df.copy()
    del test_df
    frame["row_index"] = frame.index
    frame["dataset"] = DATASET
    frame["split"] = "learner_based"
    frame["partition_id"] = f"fold{fold}"
    frame["init_seed"] = seed
    frame["model"] = "simplekt"
    frame["protocol"] = "best_validxchunk"
    frame["run_id"] = f"c3-simplekt-best_valid-chunk-fold{fold}-seed{seed}"
    frame["event_id"] = frame["row_index"]
    frame["seq_pos"] = seq_pos
    frame["history_len"] = history_len
    frame["no_history"] = flags.astype(int)
    frame["f_train"] = frame["kc_id"].map(lambda kc: int(counts.get(kc, 0)))
    frame["group"] = frame["f_train"].map(get_bucket)
    frame["y"] = frame["correct"].astype(int)
    frame["p"] = probs
    write_prediction(frame, dest)
    append_manifest(
        {
            "run_id": frame["run_id"].iloc[0],
            "dataset": DATASET,
            "partition_id": f"fold{fold}",
            "init_seed": seed,
            "model": "simplekt",
            "protocol": "best_validxchunk",
            "code_commit": code_commit(),
            "analysis_plan_commit": PLAN_COMMIT,
            "config_path": "scripts/p0_retrain_official_simplekt.py",
            "checkpoint_path": str(ckpt.relative_to(ROOT)).replace("\\", "/"),
            "selected_epoch": int(selected_epoch),
            "train_log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "pred_file": str(dest.relative_to(ROOT)).replace("\\", "/"),
            "pred_sha256": sha256(dest),
            "n_rows": len(frame),
            "status": "OK",
            "notes": (
                "C3 official pyKT simpleKT on Junyi. best_valid x chunk. "
                "Does not replace archived DKT 0.0389/0.2513. XES was not trained."
            ),
        }
    )
    print(f"WROTE {dest.name} rows={len(frame)} selected_epoch={selected_epoch}", flush=True)
    del frame, model, train_ds, valid_ds
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--fold", type=int, default=None)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    pairs = PAIRS if args.fold is None else tuple(pair for pair in PAIRS if pair[0] == args.fold)
    if not pairs:
        raise SystemExit(f"fold {args.fold} is not in {PAIRS}")
    for fold, seed in pairs:
        run_one(fold, seed, args.epochs, args.patience, args.batch_size, args.lr)
    print("C3 QUEUE DONE", flush=True)


if __name__ == "__main__":
    main()
