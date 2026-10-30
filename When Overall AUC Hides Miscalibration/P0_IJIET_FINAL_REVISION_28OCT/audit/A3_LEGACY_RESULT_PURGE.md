# A3 Legacy result purge

Date: 2026-10-29

Status: PASS

Files edited (always all three):

- `manuscript-pack/manuscript/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.docx`
- `manuscript-pack/manuscript/..._blind.docx`
- `P0_IJIET_FINAL_CORRECTION_2026/artifact_final/07_submission/..._blind.docx`

The two blind files have identical text in all 600 paragraphs; the living blind copy still carries the red (FF0000) review marks and the submission blind copy does not. The named and blind bodies differ only in Author Contributions, Ethical Statement, and Acknowledgment (anonymization). The abstract was not edited. Table 4, Table 5, and Table A2 numbers were not changed. No model was retrained. The PDF and .doc files were not regenerated.

## FAR path

Path chosen: RECOMPUTE FAR. The fold 0-4 primary-protocol exports exist for ASSISTments DKT and T-KT masked, so FAR was recomputed instead of removed. FAR stays defined in the Introduction, Section III.G, equation (10), Section IV.E, Practical Implications, Limitations, and Tables A3 and A4. No "Not evaluated" FAR text remains.

| Item | Value |
| --- | --- |
| Script | `P0_IJIET_FINAL_REVISION_28OCT/scripts/a3_recompute_far_brier.py` |
| Inputs | `results/predictions/pred_assist2012_{dkt,tktc}_best_validxchunk_fold{0..4}_{42,2024,2025,2026,2027}.csv.gz` |
| Protocol | P0-BV200-15EW: validation-AUC checkpoint, windows of at most 200, no_history = 0, sparse 20 ≤ f < 100, dense f ≥ 500 |
| Threshold | τ = 0.7 |
| Definitions | FAR = mean(y = 0 given p ≥ τ); E[FAR] = mean(1 − p given p ≥ τ); excess = FAR − E[FAR]; FPR = mean(p ≥ τ given y = 0); ΔFAR = FAR_sparse − FAR_dense |
| Fold-0 interval | KC-clustered percentile bootstrap, KCs resampled within each group, B = 2,000, `numpy.random.default_rng(20261021)` new for each model, 2.5 and 97.5 percentiles |
| Invalid replicates | 0 of 2,000 for each model (38 sparse KCs, 147 dense KCs) |
| Four-partition summary | fold 2 and fold 3 averaged first, SD with ddof = 1 |
| Outputs | `results/A3_far_fold0.csv`, `A3_far_partitions.csv`, `A3_far_four_partition.csv` |

Fold 0 (Table A3):

| Model | Group | N | Nadv | Ninc | FAR [95% CI] | E[FAR] | Excess | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DKT | sparse | 430 | 200 | 195 | 0.215 [0.138, 0.304] | 0.142 | 0.073 | 0.221 |
| DKT | dense | 521,348 | 300,610 | 156,258 | 0.179 [0.170, 0.187] | 0.178 | 0.001 | 0.344 |
| T-KT masked | sparse | 430 | 198 | 195 | 0.232 [0.163, 0.320] | 0.119 | 0.113 | 0.236 |
| T-KT masked | dense | 521,348 | 298,201 | 156,258 | 0.182 [0.173, 0.191] | 0.176 | 0.006 | 0.347 |

ΔFAR on fold 0: DKT 0.036 [−0.041, 0.125]; T-KT masked 0.051 [−0.019, 0.141]. Both intervals include 0.

Four partitions (Table A4): DKT ΔFAR 0.021 ± 0.019, range −0.001 to 0.038, 3 of 4 positive. T-KT masked 0.036 ± 0.038, range −0.007 to 0.081, 3 of 4 positive. Mean sparse N 397.75; mean sparse Nadv 190.63 (DKT) and 191.88 (T-KT masked); mean sparse Ninc 156.50.

## Base-rate paragraph in IV.B and Table A1

