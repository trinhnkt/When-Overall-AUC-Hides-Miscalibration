import copy
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import yaml
import argparse
import os
import time
from pathlib import Path
from tqdm import tqdm
from pyBKT.models import Model as BKTModel

# --- Torch Models ---

class DKT(nn.Module):
    def __init__(self, n_kcs, embed_dim=64, hidden_dim=128):
        super(DKT, self).__init__()
        self.n_kcs = n_kcs
        self.embed = nn.Embedding(n_kcs * 2 + 1, embed_dim, padding_idx=n_kcs * 2)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, n_kcs)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # x shape: (batch, seq_len) where values are kc_id * 2 + correct
        embedded = self.embed(x)
        out, _ = self.lstm(embedded)
        logits = self.fc(out)
        return self.sigmoid(logits)

class SimpleKT(nn.Module):
    def __init__(self, n_kcs, embed_dim=64, n_heads=4):
        super(SimpleKT, self).__init__()
        self.n_kcs = n_kcs
        self.embed = nn.Embedding(n_kcs * 2 + 1, embed_dim, padding_idx=n_kcs * 2)
        # Local T-KT reference. Causal and padding masks live on TKTc in protocol_v2.
        encoder_layer = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=n_heads, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.fc = nn.Linear(embed_dim, n_kcs)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        embedded = self.embed(x)
        # Add a simple mask for causality if needed, but for KT we usually just look at history
        out = self.transformer(embedded)
        logits = self.fc(out)
        return self.sigmoid(logits)

# --- Data Handling ---

class KTDataset(Dataset):
    def __init__(self, df, kc_map, max_seq_len=200):
        self.data = []
        self.max_seq_len = max_seq_len
        
        # Group by user
        for user_id, group in df.groupby('user_id'):
            kcs = [kc_map[k] for k in group['kc_id'].values]
            labels = group['correct'].values
            
            # For DKT/SimpleKT, we predict label at t+1 using info up to t
            # Feature: kc_id * 2 + label
            features = [k * 2 + l for k, l in zip(kcs, labels)]
            
            # Split into chunks of max_seq_len
            for i in range(0, len(features), max_seq_len):
                feat_chunk = features[i:i+max_seq_len]
                label_chunk = labels[i:i+max_seq_len]
                kc_chunk = kcs[i:i+max_seq_len]
                
                if len(feat_chunk) < 2: continue
                
                self.data.append({
                    'features': torch.tensor(feat_chunk[:-1], dtype=torch.long),
                    'labels': torch.tensor(label_chunk[1:], dtype=torch.float),
                    'kcs': torch.tensor(kc_chunk[1:], dtype=torch.long)
                })

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

def collate_fn(batch):
    # Padding
    features = [b['features'] for b in batch]
    labels = [b['labels'] for b in batch]
    kcs = [b['kcs'] for b in batch]
    
    features_pad = nn.utils.rnn.pad_sequence(features, batch_first=True, padding_value=0)
    labels_pad = nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-1)
    kcs_pad = nn.utils.rnn.pad_sequence(kcs, batch_first=True, padding_value=-1)
    
    return features_pad, labels_pad, kcs_pad

# --- Training Loop ---

