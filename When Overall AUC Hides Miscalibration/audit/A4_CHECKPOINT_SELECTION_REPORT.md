# A4 — DKT checkpoint selection

Date: 21/10/2026

Executable check: `scripts/check_a4_checkpoint.py`

```
UT-C1 = PASS
rows 25
unique_partitions ['P0', 'P1', 'P2', 'P4']
primary_cell best_valid x chunk
four_partition_mean_delta_ece 0.089265 sd 0.009067
fold2 and fold3 are one learner partition (P2) and were averaged before that SD
A4 = PASS
```

## Bug in bản I, recorded before the test hook

Commit `f5b5d58` (`sparse-calibration-kt/src/baseline_runner.py`), the checkpoint that tag `P0-ban-I` points at:

```
149:            if valid_auc > best_valid_auc:
150:                best_valid_auc = valid_auc
151:                best_state = model.state_dict()
153:    if best_state:
154:        model.load_state_dict(best_state)
```

`state_dict()` returns the live parameter tensors. Later epochs keep writing into those same tensors, so the object stored as the best checkpoint is the final epoch by the time `load_state_dict` runs. There is no `copy.deepcopy`.

The working `train_torch_model` already stores `copy.deepcopy(model.state_dict())` when `select="best_valid"`. This audit did not put the live reference back. The only later edit is an optional `copies` list used by UT-C1. When that list is omitted, selection is unchanged.

## What the two rules do

`select="final"` does not restore an earlier epoch. `selected_epoch` is the last epoch. All five runs recorded epoch 49. That is the bản I behavior of keeping the weights after a fixed 50-epoch run.

`select="best_valid"` tracks validation AUC, keeps a deepcopy of the improving epoch, uses patience 8 and a maximum of 50 epochs, and loads that deepcopy before scoring. Selected epochs were 7, 6, 7, 7, and 8 for folds 0–4. Each of those is earlier than the last logged epoch.

Each run writes `runs/a_dkt/assist2012_fold{k}_seed{s}_{select}/train_log.csv` with columns `epoch`, `train_loss`, `valid_auc`, `valid_nll`, `valid_ece`. `runs/manifest.csv` has `selected_epoch`. The check compared every required cell with the train log: `final` must match the last epoch, and `best_valid` must match the first epoch of maximum validation AUC. No mismatch.

## UT-C1

The test trains a tiny model for 5 epochs on one small batch. Validation AUC is forced to `[0.60, 0.95, 0.80, 0.70, 0.55]`, so the best epoch is 1 and the last epoch is 4. The trainer appends an explicit deepcopy after every epoch. The returned `best_valid` weights equal the epoch-1 copy and differ from the epoch-4 copy. The script printed `UT-C1 = PASS` before it read the ASSISTments files.

## Design

ASSISTments 2012, DKT, five training runs. Cells in `results/A4_dkt_2x2.csv`: `final × full`, `final × chunk`, `best_valid × full`, `best_valid × chunk`, and `best_valid × slide`. Primary cell: `best_valid × chunk`. Primary rows are `no_history = 0`. ECE uses the manuscript equal-width 15-bin function. `delta_ece_star = delta_ece - 0.5 * sqrt(15 / N_sparse)`. AUC and accuracy are on all primary rows, not only the dense and sparse strata. `n_no_history` counts every dropped row in the file.

Fold 2 (init seed 2025) and fold 3 (init seed 2026) are one learner partition. The check labels that partition P2, averages those two runs first, and only then computes the four-partition mean and SD. They are not five independent samples. The CSV still lists both runs so neither seed is hidden. R1–R4 are not applied here.

Bản I DKT weights remain NOT_RECOVERED. `final × full` is a new training. It is not a rescore of 0.0602 and 0.2333.

## Table

Source file, not a hand edit: `results/A4_dkt_2x2.csv`. Figures below are rounded from that file.

