# B1 — T-KT-c on ASSISTments

Date: 22/10/2026

Decision recorded before training: keep T-KT and correct it to T-KT-c. Causal mask, padding mask, `PAD = 2 * n_kcs`. No BOS, no extra shift, no positional encoding. The unmasked class in `src/baseline_runner.py` is unchanged. DKT still pads with 0. T-KT-c uses `collate_tktc`.

## Tests

`scripts/check_b1_tktc.py` printed `UT-A1 = PASS` through `UT-A7 = PASS` and `B1_TESTS = PASS` before `scripts/p0_b1_tktc_assist.py` started. The same script printed those lines again after training. UT-A3 and UT-A4 cover T-KT-c and DKT. UT-C1 for the shared trainer had already printed PASS in A4.

## Training

ASSISTments 2012, five runs, `best_valid × chunk`, patience 8, at most 50 epochs. Device: CUDA. Selected epochs in `runs/manifest.csv` match the first maximum of `valid_auc` in each `train_log.csv`.

| fold | init seed | selected epoch | last trained epoch | validation AUC | prediction rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 42 | 11 | 19 | 0.7268 | 534150 |
| 1 | 2024 | 15 | 23 | 0.7270 | 542748 |
| 2 | 2025 | 12 | 20 | 0.7279 | 528681 |
| 3 | 2026 | 9 | 17 | 0.7273 | 528681 |
| 4 | 2027 | 15 | 23 | 0.7261 | 515889 |

Fold 2 and fold 3 are one learner partition. Empty windows (`no_history = 1`) dropped before the ECE: 6763, 6799, 6743, 6743, and 6717 rows. Prediction files, checkpoints, and train logs are listed in the manifest. The model name in those rows is `tktc`, not simpleKT.

## Primary contrast

`scripts/check_b1_uncertainty.py`, seed `20261021`, same functions as the DKT A5 table. Primary ECE is 15 equal-width bins, rows `no_history = 0`. The cluster interval is fold 0 only, B = 2000, R = 200 inside each bootstrap. The point estimate uses R = 2000.

The script was run twice. Both writes of `results/B1_tktc_uncertainty.csv` were byte-identical (1452 bytes). Both writes of `results/B1_tktc_secondary.csv` were byte-identical (1403 bytes).

Figures below are rounded from the primary file.

| partition | ECE_sparse | ECE_dense | DeltaECE | DeltaECE_star | matched_dense_median | matched_gap | tail | cluster CI raw | cluster CI matched | N sparse | learners | KCs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| fold0 | 0.0951 | 0.0120 | 0.0832 | -0.0102 | 0.0586 | 0.0365 | 0.0235 | 0.0723 to 0.1345 | 0.0233 to 0.0878 | 430 | 155 | 38 |
| fold1 | 0.1448 | 0.0189 | 0.1259 | 0.0317 | 0.0614 | 0.0834 | 0.0010 |  |  | 423 | 140 | 39 |
| fold2 | 0.0967 | 0.0156 | 0.0811 | -0.0175 | 0.0628 | 0.0339 | 0.0470 |  |  | 386 | 145 | 37 |
| fold3 | 0.1087 | 0.0132 | 0.0955 | -0.0031 | 0.0610 | 0.0477 | 0.0085 |  |  | 386 | 145 | 37 |
| fold4 | 0.1371 | 0.0180 | 0.1191 | 0.0159 | 0.0656 | 0.0715 | 0.0015 |  |  | 352 | 153 | 40 |

The script printed the four-partition summary after averaging fold 2 with fold 3: ΔECE 0.104112 (SD 0.021516), ΔECE* 0.006782 (SD 0.020703), matched gap 0.058075 (SD 0.022980), sparse ECE 0.119936 (SD 0.024683), dense ECE 0.015823 (SD 0.003233).

On fold 0 the raw interval and the size-matched interval both exclude 0. ΔECE* is negative on fold 0 and on the shared fold 2/3 partition. It is positive on fold 1 and fold 4. The matched gap is positive on all five rows. Sparse support is 352 to 430 events, 140 to 155 learners, and 37 to 40 KCs. Fold 0 had 0 empty sparse bootstrap replicates and 2000 used matched replicates.

## Secondary checks

Source: `results/B1_tktc_secondary.csv`. These do not replace the primary ECE.

Event-level matched gaps, which ignore learner clusters: fold 0 is 0.0398 (tail 0.0035); fold 1 is 0.0871 (tail 0); fold 2 is 0.0382 (tail 0.006); fold 3 is 0.0506 (tail 0); fold 4 is 0.0739 (tail 0). No draw was invalid.

Equal-width and equal-mass ΔECE at M = 10, 15, and 20 stay positive on every row. On fold 0 the equal-width values are 0.0674, 0.0832, and 0.1025, and the equal-mass values are 0.0863, 0.0745, and 0.0919. ECE_sweep stops at 7 and 36 equal-mass bins. Kumar’s debiased squared calibration error on fold 0 is 0.00613 on sparse rows and 0.000275 on dense rows.

## Archived T-KT numbers

`manuscript-pack/analysis/si_threecut_tkt.csv` records the living four-partition pair: dense ECE 0.1136 on about 523971 events, sparse ECE 0.2280 on about 415 events, difference 0.1145. Those rows are the unmasked model under the archived protocol. They are LEGACY. They are not a second model and they are not a rescore of T-KT-c.

The new four-partition sparse ECE is 0.120 and the dense ECE is 0.016. Both differ from the archived pair by about a tenth, well past the 0.005 band the guidance uses when a rerun is close. Rule R8 is the matching rule: the old T-KT numbers carry a training-mask error, and a later manuscript edit should replace them rather than set the two pairs side by side. This run also changes the checkpoint and the window, so the whole drop is not identified as a mask-only effect. The manuscript was not edited in this step.
