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
    """Draw learners without replacement until at least n rows, then keep n at random.

    Matches appendix P-6.3: the last learner may overshoot n, so the kept
    rows are a random subset, not a prefix of the concatenated clusters.
    """
    ys, ps, total = [], [], 0
    order = rng.permutation(len(dense_clusters))
    for j in order:
        y, p = dense_clusters[j]
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
    """Draw n rows without replacement, ignoring learner clusters."""
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    if len(y) < n:
        return None
    keep = rng.choice(len(y), size=n, replace=False)
    return y[keep], p[keep]


def size_matched_contrast(
    sparse_y, sparse_p, dense_clusters, rng, n_draws=2000, n_bins=15, draw_store=None
):
    """Return sparse ECE, median dense ECE at the same N, and the exceedance rate.

    draw_store, when given, receives every valid dense ECE in draw order.
    """
    n = len(sparse_y)
    ece_s = ece(sparse_y, sparse_p, n_bins=n_bins)
    draws = []
    invalid = 0
    for _ in range(n_draws):
        got = dense_at_n(dense_clusters, n, rng)
        if got is None:
            invalid += 1
            if draw_store is not None:
                draw_store.append(float("nan"))
            continue
        value = ece(got[0], got[1], n_bins=n_bins)
        draws.append(value)
        if draw_store is not None:
            draw_store.append(value)
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


def _concat_picked(groups, pick):
    parts_y, parts_p = [], []
    for j in pick:
        y, p = groups[j]
        if len(y) == 0:
            continue
        parts_y.append(np.asarray(y))
        parts_p.append(np.asarray(p, dtype=float))
    if not parts_y:
        return None
    return np.concatenate(parts_y), np.concatenate(parts_p)


def cluster_bootstrap_diff(
    user_sparse,
    user_dense,
    rng,
    n_boot=2000,
    n_inner=200,
    n_bins=15,
    replicate_store=None,
):
    """95% intervals on one partition for raw ΔECE and the size-matched gap.

    user_sparse and user_dense are aligned by test learner. A learner may
    have an empty side. Each replicate resamples learners with replacement;
    a repeated learner is a separate cluster. Empty sparse replicates are
    counted and are not dropped silently. The dense side of the size-matched
    draw is built from that same replicate.
    """
    if len(user_sparse) != len(user_dense):
        raise ValueError("sparse and dense learner lists must be aligned")
    n_learners = len(user_sparse)
    raw, matched = [], []
    empty = 0
    empty_sparse = 0
    for replicate_id in range(n_boot):
        pick = rng.integers(0, n_learners, size=n_learners)
        sparse = _concat_picked(user_sparse, pick)
        dense = _concat_picked(user_dense, pick)
        record = {
            "replicate_id": replicate_id,
            "ece_focal": float("nan"),
            "ece_dense": float("nan"),
            "delta_ece": float("nan"),
            "matched_dense_median": float("nan"),
            "matched_gap": float("nan"),
        }
        if sparse is None:
            empty_sparse += 1
            empty += 1
            if replicate_store is not None:
                replicate_store.append(record)
            continue
        if dense is None:
            empty += 1
            if replicate_store is not None:
                replicate_store.append(record)
            continue
        ece_s = ece(sparse[0], sparse[1], n_bins=n_bins)
        ece_d = ece(dense[0], dense[1], n_bins=n_bins)
        raw.append(ece_s - ece_d)
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
        record["ece_focal"] = ece_s
        record["ece_dense"] = ece_d
        record["delta_ece"] = ece_s - ece_d
        record["matched_dense_median"] = row["ece_dense_at_n_median"]
        record["matched_gap"] = row["size_matched_diff"]
        if replicate_store is not None:
            replicate_store.append(record)
        if np.isnan(row["size_matched_diff"]):
            empty += 1
            continue
        matched.append(row["size_matched_diff"])
    def _ci(values):
        if not values:
            return float("nan"), float("nan")
        lo, hi = np.percentile(values, [2.5, 97.5])
        return float(lo), float(hi)
    raw_lo, raw_hi = _ci(raw)
    mat_lo, mat_hi = _ci(matched)
    return {
        "n_boot": n_boot,
        "n_inner": n_inner,
        "n_empty_or_invalid": empty,
        "n_empty_sparse": empty_sparse,
        "n_used": len(matched),
        "ci95_low": mat_lo,
        "ci95_high": mat_hi,
        "raw_ci95_low": raw_lo,
        "raw_ci95_high": raw_hi,
        "n_raw_used": len(raw),
    }


