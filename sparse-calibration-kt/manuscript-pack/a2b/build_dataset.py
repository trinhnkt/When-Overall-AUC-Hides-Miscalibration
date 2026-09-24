#!/usr/bin/env python3
"""A2B: flatten XES3G5M with valid masking, preprocess, splits, strata.

Writes only under IJIET_FINAL_REVISION/a2b/. Does not touch historical artifacts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import (  # noqa: E402
    A2B,
    ANALYSIS,
    DUP_DST_FOLD,
    DUP_SRC_FOLD,
    FLAT,
    LOG,
    MIN_SEQ,
    PROCESSED,
    SPLIT_SEEDS,
    SPLITS,
    TABLES,
    TE,
    TV,
    DS,
)


def _tok(x) -> str:
    return str(x).strip()


def _is_pad_id(s: str) -> bool:
    return s in {"-1", "-1.0", "nan", "None", "NaN", ""}


def flatten_one(path: Path, has_selectmask: bool) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path)
    stats = {
        "file": path.name,
        "n_sequences": int(len(df)),
        "tokens_seen": 0,
        "kept": 0,
        "drop_selectmask": 0,
        "drop_kc": 0,
        "drop_item": 0,
        "drop_label": 0,
    }
    rows = []
    sm_col = "selectmasks" if has_selectmask and "selectmasks" in df.columns else None
    for _, row in df.iterrows():
        uid = str(row["uid"])
        qs = str(row["questions"]).split(",")
        cs = str(row["concepts"]).split(",")
        rs = str(row["responses"]).split(",")
        ts = str(row["timestamps"]).split(",")
        n = min(len(qs), len(cs), len(rs), len(ts))
        if sm_col is not None and pd.notna(row[sm_col]):
            sm = str(row[sm_col]).split(",")
        else:
            sm = ["1"] * n
        if len(sm) < n:
            sm = sm + ["1"] * (n - len(sm))
        for i in range(n):
            stats["tokens_seen"] += 1
            q, c, r, t = _tok(qs[i]), _tok(cs[i]), _tok(rs[i]), _tok(ts[i])
            m = _tok(sm[i])
            if m not in {"1", "1.0"}:
                stats["drop_selectmask"] += 1
                continue
            if _is_pad_id(c):
                stats["drop_kc"] += 1
                continue
            if _is_pad_id(q):
                stats["drop_item"] += 1
                continue
            try:
                lab = int(float(r))
            except (TypeError, ValueError):
                stats["drop_label"] += 1
                continue
            if lab not in (0, 1):
                stats["drop_label"] += 1
                continue
            rows.append(
                {
                    "user_id": uid,
                    "question_id": q,
                    "skill_id": c,
                    "correct": lab,
                    "timestamp": pd.to_datetime(int(t), unit="ms").strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            stats["kept"] += 1
    return pd.DataFrame(rows), stats


def flatten() -> pd.DataFrame:
    FLAT.parent.mkdir(parents=True, exist_ok=True)
    LOG.mkdir(parents=True, exist_ok=True)
    tv, st_tv = flatten_one(TV, has_selectmask=True)
    te, st_te = flatten_one(TE, has_selectmask="selectmasks" in pd.read_csv(TE, nrows=0).columns)
    out = pd.concat([tv, te], ignore_index=True)
    out.to_csv(FLAT, index=False)
    (LOG / "flatten_drop_log.json").write_text(
        json.dumps({"train_valid": st_tv, "test": st_te, "n_flat": int(len(out))}, indent=2),
        encoding="utf-8",
    )
    print(f"flatten kept={len(out)} tv={st_tv} te={st_te}", flush=True)
    return out


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    d = df.rename(
        columns={
            "question_id": "item_id",
            "skill_id": "kc_id",
        }
    )[["user_id", "item_id", "kc_id", "timestamp", "correct"]].copy()
    d = d.dropna(subset=["user_id", "kc_id", "correct"])
    d["correct"] = pd.to_numeric(d["correct"], errors="coerce")
    d = d.dropna(subset=["correct"])
    d = d[d["correct"].isin([0, 1])]
    d["correct"] = d["correct"].astype(int)
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d = d.dropna(subset=["timestamp"])
    for col in ("user_id", "item_id", "kc_id"):
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna(subset=["user_id", "item_id", "kc_id"])
    d["user_id"] = d["user_id"].astype("int64")
    d["item_id"] = d["item_id"].astype("int64")
    d["kc_id"] = d["kc_id"].astype("int64")
    d = d[(d["kc_id"] != -1) & (d["item_id"] != -1)]
    d = d.sort_values(["user_id", "timestamp"])
    vc = d["user_id"].value_counts()
    d = d[d["user_id"].isin(vc[vc >= MIN_SEQ].index)]
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(PROCESSED, index=False)
    stats = {
        "dataset": DS,
        "processed_interactions": int(len(d)),
        "n_users": int(d["user_id"].nunique()),
        "n_items": int(d["item_id"].nunique()),
        "n_kcs": int(d["kc_id"].nunique()),
        "avg_seq_len": float(d.groupby("user_id").size().mean()),
        "n_kc_minus1": int((d["kc_id"].astype(str).str.replace(r"\.0$", "", regex=True) == "-1").sum()),
        "n_item_minus1": int((d["item_id"].astype(str).str.replace(r"\.0$", "", regex=True) == "-1").sum()),
        "correct_mean": float(d["correct"].mean()),
    }
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([stats]).to_csv(TABLES / "dataset_stats.csv", index=False)
    print(f"processed {stats}", flush=True)
    if stats["n_kcs"] != 865 or stats["n_items"] != 7652 or stats["n_kc_minus1"] != 0:
        raise SystemExit(f"masking failed: {stats}")
    return d


def save_split(df: pd.DataFrame, mode: str, fold: int, name: str) -> None:
    out = SPLITS / mode / f"fold_{fold}"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"{name}.csv", index=False)
    print(f"  saved {mode}/fold_{fold}/{name}.csv n={len(df)}", flush=True)


def learner_split_from_historical_users(df: pd.DataFrame, fold: int) -> None:
    """Same learners as the published folds; padding rows already removed from df."""
    old = Path(__file__).resolve().parents[2] / "data" / "processed" / "xes3g5m" / "splits" / "learner_based"
    for part in ("train", "valid", "test"):
        users = pd.read_csv(old / f"fold_{fold}" / f"{part}.csv", usecols=["user_id"])["user_id"]
        users = set(pd.to_numeric(users, errors="coerce").dropna().astype("int64"))
        sub = df[df["user_id"].isin(users)]
        if len(sub) == 0:
            raise SystemExit(f"no rows for historical {part} users fold_{fold}")
        save_split(sub, "learner_based", fold, part)


def copy_fold(src: int, dst: int, mode: str = "learner_based") -> None:
    sdir = SPLITS / mode / f"fold_{src}"
    ddir = SPLITS / mode / f"fold_{dst}"
    ddir.mkdir(parents=True, exist_ok=True)
    for name in ("train.csv", "valid.csv", "test.csv"):
        (ddir / name).write_bytes((sdir / name).read_bytes())
    print(f"  copied {mode}/fold_{src} -> fold_{dst}", flush=True)


def temporal_split(df: pd.DataFrame) -> None:
    d = df.sort_values("timestamp")
    n = len(d)
    n_train = int(n * 0.7)
    n_valid = int(n * 0.1)
    save_split(d.iloc[:n_train], "temporal", 0, "train")
    save_split(d.iloc[n_train : n_train + n_valid], "temporal", 0, "valid")
    save_split(d.iloc[n_train + n_valid :], "temporal", 0, "test")


def get_bucket(freq: int) -> str:
    if freq == 0:
        return "strict_cold_start"
    if freq < 20:
        return "very_sparse"
    if freq < 100:
        return "sparse"
    if freq < 500:
        return "medium"
    return "dense"


def strata() -> pd.DataFrame:
    rows = []
    for mode, folds in (("learner_based", range(5)), ("temporal", [0])):
        for fold in folds:
            base = SPLITS / mode / f"fold_{fold}"
            train = pd.read_csv(base / "train.csv", usecols=["kc_id"])
            valid = pd.read_csv(base / "valid.csv", usecols=["kc_id"])
            test = pd.read_csv(base / "test.csv", usecols=["kc_id"])
            tr = train["kc_id"].value_counts().to_dict()
            va = valid["kc_id"].value_counts().to_dict()
            te = test["kc_id"].value_counts().to_dict()
            kcs = sorted(set(tr) | set(va) | set(te), key=lambda x: str(x))
            for kc in kcs:
                tf = int(tr.get(kc, 0))
                rows.append(
                    {
                        "dataset": DS,
                        "split": mode,
                        "fold": fold,
                        "kc_id": kc,
                        "train_freq": tf,
                        "valid_freq": int(va.get(kc, 0)),
                        "test_freq": int(te.get(kc, 0)),
                        "bucket": get_bucket(tf),
                    }
                )
    out = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES / "kc_strata.csv", index=False)
    n_m1 = int((out["kc_id"].astype(str).str.replace(r"\.0$", "", regex=True) == "-1").sum())
    print(f"strata rows={len(out)} kc_-1_rows={n_m1}", flush=True)
    if n_m1:
        raise SystemExit("strata still contains kc_id=-1")
    return out


def verify_users_vs_historical() -> None:
    old = Path(__file__).resolve().parents[2] / "data" / "processed" / "xes3g5m" / "splits" / "learner_based"
    report = []
    for fold in range(5):
        for part in ("train", "valid", "test"):
            a = set(pd.read_csv(SPLITS / "learner_based" / f"fold_{fold}" / f"{part}.csv", usecols=["user_id"])["user_id"].astype(str))
            b = set(pd.read_csv(old / f"fold_{fold}" / f"{part}.csv", usecols=["user_id"])["user_id"].astype(str))
            report.append(
                {
                    "fold": fold,
                    "part": part,
                    "n_new": len(a),
                    "n_old": len(b),
                    "equal": a == b,
                    "symdiff": len(a ^ b),
                }
            )
    pd.DataFrame(report).to_csv(LOG / "split_user_overlap.csv", index=False)
    print(pd.DataFrame(report).to_string(index=False), flush=True)


def repair_learner_splits() -> None:
    df = pd.read_csv(PROCESSED)
    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("int64")
    print("== repair learner splits ==", flush=True)
    for fold in range(5):
        print(f" fold_{fold}", flush=True)
        learner_split_from_historical_users(df, fold)
    print("== strata ==", flush=True)
    strata()
    print("== verify users ==", flush=True)
    verify_users_vs_historical()


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--repair-splits", action="store_true")
    args = p.parse_args()
    if args.repair_splits:
        repair_learner_splits()
        print("repair done", flush=True)
        return
    A2B.mkdir(parents=True, exist_ok=True)
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    print("== flatten ==", flush=True)
    raw = flatten()
    print("== preprocess ==", flush=True)
    df = preprocess(raw)
    print("== learner splits (historical users, masked rows) ==", flush=True)
    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("int64")
    for fold in range(5):
        print(f" fold_{fold} from historical user sets", flush=True)
        learner_split_from_historical_users(df, fold)
    print("== temporal ==", flush=True)
    temporal_split(df)
    print("== strata ==", flush=True)
    strata()
    print("== verify users ==", flush=True)
    verify_users_vs_historical()
    print("build_dataset done", flush=True)


if __name__ == "__main__":
    main()
