# B3 — official simpleKT on ASSISTments

Date: 22/10/2026

The fixed config is `OFFICIAL` in `scripts/p0_retrain_official_simplekt.py`: pyKT `simpleKT`, `d_model` 256, 2 blocks, 8 heads, dropout 0.05, sequence 200, Adam learning rate 0.001, batch 24, patience 8, at most 50 epochs. Selection is the best validation AUC. The May 2026 prediction CSVs and checkpoints were left in place. This training writes new logs because those runs had none.

`scripts/check_b3_simplekt.py` printed `B3_FILES = PASS`. Each manifest row has a train log, a checkpoint, and a P-2 prediction file. Selected epochs match the first maximum of `valid_auc`.

| fold | init seed | selected epoch | last trained epoch | validation AUC | prediction rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 42 | 3 | 11 | 0.7735 | 534150 |
| 1 | 2024 | 3 | 11 | 0.7730 | 542748 |
| 2 | 2025 | 2 | 10 | 0.7721 | 528681 |
| 3 | 2026 | 3 | 11 | 0.7727 | 528681 |
| 4 | 2027 | 2 | 10 | 0.7728 | 515889 |

Fold 2 and fold 3 are one learner partition. Empty chunk starts (`no_history = 1`) are 6763, 6799, 6743, 6743, and 6717 rows. `predict_test` is unchanged and still returns a probability on those rows. Primary ECE drops them.

## Comparison with the bản I pair

Source of the archived pair: `results/reports/p0_official_simplekt_assist_ece.json`. Dense ECE 0.020321, sparse ECE 0.088378, all scored rows, four-partition mean. The new all-rows four-partition means are dense 0.025130 (difference +0.004809) and sparse 0.089366 (difference +0.000988). Both are inside 0.005, so the published pair 0.0203 / 0.0884 is not replaced.

Individual folds move by more than 0.005. Dense: fold 3 +0.011380, fold 4 +0.006778. Sparse: fold 1 +0.012383, fold 2 +0.010981, fold 3 −0.025601. The new logs stop at epoch 2 or 3. There is no archived epoch log to compare with that choice. Sparse cells have a few hundred events, so one fresh initialization can move a fold while the four-partition mean stays inside the band. Both sets are recorded. The May files were not overwritten.

## Primary contrast, no_history = 0

`scripts/check_b3_simplekt.py`, seed `20261021`, same functions as the DKT A5 table. The script was run twice. Both writes of `results/B3_simplekt_uncertainty.csv` were byte-identical (1455 bytes). Both writes of `results/B3_simplekt_secondary.csv` were byte-identical (1416 bytes).

Figures below are rounded from the primary file. The cluster interval is fold 0 only.

| partition | ECE_sparse | ECE_dense | DeltaECE | DeltaECE_star | matched_gap | tail | cluster CI raw | cluster CI matched | N sparse | learners | KCs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| fold0 | 0.0695 | 0.0307 | 0.0388 | -0.0545 | 0.0061 | 0.3625 | 0.0294 to 0.0941 | -0.0049 to 0.0616 | 430 | 155 | 38 |
| fold1 | 0.0981 | 0.0209 | 0.0772 | -0.0170 | 0.0368 | 0.0115 |  |  | 423 | 140 | 39 |
| fold2 | 0.0907 | 0.0205 | 0.0702 | -0.0284 | 0.0273 | 0.0490 |  |  | 386 | 145 | 37 |
| fold3 | 0.0572 | 0.0254 | 0.0318 | -0.0667 | -0.0072 | 0.6530 |  |  | 386 | 145 | 37 |
| fold4 | 0.0968 | 0.0261 | 0.0707 | -0.0325 | 0.0330 | 0.0695 |  |  | 352 | 153 | 40 |

The script printed the four-partition summary after averaging fold 2 with fold 3: ΔECE 0.059438 (SD 0.017676), ΔECE* −0.037892 (SD 0.016711), matched gap 0.021479 (SD 0.015661), sparse ECE 0.084597 (SD 0.014952), dense ECE 0.025159 (SD 0.004284).

ΔECE* is negative on every row. The fold-0 size-matched interval contains 0. The matched gap is negative on fold 3. Four-partition sparse and dense ECE under this drop-empty-window rule, 0.0846 and 0.0252, also stay inside 0.005 of the archived pair. The manuscript was not edited.
