"""FAR at tau = 0.7 and the binned Brier decomposition for Tables A1, A3, and A4.

Same definitions as P0_IJIET_FINAL_REVISION_28OCT/scripts/a3_recompute_far_brier.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TAU = 0.7
SEED = 20261021
B = 2000


def far_stats(y: np.ndarray, p: np.ndarray) -> dict:
    adv = p >= TAU
    inc = y == 0
    n_adv = int(adv.sum())
    n_inc = int(inc.sum())
    far = float(np.mean(inc[adv])) if n_adv else float("nan")
    e_far = float(np.mean(1.0 - p[adv])) if n_adv else float("nan")
    return {
        "N": int(len(y)),
        "N_adv": n_adv,
        "N_inc": n_inc,
        "FAR": far,
        "E_FAR": e_far,
        "excess": far - e_far,
        "FPR": float(np.mean(adv[inc])) if n_inc else float("nan"),
    }


def _kc_table(kc: np.ndarray, y: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    adv = p >= TAU
    bad = adv & (y == 0)
    agg = (
        pd.DataFrame({"kc": kc, "adv": adv.astype(int), "bad": bad.astype(int)})
        .groupby("kc", sort=True)
        .sum()
    )
    return agg["adv"].to_numpy(), agg["bad"].to_numpy()


def far_bootstrap(sparse: tuple, dense: tuple) -> dict:
    """KC-clustered percentile bootstrap; a fresh Generator per model."""
    rng = np.random.default_rng(SEED)
    s_adv, s_bad = _kc_table(*sparse)
    d_adv, d_bad = _kc_table(*dense)
    far_s, far_d, delta = [], [], []
    invalid = 0
    for _ in range(B):
        i = rng.integers(0, len(s_adv), size=len(s_adv))
        j = rng.integers(0, len(d_adv), size=len(d_adv))
        na_s, na_d = s_adv[i].sum(), d_adv[j].sum()
        if na_s == 0 or na_d == 0:
            invalid += 1
            continue
        fs = s_bad[i].sum() / na_s
        fd = d_bad[j].sum() / na_d
        far_s.append(fs)
        far_d.append(fd)
        delta.append(fs - fd)

    def ci(values):
        lo, hi = np.percentile(values, [2.5, 97.5])
        return float(lo), float(hi)

    return {"sparse": ci(far_s), "dense": ci(far_d), "delta": ci(delta), "invalid": invalid}


def brier_decomposition(y: np.ndarray, p: np.ndarray, n_bins: int = 15) -> tuple[float, float, float, float]:
    y = y.astype(float)
    n = len(y)
    y_bar = float(np.mean(y))
    unc = y_bar * (1 - y_bar)
    edges = np.linspace(0, 1, n_bins + 1)
    rel = res = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        inside = (p > left) & (p <= right)
        if left == 0:
            inside |= p == 0
        n_m = int(inside.sum())
        if n_m:
            acc = float(np.mean(y[inside]))
            conf = float(np.mean(p[inside]))
            rel += n_m * (conf - acc) ** 2
            res += n_m * (acc - y_bar) ** 2
    brier = float(np.mean((p - y) ** 2))
    return brier, unc, rel / n, res / n