def train_torch_model(
    model,
    train_loader,
    valid_loader,
    device,
    n_epochs=50,
    lr=1e-3,
    select="final",
    patience=8,
    log_path=None,
):
    """select='final' keeps bản I behavior (weights after the last epoch).

    select='best_valid' stores a deepcopy of the best validation-AUC epoch
    and stops after `patience` epochs without an improvement. The old
    assignment best_state = model.state_dict() kept a live reference, so
    load_state_dict restored the final epoch even when a better epoch existed.
    """
    if select not in ("final", "best_valid"):
        raise ValueError(f"unknown select={select}")
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss(reduction='none')

    best_valid_auc = -1.0
    best_state = None
    best_epoch = None
    since_improve = 0
    epoch_logs = []
    last_epoch = 0

    for epoch in range(n_epochs):
        last_epoch = epoch
        model.train()
        loss_sum = 0.0
        loss_n = 0
        for feats, labels, kcs in train_loader:
            feats, labels, kcs = feats.to(device), labels.to(device), kcs.to(device)
            optimizer.zero_grad()
            
            preds = model(feats) # (batch, seq, n_kcs)
            # Pick the prediction for the target KC
            batch_size, seq_len, _ = preds.shape
            # preds is (B, S, K), kcs is (B, S)
            # Flatten to (B*S, K) and use gather or indexing
            preds_flat = preds.view(-1, model.n_kcs)
            kcs_flat = kcs.view(-1)
            labels_flat = labels.view(-1)
            
            mask = (labels_flat != -1)
            target_preds = preds_flat[torch.arange(preds_flat.size(0)), kcs_flat.clamp(min=0)]
            
            loss = criterion(target_preds[mask], labels_flat[mask]).mean()
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.item())
            loss_n += 1

        # Validation
        model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for feats, labels, kcs in valid_loader:
                feats, labels, kcs = feats.to(device), labels.to(device), kcs.to(device)
                preds = model(feats)
                preds_flat = preds.view(-1, model.n_kcs)
                kcs_flat = kcs.view(-1)
                labels_flat = labels.view(-1)
                mask = (labels_flat != -1)
                target_preds = preds_flat[torch.arange(preds_flat.size(0)), kcs_flat.clamp(min=0)]
                
                all_preds.extend(target_preds[mask].cpu().numpy())
                all_labels.extend(labels_flat[mask].cpu().numpy())
        
        from sklearn.metrics import roc_auc_score
        valid_auc = float("nan")
        if len(all_labels) > 0 and len(set(np.asarray(all_labels).tolist())) > 1:
            valid_auc = float(roc_auc_score(all_labels, all_preds))
            if valid_auc > best_valid_auc:
                best_valid_auc = valid_auc
                best_epoch = epoch
                since_improve = 0
                if select == "best_valid":
                    best_state = copy.deepcopy(model.state_dict())
            else:
                since_improve += 1
        else:
            since_improve += 1
        train_loss = loss_sum / loss_n if loss_n else float("nan")
        epoch_logs.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "valid_auc": valid_auc,
            "valid_nll": float("nan"),
            "valid_ece": float("nan"),
        })
        if select == "best_valid" and since_improve >= patience:
            break

    if select == "best_valid" and best_state is not None:
        model.load_state_dict(best_state)
    model.selected_epoch = best_epoch if select == "best_valid" else last_epoch
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(epoch_logs).to_csv(log_path, index=False)
    return model

def predict_sequential(model, test_df, kc_map, device, batch_size=2048):
    """
    Predict outcomes sequentially per user to avoid prediction-label misalignment.
    Ensures causal correctness by predicting step i from history 0..i-1.
    Optimized with batched evaluations across users at each step.
    """
    if len(test_df) == 0:
        return np.array([])
        
    model.eval()
    test_df_sorted = test_df.sort_values(['user_id', 'timestamp']) if 'timestamp' in test_df.columns else test_df.sort_values('user_id')
    
    user_groups = test_df_sorted.groupby('user_id', sort=True)
    
    users_data = []
    for user_id, group in user_groups:
        kcs = [kc_map[k] for k in group['kc_id'].values]
        labels = group['correct'].values
        row_indices = group.index.tolist()
        state_feats = [kcs[i] * 2 + int(labels[i]) for i in range(len(group))]
        users_data.append({
            'kcs': kcs,
            'labels': labels,
            'row_indices': row_indices,
            'state_feats': state_feats,
            'len': len(group)
        })
        
    max_len = max(u['len'] for u in users_data)
    test_preds_dict = {}
    
    # Initialize all step 0 predictions to 0.5
    for u in users_data:
        test_preds_dict[u['row_indices'][0]] = 0.5
        
    with torch.no_grad():
        for step_idx in range(1, max_len):
            active_users = [u for u in users_data if u['len'] > step_idx]
            if not active_users:
                break
                
            for start_u in range(0, len(active_users), batch_size):
                sub_batch = active_users[start_u:start_u + batch_size]
                
                inp_list = [u['state_feats'][:step_idx] for u in sub_batch]
                inp_tensor = torch.tensor(inp_list, dtype=torch.long, device=device)
                
                target_kcs = [u['kcs'][step_idx] for u in sub_batch]
                
                out = model(inp_tensor) # (sub_batch_size, step_idx, n_kcs)
                
                preds = out[torch.arange(len(sub_batch)), -1, target_kcs].cpu().numpy()
                
                for idx, u in enumerate(sub_batch):
                    row_idx = u['row_indices'][step_idx]
                    test_preds_dict[row_idx] = float(preds[idx])
                    
    p_pred = np.array([test_preds_dict[idx] for idx in test_df.index])
    return p_pred

# --- Runner ---

