# -*- coding: utf-8 -*-
"""A1: DKT token-0 checks against the implementation frozen at 4ff6683.

Does not edit the manuscript and does not train.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.baseline_runner import DKT, collate_fn  # noqa: E402

COMMIT = "4ff6683"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
WINDOW = 200
# Locked before looking at checkpoint norms.
COMPARABLE_LOW = 0.1
COMPARABLE_HIGH = 10.0
ATOL = 1e-6


def line(text=""):
    print(text, flush=True)


def t0_a():
    model = DKT(10)
    padding_idx = model.embed.padding_idx
    line(f"T0-a embedding.padding_idx={padding_idx}")
    line(f"T0-a num_embeddings={model.embed.num_embeddings} embedding_dim={model.embed.embedding_dim}")
    passed = padding_idx is None or padding_idx != 0
    line(f"T0-a {'PASS' if passed else 'FAIL'}")
    return passed, padding_idx


def t0_b():
    torch.manual_seed(20261029)
    model = DKT(6)
    batch = [
        {
            "features": torch.tensor([0, 2]),
            "labels": torch.tensor([1.0, 0.0]),
            "kcs": torch.tensor([1, 2]),
        },
        {
            "features": torch.tensor([4]),
            "labels": torch.tensor([1.0]),
            "kcs": torch.tensor([3]),
        },
    ]
    feats, labels, kcs = collate_fn(batch)
    line(f"T0-b collate features=\n{feats.tolist()}")
    line(f"T0-b collate labels=\n{labels.tolist()}")
    line(f"T0-b collate padding feature at short row={int(feats[1, 1])} label={float(labels[1, 1])}")
    preds = model(feats)
    preds_flat = preds.view(-1, model.n_kcs)
    kcs_flat = kcs.view(-1)
    labels_flat = labels.view(-1)
    mask = labels_flat != -1
    token0_and_supervised = (feats.view(-1) == 0) & mask
    line(f"T0-b mask depends on labels != -1; mask={mask.tolist()}")
    line(f"T0-b supervised positions whose token is 0={int(token0_and_supervised.sum())}")
    target = preds_flat[torch.arange(preds_flat.size(0)), kcs_flat.clamp(min=0)]
    loss = nn.BCELoss(reduction="none")(target[mask], labels_flat[mask]).mean()
    loss.backward()
    grad = model.embed.weight.grad
    row0 = float(grad[0].norm())
    line(f"T0-b loss={float(loss)} grad_norm_row0={row0}")
    passed = row0 > 0.0 and bool(token0_and_supervised.any())
    line(f"T0-b {'PASS' if passed else 'FAIL'}")
    return passed, row0


def theoretical_counts(test: pd.DataFrame):
    ordered = test.sort_values(["user_id", "timestamp"]) if "timestamp" in test.columns else test
    lengths = ordered.groupby("user_id", sort=True).size()
    n = int(lengths.sum())
    no_history = int(sum((int(length) + WINDOW - 1) // WINDOW for length in lengths))
    return n, no_history, n - no_history


def t0_c_and_rest():
    results = []
    all_pass = True
    device = torch.device("cpu")
    for fold, seed in PAIRS:
        run_dir = ROOT / "runs" / "a_dkt" / f"assist2012_fold{fold}_seed{seed}_best_valid"
        ckpt = run_dir / "model.pt"
        pred_path = (
            ROOT
            / "results"
            / "predictions"
            / f"pred_assist2012_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz"
        )
        split = ROOT / "data" / "processed" / "assist2012" / "splits" / "learner_based" / f"fold_{fold}" / "test.csv"
        line(f"--- fold={fold} seed={seed}")
        line(f"checkpoint={ckpt}")
        line(f"prediction={pred_path.name}")
        blob = torch.load(ckpt, map_location="cpu", weights_only=False)
        n_kcs = int(blob["n_kcs"])
        kc_map = {int(k): int(v) for k, v in blob["kc_map"].items()}
        model = DKT(n_kcs)
        model.load_state_dict(blob["state"])
        model.eval()
        weight = model.embed.weight.detach()
        norms = weight.norm(dim=1)
        row0 = float(norms[0])
        other = norms[1:]
        median_other = float(other.median())
        ratio = row0 / median_other if median_other > 0 else float("inf")
        pad_row = int(model.embed.padding_idx)
        pad_norm = float(norms[pad_row])
        line(
            f"T0-c n_kcs={n_kcs} padding_idx={pad_row} "
            f"norm_row0={row0:.8f} median_other={median_other:.8f} ratio={ratio:.6f} "
            f"norm_padding_idx_row={pad_norm:.8e}"
        )
        c_pass = row0 != 0.0 and COMPARABLE_LOW <= ratio <= COMPARABLE_HIGH
        line(f"T0-c {'PASS' if c_pass else 'FAIL'}")

        test = pd.read_csv(split)
        n_test, n_no, n_scored = theoretical_counts(test)
        pred = pd.read_csv(
            pred_path,
            usecols=["row_index", "user_id", "seq_pos", "history_len", "no_history", "kc_id", "y", "p"],
        )
        file_no = int((pred["no_history"] == 1).sum())
        file_scored = int((pred["no_history"] == 0).sum())
        count_pass = (
            len(pred) == n_test
            and file_no == n_no
            and file_scored == n_scored
            and int(pred["row_index"].nunique()) == n_test
        )
        line(
            f"T0-d rows file={len(pred)} test={n_test} "
            f"no_history file={file_no} theory={n_no} "
            f"scored file={file_scored} theory={n_scored}"
        )

        pred = pred.sort_values(["user_id", "seq_pos"])
        mapped = pred["kc_id"].map(kc_map)
        if mapped.isna().any():
            raise RuntimeError(f"kc_id missing from checkpoint map fold {fold}")
        token = 2 * mapped.to_numpy(dtype=np.int64) + pred["y"].to_numpy(dtype=np.int64)
        pred = pred.copy()
        pred["token"] = token
        missing = 0
        bad = 0
        n_follow = 0
        n_boundary = 0
        n_inside = 0
        examples = []
        for uid, group in pred.groupby("user_id", sort=False):
            group = group.reset_index(drop=True)
            tokens = group["token"].to_numpy()
            seq = group["seq_pos"].to_numpy()
            hist = group["history_len"].to_numpy()
            noh = group["no_history"].to_numpy()
            probs = group["p"].to_numpy()
            for i in range(len(group) - 1):
                if tokens[i] != 0:
                    continue
                if int(seq[i + 1]) != int(seq[i]) + 1:
                    missing += 1
                    continue
                n_follow += 1
                boundary = int(seq[i + 1]) % WINDOW == 0
                if boundary:
                    n_boundary += 1
                    ok = int(noh[i + 1]) == 1 and int(hist[i + 1]) == 0
                else:
                    n_inside += 1
                    ok = (
                        int(noh[i + 1]) == 0
                        and int(hist[i + 1]) == int(seq[i + 1]) % WINDOW
                        and np.isfinite(probs[i + 1])
                    )
                    if ok and len(examples) < 5 and fold == 0:
                        examples.append(group.iloc[: i + 2].copy())
                if not ok:
                    bad += 1
        line(
            f"T0-d successors_of_token0={n_follow} inside_chunk={n_inside} "
            f"chunk_boundary={n_boundary} missing={missing} bad={bad}"
        )
        replay_bad = 0
        for sample in examples:
            sample = sample.reset_index(drop=True)
            target = sample.iloc[-1]
            start = (int(target.seq_pos) // WINDOW) * WINDOW
            hist_rows = sample[sample["seq_pos"] >= start].iloc[:-1]
            hist_tokens = hist_rows["token"].astype(int).tolist()
            if 0 not in hist_tokens:
                replay_bad += 1
                line("T0-d replay history does not contain token 0")
                continue
            x = torch.tensor([hist_tokens], dtype=torch.long)
            with torch.no_grad():
                got = float(model(x)[0, -1, int(kc_map[int(target.kc_id)])])
            err = abs(got - float(target.p))
            line(
                f"T0-d replay seq_pos={int(target.seq_pos)} history_len={len(hist_tokens)} "
                f"saved_p={float(target.p):.8f} model_p={got:.8f} abs_err={err:.3e}"
            )
            if err > 1e-4:
                replay_bad += 1
        d_pass = count_pass and n_follow > 0 and missing == 0 and bad == 0 and replay_bad == 0
        if fold != 0:
            d_pass = count_pass and n_follow > 0 and missing == 0 and bad == 0
        line(f"T0-d {'PASS' if d_pass else 'FAIL'}")

        if fold == 0:
            tokens = [0, 3, 5, 0, 8, 1]
            x = torch.tensor([tokens], dtype=torch.long, device=device)
            with torch.no_grad():
                base = model(x)
                padded = model(torch.cat([x, torch.zeros(1, 20, dtype=torch.long)], dim=1))
            diff = float((base - padded[:, : x.size(1), :]).abs().max())
            line(f"UT-A4 max_abs_diff_after_20_zero_pads={diff:.3e}")
            ut_pass = diff <= ATOL
            line(f"UT-A4 {'PASS' if ut_pass else 'FAIL'}")
        else:
            ut_pass = True

        all_pass = all_pass and c_pass and d_pass and ut_pass
        results.append((fold, seed, c_pass, d_pass, row0, ratio, n_follow))
    return all_pass, results


def main():
    line(f"commit={COMMIT}")
    line("encoding token = 2 * KC + y; token 0 = KC 0 + incorrect")
    line("comparable-scale rule: 0 < norm(row0) and 0.1 <= norm(row0)/median(other rows) <= 10")
    line("DKT class and collate_fn match commit 4ff6683; later edits to train_torch_model only add logs")
    line("embedding: nn.Embedding(n_kcs * 2 + 1, embed_dim, padding_idx=n_kcs * 2)")
    line("collate padding_value: features=0, labels=-1, kcs=-1")
    line("loss mask: labels_flat != -1")
    line("scoring mask: none on token != 0; a row is unscored only when its chunk history is empty")
    a_pass, padding_idx = t0_a()
    b_pass, row0_grad = t0_b()
    rest_pass, results = t0_c_and_rest()
    overall = a_pass and b_pass and rest_pass
    line("====")
    line(f"T0-a={a_pass} padding_idx={padding_idx}")
    line(f"T0-b={b_pass} grad_norm_row0={row0_grad}")
    for fold, seed, c_pass, d_pass, row0, ratio, n_follow in results:
        line(
            f"fold={fold} seed={seed} T0-c={c_pass} T0-d={d_pass} "
            f"norm_row0={row0:.8f} ratio={ratio:.6f} token0_successors={n_follow}"
        )
    line(f"A1={'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