def ece0_bound(n, n_bins=15) -> float:
    """Bản I reference bound, 0.5 * sqrt(M / N). Not a confidence interval.

    Subtracting this sparse-side bound from ΔECE reproduced the published
    ΔECE* of 0.078 on N = 415 and M = 15.
    """
    if n <= 0:
        return float("nan")
    return float(0.5 * np.sqrt(n_bins / n))


def equal_mass_edges(n, n_bins):
    if n_bins > n or n_bins < 1:
        raise ValueError("n_bins must be between 1 and n")
    base, rem = divmod(n, n_bins)
    sizes = [base + 1] * rem + [base] * (n_bins - rem)
    edges = np.cumsum([0] + sizes)
    return edges


def ece_from_sorted(y_sorted, p_sorted, edges) -> float:
    total = len(y_sorted)
    score = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        yb = y_sorted[left:right]
        pb = p_sorted[left:right]
        if len(yb) == 0:
            continue
        score += (len(yb) / total) * abs(float(np.mean(yb)) - float(np.mean(pb)))
    return float(score)


def ece_equal_mass(y, p, n_bins=15) -> float:
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    mask = ~np.isnan(p)
    y, p = y[mask], p[mask]
    if len(y) < n_bins:
        return float("nan")
    order = np.argsort(p, kind="mergesort")
    edges = equal_mass_edges(len(y), n_bins)
    return ece_from_sorted(y[order], p[order], edges)


def ece_sweep(y, p) -> tuple[float, int]:
    """Equal-mass L1 ECE at the largest monotonic bin count (Roelofs et al. 2022).

    Algorithm 1 starts at 2 bins and stops at the first non-monotonic accuracy
    curve, then reports the previous bin count. One bin is the fallback.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    mask = ~np.isnan(p)
    y, p = y[mask], p[mask]
    n = len(y)
    if n == 0:
        return float("nan"), 0
    order = np.argsort(p, kind="mergesort")
    y_sorted, p_sorted = y[order], p[order]
    chosen = 1
    for b in range(2, n + 1):
        edges = equal_mass_edges(n, b)
        accs = [float(np.mean(y_sorted[left:right])) for left, right in zip(edges[:-1], edges[1:])]
        if any(accs[i] < accs[i - 1] for i in range(1, len(accs))):
            break
        chosen = b
    edges = equal_mass_edges(n, chosen)
    return ece_from_sorted(y_sorted, p_sorted, edges), chosen


def kumar_squared_ce(y, p, n_bins=15) -> float:
    """Less-biased squared calibration error on the same 15 equal-width bins.

    For a bin with n_b >= 2 the contribution is
    (acc - conf)^2 - acc * (1 - acc) / (n_b - 1), weighted by n_b / N.
    The correction is the sampling variance of the bin accuracy. The sum may
    be negative. Bins smaller than 2 are omitted.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    mask = ~np.isnan(p)
    y, p = y[mask], p[mask]
    n = len(y)
    if n == 0:
        return float("nan")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        if left == 0:
            inside = (p >= left) & (p <= right)
        else:
            inside = (p > left) & (p <= right)
        n_b = int(np.sum(inside))
        if n_b < 2:
            continue
        acc = float(np.mean(y[inside]))
        conf = float(np.mean(p[inside]))
        debiased = (acc - conf) ** 2 - (acc * (1.0 - acc) / (n_b - 1))
        total += (n_b / n) * debiased
    return float(total)
