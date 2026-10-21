"""Size-matched ECE contrast and learner-cluster bootstrap.

The primary contrast is ECE_sparse - median(ECE of a dense draw with the
same number of rows). A cluster bootstrap that keeps N fixed does not remove
the small-sample bias of binned ECE, so the size-matched draw is the
bias control. Four learner partitions are not independent samples and are
not pooled into one interval.
"""
from __future__ import annotations

import numpy as np

from src.calibration_eval import compute_ece


def ece(y, p, n_bins=15) -> float:
    value = compute_ece(np.asarray(y), np.asarray(p, dtype=float), n_bins=n_bins)[0]
    return float(value)


def dense_at_n(dense_clusters, n, rng):
    """Draw learners without replacement until the draw has n rows, then keep n."""
    ys, ps, total = [], [], 0
    order = rng.permutation(len(dense_clusters))
    for j in order:
        y, p = dense_clusters[j]
        ys.append(np.asarray(y))
        ps.append(np.asarray(p))
        total += len(y)
        if total >= n:
            break
    if total < n or not ys:
        return None
    y = np.concatenate(ys)[:n]
    p = np.concatenate(ps)[:n]
    return y, p


def size_matched_contrast(sparse_y, sparse_p, dense_clusters, rng, n_draws=2000, n_bins=15):
    """Return sparse ECE, median dense ECE at the same N, and the exceedance rate."""
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
            "exceedance_rate": float("nan"),
            "n_draws": n_draws,
            "n_invalid": invalid,
        }
    med = float(np.median(draws))
    exceed = float(np.mean(np.asarray(draws) >= ece_s))
    return {
        "ece_sparse": ece_s,
        "ece_dense_at_n_median": med,
        "size_matched_diff": ece_s - med,
        "exceedance_rate": exceed,
        "n_draws": n_draws,
        "n_invalid": invalid,
    }


def cluster_bootstrap_diff(
    sparse_clusters,
    dense_clusters,
    rng,
    n_boot=2000,
    n_inner=200,
    n_bins=15,
):
    """95% percentile interval of the size-matched difference on one partition.

    Each replicate resamples test learners with replacement. Empty sparse
    replicates are counted and are not dropped silently.
    """
    diffs = []
    empty = 0
    n_learners = len(sparse_clusters)
    for _ in range(n_boot):
        pick = rng.integers(0, n_learners, size=n_learners)
        ys, ps = [], []
        for j in pick:
            y, p = sparse_clusters[j]
            if len(y) == 0:
                continue
            ys.append(np.asarray(y))
            ps.append(np.asarray(p))
        if not ys:
            empty += 1
            continue
        sy = np.concatenate(ys)
        sp = np.concatenate(ps)
        inner = np.random.default_rng(int(rng.integers(0, 2**31 - 1)))
        row = size_matched_contrast(sy, sp, dense_clusters, inner, n_draws=n_inner, n_bins=n_bins)
        if np.isnan(row["size_matched_diff"]):
            empty += 1
            continue
        diffs.append(row["size_matched_diff"])
    if not diffs:
        lo = hi = float("nan")
    else:
        lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "n_boot": n_boot,
        "n_inner": n_inner,
        "n_empty_or_invalid": empty,
        "ci95_low": float(lo),
        "ci95_high": float(hi),
        "n_used": len(diffs),
    }
