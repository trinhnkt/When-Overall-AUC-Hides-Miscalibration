import pandas as pd
import numpy as np
import yaml
import argparse
import os
from pathlib import Path

def load_config(config_path):
    """Loads YAML configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_split(df, dataset, mode, fold, name):
    """Saves a dataframe as a CSV in the specified split directory."""
    output_dir = Path(f"data/processed/{dataset}/splits/{mode}/fold_{fold}")
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / f"{name}.csv", index=False)
    print(f"      - Saved {name}.csv ({len(df)} rows)")

def create_learner_based_split(df, config, fold=0):
    """
    Split 1: learner_based
    - train users: 80% (including valid)
    - valid users: from train users
    - test users: 20%
    - no user_id overlap between train and test
    """
    dataset = config['dataset_name']
    ratios = config['split_ratios']
    seed = config['seeds'][fold] if fold < len(config['seeds']) else 42
    
    users = list(df['user_id'].dropna().unique())
    np.random.seed(seed)
    np.random.shuffle(users)
    
    n_users = len(users)
    # Target: 20% test, 80% train+valid
    n_test = int(n_users * 0.2)
    # Of the remaining 80%, we take a portion for valid (as defined in config, usually 0.1 of total)
    n_valid = int(n_users * ratios.get('valid', 0.1))
    
    test_users = users[:n_test]
    valid_users = users[n_test:n_test+n_valid]
    train_users = users[n_test+n_valid:]
    
    train_df = df[df['user_id'].isin(train_users)]
    valid_df = df[df['user_id'].isin(valid_users)]
    test_df = df[df['user_id'].isin(test_users)]
    
    save_split(train_df, dataset, "learner_based", fold, "train")
    save_split(valid_df, dataset, "learner_based", fold, "valid")
    save_split(test_df, dataset, "learner_based", fold, "test")
    
    return train_df, valid_df, test_df

def create_temporal_split(df, config, fold=0):
    """
    Split 2: temporal
    - sort all interactions by timestamp
    - earliest 70% for train
    - next 10% for valid
    - latest 20% for test
    - train timestamps must be earlier than test timestamps
    """
    dataset = config['dataset_name']
    
    # Sort by timestamp
    df_sorted = df.sort_values(by='timestamp')
    
    n = len(df_sorted)
    n_train = int(n * 0.7)
    n_valid = int(n * 0.1)
    
    train_df = df_sorted.iloc[:n_train]
    valid_df = df_sorted.iloc[n_train:n_train+n_valid]
    test_df = df_sorted.iloc[n_train+n_valid:]
    
    save_split(train_df, dataset, "temporal", fold, "train")
    save_split(valid_df, dataset, "temporal", fold, "valid")
    save_split(test_df, dataset, "temporal", fold, "test")
    
    return train_df, valid_df, test_df

def create_cold_start_concept_split(train_df, valid_df, test_df, config, fold=0):
    """
    Split 3: cold_start_concept
    - compute train_freq(c) using train interactions only
    - create strict cold-start group: train_freq(c) = 0
    - create limited cold-start groups: train_freq(c) <= 5 and <= 10
    """
    dataset = config['dataset_name']
    
    # Compute frequencies in train
    train_freqs = train_df['kc_id'].value_counts().to_dict()
    
    def get_freq(kc):
        return train_freqs.get(kc, 0)
    
    # Annotate test set
    test_df = test_df.copy()
    test_df['train_freq'] = test_df['kc_id'].apply(get_freq)
    
    # Create groups
    test_strict = test_df[test_df['train_freq'] == 0]
    test_k5 = test_df[test_df['train_freq'] <= 5]
    test_k10 = test_df[test_df['train_freq'] <= 10]
    
    save_split(test_strict, dataset, "cold_start_concept", fold, "test_strict")
    save_split(test_k5, dataset, "cold_start_concept", fold, "test_k5")
    save_split(test_k10, dataset, "cold_start_concept", fold, "test_k10")
    
    # Also save the original train/valid for the pipeline
    save_split(train_df, dataset, "cold_start_concept", fold, "train")
    save_split(valid_df, dataset, "cold_start_concept", fold, "valid")
    # And the full test set with annotations
    save_split(test_df, dataset, "cold_start_concept", fold, "test_annotated")

def main(config_path):
    config = load_config(config_path)
    dataset_name = config['dataset_name']
    processed_path = config['processed_data_path']
    seeds = config.get('seeds', [42, 123, 2026])
    
    print(f"[{dataset_name}] Starting 3-way split construction for {len(seeds)} seeds...")
    
    if not os.path.exists(processed_path):
        print(f"[{dataset_name}] Error: Processed data not found at {processed_path}")
        return

    df = pd.read_csv(processed_path)
    
    for fold, seed in enumerate(seeds):
        print(f"  - Fold {fold} (Seed {seed})")
        
        print(f"    - Mode: learner_based")
        train_l, valid_l, test_l = create_learner_based_split(df, config, fold=fold)
        
        # Temporal split is usually deterministic, but we save it under each fold for consistency 
        # or just once. Here we follow the requested structure.
        if fold == 0:
            print(f"    - Mode: temporal")
            train_t, valid_t, test_t = create_temporal_split(df, config, fold=fold)
        
        print(f"    - Mode: cold_start_concept")
        # Usually we use the learner-based train set to define concept "coldness"
        create_cold_start_concept_split(train_l, valid_l, test_l, config, fold=fold)
    
    print(f"[{dataset_name}] All splits created successfully for all seeds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create three types of splits for KT.")
    parser.add_argument("--config", type=str, required=True, help="Path to dataset config.")
    args = parser.parse_args()
    
    main(args.config)

