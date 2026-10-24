# C1 — one new ASSISTments learner partition

Date: 22/10/2026

Fold index 5. Shuffle seed 2028, using `np.random.seed` then `np.random.shuffle`, the same algorithm as `scripts/create_new_folds.py`. Split ratios 20% test and 10% valid. Init seed 42 for one run of each primary-protocol model. Protocol `best_valid × chunk` only. Folds 0–4 were not overwritten.

## Why fold 2 and fold 3 are one partition

`docs/answers_hau_2026-10-21.md` records the cause. `configs/assist2012.yaml` lists shuffle seeds `[42, 123, 2026]`, so fold 2 is shuffled with 2026. `scripts/create_new_folds.py` sets `NEW_FOLDS = {3: 2026, 4: 2027}`, so fold 3 reuses shuffle seed 2026. The labels “seed 2025” and “seed 2026” in the paper are init seeds, not shuffle seeds.

`scripts/check_c1_fold5.py` printed `fold2_eq_fold3 = 1` and `C1_SPLIT = PASS`. Each of folds 0–4 has 5561 test learners. Fold 5 also has 5561 test learners. Overlaps with fold 5: fold 0 is 1128, fold 1 is 1092, fold 2 is 1112, fold 4 is 1115. The five distinct test sets are folds 0, 1, 2, 4, and 5. Fold 3 remains the duplicate of fold 2. Fold 5 is not a sixth independent partition and is not folded into the four-partition mean.

Split sizes written by `scripts/p0_c1_fold5.py`: train 1,859,797 rows / 19,465 learners; valid 266,667 / 2,780; test 531,026 / 5,561.

## Training

`runs/c1_fold5.log` ended with `C1 QUEUE DONE`. Device: CUDA. Patience 8, at most 50 epochs. `scripts/check_c1_fold5.py` printed `C1_FILES = PASS`. The selected epoch in `runs/manifest.csv` is the first maximum of `valid_auc` in each train log. DKT and T-KT-c logs start at epoch 0. The simpleKT log starts at epoch 1.

| model | selected epoch | last trained epoch | validation AUC | prediction rows | no_history dropped |
| --- | ---: | ---: | ---: | ---: | ---: |
| DKT | 6 | 14 | 0.732821 | 531026 | 6748 |
| T-KT-c | 10 | 18 | 0.727627 | 531026 | 6748 |
| simpleKT | 2 | 10 | 0.773283 | 531026 | 6748 |

Prediction files:

- `results/predictions/pred_assist2012_dkt_best_validxchunk_fold5_42.csv.gz`
- `results/predictions/pred_assist2012_tktc_best_validxchunk_fold5_42.csv.gz`
- `results/predictions/pred_assist2012_simplekt_best_validxchunk_fold5_42.csv.gz`

## Group AUC and ECE

Source: `scripts/check_c1_fold5.py`, seed `20261021` for the size-matched draws only. Rows `no_history = 0`. ECE uses 15 equal-width bins. The cluster interval is not computed: that interval is specified for fold 0 only. Figures below are rounded from the script print. The full values are in `results/C1_fold5_group_metrics.csv`.

| model | group | N | learners | KCs | AUC | ECE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| DKT | sparse | 539 | 153 | 38 | 0.7939 | 0.0890 |
| DKT | dense | 517991 | 5538 | 147 | 0.7303 | 0.0054 |
| T-KT-c | sparse | 539 | 153 | 38 | 0.7670 | 0.1037 |
| T-KT-c | dense | 517991 | 5538 | 147 | 0.7256 | 0.0075 |
| simpleKT | sparse | 539 | 153 | 38 | 0.8011 | 0.0699 |
| simpleKT | dense | 517991 | 5538 | 147 | 0.7699 | 0.0159 |

Strict cold start has 1 event. Very sparse has 26 events, 14 learners, and 8 KCs. Those two groups are too small for a contrast and are left in the CSV.

| model | overall AUC | DeltaECE | DeltaECE* | matched dense median | matched gap | tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DKT | 0.7322 | 0.0836 | 0.0002 | 0.0509 | 0.0381 | 0.0125 |
| T-KT-c | 0.7275 | 0.0962 | 0.0127 | 0.0527 | 0.0510 | 0.0070 |
| simpleKT | 0.7712 | 0.0540 | -0.0294 | 0.0531 | 0.0167 | 0.1555 |

Size-matched draws: R = 2000, invalid = 0 on all three models. ΔECE* is essentially zero for DKT on this one partition, positive for T-KT-c, and negative for simpleKT. This does not replace the five-run tables, the archived simpleKT pair 0.0203/0.0884, or rules R1–R4. The manuscript was not edited.
