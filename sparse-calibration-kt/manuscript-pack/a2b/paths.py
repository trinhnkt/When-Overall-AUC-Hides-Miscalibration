"""A2B output tree. Never write to historical data/processed/xes3g5m or results/predictions."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REV = Path(__file__).resolve().parents[1]
A2B = REV / "a2b"
RAW_KC = REPO / "data" / "raw" / "xes3g5m" / "kc_level"
TV = RAW_KC / "train_valid_sequences.csv"
TE = RAW_KC / "test.csv"
FLAT = A2B / "data" / "raw" / "xes3g5m" / "raw_data.csv"
PROCESSED = A2B / "data" / "processed" / "xes3g5m" / "interactions.csv"
SPLITS = A2B / "data" / "processed" / "xes3g5m" / "splits"
PRED = A2B / "results" / "predictions"
TABLES = A2B / "results" / "tables"
ANALYSIS = A2B / "analysis"
CKPT = A2B / "checkpoints"
LOG = A2B / "logs"
DS = "xes3g5m"
SEEDS = (42, 2024, 2025, 2026, 2027)
# fold_i trains with SEEDS[i]. fold_3 copies fold_2 users (locked duplicate partition).
SPLIT_SEEDS = {0: 42, 1: 2024, 2: 2025, 4: 2027}
DUP_SRC_FOLD, DUP_DST_FOLD = 2, 3
MODELS = ("irt_1pl", "dkt", "simplekt")
NEURAL = ("dkt", "simplekt")
BATCH_SIZE = 64
EPOCHS = 50
MAX_SEQ = 200
N_BINS = 15
TAU = 0.7
MIN_SEQ = 2
