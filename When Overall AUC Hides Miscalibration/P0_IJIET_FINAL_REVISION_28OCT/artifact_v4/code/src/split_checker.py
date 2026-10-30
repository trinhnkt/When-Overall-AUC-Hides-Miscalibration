import pandas as pd
import argparse
import os
from pathlib import Path

def audit_learner_split(dataset, fold=0):
    """Audits learner_based split for user overlap."""
    base_path = Path(f"data/processed/{dataset}/splits/learner_based/fold_{fold}")
    if not (base_path / "train.csv").exists(): return None
    
    train = pd.read_csv(base_path / "train.csv")
    valid = pd.read_csv(base_path / "valid.csv")
    test = pd.read_csv(base_path / "test.csv")
    
    train_users = set(train['user_id'].unique())
    valid_users = set(valid['user_id'].unique())
    test_users = set(test['user_id'].unique())
    
    overlap_tt = train_users.intersection(test_users)
    overlap_vt = valid_users.intersection(test_users)
    
    status = "PASS" if not (overlap_tt or overlap_vt) else "FAIL"
    
    return {
        "dataset": dataset,
        "split_mode": "learner_based",
        "fold": fold,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
        "violation_count": len(overlap_tt) + len(overlap_vt),
        "status": status
    }

def audit_temporal_split(dataset, fold=0):
    """Audits temporal split for timestamp leakage."""
    base_path = Path(f"data/processed/{dataset}/splits/temporal/fold_{fold}")
    if not (base_path / "train.csv").exists(): return None
    
    train = pd.read_csv(base_path / "train.csv")
    valid = pd.read_csv(base_path / "valid.csv")
    test = pd.read_csv(base_path / "test.csv")
    
    train_max = pd.to_datetime(train['timestamp']).max()
    test_min = pd.to_datetime(test['timestamp']).min()
    
    status = "PASS" if train_max <= test_min else "FAIL"
    
    return {
        "dataset": dataset,
        "split_mode": "temporal",
        "fold": fold,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
        "violation_count": 1 if train_max > test_min else 0,
        "status": status
    }

def audit_cold_start_split(dataset, fold=0):
    """Audits cold_start_concept split for frequency constraints."""
    base_path = Path(f"data/processed/{dataset}/splits/cold_start_concept/fold_{fold}")
    if not (base_path / "train.csv").exists(): return None
    
    train = pd.read_csv(base_path / "train.csv")
    train_freqs = train['kc_id'].value_counts().to_dict()
    
    checks = {
        "test_strict": 0,
        "test_k5": 5,
        "test_k10": 10
    }
    
    results = []
    for name, limit in checks.items():
        file_path = base_path / f"{name}.csv"
        if not file_path.exists(): continue
        
        df = pd.read_csv(file_path)
        violations = df[df['kc_id'].apply(lambda x: train_freqs.get(x, 0)) > limit]
        
        status = "PASS" if len(violations) == 0 else "FAIL"
        results.append({
            "dataset": dataset,
            "split_mode": f"cold_start_{name}",
            "fold": fold,
            "n_train": len(train),
            "n_valid": 0,
            "n_test": len(df),
            "violation_count": len(violations),
            "status": status
        })
    return results

def main(dataset):
    print(f"[{dataset}] Auditing all splits...")
    all_results = []
    
    # 1. Learner Split
    res_l = audit_learner_split(dataset)
    if res_l: all_results.append(res_l)
    
    # 2. Temporal Split
    res_t = audit_temporal_split(dataset)
    if res_t: all_results.append(res_t)
    
    # 3. Cold Start Split
    res_c_list = audit_cold_start_split(dataset)
    if res_c_list: all_results.extend(res_c_list)
    
    if not all_results:
        print(f"[{dataset}] No splits found to audit.")
        return
        
    df_results = pd.DataFrame(all_results)
    # Ensure consistent column order
    cols = ["dataset", "split_mode", "fold", "n_train", "n_valid", "n_test", "violation_count", "status"]
    df_results = df_results[cols]
    
    # Save/Update report
    report_path = Path("results/tables/split_report.csv")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    if report_path.exists():
        df_old = pd.read_csv(report_path)
        # Filter out old results for this dataset to avoid duplicates
        df_old = df_old[df_old['dataset'] != dataset]
        # Only keep columns we care about if old report had more
        df_old = df_old[df_old.columns.intersection(cols)]
        df_final = pd.concat([df_old, df_results], ignore_index=True)
    else:
        df_final = df_results
        
    df_final.to_csv(report_path, index=False)
    
    # Save audit log (append always)
    audit_log = Path("logs/split_audit.csv")
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(audit_log, mode='a', header=not audit_log.exists(), index=False)
    
    print(f"[{dataset}] Audit complete. Results in {report_path} and {audit_log}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit KT splits for integrity.")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name to audit.")
    args = parser.parse_args()
    
    main(args.dataset)

