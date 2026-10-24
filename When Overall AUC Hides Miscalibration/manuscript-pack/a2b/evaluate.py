#!/usr/bin/env python3
"""A2B evaluation on the masked XES3G5M tree only. Does not touch ASSISTments/Junyi."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.metrics import roc_auc_score
from scipy import stats

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from paths import ANALYSIS, DS, N_BINS, PRED, SEEDS, SPLITS, TABLES, TAU  # noqa: E402
from src.kc_strata import get_bucket  # noqa: E402

BUCKETS = ("dense", "medium", "sparse", "very_sparse", "strict_cold_start")
MODELS = ("irt_1pl", "dkt", "simplekt")
DUP_A, DUP_B = 2025, 2026


def kc_key(x) -> str:
    return str(x).replace(".0", "")


def flag(n: float) -> str:
    if n >= 1000:
        return "R"
    if n >= 100:
        return "L"
    return "I"


def compute_ece(y, p, n_bins=N_BINS) -> float:
    n = y.size
    if n == 0:
        return np.nan
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(p, edges[1:-1], right=True)
    ece = 0.0
    for m in range(n_bins):
        mask = idx == m
        n_m = int(mask.sum())
        if n_m == 0:
            continue
        ece += (n_m / n) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return ece


def brier_decomp(y, p, n_bins=N_BINS):
    n = y.size
    if n == 0:
        return np.nan, np.nan, np.nan, np.nan
    y_bar = float(y.mean())
    unc = y_bar * (1.0 - y_bar)
    brier = float(np.mean((p - y) ** 2))
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(p, edges[1:-1], right=True)
    rel = 0.0
    res = 0.0
    for m in range(n_bins):
        mask = idx == m
        n_m = int(mask.sum())
        if n_m == 0:
            continue
        acc_m = float(y[mask].mean())
        conf_m = float(p[mask].mean())
        rel += n_m * (conf_m - acc_m) ** 2
        res += n_m * (acc_m - y_bar) ** 2
    return brier, unc, rel / n, res / n


def calculate_metrics(y, p):
    if y.size == 0:
        return np.nan, np.nan, np.nan, np.nan
    p_c = np.clip(p, 1e-15, 1.0 - 1e-15)
    auc = roc_auc_score(y, p_c) if len(np.unique(y)) >= 2 else np.nan
    acc = float(np.mean(y == (p_c >= 0.5)))
    nll = float(-np.mean(y * np.log(p_c) + (1.0 - y) * np.log(1.0 - p_c)))
    rmse = float(np.sqrt(np.mean((p_c - y) ** 2)))
    return auc, acc, nll, rmse


def pred_file(split: str, model: str, seed: int) -> Path:
    return PRED / f"{DS}_{split}_{model}_seed{seed}_predictions_rerun.csv"


def load_pred(split: str, model: str, seed: int) -> pd.DataFrame | None:
    p = pred_file(split, model, seed)
    if not p.exists():
        return None
    df = pd.read_csv(p, usecols=["kc_id", "y_true", "p_pred"])
    df = df.dropna(subset=["y_true", "p_pred"])
    df = df[df["kc_id"].astype(str).str.replace(r"\.0$", "", regex=True) != "-1"]
    return df


def train_freq_map(split: str, fold: int) -> dict[str, int]:
    train = pd.read_csv(SPLITS / split / f"fold_{fold}" / "train.csv", usecols=["kc_id"])
    vc = train["kc_id"].map(kc_key).value_counts()
    return {k: int(v) for k, v in vc.items()}


def partition_id(seed: int) -> str:
    if seed in (DUP_A, DUP_B):
        return "P2_dup"
    return f"P_{seed}"


def agg_units(df: pd.DataFrame, keys: list[str], metric_cols: list[str]) -> pd.DataFrame:
    work = df.copy()
    work["partition"] = work["seed"].map(partition_id)
    part = work.groupby(keys + ["partition"], dropna=False)[metric_cols].mean().reset_index()
    g = part.groupby(keys, dropna=False)
    out = g[metric_cols].mean().add_suffix("_mean")
    out = out.join(g[metric_cols].std(ddof=1).add_suffix("_std"))
    out = out.join(g.size().rename("n_partitions"))
    return out.reset_index()


def score_learner_based() -> tuple[pd.DataFrame, pd.DataFrame]:
    overall, bucket = [], []
    for fold, seed in enumerate(SEEDS):
        freq = train_freq_map("learner_based", fold)
        for model in MODELS:
            df = load_pred("learner_based", model, seed)
            if df is None:
                print(f"MISSING learner_based {model} seed{seed}", flush=True)
                continue
            y = df["y_true"].to_numpy(dtype=int)
            p = df["p_pred"].to_numpy(dtype=float)
            auc, acc, nll, rmse = calculate_metrics(y, p)
            overall.append(
                dict(dataset=DS, model=model, seed=seed, fold=fold, n_events=int(y.size), auc=auc, acc=acc, nll=nll, rmse=rmse)
            )
            ftrain = df["kc_id"].map(lambda k: freq.get(kc_key(k), 0)).to_numpy()
            buckets = np.array([get_bucket(int(v)) for v in ftrain])
            kc = df["kc_id"].map(kc_key).to_numpy()
            for b in BUCKETS:
                mask = buckets == b
                if not mask.any():
                    continue
                yb, pb = y[mask], p[mask]
                bauc, bacc, bnll, brmse = calculate_metrics(yb, pb)
                ece = compute_ece(yb, pb)
                brier, unc, rel, res = brier_decomp(yb, pb)
                bucket.append(
                    dict(
                        dataset=DS, model=model, seed=seed, fold=fold, bucket=b,
                        n_kcs=int(pd.unique(kc[mask]).size), n_events=int(mask.sum()),
                        auc=bauc, acc=bacc, nll=bnll, rmse=brmse, ece=ece,
                        brier=brier, uncertainty=unc, reliability=rel, resolution=res,
                    )
                )
    ov = pd.DataFrame(overall)
    bk = pd.DataFrame(bucket)
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    if not ov.empty:
        ov.to_csv(ANALYSIS / "run_overall.csv", index=False)
        agg_units(ov, ["dataset", "model"], ["n_events", "auc", "acc", "nll", "rmse"]).to_csv(
            ANALYSIS / "summary_4part_overall.csv", index=False
        )
    if not bk.empty:
        bk.to_csv(ANALYSIS / "run_bucket.csv", index=False)
        cols = ["n_kcs", "n_events", "auc", "acc", "nll", "rmse", "ece", "brier", "uncertainty", "reliability", "resolution"]
        agg_units(bk, ["dataset", "model", "bucket"], cols).to_csv(ANALYSIS / "summary_4part_bucket.csv", index=False)
    return ov, bk


def score_temporal() -> pd.DataFrame:
    rows = []
    freq = train_freq_map("temporal", 0)
    for model in MODELS:
        df = load_pred("temporal", model, 42)
        if df is None:
            continue
        y = df["y_true"].to_numpy(dtype=int)
        p = df["p_pred"].to_numpy(dtype=float)
        auc, acc, nll, rmse = calculate_metrics(y, p)
        ece = compute_ece(y, p)
        brier, unc, rel, res = brier_decomp(y, p)
        rows.append(dict(split="temporal", model=model, seed=42, bucket="all", n_events=int(y.size), auc=auc, acc=acc, ece=ece, brier=brier, reliability=rel, resolution=res))
        ftrain = df["kc_id"].map(lambda k: freq.get(kc_key(k), 0)).to_numpy()
        buckets = np.array([get_bucket(int(v)) for v in ftrain])
        for b in BUCKETS:
            mask = buckets == b
            if not mask.any():
                continue
            yb, pb = y[mask], p[mask]
            bauc, bacc, bnll, brmse = calculate_metrics(yb, pb)
            bece = compute_ece(yb, pb)
            bbrier, bunc, brel, bres = brier_decomp(yb, pb)
            rows.append(dict(split="temporal", model=model, seed=42, bucket=b, n_events=int(mask.sum()), auc=bauc, acc=bacc, ece=bece, brier=bbrier, reliability=brel, resolution=bres))
    out = pd.DataFrame(rows)
    if not out.empty:
        out.to_csv(ANALYSIS / "temporal_seed42.csv", index=False)
    return out


def fm_miss(y, p, tau):
    y = y.astype(int)
    p = p.astype(float)
    adv = p >= tau
    n_adv = int(adv.sum())
    n_inc = int((y == 0).sum())
    fm = float(((y == 0) & adv).sum() / n_adv) if n_adv else np.nan
    miss = float(((y == 0) & adv).sum() / n_inc) if n_inc else np.nan
    return fm, miss, n_adv, int(y.size)


def score_gate() -> None:
    rows = []
    for fold, seed in enumerate(SEEDS):
        freq = train_freq_map("learner_based", fold)
        for model in ("dkt", "simplekt"):
            df = load_pred("learner_based", model, seed)
            if df is None:
                continue
            f = df["kc_id"].map(lambda k: freq.get(kc_key(k), 0))
            df = df.assign(bucket=f.map(get_bucket))
            dense = df[df["bucket"] == "dense"]
            sparse = df[df["bucket"] == "sparse"]
            fm_d, miss_d, nadv_d, n_d = fm_miss(dense["y_true"].to_numpy(), dense["p_pred"].to_numpy(), TAU)
            fm_s, miss_s, nadv_s, n_s = fm_miss(sparse["y_true"].to_numpy(), sparse["p_pred"].to_numpy(), TAU)
            rows.append(
                dict(
                    dataset=DS, model=model, seed=seed, fold=fold, tau=TAU,
                    sparse_n=n_s, sparse_flag=flag(n_s) if n_s else "empty",
                    sparse_n_advance=nadv_s, dense_n=n_d,
                    FM_sparse=fm_s, FM_dense=fm_d,
                    dFM=(fm_s - fm_d) if pd.notna(fm_s) and pd.notna(fm_d) else np.nan,
                    Miss_sparse=miss_s, Miss_dense=miss_d,
                    dMiss=(miss_s - miss_d) if pd.notna(miss_s) and pd.notna(miss_d) else np.nan,
                )
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out.to_csv(ANALYSIS / "gate_fivefold.csv", index=False)
        sk = out[out["model"] == "simplekt"]
        dkt = out[out["model"] == "dkt"]
        lines = []
        for name, g in (("dkt", dkt), ("simplekt", sk)):
            if g.empty:
                continue
            lines.append(
                f"{DS} {name}: dFM mean={g['dFM'].mean():.3f} sd={g['dFM'].std(ddof=1):.3f} "
                f"pos={(g['dFM']>0).sum()}/{len(g)} dMiss mean={g['dMiss'].mean():.3f} "
                f"sparse_n mean={g['sparse_n'].mean():.0f}"
            )
        (ANALYSIS / "c2_xes_verdict.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_kc_features(split="learner_based", fold=0) -> pd.DataFrame:
    train = pd.read_csv(SPLITS / split / f"fold_{fold}" / "train.csv", parse_dates=["timestamp"])
    train = train.sort_values(["user_id", "timestamp"]).copy()
    train["seq_rank"] = train.groupby("user_id").cumcount()
    user_seq_len = train.groupby("user_id")["seq_rank"].transform("max").replace(0, 1)
    train["normalized_seq_pos"] = train["seq_rank"] / user_seq_len
    rows = []
    for kc, grp in train.groupby("kc_id"):
        tf = len(grp)
        rows.append(
            dict(
                dataset=DS, split=split, fold=fold, kc_id=kc_key(kc),
                train_freq=tf, log_train_freq=np.log1p(tf),
                n_train_learners=int(grp["user_id"].nunique()),
                n_train_items=int(grp["item_id"].nunique()),
                train_correct_rate=float(grp["correct"].mean()),
                difficulty_proxy=1.0 - float(grp["correct"].mean()),
                median_sequence_position_train=float(grp["normalized_seq_pos"].median()),
            )
        )
    return pd.DataFrame(rows)


def regression_xes() -> None:
    feat = build_kc_features()
    feat.to_csv(ANALYSIS / "kc_covariates.csv", index=False)
    df = load_pred("learner_based", "simplekt", 42)
    if df is None:
        print("skip regression: no SimpleKT seed42", flush=True)
        return
    df["kc_id"] = df["kc_id"].map(kc_key)
    rows = []
    for kc, g in df.groupby("kc_id"):
        y = g["y_true"].to_numpy(dtype=int)
        p = np.clip(g["p_pred"].to_numpy(dtype=float), 1e-7, 1 - 1e-7)
        rows.append(dict(kc_id=kc, test_events=len(y), ECE=compute_ece(y, p)))
    met = pd.DataFrame(rows)
    merged = met.merge(feat, on="kc_id", how="inner")
    merged = merged.dropna(subset=["ECE", "log_train_freq", "difficulty_proxy", "n_train_items", "n_train_learners", "median_sequence_position_train"])
    merged.to_csv(ANALYSIS / "regression_input.csv", index=False)
    covariates = ["log_train_freq", "difficulty_proxy", "n_train_items", "n_train_learners", "median_sequence_position_train"]
    out_rows = []
    for weighted in (True, False):
        X = merged[covariates].to_numpy(dtype=float)
        X_std = (X - X.mean(0)) / (X.std(0, ddof=0) + 1e-12)
        y = merged["ECE"].to_numpy(dtype=float)
        w = merged["test_events"].to_numpy(dtype=float) if weighted else None
        try:
            model = HuberRegressor(max_iter=500)
            model.fit(X_std, y, sample_weight=w)
            coefs = model.coef_
        except Exception:
            model = LinearRegression()
            model.fit(X_std, y, sample_weight=w)
            coefs = model.coef_
        rng = np.random.default_rng(42)
        boot = []
        n = len(y)
        for _ in range(500):
            idx = rng.choice(n, size=n, replace=True)
            m = LinearRegression()
            m.fit(X_std[idx], y[idx], sample_weight=None if w is None else w[idx])
            boot.append(m.coef_)
        se = np.std(boot, axis=0)
        for name, coef, se_v in zip(covariates, coefs, se):
            t = coef / se_v if se_v > 0 else np.nan
            pval = 2 * (1 - stats.norm.cdf(abs(t))) if not np.isnan(t) else np.nan
            out_rows.append(
                dict(
                    covariate=name, coef_std=coef, SE=se_v, t=t, p=pval,
                    CI_lo=coef - 1.96 * se_v, CI_hi=coef + 1.96 * se_v,
                    n=n, weighted=weighted, dataset=DS, model="simplekt",
                )
            )
    pd.DataFrame(out_rows).to_csv(ANALYSIS / "regression_results.csv", index=False)


def a9_select() -> None:
    """XES-only A9 selection + downsample into a2b tree."""
    d = SPLITS / "learner_based" / "fold_0"
    train = pd.read_csv(d / "train.csv")
    test = pd.read_csv(d / "test.csv", usecols=["kc_id", "correct"])
    train["_kc"] = train["kc_id"].map(kc_key)
    test["kc_id"] = test["kc_id"].map(kc_key)
    pred_kcs = None
    for m in ("dkt", "simplekt"):
        p = pred_file("learner_based", m, 42)
        if not p.exists():
            print("skip a9: missing seed42 preds", flush=True)
            return
        s = set(pd.read_csv(p, usecols=["kc_id"])["kc_id"].map(kc_key))
        pred_kcs = s if pred_kcs is None else (pred_kcs & s)
    tr = train.groupby("_kc").agg(train_freq=("correct", "size"), train_correct_rate=("correct", "mean"))
    te = test.groupby("kc_id").agg(test_n=("correct", "size"), test_pos=("correct", "sum"))
    te["test_neg"] = te["test_n"] - te["test_pos"]
    tr.index.name = "kc_id"
    te.index.name = "kc_id"
    tab = tr.join(te, how="inner").reset_index()
    tab["difficulty_proxy"] = 1.0 - tab["train_correct_rate"]
    tab["in_official_preds"] = tab["kc_id"].isin(pred_kcs)
    tab["eligible"] = (
        (tab["train_freq"] >= 500)
        & (tab["test_n"] >= 100)
        & (tab["test_pos"] >= 20)
        & (tab["test_neg"] >= 20)
        & (tab["in_official_preds"])
    )
    eligible = tab[tab["eligible"]].copy()
    if len(eligible) <= 30:
        selected = eligible.sort_values("kc_id")
    else:
        eligible["tert"] = pd.qcut(eligible["difficulty_proxy"], 3, labels=["T1_easier", "T2", "T3_harder"], duplicates="drop")
        parts = [g.sort_values("kc_id").head(10) for _, g in eligible.groupby("tert", observed=True)]
        selected = pd.concat(parts, ignore_index=True).sort_values("kc_id")
    selected["dataset"] = DS
    tab["dataset"] = DS
    a9 = ANALYSIS / "a9"
    a9.mkdir(parents=True, exist_ok=True)
    tab.to_csv(a9 / "kc_eligibility.csv", index=False)
    selected.to_csv(a9 / "selected_kcs.csv", index=False)
    selected_ids = set(selected["kc_id"].map(kc_key))
    freq = selected.set_index("kc_id")["train_freq"].to_dict()
    dest_root = HERE / "data" / "processed" / "a9" / DS
    for split_name in ("valid.csv", "test.csv"):
        src = d / split_name
        for k in (500, 100, 50):
            dest = dest_root / f"t{k}" / "learner_based" / "fold_0"
            dest.mkdir(parents=True, exist_ok=True)
            (dest / split_name).write_bytes(src.read_bytes())
    others = train[~train["_kc"].isin(selected_ids)]
    for k in (500, 100, 50):
        keep_parts = [others]
        for kc in sorted(selected_ids):
            n_full = int(freq[kc])
            n_keep = k if n_full > k else n_full
            sub = train[train["_kc"] == kc]
            if n_full > k:
                h = hashlib.sha256(f"{DS}|{kc}|{k}|a9".encode()).hexdigest()
                salt = int(h[:8], 16) % (2**31)
                rng = np.random.default_rng(salt)
                pick = rng.choice(len(sub), size=n_keep, replace=False)
                pick.sort()
                keep_parts.append(sub.iloc[pick])
            else:
                keep_parts.append(sub)
        out = pd.concat(keep_parts, ignore_index=True).drop(columns=["_kc"], errors="ignore")
        dest = dest_root / f"t{k}" / "learner_based" / "fold_0"
        dest.mkdir(parents=True, exist_ok=True)
        out.to_csv(dest / "train.csv", index=False)
        n_pad = int((out["kc_id"].astype(str).str.replace(r"\.0$", "", regex=True) == "-1").sum())
        print(f"a9 t{k} train={len(out)} pad={n_pad} selected={len(selected_ids)}", flush=True)


def main() -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    print("== four-partition ==", flush=True)
    score_learner_based()
    print("== temporal ==", flush=True)
    score_temporal()
    print("== gate ==", flush=True)
    score_gate()
    print("== covariates / regression ==", flush=True)
    regression_xes()
    print("== a9 select ==", flush=True)
    a9_select()
    print("evaluate done", flush=True)


if __name__ == "__main__":
    main()