The base-rate reference has no primary-protocol prediction export, so its ECE and RES could not be recomputed. The base-rate paragraph was removed. It was replaced by a paragraph on the Brier decomposition of the two primary models, and Table A1 was rebuilt from the same exports with `src.brier_decomposition.compute_brier_decomposition` (15 equal-width bins), averaged over four partitions. Outputs: `results/A3_brier_partitions.csv`, `results/A3_brier_four_partition.csv`.

| Model | Group | Brier | UNC | REL | RES |
| --- | --- | --- | --- | --- | --- |
| DKT | sparse | 0.1904 ± 0.0088 | 0.2356 ± 0.0119 | 0.0137 ± 0.0026 | 0.0589 ± 0.0090 |
| DKT | dense | 0.1797 ± 0.0004 | 0.2100 ± 0.0003 | 0.0001 ± 0.0000 | 0.0301 ± 0.0001 |
| T-KT masked | sparse | 0.2039 ± 0.0187 | 0.2356 ± 0.0119 | 0.0215 ± 0.0076 | 0.0530 ± 0.0125 |
| T-KT masked | dense | 0.1817 ± 0.0004 | 0.2100 ± 0.0003 | 0.0004 ± 0.0001 | 0.0284 ± 0.0001 |

## Artifact

`artifact_v4/rebuild/far_brier.py` reimplements FAR, the KC-clustered bootstrap, and the 15-bin Brier decomposition without importing `src`. `artifact_v4/rebuild/reproduce_tables.py` now also checks every printed cell of Tables A1, A3, and A4. Data and Code Availability now says the one command recomputes "Tables 4, 5, A1, A2, A3, and A4". MANIFEST hashes were refreshed by `scripts/a3_patch_artifact.py`. The clean-copy result is in the section "Clean-copy check" below.

## Removed from the manuscript

| Removed item | Where | Class | Reason |
| --- | --- | --- | --- |
| Test-response-weighted regression of T-KT KC-level ECE on log(1 + ftrain) and descriptors (−0.063 [−0.081, −0.045]; −0.006 [−0.009, −0.003]) | IV.E paragraph 1; sentence in III.G | INVALID | fitted on unmasked T-KT, trained and scored under different contexts |
| Controlled within-KC sparsification, 12 cells, seed 42, B = 10,000 | IV.E paragraph 2; sentence in III.G | LEGACY / INVALID | old final-checkpoint models, includes unmasked T-KT, not the primary protocol |
| Heading "E. KC-level associations and controlled sparsification" | IV.E | LEGACY | section emptied |
| Old Table A1, archived final-checkpoint full-history Brier decomposition | Appendix | LEGACY | obsolete checkpoint protocol; rows included unmasked T-KT and base rate |
| Old Tables A3 and A4, archived threshold probe | Appendix | LEGACY / INVALID | obsolete checkpoint protocol and unmasked T-KT; replaced by recomputed tables |
| "FAR is Not evaluated under P0-BV200-15EW" paragraph | IV.F | LEGACY | replaced by recomputed FAR results |
| Base-rate paragraph (ECE 0.0031 dense, 0.0777 sparse, RES 0) | IV.B | LEGACY | taken from old Table A1 |
| IRT base-rate sentence (AUC 0.5000) | III.C | LEGACY | no primary-protocol export |
| Table 2 caption sentence on the base-rate reference | Table 2 caption | LEGACY | reference removed |
| Junyi T-KT seed-alignment sentence; "On every dataset, seeds" | III.B | LEGACY | Junyi T-KT is unmasked; now "On ASSISTments 2012 and Junyi Academy, seeds" |
| "original weights behind the archived final-checkpoint pairs were not recovered. Those pairs are not results of this protocol." | III.C checkpoint paragraph | LEGACY | no longer referenced |
| "The archived full-history pairs are not this protocol, and their weights were not recovered." | Limitations | LEGACY | no longer referenced |
| "alternative frequency grids of the archived final-checkpoint analysis" | IV.D | LEGACY | replaced by "Alternative frequency cut points were not evaluated under this protocol." |
| "FAR was not recomputed." | Limitations | LEGACY | replaced by "FAR uses one threshold, and its interval covers fold 0 only." |

