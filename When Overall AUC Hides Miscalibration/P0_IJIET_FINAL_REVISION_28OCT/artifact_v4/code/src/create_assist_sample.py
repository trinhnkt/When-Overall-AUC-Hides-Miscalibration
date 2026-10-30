import pandas as pd
from pathlib import Path

def main():
    raw_path = Path("data/raw/assistments2012/2012-2013-data-with-predictions-4-final.csv")
    sample_dir = Path("data/sample")
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_path = sample_dir / "2012-2013-data_sample.csv"
    
    if not raw_path.exists():
        print(f"Raw ASSISTments 2012 file not found at {raw_path}")
        return
        
    print(f"Reading sample from {raw_path}...")
    # Load first 100,000 rows
    df = pd.read_csv(raw_path, nrows=100000, low_memory=False)
    df.to_csv(sample_path, index=False)
    print(f"Saved sample to {sample_path}")

if __name__ == "__main__":
    main()