def run_experiments(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    dataset_name = config['dataset_name']
    seeds = config.get('seeds', [42, 123, 2026])
    baselines = config.get('baselines', ['bkt', 'dkt', 'simplekt'])
    split_modes = config.get('split_modes', ['learner_based', 'temporal'])
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[{dataset_name}] Using device: {device}")
    
    results_records = []
    
    for mode in split_modes:
        print(f"[{dataset_name}] Split mode: {mode}")
        for seed_idx, seed in enumerate(seeds):
            # For learner_based, we use fold=seed_idx. For temporal, fold=0.
            fold = seed_idx if mode == 'learner_based' else 0
            base_path = Path(f"data/processed/{dataset_name}/splits/{mode}/fold_{fold}")
            
            if not (base_path / "train.csv").exists():
                print(f"      - Skipping fold {fold} (files not found)")
                continue
                
            print(f"    - Seed {seed} (Fold {fold})")
            train_df = pd.read_csv(base_path / "train.csv")
            valid_df = pd.read_csv(base_path / "valid.csv")
            test_df = pd.read_csv(base_path / "test.csv")
            
            # Prepare KC mapping
            all_kcs = sorted(pd.concat([train_df['kc_id'], valid_df['kc_id'], test_df['kc_id']]).unique())
            kc_map = {kc: i for i, kc in enumerate(all_kcs)}
            inv_kc_map = {i: kc for kc, i in kc_map.items()}
            n_kcs = len(all_kcs)
            
            for model_name in baselines:
                model_name = model_name.lower()
                print(f"      - Training {model_name}...")
                
                start_time = time.time()
                
                if model_name == 'bkt':
                    # Use pyBKT
                    bkt = BKTModel(seed=seed)
                    # pyBKT fit expects a dataframe with specific columns
                    # We map: user_id -> user_id, kc_id -> skill_name, correct -> correct
                    # To avoid pyBKT regex matching crash with special characters, map KCs to clean alphanumeric strings
                    bkt_train = train_df[['user_id', 'kc_id', 'correct']].copy()
                    bkt_train['skill_name'] = bkt_train['kc_id'].map(lambda x: f"skill_{kc_map[x]}")
                    bkt_train = bkt_train[['user_id', 'skill_name', 'correct']]
                    bkt.fit(data=bkt_train)
                    
                    # Predict on test
                    bkt_test = test_df[['user_id', 'kc_id', 'correct']].copy()
                    bkt_test['skill_name'] = bkt_test['kc_id'].map(lambda x: f"skill_{kc_map[x]}")
                    bkt_test = bkt_test[['user_id', 'skill_name', 'correct']]
                    preds_dict = bkt.predict(data=bkt_test)
                    p_pred = preds_dict['correct_predictions'].values
                    y_true = test_df['correct'].values
                    
                elif model_name in ['dkt', 'simplekt']:
                    torch.manual_seed(seed)
                    np.random.seed(seed)
                    
                    train_ds = KTDataset(train_df, kc_map)
                    valid_ds = KTDataset(valid_df, kc_map)
                    
                    batch_size = config.get('batch_size', 64)
                    n_epochs = config.get('epochs', 50)
                    
                    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
                    valid_loader = DataLoader(valid_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
                    
                    if model_name == 'dkt':
                        model = DKT(n_kcs).to(device)
                    else:
                        model = SimpleKT(n_kcs).to(device)
                    
                    model = train_torch_model(model, train_loader, valid_loader, device, n_epochs=n_epochs)
                    
                    # Predict on test
                    p_pred = predict_sequential(model, test_df, kc_map, device)
                    y_true = test_df['correct'].values
                else:
                    print(f"        - Model {model_name} not implemented.")
                    continue
                
                duration = time.time() - start_time
                
                # Save Predictions
                pred_df = test_df.copy()
                pred_df['dataset'] = dataset_name
                pred_df['split_mode'] = mode
                pred_df['model'] = model_name
                pred_df['seed'] = seed
                pred_df['p_pred'] = p_pred
                pred_df['y_true'] = pred_df['correct']
                
                output_cols = ['dataset', 'split_mode', 'model', 'seed', 'user_id', 'item_id', 'kc_id', 'timestamp', 'y_true', 'p_pred']
                pred_df = pred_df[output_cols]
                
                pred_dir = Path("results/predictions")
                pred_dir.mkdir(parents=True, exist_ok=True)
                pred_file = pred_dir / f"{dataset_name}_{mode}_{model_name}_seed{seed}.csv"
                pred_df.to_csv(pred_file, index=False)
                
                # Log record
                results_records.append({
                    "dataset": dataset_name,
                    "split_mode": mode,
                    "fold": fold,
                    "model": model_name,
                    "seed": seed,
                    "duration": duration,
                    "status": "SUCCESS"
                })
                
    # Save experiment log
    log_file = Path("logs/experiment_log.csv")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_df = pd.DataFrame(results_records)
    if log_file.exists():
        old_log = pd.read_csv(log_file)
        log_df = pd.concat([old_log, log_df], ignore_index=True)
    log_df.to_csv(log_file, index=False)
    print(f"[{dataset_name}] Experiments complete. Log saved to {log_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    run_experiments(args.config)
