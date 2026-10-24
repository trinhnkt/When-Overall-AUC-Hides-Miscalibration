import pandas as pd
import yaml
import json
import argparse
import os
from pathlib import Path

def load_config(config_path):
    """Loads a YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_stats(stats_dict, output_path="results/tables/dataset_stats.csv"):
    """Saves dataset statistics to a CSV, appending if it exists."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_new = pd.DataFrame([stats_dict])
    if output_path.exists():
        df_old = pd.read_csv(output_path)
        # Avoid duplicate entries for the same dataset
        df_old = df_old[df_old['dataset'] != stats_dict['dataset']]
        df_new = pd.concat([df_old, df_new], ignore_index=True)
    
    df_new.to_csv(output_path, index=False)

def preprocess(config_path):
    """
    Normalizes raw dataset into canonical schema using configuration.
    """
    config = load_config(config_path)
    dataset_name = config['dataset_name']
    raw_path = config['raw_data_path']
    processed_path = config['processed_data_path']
    min_seq_len = config.get('min_sequence_length', 2)
    
    print(f"[{dataset_name}] Starting preprocessing...")
    
    if not Path(raw_path).exists():
        print(f"[{dataset_name}] Error: Raw data not found at {raw_path}")
        return

    # Load data
    df = pd.read_csv(raw_path, low_memory=False)
    initial_count = len(df)
    
    # Mapping columns from config
    mapping = {
        config['user_col']: 'user_id',
        config['item_col']: 'item_id',
        config['kc_col']: 'kc_id',
        config['timestamp_col']: 'timestamp',
        config['correct_col']: 'correct'
    }
    
    # Check if all required columns exist
    missing_cols = [c for c in mapping.keys() if c not in df.columns]
    if missing_cols:
        print(f"[{dataset_name}] Error: Missing columns in raw data: {missing_cols}")
        return

    # Filter and rename
    df = df.rename(columns=mapping)
    df = df[['user_id', 'item_id', 'kc_id', 'timestamp', 'correct']]
    
    # 1. Remove rows with missing identifiers or labels
    df = df.dropna(subset=['user_id', 'kc_id', 'correct'])
    after_dropna = len(df)
    
    # 2. Normalize 'correct' to binary 0/1
    # Handle boolean or string labels
    if df['correct'].dtype == bool:
        df['correct'] = df['correct'].astype(int)
    else:
        # Try to convert to numeric, invalid becomes NaN
        df['correct'] = pd.to_numeric(df['correct'], errors='coerce')
        df = df.dropna(subset=['correct'])
        df['correct'] = df['correct'].apply(lambda x: 1 if x > 0 else 0)
    
    # 3. Handle timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    after_timestamp = len(df)
    
    # 4. Sort by user and timestamp
    df = df.sort_values(by=['user_id', 'timestamp'])
    
    # 5. Filter short sequences
    user_counts = df['user_id'].value_counts()
    valid_users = user_counts[user_counts >= min_seq_len].index
    df = df[df['user_id'].isin(valid_users)]
    after_min_seq = len(df)
    
    # Save processed data
    output_path = Path(processed_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    # Statistics for table
    stats = {
        "dataset": dataset_name,
        "raw_interactions": initial_count,
        "processed_interactions": after_min_seq,
        "n_users": df['user_id'].nunique(),
        "n_items": df['item_id'].nunique(),
        "n_kcs": df['kc_id'].nunique(),
        "avg_seq_len": df.groupby('user_id').size().mean(),
        "sparsity_kc": 1 - (len(df) / (df['user_id'].nunique() * df['kc_id'].nunique()))
    }
    save_stats(stats)
    
    # Log transformation counts
    log_entry = {
        "dataset": dataset_name,
        "steps": {
            "initial": initial_count,
            "after_dropna_identifiers": after_dropna,
            "after_timestamp_clean": after_timestamp,
            "after_min_seq_filter": after_min_seq
        },
        "dropped_rows": initial_count - after_min_seq
    }
    
    log_file = Path("logs/preprocess_log.json")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    current_logs = []
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                current_logs = json.load(f)
                if not isinstance(current_logs, list): current_logs = [current_logs]
            except:
                current_logs = []
    
    # Update or append log
    current_logs = [l for l in current_logs if l.get('dataset') != dataset_name]
    current_logs.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(current_logs, f, indent=4)
        
    print(f"[{dataset_name}] Preprocessing complete. Saved to {processed_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess KT dataset.")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file.")
    args = parser.parse_args()
    
    preprocess(args.config)
