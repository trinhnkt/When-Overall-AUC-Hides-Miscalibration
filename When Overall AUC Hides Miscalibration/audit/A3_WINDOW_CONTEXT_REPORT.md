# A3 — DKT evaluation-context audit

Date: 21/10/2026

Executable check: `scripts/check_a3_window.py`

```
UT-W1 PASS
UT-W2 PASS
simpleKT no_history rule PASS
Version-I DKT checkpoints NOT_RECOVERED
A3 = PARTIAL_NOT_RECOVERED
```

## What was not done

`predict_sequential` was left in place. Ban I DKT weights are not on disk, so full-mode scoring was not asked to reproduce ECE 0.0602 and 0.2333. Those two targets were not written into the table. `REPRODUCTION_MISMATCH` was not raised, because there is no old checkpoint to score. The numbers below are from A4 retrains.

Folds 3 (seed 2026) and 4 (seed 2027) are not in the table yet. The training queue had not written those prediction files when the check ran.

## Rules that the tests cover

`predict_windowed` scores `full`, `chunk` (non-overlapping blocks of 200), and `slide` (at most 199 preceding events). `no_history = 1` when that window is empty. Primary ECE drops those rows. Keeping them with p = 0.5 is only the Version-I sensitivity.

UT-W1: chunk-mode probabilities on `no_history = 0` match a training-style forward on the same chunk. UT-W2: `full` and `slide` flag one row per learner; `chunk` flags one row per chunk, including a one-row tail.

The same chunk-start rule is implemented for simpleKT in `simplekt_no_history`. `predict_test` itself is unchanged. T-KT-c uses `predict_windowed`, so it gets the same flag. Neither simpleKT nor T-KT-c was trained in this step.

## Table

Source file, not a hand edit: `results/tables/p0_a3_window_context.csv`. Primary rows are `no_history = 0`. `DeltaECE_star = DeltaECE - 0.5 * sqrt(15 / N_sparse)`. That bound is the ban I reference, not a confidence interval. Values below are rounded from that file.

| partition | protocol | N_dense | N_sparse | ECE_dense | ECE_sparse | DeltaECE | DeltaECE_star | n_no_history_dense | n_no_history_sparse |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fold0 | best_validxchunk | 521348 | 430 | 0.0070 | 0.0916 | 0.0846 | -0.0088 | 6670 | 14 |
| fold1 | best_validxchunk | 530083 | 423 | 0.0094 | 0.1109 | 0.1016 | 0.0074 | 6690 | 16 |
| fold2 | best_validxchunk | 514907 | 386 | 0.0082 | 0.0950 | 0.0867 | -0.0118 | 6613 | 16 |
| fold0 | best_validxfull | 522542 | 430 | 0.0067 | 0.1045 | 0.0977 | 0.0044 | 5476 | 14 |
| fold1 | best_validxfull | 531313 | 423 | 0.0091 | 0.1108 | 0.1017 | 0.0075 | 5460 | 16 |
| fold2 | best_validxfull | 516078 | 387 | 0.0078 | 0.0983 | 0.0905 | -0.0079 | 5442 | 15 |
| fold0 | best_validxslide | 522542 | 430 | 0.0067 | 0.1045 | 0.0978 | 0.0045 | 5476 | 14 |
| fold1 | best_validxslide | 531313 | 423 | 0.0092 | 0.1107 | 0.1015 | 0.0074 | 5460 | 16 |
| fold2 | best_validxslide | 516078 | 387 | 0.0078 | 0.0983 | 0.0905 | -0.0080 | 5442 | 15 |
| fold0 | finalxchunk | 521348 | 430 | 0.0559 | 0.2179 | 0.1620 | 0.0687 | 6670 | 14 |
| fold1 | finalxchunk | 530083 | 423 | 0.0580 | 0.2312 | 0.1732 | 0.0791 | 6690 | 16 |
| fold2 | finalxchunk | 514907 | 386 | 0.0576 | 0.1660 | 0.1084 | 0.0098 | 6613 | 16 |
| fold0 | finalxfull | 522542 | 430 | 0.0562 | 0.2251 | 0.1689 | 0.0755 | 5476 | 14 |
| fold1 | finalxfull | 531313 | 423 | 0.0575 | 0.2320 | 0.1746 | 0.0804 | 5460 | 16 |
| fold2 | finalxfull | 516078 | 387 | 0.0576 | 0.1662 | 0.1086 | 0.0102 | 5442 | 15 |
| fold0 | finalxslide | 522542 | 430 | 0.0560 | 0.2249 | 0.1689 | 0.0755 | 5476 | 14 |
| fold1 | finalxslide | 531313 | 423 | 0.0577 | 0.2343 | 0.1766 | 0.0824 | 5460 | 16 |
| fold2 | finalxslide | 516078 | 387 | 0.0576 | 0.1625 | 0.1049 | 0.0065 | 5442 | 15 |

R1–R4 are not applied in this report. Folds 3 and 4 are absent, and the matched-size interval belongs to A5.
