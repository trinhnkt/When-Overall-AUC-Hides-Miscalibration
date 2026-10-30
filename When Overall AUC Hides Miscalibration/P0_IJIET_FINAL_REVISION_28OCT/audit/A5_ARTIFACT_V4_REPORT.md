# A5 — Artifact v4

Date: 2026-10-29

Decision: **A5 = PASS**.

Package: `P0_IJIET_FINAL_REVISION_28OCT/artifact_v4/`.

Index: `artifact_v4/MANIFEST.csv`.

## Code snapshot

`code/` is commit `4ff66835561e2597a50197dcfb93aba1ec74583b` (2026-10-21 16:03:08 +0700). It includes `src/`, the scripts and tests from that commit, and `docs/analysis_plan_P0_v2.md`.

The parent commit `46e0208` (2026-10-21 16:02:55 +0700) locked that plan before the supplementary runs. The first ASSISTments DKT training log on disk is timestamped 2026-10-21 21:58. A timestamped pre-result plan therefore exists for the ASSISTments DKT checkpoint-by-window grid and for the masked T-KT correction. The manuscript phrases “pre-specified” and “locked protocol” were left in place. Junyi DKT, simpleKT, and fold 5 remain described as later additions.

## Size-match function

`code/src/ece_uncertainty.py` keeps a prefix of the concatenated dense rows. The published gap does not. `rebuild/published_gap.py` keeps exactly N rows by a second sample without replacement, then runs the fold-0 learner-cluster bootstrap. The reproduce command calls that file. It does not call the 4ff6683 prefix function.

## Prediction coverage

Prediction exports exist for every fold used in Tables 4, 5, and A2. This is not a fold-0-only package.

| Export in `predictions/` | Folds | Recompute |
| --- | --- | --- |
| ASSISTments DKT, final and best validation, full history and window 200 | 0–4 | Table A2, and the primary rows of Tables 4 and 5 |
| ASSISTments T-KT masked, best validation, window 200 | 0–4 | Tables 4 and 5 |
| ASSISTments simpleKT, best validation, window 200 | 0–4 | Table 4 only |
| Junyi DKT, best validation, window 200 | 0–4 | post-hoc rows of Tables 4 and 5; focal group is medium |

Fold 2 and fold 3 are averaged before the four-partition standard deviation.

Not in the artifact, and not claimed as reproducible from it:

- fold 5
- the slide window
- XES3G5M predictions (Table 4 already says Not evaluated)
- Junyi simpleKT
- unmasked T-KT
- raw datasets
- model weights

Retraining is not supported.

## Logs, configs, tests

`configs/` holds the YAML files from commit 4ff6683. `configs/SEEDS.txt` records the five scored initialization seeds and the bootstrap seed 20261021. Those five seeds are not the seed list in the YAML files.

`logs/training/` holds the per-run training logs, including post-hoc runs. The weights are not included.

`logs/A1_DKT_TOKEN0_LOG.txt` is the token-0 check. `logs/UT_A1_A7_TKT_MASKED.txt` records UT-A1 through UT-A7, all PASS, run from the 4ff6683 test file on synthetic sequences.

`statistics/archived/` holds the earlier summary CSVs. The reproduce command does not read them.

## Clean-copy test

The package was copied to `C:\Users\EDM\AppData\Local\Temp\a5_v4_extract` (175 files, outside the project tree). From that copy:

```
py -3 rebuild/reproduce_tables.py
```

Exit code 0. Elapsed time about 11 minutes. Every checked digit matched the manuscript, including Table 4, Table 5, Table A2, the matched gaps, and the fold-0 intervals for ASSISTments DKT (0.0351; 0.0170 to 0.0821), masked T-KT (0.0365; 0.0233 to 0.0878), and Junyi DKT (0.0085; 0.0010 to 0.0434). The check list is `statistics/recomputed_checks.csv`.

Update during A3 (2026-10-29): `rebuild/far_brier.py` was added, and `rebuild/reproduce_tables.py` now also checks Tables A1, A3, and A4. A second clean-copy run passed 177 of 177 checks. See `audit/A3_LEGACY_RESULT_PURGE.md`.

Update after B5, C1, B2 (2026-10-29): the package was rebuilt with `predictions/base_rate_constants.csv` (constant p of each IRT rerun, source sha256, test-learner check), `rebuild/partition_intervals.py` (Table A5 supplementary intervals, separate command), `statistics/recorded/`, `scripts_28oct/`, and `audits/` (GATE_B_XES_REPORT.md, xes_padding_counts.csv). `rebuild/reproduce_tables.py` now checks the 16 rows of the new Table A1, the G column of Table A5, and the printed rounded counts of Tables 4, 5, A2, and A4. The README contains P0-BV200-15EW once. Clean copy `C:\Users\EDM\AppData\Local\Temp\art_v4_29oct_221802`: exit 0, 302 of 302 checks PASS, about 11.4 minutes. After the final rebuild (MANIFEST 219 files, adding three scripts to `scripts_28oct/`), every file in `rebuild/` and `predictions/` is byte-identical to the tested copy. `statistics/recomputed_checks.csv` is the list from that run.

## Manuscript

Data and Code Availability in the named Word file and both blind Word files now describes artifact v4, including what the one command recomputes and what the package does not contain. Table 5 and Table A2 numbers were not edited. The PDF was not regenerated.
