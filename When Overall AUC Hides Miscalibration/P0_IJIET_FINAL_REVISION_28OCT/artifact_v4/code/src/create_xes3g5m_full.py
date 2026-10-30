import pandas as pd
from pathlib import Path

def expand_sequence_df(seq_df):
    flat_rows = []
    for idx, row in seq_df.iterrows():
        uid = str(row['uid'])
        questions = str(row['questions']).split(',')
        concepts = str(row['concepts']).split(',')
        responses = str(row['responses']).split(',')
        timestamps = str(row['timestamps']).split(',')
        
        # Determine the length of the sequence
        seq_len = min(len(questions), len(concepts), len(responses), len(timestamps))
        
        for i in range(seq_len):
            flat_rows.append({
                "user_id": uid,
                "question_id": questions[i],
                "skill_id": concepts[i],
                "correct": int(responses[i]),
                # Convert Unix millisecond timestamp to standard readable datetime string
                "timestamp": pd.to_datetime(int(timestamps[i]), unit='ms').strftime('%Y-%m-%d %H:%M:%S')
            })
            
    return pd.DataFrame(flat_rows)

def main():
    train_path = Path("data/raw/xes3g5m/kc_level/train_valid_sequences.csv")
    test_path = Path("data/raw/xes3g5m/kc_level/test.csv")
    output_path = Path("data/raw/xes3g5m/raw_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not train_path.exists():
        print(f"File not found at {train_path}")
        return
        
    print(f"Reading ALL sequence data from {train_path}...")
    df_seq_train = pd.read_csv(train_path)
    print(f"Reading ALL sequence data from {test_path}...")
    df_seq_test = pd.read_csv(test_path) if test_path.exists() else pd.DataFrame()
    
    df_seq = pd.concat([df_seq_train, df_seq_test], ignore_index=True)
    print(f"Total sequences to expand: {len(df_seq)}")
    
    print("Expanding sequences into flat interaction format...")
    df_flat = expand_sequence_df(df_seq)
    
    print(f"Saving flat canonical interactions to {output_path}...")
    df_flat.to_csv(output_path, index=False)
    print(f"Successfully saved {len(df_flat)} rows to {output_path}")

if __name__ == "__main__":
    main()