| partition | init_seed | select_rule | eval_context | selected_epoch | auc | acc | ece_dense | ece_sparse | delta_ece | delta_ece_star | n_dense | n_sparse | n_no_history |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fold0 | 42 | final | full | 49 | 0.7031 | 0.7210 | 0.0562 | 0.2251 | 0.1689 | 0.0755 | 522542 | 430 | 5561 |
| fold0 | 42 | final | chunk | 49 | 0.7014 | 0.7202 | 0.0559 | 0.2179 | 0.1620 | 0.0687 | 521348 | 430 | 6763 |
| fold0 | 42 | best_valid | full | 7 | 0.7319 | 0.7359 | 0.0067 | 0.1045 | 0.0977 | 0.0044 | 522542 | 430 | 5561 |
| fold0 | 42 | best_valid | chunk | 7 | 0.7305 | 0.7353 | 0.0070 | 0.0916 | 0.0846 | -0.0088 | 521348 | 430 | 6763 |
| fold0 | 42 | best_valid | slide | 7 | 0.7319 | 0.7359 | 0.0067 | 0.1045 | 0.0978 | 0.0045 | 522542 | 430 | 5561 |
| fold1 | 2024 | final | full | 49 | 0.6989 | 0.7189 | 0.0575 | 0.2320 | 0.1746 | 0.0804 | 531313 | 423 | 5561 |
| fold1 | 2024 | final | chunk | 49 | 0.6975 | 0.7181 | 0.0580 | 0.2312 | 0.1732 | 0.0791 | 530083 | 423 | 6799 |
| fold1 | 2024 | best_valid | full | 6 | 0.7311 | 0.7350 | 0.0091 | 0.1108 | 0.1017 | 0.0075 | 531313 | 423 | 5561 |
| fold1 | 2024 | best_valid | chunk | 6 | 0.7297 | 0.7344 | 0.0094 | 0.1109 | 0.1016 | 0.0074 | 530083 | 423 | 6799 |
| fold1 | 2024 | best_valid | slide | 6 | 0.7311 | 0.7351 | 0.0092 | 0.1107 | 0.1015 | 0.0074 | 531313 | 423 | 5561 |
| fold2 | 2025 | final | full | 49 | 0.6995 | 0.7203 | 0.0576 | 0.1662 | 0.1086 | 0.0102 | 516078 | 387 | 5561 |
| fold2 | 2025 | final | chunk | 49 | 0.6984 | 0.7197 | 0.0576 | 0.1660 | 0.1084 | 0.0098 | 514907 | 386 | 6743 |
| fold2 | 2025 | best_valid | full | 7 | 0.7325 | 0.7371 | 0.0078 | 0.0983 | 0.0905 | -0.0079 | 516078 | 387 | 5561 |
| fold2 | 2025 | best_valid | chunk | 7 | 0.7310 | 0.7365 | 0.0082 | 0.0950 | 0.0867 | -0.0118 | 514907 | 386 | 6743 |
| fold2 | 2025 | best_valid | slide | 7 | 0.7324 | 0.7370 | 0.0078 | 0.0983 | 0.0905 | -0.0080 | 516078 | 387 | 5561 |
| fold3 | 2026 | final | full | 49 | 0.6997 | 0.7192 | 0.0580 | 0.1934 | 0.1354 | 0.0370 | 516078 | 387 | 5561 |
| fold3 | 2026 | final | chunk | 49 | 0.6981 | 0.7184 | 0.0583 | 0.1899 | 0.1316 | 0.0330 | 514907 | 386 | 6743 |
| fold3 | 2026 | best_valid | full | 7 | 0.7323 | 0.7369 | 0.0103 | 0.0970 | 0.0867 | -0.0118 | 516078 | 387 | 5561 |
| fold3 | 2026 | best_valid | chunk | 7 | 0.7308 | 0.7364 | 0.0101 | 0.1036 | 0.0935 | -0.0050 | 514907 | 386 | 6743 |
| fold3 | 2026 | best_valid | slide | 7 | 0.7322 | 0.7369 | 0.0103 | 0.0970 | 0.0867 | -0.0118 | 516078 | 387 | 5561 |
| fold4 | 2027 | final | full | 49 | 0.7002 | 0.7199 | 0.0578 | 0.1897 | 0.1319 | 0.0288 | 504125 | 353 | 5561 |
| fold4 | 2027 | final | chunk | 49 | 0.6987 | 0.7191 | 0.0579 | 0.1914 | 0.1335 | 0.0303 | 502980 | 352 | 6717 |
| fold4 | 2027 | best_valid | full | 8 | 0.7318 | 0.7360 | 0.0101 | 0.0923 | 0.0822 | -0.0208 | 504125 | 353 | 5561 |
| fold4 | 2027 | best_valid | chunk | 8 | 0.7303 | 0.7353 | 0.0101 | 0.0909 | 0.0808 | -0.0224 | 502980 | 352 | 6717 |
| fold4 | 2027 | best_valid | slide | 8 | 0.7317 | 0.7359 | 0.0100 | 0.0923 | 0.0823 | -0.0208 | 504125 | 353 | 5561 |

On the primary cell, the four-partition mean of ΔECE is 0.0893 with SD 0.0091 after averaging fold 2 with fold 3. `best_valid` raises AUC by about 0.03 and cuts dense ECE from about 0.056–0.058 to about 0.007–0.010 relative to `final`. `full` and `slide` stay close to each other. Chunk does not remove the positive raw ΔECE. ΔECE* on the primary cell is positive on fold 1 and negative on the other four runs. That sign pattern is reported, not turned into a manuscript conclusion.