Section renumbering: IV.D renamed "Checkpoint and test-window sensitivity". IV.E deleted. IV.F "Threshold analysis" is now IV.E. No cross-reference pointed to IV.E or IV.F.

## Remaining occurrences (named manuscript, after edits)

Paragraph numbers are body paragraph indices in `word/document.xml`. Search terms: unmasked, T-KT, Table A1, Table A3, Table A4, sparsification, regression, FAR, archived, final checkpoint, final epoch, full history, full test history, Not evaluated, base rate.

| Para | Location | Term | Class | Note |
| --- | --- | --- | --- | --- |
| 13 | Introduction | FAR | PRIMARY | definition; recomputed under the primary protocol |
| 19 | RQ paragraph | final checkpoint, full test history | SENSITIVITY | RQ3 refers to the Table A2 grid |
| 20 | Contributions | T-KT masked; "Unmasked T-KT is not used as a finding" | PRIMARY; INVALID (exclusion statement) | no result from unmasked T-KT |
| 23 | Related work | logistic regression | not a result | citation of [9] |
| 62, 67, 70 | III.C, Table 2 | T-KT masked | PRIMARY | configuration |
| 63 | III.C | final epoch, full test history | SENSITIVITY | "appear only as sensitivity cells in Table A2" |
| 66, 155, 156, 158 | Fig. 1, III.F, Table 3 | archived audit records | PRIMARY-supporting audit | partition leakage audit L1-L7; not a model result |
| 207 | III.G | T-KT masked | PRIMARY | threshold analysis on primary predictions |
| 208, 209 | III.G, equation (10) | FAR | PRIMARY | definition and bootstrap description |
| 212, 228 | IV.A, Table 4 | T-KT masked | PRIMARY | |
| 247-249, 351, 355 | Tables 4 and 5 | Not evaluated | not FAR | XES3G5M cells |
| 253, 258, 287, 296, 345 | IV.B, Table 5 | T-KT masked; "not evaluated" for XES3G5M | PRIMARY | |
| 255, 385, 414, 423 | IV.B, Table A1 | Table A1, T-KT masked | PRIMARY | recomputed Brier decomposition |
| 365 | Fig. 3 | T-KT masked | PRIMARY | |
| 368 | IV.D, Table A2 text | final × full, cut points not evaluated | SENSITIVITY | the explicitly marked 2×2 cells |
| 370 | IV.E | FAR, Table A3, Table A4, T-KT masked | PRIMARY | recomputed fold-0 and four-partition FAR, descriptive |
| 373 | Discussion | final checkpoint | SENSITIVITY | "does not claim that the final checkpoint causes it" |
| 377 | Practical implications | FAR, FPR | PRIMARY | reporting recommendation |
| 380 | Limitations | T-KT masked, Junyi T-KT, FAR | PRIMARY; LEGACY exclusion | "Junyi T-KT was not retrained with a mask" states an exclusion |
| 480-543 | Tables A3 and A4 | FAR, T-KT masked | PRIMARY | recomputed |
| 559 | Data and Code Availability | unmasked T-KT | INVALID (exclusion statement) | listed as not in the artifact |

No remaining occurrence of "sparsification", "Table A1/A3/A4" as an archived table, "archived final-checkpoint", or "full-history pairs". No current claim is supported only by unmasked T-KT.

## PASS condition

No main result remains from unmasked T-KT or from the obsolete final-checkpoint protocol. Final-checkpoint and full-history values appear only in the explicitly marked 2×2 sensitivity cells of Table A2 and in the text that describes them. A3 = PASS.

## Clean-copy check

Artifact v4 was copied to `%TEMP%\a3_v4_clean` without `__pycache__` and without the old `statistics/recomputed_checks.csv`. From that copy, `py -3 rebuild/reproduce_tables.py` ran for about 11 minutes and printed "PASS all supported table checks": 177 checked cells, 0 failures. The checks cover Tables 4, 5, and A2, the matched gaps, the fold-0 intervals, and now every printed cell of Tables A1, A3, and A4. The new check list replaced `artifact_v4/statistics/recomputed_checks.csv`, and its MANIFEST row was refreshed.
