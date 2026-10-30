#!/usr/bin/env python3
"""Official pyKT simpleKT (pykt.models.simplekt.simpleKT) on a locked learner fold.

Uses the published architecture (Rasch difficulty + causal ordinary attention +
MLP head). Does not overwrite local T-KT CSVs or locked ECE/FAR cells.
Does not edit the manuscript.
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]

# pyKT / simpleKT paper search midpoints used as the default official config.
OFFICIAL = dict(
    d_model=256,
    n_blocks=2,
    dropout=0.05,
    d_ff=256,
    num_attn_heads=8,
    final_fc_dim=512,
    final_fc_dim2=256,
    seq_len=200,
    kq_same=1,
    l2=1e-5,
    emb_type="qid",
)


class SimpleKTSeqs(Dataset):
    def __init__(self, df: pd.DataFrame, kc_map: dict, q_map: dict, seq_len: int):
        self.rows = []
        d = df.sort_values(["user_id", "timestamp"]) if "timestamp" in df.columns else df
        for _, g in d.groupby("user_id", sort=False):
            cs = [kc_map[k] for k in g["kc_id"].values]
            qs = [q_map.get(i, 0) for i in g["item_id"].values] if "item_id" in g.columns else [0] * len(cs)
            rs = g["correct"].astype(int).tolist()
            for i in range(0, len(cs), seq_len):
                c = cs[i : i + seq_len]
                q = qs[i : i + seq_len]
                r = rs[i : i + seq_len]
                if len(c) < 2:
                    continue
                self.rows.append((q, c, r))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]


def collate(batch, pad_c=0, pad_q=0):
    qs = [torch.tensor(b[0], dtype=torch.long) for b in batch]
    cs = [torch.tensor(b[1], dtype=torch.long) for b in batch]
    rs = [torch.tensor(b[2], dtype=torch.long) for b in batch]
    q = nn.utils.rnn.pad_sequence(qs, batch_first=True, padding_value=pad_q)
    c = nn.utils.rnn.pad_sequence(cs, batch_first=True, padding_value=pad_c)
    r = nn.utils.rnn.pad_sequence(rs, batch_first=True, padding_value=0)
    L = q.size(1)
    lens = torch.tensor([len(b[0]) for b in batch])
    valid = torch.arange(L).unsqueeze(0) < lens.unsqueeze(1)
    qseqs, qshft = q[:, :-1], q[:, 1:]
    cseqs, cshft = c[:, :-1], c[:, 1:]
    rseqs, rshft = r[:, :-1], r[:, 1:]
    smasks = valid[:, 1:]
    masks = smasks.clone()
    z = torch.zeros_like(qseqs)
    return {
        "qseqs": qseqs,
        "cseqs": cseqs,
        "rseqs": rseqs,
        "tseqs": z,
        "shft_qseqs": qshft,
        "shft_cseqs": cshft,
        "shft_rseqs": rshft,
        "shft_tseqs": z,
        "masks": masks,
        "smasks": smasks,
    }


def to_device(dcur, device):
    return {k: v.to(device) for k, v in dcur.items()}


def train_epoch(model, loader, opt, device):
    model.train()
    losses = []
    for dcur in loader:
        dcur = to_device(dcur, device)
        opt.zero_grad()
        y, _, _ = model(dcur, train=True)
        y = y[:, 1:]
        sm = dcur["smasks"]
        pred = torch.masked_select(y, sm)
        tgt = torch.masked_select(dcur["shft_rseqs"].float(), sm)
        if pred.numel() == 0:
            continue
        loss = nn.functional.binary_cross_entropy(pred.float(), tgt.float())
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        losses.append(float(loss.item()))
    return float(np.mean(losses)) if losses else float("nan")


@torch.no_grad()
def eval_auc(model, loader, device):
    model.eval()
    ys, ps = [], []
    for dcur in loader:
        dcur = to_device(dcur, device)
        y = model(dcur)[:, 1:]
        sm = dcur["smasks"]
        ps.append(torch.masked_select(y, sm).cpu().numpy())
        ys.append(torch.masked_select(dcur["shft_rseqs"].float(), sm).cpu().numpy())
    y = np.concatenate(ys) if ys else np.array([])
    p = np.concatenate(ps) if ps else np.array([])
    if len(y) < 2 or len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, p))


@torch.no_grad()
def predict_test(model, test_df, kc_map, q_map, device, seq_len):
    model.eval()
    d = test_df.sort_values(["user_id", "timestamp"]) if "timestamp" in test_df.columns else test_df
    preds = {}
    for _, g in d.groupby("user_id", sort=False):
        cs = [kc_map[k] for k in g["kc_id"].values]
        qs = [q_map.get(i, 0) for i in g["item_id"].values] if "item_id" in g.columns else [0] * len(cs)
        rs = g["correct"].astype(int).tolist()
        idxs = g.index.tolist()
        for start in range(0, len(cs), seq_len):
            c = cs[start : start + seq_len]
            q = qs[start : start + seq_len]
            r = rs[start : start + seq_len]
            ix = idxs[start : start + seq_len]
            if len(c) < 2:
                preds[ix[0]] = 0.5
                continue
            dcur = collate([(q, c, r)])
            dcur = to_device(dcur, device)
            y = model(dcur)[0].detach().cpu().numpy()  # length = len(c)
            for j, row_i in enumerate(ix):
                preds[row_i] = float(y[j])
    return np.array([preds.get(i, 0.5) for i in test_df.index], dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="assist2012")
    ap.add_argument("--split", default="learner_based")
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=24)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--d-model", type=int, default=OFFICIAL["d_model"])
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    pred_path = (
        ROOT
        / "results/predictions"
        / f"{args.dataset}_{args.split}_simplekt_official_seed{args.seed}.csv"
    )
    ckpt_path = (
        ROOT
        / "results/checkpoints"
        / f"{args.dataset}_{args.split}_simplekt_official_seed{args.seed}.pt"
    )
    if pred_path.exists() and pred_path.stat().st_size > 1000:
        print(f"skip complete {pred_path}", flush=True)
        return

    cols = ["user_id", "item_id", "kc_id", "timestamp", "correct"]
    base = ROOT / "data/processed" / args.dataset / "splits" / args.split / f"fold_{args.fold}"
    train_df = pd.read_csv(base / "train.csv", usecols=cols)
    valid_df = pd.read_csv(base / "valid.csv", usecols=cols)
    test_df = pd.read_csv(base / "test.csv", usecols=cols)
    all_kcs = sorted(pd.concat([train_df["kc_id"], valid_df["kc_id"], test_df["kc_id"]]).unique())
    all_qs = sorted(pd.concat([train_df["item_id"], valid_df["item_id"], test_df["item_id"]]).unique())
    # reserve 0 for pad
    kc_map = {k: i + 1 for i, k in enumerate(all_kcs)}
    q_map = {q: i + 1 for i, q in enumerate(all_qs)}
    num_c = len(kc_map) + 1
    num_q = len(q_map)  # Embedding(n_pid+1) so n_pid = max q id
    print(
        f"num_c={num_c} num_q={num_q}+1 train={len(train_df)} valid={len(valid_df)} "
        f"test={len(test_df)} device={device}",
        flush=True,
    )

    seq_len = OFFICIAL["seq_len"]
    train_ds = SimpleKTSeqs(train_df, kc_map, q_map, seq_len)
    valid_ds = SimpleKTSeqs(valid_df, kc_map, q_map, seq_len)
    n_train, n_valid = len(train_df), len(valid_df)
    del train_df, valid_df
    gc.collect()
    print(f"seqs train={len(train_ds)} valid={len(valid_ds)} (rows {n_train}/{n_valid})", flush=True)

    from pykt.models.simplekt import simpleKT

    cfg = dict(OFFICIAL)
    cfg["d_model"] = args.d_model
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
    print("model on", device, flush=True)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate,
        num_workers=0,
    )
    valid_loader = DataLoader(
        valid_ds,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate,
        num_workers=0,
    )
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)

    best_auc, bad, best_state = -1.0, 0, None
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        tr_loss = train_epoch(model, train_loader, opt, device)
        va_auc = eval_auc(model, valid_loader, device)
        print(
            f"epoch {epoch} loss={tr_loss:.4f} valid_auc={va_auc:.4f} sec={time.time()-t0:.1f}",
            flush=True,
        )
        if va_auc > best_auc:
            best_auc, bad = va_auc, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            torch.save({"state": best_state, "cfg": cfg, "best_valid_auc": best_auc}, ckpt_path)
        else:
            bad += 1
            if bad >= args.patience:
                print("early stop", flush=True)
                break

    if best_state is not None:
        model.load_state_dict(best_state)
        model.to(device)

    print("predict test...", flush=True)
    p_pred = predict_test(model, test_df, kc_map, q_map, device, seq_len)
    out = test_df.copy()
    out["dataset"] = args.dataset
    out["split_mode"] = args.split
    out["model"] = "simplekt_official"
    out["seed"] = args.seed
    out["p_pred"] = p_pred
    out["y_true"] = out["correct"]
    cols = [
        "dataset",
        "split_mode",
        "model",
        "seed",
        "user_id",
        "item_id",
        "kc_id",
        "timestamp",
        "y_true",
        "p_pred",
    ]
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    out[cols].to_csv(pred_path, index=False)

    y, p = out["y_true"].to_numpy(), out["p_pred"].to_numpy()
    test_auc = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan")
    summary = {
        "dataset": args.dataset,
        "split": args.split,
        "fold": args.fold,
        "seed": args.seed,
        "n": int(len(out)),
        "best_valid_auc": best_auc,
        "test_auc": test_auc,
        "p_unique": int(pd.Series(p).nunique()),
        "implementation": "pykt.models.simplekt.simpleKT",
        "cfg": cfg,
        "wrote": str(pred_path),
        "note": "Learner-based fold, not the official pyKT 5-fold; ±2–3% vs published needs that split.",
    }
    sum_path = (
        ROOT / "results/reports" / f"p0_simplekt_official_{args.dataset}_seed{args.seed}.json"
    )
    sum_path.parent.mkdir(parents=True, exist_ok=True)
    sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
