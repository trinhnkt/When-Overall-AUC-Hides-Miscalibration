# Gate A — protocol and model validity

Source: `Check list\25.10\Huong_dan_hop_nhat_P0_IJIET_NCS_Trinh_A_B_C_D_E.docx` (25/10/2026).

Date of this check: 25/10/2026.

Superseded by `audit/GATE_A_REPORT.md`. Verdict there: GATE_A_PASS_WITH_SCOPE_REDUCTION.

Overall on this first pass: **FAIL**

The manuscript was not edited. Abstract and Conclusion were not edited. The title was not changed.

## A-1. Lookahead tests and unmasked T-KT

Status: **FAIL**

`python -m pytest -q tests/test_protocol_v2.py` on 25/10/2026: 15 passed in 4.86s.

The tests that match the guidance are in that file:

- UT-A1: flipping the label at position t does not change predictions for earlier rows.
- UT-A2: flipping future labels does not change the current prediction.
- UT-A3: a prefix matches the masked full sequence, for T-KT-c and DKT, dropout off.
- UT-A4: trailing pad does not change valid positions, for T-KT-c and DKT.
- UT-A7: flipping the previous label does change the prediction.
- UT-C1: `best_valid` restores the epoch of maximum validation AUC, not the last epoch.

T-KT-c is `src/protocol_v2.py` class `TKTc`: causal upper triangle with diagonal 1, padding id `2 * n_kcs`, no second shift. The unmasked class in `src/baseline_runner.py` is still present and is not the class these tests cover.

ASSISTments T-KT-c has a train log and a checkpoint for each of the five runs. Manifest rows `b1-tktc-best_valid-chunk-fold0` through `fold4`. Selected epochs 11, 15, 12, 9, 15. Prediction files named in `runs/manifest.csv` are on disk. Dataset coverage of `tktc` is `assist2012` only.

The current blind manuscript still puts the unmasked T-KT pair in the main calibration table and still states the Junyi T-KT rise 0.0817 to 0.1136. No masked T-KT retraining exists for Junyi. Gate A-1 requires that no primary table or conclusion still rests on the unfixed T-KT. That condition is not met. Removing those sentences is Gate D, so it was not done here.

## A-2. DKT 2×2 and protocol lock

Status: **PASS** for the traced 2×2. The manuscript still states a single-cause checkpoint story; removing that sentence is Gate D.

`results/A4_dkt_2x2.csv` has, for each of the five ASSISTments DKT runs, `final × full`, `final × chunk`, `best_valid × full`, and `best_valid × chunk`, plus `best_valid × slide`. Each cell has AUC, ECE dense, ECE sparse, ΔECE, ΔECE*, N dense, and N sparse. Brier is not in this CSV.

For every `finalxfull`, `finalxchunk`, `best_validxfull`, and `best_validxchunk` row of models `dkt` and `tktc` in `runs/manifest.csv`, the checkpoint, the train log, and the prediction file exist. Code commit on those rows is `4ff6683`. Analysis-plan commit is `46e0208`.

`final` and `best_valid` are stored in two directories, not one checkpoint file. On folds 0, 1, 2, 3, and 4 the validation-AUC column is identical on every shared epoch (maximum absolute difference 0). The `final` logs have 50 epochs. The `best_valid` logs stop earlier (patience). The comparison of final weights with best-validation weights is the same training trajectory under the same seed, not two unrelated fits. Bản I weights remain NOT_RECOVERED, so `final × full` is not a rescore of 0.0602 / 0.2333.

Checkpoint selection uses validation AUC. The plan commit `46e0208d0fcd3d03d880449e5a6fdd2643619ee0` is 2026-10-21 16:02:55 +0700, message “Lock the 21/10 analysis plan before any supplementary run.” The first new train log, `runs/a_dkt/assist2012_fold0_seed42_final/train_log.csv`, is later the same day. The locked plan names `best_valid × chunk` as the primary DKT cell. There is no separate supervisor signature that this cell replaces Table 5 in the paper.

## What this gate does not close

- Old T-KT and the Junyi T-KT sentence are still in the primary text. Status for that use: **LEGACY**, and still present.
- XES3G5M is Gate B. Not scored here.
- Junyi ΔECE* −0.0032 is Gate C. Not scored here.
- Abstract and Conclusion were not rewritten.
