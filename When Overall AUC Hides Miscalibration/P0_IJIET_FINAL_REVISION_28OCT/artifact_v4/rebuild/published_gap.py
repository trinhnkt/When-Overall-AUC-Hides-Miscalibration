"""Size-matched gap used for the published tables.

This is the draw that wrote results/A5_uncertainty_dkt_assist.csv.
It is not the function in the 4ff6683 snapshot. That snapshot keeps a
prefix of the concatenated dense rows. This module keeps exactly N rows
by a second sample without replacement.
"""
from __future__ import annotations

import numpy as np


def compute_ece(y_true, p_pred, n_bins=15):
    y_true = np.asarray(y_true)
    p_pred = np.asarray(p_pred, dtype=float)
    mask = ~np.isnan(p_pred)
    y_true = y_true[mask]
    p_pred = p_pred[mask]
    if len(y_true) == 0:
        return float("nan")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    score = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        inside = (p_pred > left) & (p_pred <= right)
        if left == 0:
            inside = inside | (p_pred == 0)
        prop = float(np.mean(inside))
        if prop > 0:
            gap = abs(float(np.mean(p_pred[inside])) - float(np.mean(y_true[inside])))
            score += gap * prop
    return float(score)


def ece(y, p, n_bins=15) -> float:
    return compute_ece(y, p, n_bins=n_bins)


def ece0_bound(n, n_bins=15) -> float:
    if n <= 0:
        return float("nan")
    return float(0.5 * np.sqrt(n_bins / n))


def dense_at_n(dense_clusters, n, rng):
    ys, ps, total = [], [], 0
    order = rng.permutation(len(dense_clusters))
    for j in order:
        y, p = dense_clusters[int(j)]
        ys.append(np.asarray(y))
        ps.append(np.asarray(p, dtype=float))
        total += len(y)
        if total >= n:
            break
    if total < n or not ys:
        return None
    y = np.concatenate(ys)
    p = np.concatenate(ps)
    keep = rng.choice(len(y), size=n, replace=False)
    return y[keep], p[keep]


def rows_at_n(y, p, n, rng):
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    if len(y) < n:
        return None
    keep = rng.choice(len(y), size=n, replace=False)
    return y[keep], p[keep]


def size_matched_contrast(sparse_y, sparse_p, dense_clusters, rng, n_draws=2000, n_bins=15):
    n = len(sparse_y)
    ece_s = ece(sparse_y, sparse_p, n_bins=n_bins)
    draws = []
    invalid = 0
    for _ in range(n_draws):
        got = dense_at_n(dense_clusters, n, rng)
        if got is None:
            invalid += 1
            continue
        draws.append(ece(got[0], got[1], n_bins=n_bins))
    if not draws:
        return {
            "ece_sparse": ece_s,
            "ece_dense_at_n_median": float("nan"),
            "size_matched_diff": float("nan"),
            "n_draws": n_draws,
            "n_invalid": invalid,
        }
    med = float(np.median(draws))
    return {
        "ece_sparse": ece_s,
        "ece_dense_at_n_median": med,
        "size_matched_diff": ece_s - med,
        "n_draws": n_draws,
        "n_invalid": invalid,
    }


def _concat_picked(groups, pick):
    parts_y, parts_p = [], []
    for j in pick:
        y, p = groups[int(j)]
        if len(y) == 0:
            continue
        parts_y.append(np.asarray(y))
        parts_p.append(np.asarray(p, dtype=float))
    if not parts_y:
        return None
    return np.concatenate(parts_y), np.concatenate(parts_p)


def cluster_bootstrap_diff(user_sparse, user_dense, rng, n_boot=2000, n_inner=200, n_bins=15):
    if len(user_sparse) != len(user_dense):
        raise ValueError("sparse and dense learner lists must be aligned")
    n_learners = len(user_sparse)
    matched = []
    empty = 0
    empty_sparse = 0
    for _ in range(n_boot):
        pick = rng.integers(0, n_learners, size=n_learners)
        sparse = _concat_picked(user_sparse, pick)
        dense = _concat_picked(user_dense, pick)
        if sparse is None:
            empty_sparse += 1
            empty += 1
            continue
        if dense is None:
            empty += 1
            continue
        clusters = []
        for j in pick:
            y, p = user_dense[int(j)]
            if len(y) == 0:
                continue
            clusters.append((y, p))
        inner = np.random.default_rng(int(rng.integers(0, 2**31 - 1)))
        row = size_matched_contrast(
            sparse[0], sparse[1], clusters, inner, n_draws=n_inner, n_bins=n_bins
        )
        if np.isnan(row["size_matched_diff"]):
            empty += 1
            continue
        matched.append(row["size_matched_diff"])
    if not matched:
        lo = hi = float("nan")
    else:
        lo, hi = np.percentile(matched, [2.5, 97.5])
    return {
        "n_empty_or_invalid": empty,
        "n_empty_sparse": empty_sparse,
        "n_used": len(matched),
        "ci95_low": float(lo),
        "ci95_high": float(hi),
    }


def aligned_users(frame, focal: str):
    kept = frame[frame["no_history"] == 0]
    users = kept["user_id"].drop_duplicates().tolist()
    grouped = {uid: g for uid, g in kept.groupby("user_id", sort=False)}
    focal_side, dense_side = [], []
    for uid in users:
        g = grouped[uid]
        part_f = g[g["group"] == focal]
        part_d = g[g["group"] == "dense"]
        focal_side.append((part_f["y"].to_numpy(), part_f["p"].to_numpy(dtype=float)))
        dense_side.append((part_d["y"].to_numpy(), part_d["p"].to_numpy(dtype=float)))
    return focal_side, dense_side


def row_matched(focal_y, focal_p, dense_y, dense_p, rng, n_draws):
    n = len(focal_y)
    ece_s = ece(focal_y, focal_p)
    draws = []
    for _ in range(n_draws):
        got = rows_at_n(dense_y, dense_p, n, rng)
        if got is None:
            continue
        draws.append(ece(got[0], got[1]))
    return draws
