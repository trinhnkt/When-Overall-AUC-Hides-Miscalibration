# B4 — Table 2 configuration trace

Date: 2026-10-29

Commit inspected: `4ff6683` (`4ff66835561e2597a50197dcfb93aba1ec74583b`).

`configs/assist2012.yaml` at that commit has no architecture, optimizer, learning rate, batch size, epoch, patience, or checkpoint key. Those values come from the code and from the saved checkpoints. Nothing was copied from Version I.

`artifact_final/02_training/assist2012.yaml` matches the commit file and likewise has no model hyperparameters. simpleKT hyperparameters are in `scripts/p0_retrain_official_simplekt.py` at the same commit. The saved simpleKT checkpoint stores that dictionary under `cfg`.

DKT `num_layers` is not an argument of the LSTM call. Constructing `DKT` from that call yields `num_layers=1`. T-KT `dim_feedforward` is not set; the configured width is `d=64`. The table uses that configured width, not the PyTorch feed-forward default.

| Table2_field | Model | Value | Source config/file | Line/key |
| --- | --- | --- | --- | --- |
| Architecture | DKT | LSTM | `src/baseline_runner.py` at 4ff6683 | line 22, `nn.LSTM` |
| Architecture | T-KT masked | Causal Transformer | `src/protocol_v2.py` at 4ff6683 | line 25, class `TKTc`; causal mask in `forward` |
| Architecture | simpleKT | pyKT simpleKT | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 221, `pykt.models.simplekt.simpleKT` |
| Embedding size | DKT | 64 | `src/baseline_runner.py` at 4ff6683 | line 18, `embed_dim=64` |
| Embedding size | T-KT masked | 64 | `src/protocol_v2.py` at 4ff6683 | line 25, `d=64` |
| Embedding size | simpleKT | 256 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 28, `d_model=256`; checkpoint key `cfg.d_model` |
| Hidden size | DKT | 128 | `src/baseline_runner.py` at 4ff6683 | line 18, `hidden_dim=128` |
| Hidden size | T-KT masked | 64 | `src/protocol_v2.py` at 4ff6683 | line 30, `d_model=d` |
| Hidden size | simpleKT | 256 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 31, `d_ff=256`; checkpoint key `cfg.d_ff` |
| Number of layers | DKT | 1 | `src/baseline_runner.py` at 4ff6683 | line 22; `num_layers` omitted, constructed LSTM has 1 layer |
| Number of layers | T-KT masked | 2 | `src/protocol_v2.py` at 4ff6683 | line 25, `n_layers=2` |
| Number of layers | simpleKT | 2 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 29, `n_blocks=2`; checkpoint key `cfg.n_blocks` |
| Attention heads | DKT | none | `src/baseline_runner.py` at 4ff6683 | line 22; the LSTM call has no attention-head argument |
| Attention heads | T-KT masked | 4 | `src/protocol_v2.py` at 4ff6683 | line 25, `n_heads=4` |
| Attention heads | simpleKT | 8 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 32, `num_attn_heads=8`; checkpoint key `cfg.num_attn_heads` |
| Optimizer | DKT | Adam | `src/baseline_runner.py` at 4ff6683 | line 121, `torch.optim.Adam` |
| Optimizer | T-KT masked | Adam | `src/baseline_runner.py` at 4ff6683 | line 121, `torch.optim.Adam` |
| Optimizer | simpleKT | Adam | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 257, `torch.optim.Adam` |
| Learning rate | DKT | 0.001 | `src/baseline_runner.py` at 4ff6683 | line 107, `lr=1e-3` |
| Learning rate | T-KT masked | 0.001 | `src/baseline_runner.py` at 4ff6683 | line 107, `lr=1e-3` |
| Learning rate | simpleKT | 0.001 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 172, `--lr` default `1e-3` |
| Batch size | DKT | 64 | `src/baseline_runner.py` at 4ff6683 | line 338, `config.get('batch_size', 64)`; `configs/assist2012.yaml` has no `batch_size` |
| Batch size | T-KT masked | 64 | `src/baseline_runner.py` at 4ff6683 | line 338, same default; `configs/assist2012.yaml` has no `batch_size` |
| Batch size | simpleKT | 24 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 171, `--batch-size` default `24` |
| Max epochs | DKT | 50 | `src/baseline_runner.py` at 4ff6683 | line 106, `n_epochs=50`; line 339, `config.get('epochs', 50)` |
| Max epochs | T-KT masked | 50 | `src/baseline_runner.py` at 4ff6683 | line 106, `n_epochs=50` |
| Max epochs | simpleKT | 50 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 169, `--epochs` default `50` |
| Patience | DKT | 8 | `src/baseline_runner.py` at 4ff6683 | line 109, `patience=8` |
| Patience | T-KT masked | 8 | `src/baseline_runner.py` at 4ff6683 | line 109, `patience=8` |
| Patience | simpleKT | 8 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 170, `--patience` default `8` |
| Checkpoint rule | DKT | Best validation AUC | `runs/a_dkt/assist2012_fold{0-4}_*_best_valid/model.pt` | key `select` = `best_valid`; implementation `src/baseline_runner.py` line 114 |
| Checkpoint rule | T-KT masked | Best validation AUC | `runs/b1_tktc/assist2012_fold{0-4}_*_best_valid/model.pt` | key `select` = `best_valid`; implementation `src/baseline_runner.py` line 114 |
| Checkpoint rule | simpleKT | Best validation AUC | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | lines 269–280; saved state is the best validation-AUC epoch |
| Test history rule | DKT | Non-overlapping chunks of 200 | `src/protocol_v2.py` at 4ff6683 | line 48, `window=200`; chunk start `i // window * window` |
| Test history rule | T-KT masked | Non-overlapping chunks of 200 | `src/protocol_v2.py` at 4ff6683 | line 48, `window=200` |
| Test history rule | simpleKT | Non-overlapping chunks of 200 | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 35, `seq_len=200`; checkpoint key `cfg.seq_len` |
| Split rule | DKT | Learner-disjoint; 20% test users | `src/three_split_constructor.py` at 4ff6683 and `configs/assist2012.yaml` | constructor line 38, `n_test = int(n_users * 0.2)`; yaml line 12, `valid: 0.1` |
| Split rule | T-KT masked | Same learner split | `src/three_split_constructor.py` at 4ff6683 | line 38 |
| Split rule | simpleKT | Same learner split | `scripts/p0_retrain_official_simplekt.py` at 4ff6683 | line 166, `--split` default `learner_based` |
| Provenance | DKT | Commit 4ff6683; baseline_runner.py | `runs/manifest.csv` | `code_commit=4ff6683`; `config_path=configs/assist2012.yaml` |
| Provenance | T-KT masked | Commit 4ff6683; protocol_v2.py | `runs/manifest.csv` | `code_commit=4ff6683`; `config_path=configs/assist2012.yaml` |
| Provenance | simpleKT | Commit 4ff6683; p0_retrain_official_simplekt.py | `runs/manifest.csv` | `code_commit=4ff6683`; `config_path=scripts/p0_retrain_official_simplekt.py` |

The default argument `select="final"` at `baseline_runner.py` line 108 is the untouched-runner default. The ten saved DKT and T-KT checkpoints store `select=best_valid`, so Table 2 uses that executed rule.

## Decision

**B4 = PASS**

Every Table 2 hyperparameter above has a source file and a line or checkpoint key. Manuscript Table 5 and Table A2 were not changed.
