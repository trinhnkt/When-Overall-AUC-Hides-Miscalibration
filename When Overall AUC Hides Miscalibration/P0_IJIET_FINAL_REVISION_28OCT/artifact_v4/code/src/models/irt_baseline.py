"""
irt_baseline.py
===============
IRT 1PL (Rasch Model) baseline for Knowledge Tracing.

Convention:
  P(correct | learner u, KC c) = sigmoid(theta_u - beta_c)
  where:
    theta_u: learner ability parameter
    beta_c:  KC difficulty parameter (in KT context, per-KC rather than per-item)

Training:
  - Fit on train split ONLY (P1-compliant)
  - SGD optimization with L2 regularization
  - Out-of-vocabulary (new) users/KCs at test time: use bias-only prediction (global mean)

Output schema (same as DKT/SimpleKT/BKT):
  user_id, item_id, kc_id, timestamp, y_true, p_pred, dataset, split_mode, model, seed
"""

import numpy as np
import pandas as pd
from scipy.special import expit
from pathlib import Path


class IRT1PL:
    """
    IRT 1-Parameter Logistic (Rasch) model.
    
    P(correct | user u, KC c) = sigmoid(theta_u - beta_c)
    
    Fitted via mini-batch SGD on (user, KC, correct) triples from train data.
    Parameters are indexed by integer index — OOV entities get global-mean prediction.
    """

    def __init__(self, seed=42, lr=0.01, reg=0.01, epochs=10, batch_size=512):
        self.seed = seed
        self.lr = lr
        self.reg = reg
        self.epochs = epochs
        self.batch_size = batch_size

        # To be populated on fit
        self.theta = None     # (n_users,) learner ability
        self.beta  = None     # (n_kcs,) KC difficulty
        self.bias  = 0.0      # global log-odds (fallback for OOV)
        self.user_to_idx = {}
        self.kc_to_idx   = {}

    def fit(self, train_df, verbose=True):
        """
        Fit on train_df with columns: user_id, kc_id, correct.
        """
        np.random.seed(self.seed)

        users = sorted(train_df["user_id"].unique())
        kcs   = sorted(train_df["kc_id"].unique())

        self.user_to_idx = {u: i for i, u in enumerate(users)}
        self.kc_to_idx   = {c: i for i, c in enumerate(kcs)}

        n_u, n_c = len(users), len(kcs)
        self.theta = np.zeros(n_u, dtype=np.float64)
        self.beta  = np.zeros(n_c, dtype=np.float64)

        # Set bias to log-odds of global mean
        mean_y = train_df["correct"].mean()
        self.bias = np.log(mean_y / (1 - mean_y + 1e-10))

        u_idx = train_df["user_id"].map(self.user_to_idx).values
        c_idx = train_df["kc_id"].map(self.kc_to_idx).values
        y     = train_df["correct"].values.astype(np.float64)
        n     = len(y)

        if verbose:
            print(f"  IRT 1PL: n_users={n_u}, n_kcs={n_c}, n_train={n}, "
                  f"epochs={self.epochs}, lr={self.lr}, reg={self.reg}")

        for ep in range(self.epochs):
            perm = np.random.permutation(n)
            epoch_loss = 0.0
            for b in range(0, n, self.batch_size):
                batch = perm[b:b + self.batch_size]
                u, c, yb = u_idx[batch], c_idx[batch], y[batch]
                p = expit(self.theta[u] - self.beta[c])
                err = p - yb
                # SGD update
                self.theta[u] -= self.lr * (err + self.reg * self.theta[u])
                self.beta[c]  += self.lr * (err - self.reg * self.beta[c])
                p_safe = np.clip(p, 1e-7, 1 - 1e-7)
                epoch_loss -= np.mean(yb * np.log(p_safe) + (1 - yb) * np.log(1 - p_safe))
            if verbose:
                print(f"    Epoch {ep+1}/{self.epochs}: loss={epoch_loss:.4f}")

    def predict(self, df):
        """
        Predict P(correct) for rows in df (user_id, kc_id columns required).
        OOV users/KCs → global bias-only prediction.
        
        Returns np.array of shape (len(df),) in original row order.
        """
        u_idx = df["user_id"].map(self.user_to_idx)
        c_idx = df["kc_id"].map(self.kc_to_idx)

        p_pred = np.full(len(df), expit(self.bias), dtype=np.float64)

        known = ~u_idx.isna() & ~c_idx.isna()
        if known.any():
            u = u_idx[known].astype(int).values
            c = c_idx[known].astype(int).values
            p_pred[known.values] = expit(self.theta[u] - self.beta[c])

        return p_pred

    def get_params_df(self, top_n=50):
        """Return top_n most extreme parameters for audit."""
        records = []
        for u, i in list(self.user_to_idx.items())[:top_n]:
            records.append({"type": "user", "id": u, "theta_or_beta": self.theta[i]})
        for c, i in list(self.kc_to_idx.items()):
            records.append({"type": "kc", "id": c, "theta_or_beta": self.beta[i]})
        return pd.DataFrame(records)


def run_irt_on_split(dataset, split_mode, fold, seed,
                     split_base=Path("data/processed"),
                     pred_dir=Path("results/predictions"),
                     verbose=True):
    """
    Full pipeline: load splits, fit IRT on train, predict on test, save CSV.
    Returns pred_df.
    """
    fold_path = split_base / dataset / "splits" / split_mode / f"fold_{fold}"
    if not (fold_path / "train.csv").exists():
        print(f"  Split not found: {fold_path}")
        return None

    train = pd.read_csv(fold_path / "train.csv")
    test  = pd.read_csv(fold_path / "test.csv")

    if verbose:
        print(f"\n  [{dataset} | {split_mode} | fold={fold} | seed={seed}]")
        print(f"  Train: {len(train)}, Test: {len(test)}")

    model = IRT1PL(seed=seed)
    model.fit(train, verbose=verbose)

    p_pred = model.predict(test)
    y_true = test["correct"].values

    pred_df = test.copy()
    pred_df["dataset"]    = dataset
    pred_df["split_mode"] = split_mode
    pred_df["model"]      = "irt_1pl"
    pred_df["seed"]       = seed
    pred_df["p_pred"]     = p_pred
    pred_df["y_true"]     = y_true

    output_cols = ["dataset", "split_mode", "model", "seed",
                   "user_id", "item_id", "kc_id", "timestamp", "y_true", "p_pred"]
    output_cols = [c for c in output_cols if c in pred_df.columns]
    pred_df = pred_df[output_cols]

    pred_dir.mkdir(parents=True, exist_ok=True)
    out_path = pred_dir / f"{dataset}_{split_mode}_irt_1pl_seed{seed}.csv"
    pred_df.to_csv(out_path, index=False)
    if verbose:
        print(f"  Saved: {out_path}")

    # Quick metrics
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y_true)) >= 2:
        auc = roc_auc_score(y_true, p_pred)
        print(f"  AUC={auc:.4f}, y_mean={y_true.mean():.4f}, p_mean={p_pred.mean():.4f}")

    return pred_df


if __name__ == "__main__":
    # Sanity run: ASSIST2012 both splits, seed=42
    import argparse
    parser = argparse.ArgumentParser(description="IRT 1PL Baseline for KT")
    parser.add_argument("--dataset", default="assist2012")
    parser.add_argument("--split", default="temporal")
    parser.add_argument("--fold", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_irt_on_split(args.dataset, args.split, args.fold, args.seed)
