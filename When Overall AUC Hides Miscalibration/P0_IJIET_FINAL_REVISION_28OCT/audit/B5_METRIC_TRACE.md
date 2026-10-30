# B5 Stratified Brier and discrimination metrics

Date: 2026-10-29

Status: PASS

## Sources

| Item | Value |
| --- | --- |
| Script | `P0_IJIET_FINAL_REVISION_28OCT/scripts/b5_stratified_metrics.py` |
| Output | `P0_IJIET_FINAL_REVISION_28OCT/results/B5_STRATIFIED_METRICS.csv` (per run and four-partition rows) |
| Manuscript edit | `P0_IJIET_FINAL_REVISION_28OCT/scripts/b5_edit_manuscript.py --write` |
| Rows | primary exports `results/predictions/pred_{dataset}_{model}_best_validxchunk_fold{f}_{seed}.csv.gz`, no_history = 0, p not missing |
| Runs | (0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027); fold 2 and fold 3 averaged first; SD ddof = 1 |
| Brier decomposition | 15 equal-width bins, `rebuild/far_brier.py::brier_decomposition` (same values as `src.brier_decomposition` in A3) |
| AUC | `sklearn.metrics.roc_auc_score`; ACC uses p ≥ 0.5 |

Models:

- ASSISTments 2012: DKT and T-KT masked (primary), simpleKT (sensitivity, kept because Table 4 keeps it), base-rate reference.
- Junyi Academy: DKT (post-hoc) and the base-rate reference. Junyi simpleKT is not in Table 4 and was not added.
- Base-rate reference: the constant training proportion correct from `results/predictions/{dataset}_learner_based_irt_1pl_seed{seed}_predictions_rerun.csv` (one value per seed, checked constant). It was applied to the DKT primary row set of the same partition. The script stops if the IRT test learners differ from the DKT export learners; they matched in all ten files. AUC is 0.5000 and RES is 0 by construction.

Groups: sparse, medium, dense where present, plus `overall` (all nonempty-window rows) as a check against Table 4. Junyi has no sparse group.

## Checks

| Check | Result |
| --- | --- |
| Overall AUC and ACC equal Table 4 | DKT 0.7303/0.7354, T-KT masked 0.7244/0.7314, simpleKT 0.7711/0.7533, Junyi DKT 0.7554/0.7469: PASS |
| Group N equals Table 5 | 397.75, 517,329.5, 397.75, 517,329.5, 3,676.75, 3,200,666.25 (printed 3200666.3): PASS |
| Brier, UNC, REL, RES for DKT and T-KT masked sparse/dense equal the A3 Table A1 | PASS |

## Four-partition results (mean ± SD)

| Dataset | Model | Group | N | AUC | REL |
| --- | --- | --- | --- | --- | --- |
| ASSISTments | DKT | overall | 523,611.5 | 0.7303 ± 0.0005 | 0.0001 |
| ASSISTments | DKT | sparse | 397.75 | 0.7670 ± 0.0188 | 0.0137 ± 0.0026 |
| ASSISTments | DKT | dense | 517,329.5 | 0.7285 ± 0.0004 | 0.0001 ± 0.0000 |
| ASSISTments | T-KT masked | overall | 523,611.5 | 0.7244 ± 0.0007 | 0.0004 |
| ASSISTments | T-KT masked | sparse | 397.75 | 0.7476 ± 0.0344 | 0.0215 ± 0.0076 |
| ASSISTments | T-KT masked | dense | 517,329.5 | 0.7227 ± 0.0006 | 0.0004 ± 0.0001 |

Per run, DKT sparse AUC exceeded overall AUC in all five runs. T-KT masked sparse AUC was below overall AUC in fold 1 (0.7211 vs 0.7241) and fold 4 (0.7159 vs 0.7240).

The full table, including medium groups, ACC, Brier, UNC, RES, simpleKT, the base-rate reference, and Junyi, is in the CSV and in the new Table A1.

## Manuscript changes

- Table A1 replaced: "Group-level discrimination and Brier decomposition under the primary protocol". Columns Dataset, Model, Group, N (mean count, rounded), AUC, ACC, Brier, UNC, REL, RES. 16 rows. Group-level AUC is in this appendix table, not in Table 5.
- IV.B paragraph on Table A1 rewritten: sparse vs dense REL for both primary models; sparse-group AUC vs overall AUC, with the per-run qualification for T-KT masked.
- Table 4, Table 5, and Table A2 numbers unchanged. Abstract not edited.

## Open item

Artifact v4 checks only the A3 version of Table A1 (primary sparse and dense rows). The added rows and the IRT base-rate files are folded into the artifact at the end of this task batch; see the final gate.
