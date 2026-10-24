# C3 — official simpleKT on Junyi

Date: 22/10/2026

Official pyKT simpleKT, the same fixed config as `scripts/p0_retrain_official_simplekt.py`. Junyi learner splits, five runs, `best_valid × chunk`, patience 8, at most 50 epochs. Batch size 24, learning rate 1e-3. Device: CUDA. Fold 0 was trained first. Its first epoch finished in a few minutes, so folds 1–4 were trained with the same script. XES simpleKT was not trained: B4 failed UT-B8.

The contrast is medium minus dense. Medium is `100 ≤ f < 500`. It is not called sparse. The archived Junyi pair 0.0389/0.2513 is DKT under the old final-checkpoint full-history protocol. It is not replaced, and this cell is not written into Table 5.

## Training

`scripts/check_c3_simplekt_junyi.py` printed `C3_FILES = PASS`. The selected epoch in `runs/manifest.csv` is the first maximum of `valid_auc`. The simpleKT log starts at epoch 1. Each fold has 1327 concept ids and 25784 question ids in the model.

| fold | init seed | selected epoch | last trained epoch | validation AUC | prediction rows | no_history dropped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 42 | 5 | 13 | 0.8091 | 3269022 | 26138 |
| 1 | 2024 | 6 | 14 | 0.8061 | 3243926 | 25974 |
| 2 | 2025 | 4 | 12 | 0.8073 | 3244494 | 25934 |
| 3 | 2026 | 4 | 12 | 0.8074 | 3244494 | 25934 |
| 4 | 2027 | 4 | 12 | 0.8085 | 3163548 | 25572 |

Fold 2 and fold 3 are one learner partition. Logs: `runs/c3_simplekt_junyi.log` for fold 0 and `runs/c3_simplekt_junyi_rest.log` for the later folds. Prediction files are `results/predictions/pred_junyi_simplekt_best_validxchunk_fold{k}_{seed}.csv.gz`.

## Primary contrast

`scripts/check_c3_simplekt_junyi.py`, seed `20261021`, same functions as the Junyi DKT check. Rows `no_history = 0`. ECE uses 15 equal-width bins. The cluster interval is fold 0 only, B = 2000, R = 200 inside each bootstrap. The point estimate uses R = 2000.

The script was run twice. Both writes of `results/C3_junyi_simplekt_uncertainty.csv` were byte-identical (1466 bytes). Both writes of `results/C3_junyi_simplekt_secondary.csv` were byte-identical (1421 bytes).

Figures below are rounded from the primary file.

| partition | ECE_medium | ECE_dense | DeltaECE | DeltaECE* | matched_dense_median | matched_gap | tail | cluster CI raw | cluster CI matched | N medium | learners | KCs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| fold0 | 0.0516 | 0.0055 | 0.0461 | 0.0175 | 0.0197 | 0.0319 | 0 | 0.0327 to 0.0673 | 0.0190 to 0.0526 | 4580 | 169 | 33 |
| fold1 | 0.0663 | 0.0165 | 0.0498 | 0.0162 | 0.0263 | 0.0400 | 0.0010 |  |  | 3320 | 150 | 31 |
| fold2 | 0.0407 | 0.0073 | 0.0333 | -0.0101 | 0.0274 | 0.0133 | 0.0805 |  |  | 1991 | 123 | 25 |
| fold3 | 0.0349 | 0.0054 | 0.0295 | -0.0139 | 0.0272 | 0.0077 | 0.1445 |  |  | 1991 | 123 | 25 |
| fold4 | 0.0416 | 0.0078 | 0.0338 | 0.0059 | 0.0190 | 0.0226 | 0.0045 |  |  | 4816 | 142 | 35 |

The script printed the four-partition summary after averaging fold 2 with fold 3: ΔECE 0.040292 (SD 0.009049), ΔECE* 0.006910 (SD 0.013632), matched gap 0.026267 (SD 0.012693), medium ECE 0.049340 (SD 0.012754), dense ECE 0.009048 (SD 0.005077).

On fold 0 the raw interval and the size-matched interval both exclude 0. ΔECE* is positive on fold 0, fold 1, and fold 4. It is negative on the shared fold 2/3 partition. The four-partition mean of ΔECE* is smaller than its SD. The matched gap is positive on all five rows. Medium support is 1991 to 4816 events. Fold 0 had 0 empty medium bootstrap replicates and 2000 used matched replicates.

## Secondary checks

Source: `results/C3_junyi_simplekt_secondary.csv`. These do not replace the primary ECE.

On fold 0 the event-level matched gap is 0.0338 (tail 0). No draw was invalid. Equal-width ΔECE at M = 10, 15, and 20 is 0.0460, 0.0461, and 0.0469. Equal-mass ΔECE is 0.0470, 0.0466, and 0.0475. ECE_sweep stops at 12 and 73 equal-mass bins. Kumar’s debiased squared calibration error on fold 0 is 0.00286 on medium rows and 0.000101 on dense rows.

## What this does not change

The living Junyi sentence stays the archived DKT pair 0.0389/0.2513. The new DKT `best_valid × chunk` cell in `audit/B2_JUNYI_DKT_REPORT.md` also stays as DKT. This simpleKT table is a separate model under the new protocol. The manuscript was not edited, and the anonymous file was not rebuilt.
