# Gate A report

Date: 25/10/2026.

Source: `Check list\25.10\Huong_dan_hop_nhat_P0_IJIET_NCS_Trinh_A_B_C_D_E.docx`.

Decision log: `docs/PROTOCOL_DECISION_LOG.md`.

The manuscript was not edited.

## Verdict

GATE_A_PASS_WITH_SCOPE_REDUCTION

## Primary protocol ID

`P0-BV200-15EW`

Learner-disjoint train/validation/test. Checkpoint = best validation AUC. Test window = non-overlapping chunks of at most 200. KC groups from training counts only (cuts 0, 20, 100, 500). ECE = 15 equal-width bins, rows `no_history = 0`. Same `compute_ece` for every model.

Pre-specified primary estimand, commit `46e0208` (2026-10-21 16:02:55 +0700), before the first supplementary train log: DKT on ASSISTments 2012 under this protocol. The same commit decides, before T-KT-c training, that unmasked T-KT is replaced by T-KT masked (`TKTc`).

`final` + full history is SENSITIVITY when it is the 21/10 retrain, and LEGACY when it is a bản I number whose weights were not recovered.

## Is “pre-specified” justified?

Yes, only for the DKT ASSISTments grid and the T-KT-c correction written in commit `46e0208`.

No, for Junyi DKT, the simpleKT reruns, fold 5, the positional ablation, and Junyi simpleKT. Those are post-hoc robustness analyses. The manuscript may keep the word “pre-specified” only on the DKT check named in that commit.

## T-KT leak-test status

PASS for T-KT masked. FAIL for unmasked T-KT as a main-claim model.

On 25/10/2026, `tests/test_protocol_v2.py`: 15 passed.

| Test | Result for T-KT masked |
| --- | --- |
| Flip `y_t`: earlier predictions unchanged | PASS (UT-A1) |
| Flip future labels: current prediction unchanged | PASS (UT-A2) |
| Trailing pad: valid positions unchanged | PASS (UT-A4) |
| Prefix versus masked full sequence in `eval` | PASS (UT-A3) |
| Flip the previous interaction: current prediction may change | PASS (UT-A7) |

Input at position `i` is the token of row `i`. The dataset shift already targets the next row, so the module does not shift again. The causal mask is `triu(..., diagonal=1)`. The padding id is `2 * n_kcs`, not a real interaction. DKT still pads with 0. That is a different model and was not changed.

T-KT masked was retrained on ASSISTments only (five runs, plus post-hoc fold 5). The label in this log is **T-KT masked** (`tktc` in the files). Junyi was not retrained with the mask.

Unmasked T-KT (Table 5: 0.1136 to 0.2280; Junyi: 0.0817 to 0.1136) is **INVALID** for a main claim. Those numbers stay LEGACY. They are not reused as T-KT masked.

## 2×2 completeness

COMPLETE for ASSISTments DKT, five runs. No cell was inferred.

Cells: A = `final × full`, B = `final × chunk`, C = `best_valid × full`, D = `best_valid × chunk`. Source: `results/A4_dkt_2x2.csv`. Each cell has a prediction file. All 54 manifest checksums matched on 25/10/2026.

`final` and `best_valid` are two directories. On folds 0–4 the validation-AUC series is identical on every shared epoch (maximum absolute difference 0). B versus D is a checkpoint contrast on the same training trajectory and the same window. Bản I weights are NOT_RECOVERED, so A is not a rescore of 0.0602 / 0.2333.

Fold 0, from the CSV, with Brier computed on `no_history = 0` from the prediction files (`results/A4_dkt_2x2_brier.csv`):

| Cell | AUC | ECE dense | ECE sparse | ΔECE | N dense | N sparse | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A final × full | 0.7031 | 0.0562 | 0.2251 | 0.1689 | 522542 | 430 | 0.1910 |
| B final × window ≤ 200 | 0.7014 | 0.0559 | 0.2179 | 0.1620 | 521348 | 430 | 0.1915 |
| C best-valid × full | 0.7319 | 0.0067 | 0.1045 | 0.0977 | 522542 | 430 | 0.1792 |
| D best-valid × window ≤ 200 | 0.7305 | 0.0070 | 0.0916 | 0.0846 | 521348 | 430 | 0.1795 |

A versus B changes only the test window. The sparse ECE moves from 0.2251 to 0.2179.

B versus D changes only the checkpoint, window fixed. The sparse ECE moves from 0.2179 to 0.0916.

A versus D changes both. That gap is not attributed to either factor alone.

## Primary / sensitivity / legacy

| Item | Status |
| --- | --- |
| ASSISTments DKT `best_valid × chunk` | PRIMARY, pre-specified |
| ASSISTments T-KT masked `best_valid × chunk` | PRIMARY replacement for unmasked T-KT, pre-specified as the correction |
| ASSISTments DKT `final × full`, `final × chunk`, `best_valid × full`, slide | SENSITIVITY, pre-specified as the secondary grid |
| Junyi DKT `best_valid × chunk` | Same rules, post-hoc. Not called pre-specified. |
| ASSISTments simpleKT rerun | SENSITIVITY, post-hoc. Archived 0.0203/0.0884 is LEGACY. |
| Fold 5, TKT_PE, Junyi simpleKT | SENSITIVITY, post-hoc. Not in the four-partition mean. |
| Bản I final/full pairs | LEGACY. Weights NOT_RECOVERED. |
| Unmasked T-KT, both datasets | INVALID for a main claim |
| XES3G5M model results | NOT_EVALUATED here (Gate B) |

## Statements that must be removed or narrowed

Not edited in this step. Gate D must apply this list.

1. Table 5, its caption, and the opening of IV.B still lead with final-checkpoint full-history numbers, including unmasked T-KT 0.1136 to 0.2280. Those rows are LEGACY or INVALID. They cannot remain the primary result.
2. The Junyi sentence “ECE rose from 0.0817 to 0.1136” is unmasked T-KT. Remove it from any primary claim. The manuscript already says the masked retraining was not run.
3. Do not explain the gap between the full-history Table 5 pair (0.0602 / 0.2333, or the new final × full pair 0.0562 / 0.2251) and the primary cell 0.0070 / 0.0916 as the effect of the checkpoint alone. That comparison changes checkpoint and test context together.
4. The limitations sentence that final-epoch weights scored in windows of 200 still showed a positive raw ΔECE, and that the large drop came from restoring the validation-AUC checkpoint, is a B-versus-D statement. Keep it only if it names window 200 on both sides. Do not let it explain the full-history table.
5. “Pre-specified” in III.C and IV.B is justified for the DKT check in commit `46e0208`. Remove it from any later round (fold 5, positional ablation, Junyi simpleKT, Junyi DKT).

## Scope reduction

Primary model claims under this gate are ASSISTments DKT and ASSISTments T-KT masked, both at `P0-BV200-15EW`. Unmasked T-KT is out. Junyi T-KT is out. Bản I final/full numbers are audit history, not the primary protocol. XES model claims are untouched until Gate B.
