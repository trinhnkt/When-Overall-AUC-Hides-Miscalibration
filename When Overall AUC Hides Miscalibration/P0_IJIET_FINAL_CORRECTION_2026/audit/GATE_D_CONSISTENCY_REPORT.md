# Gate D — consistency of the rebuilt manuscript

Date: 25/10/2026.

Prerequisites: Gate A is `GATE_A_PASS_WITH_SCOPE_REDUCTION`. Gate B is `DESCRIPTIVE_AUDIT_ONLY`. Gate C is `GATE_C_PASS`.

**GATE_D_PASS**

The manuscript text was rebuilt from the locked exports. Legacy pairs and unmasked T-KT are not current findings. The title punctuation was not changed.

## What a reviewer sees

The four surfaces use the same primary models, the same protocol, the same conclusion, and the same limits.

| Surface | Primary models | Protocol | Central conclusion | Limits |
| --- | --- | --- | --- | --- |
| Abstract | DKT and causally masked Transformer on ASSISTments 2012 | Validation-AUC checkpoint, windows of at most 200, 15 bins, four unique partitions | Overall AUC can hide frequency-stratified calibration differences, but size and presence depend on protocol, checkpoint, sample size, model, and dataset | ΔECE* is not a significance test. Junyi has no sparse group and ΔECE* is −0.0032. XES3G5M is a descriptive audit only. |
| Table 5 | ASSISTments DKT and T-KT masked. Junyi DKT is marked post-hoc. | P0-BV200-15EW | Sparse ECE is higher than dense ECE. The gap is not attributed to the checkpoint alone. | ΔECE* is a bias reference. The 95% interval is fold 0 only. XES3G5M is not evaluated. |
| Fig. 3 | DKT and T-KT masked, fold 0, dense and sparse | Same protocol, N sparse = 430 | The figure does not show that a checkpoint removed or caused the difference. The four-partition means are in Table 5. | One partition. Junyi is not plotted. XES3G5M is a descriptive audit only and is not plotted. |
| Conclusion | DKT and the masked Transformer | Locked validation-AUC and window-200 protocol | Same sentence as the abstract | ΔECE* is −0.0081 for DKT and 0.0068 for the masked Transformer, and is not a test. Junyi −0.0032. XES3G5M has no model-based result. |

## Numbers on those surfaces

They match `results/C_unique_partition_summary.csv` and the fold-0 intervals in `results/C_bootstrap_replicates_fold0.csv.gz`.

- DKT four-partition ECE 0.0982 and 0.0089, ΔECE 0.0893, ΔECE* −0.0081, matched gap 0.0400.
- DKT fold 0 matched interval 0.0170 to 0.0821.
- T-KT masked fold 0 interval 0.0233 to 0.0878. Four-partition ΔECE* 0.0068.
- Junyi post-hoc ΔECE* −0.0032.

Fig. 3 was redrawn from `pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz` and `pred_assist2012_tktc_best_validxchunk_fold0_42.csv.gz`, rows with `no_history = 0`, using the same 15-bin rule as `compute_ece`.

## Source files

- `results/results_primary.csv`
- `results/results_sensitivity.csv`
- `results/results_legacy.csv`
- `results/results_invalid.csv`
- `docs/claim_evidence.csv`

Table A2 is the DKT checkpoint-by-window grid. No cell is missing. The final-by-full versus best-by-200 contrast is not given a single cause. Tables A1, A3, and A4 are captioned as archived and are not current findings. FAR is Not evaluated under the primary protocol.

## What this gate did not do

The blind file still needs the submission scrub in Gate E: red color, metadata, and the export package. Gates E was not started by this report.
