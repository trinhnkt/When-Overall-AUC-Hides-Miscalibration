# Reproduce one diagnostic table

Two tracks. **LEVEL A** (also called Track B) rebuilds locked tables from frozen CSVs and **does not** change ASSISTments T-KT ECE `0.1136` / `0.2280` or FAR `0.196` / `0.268`. Track A retrains local models and does **not** recreate those locked cells.

The Word manuscript prints Tables 1–6 and Appendix Tables A1–A4. Validation-AUC checkpoint summaries used in the text, and not in those tables, are the nine CSVs in `results/validation_checkpoint/` of the review zip. They do not replace the locked Table 5 cells.

## LEVEL A / Track B — rebuild locked tables (no retrain)

```bash
scripts/rebuild_locked_tables.sh
# Windows: scripts/rebuild_locked_tables.ps1
```

This reads `manuscript-pack/analysis/summary_4part_bucket.csv` (ASSISTments, Junyi) and the masked XES a2b summary, verifies the T-KT ECE locks, and writes the frozen CSVs that feed the printed Appendix (A1–A4 in the Word manuscript; TeX sources may still use old S-numbers). Three-cut sensitivity (Appendix Table A2) is `scripts/p0_si_threecut.py` on the frozen T-KT and DKT prediction CSVs. Full L1–L7 records are `scripts/p0_si_s10_leakage.py` on the frozen train/test split files; the Word manuscript reports that audit as Table 3.

## Track A — retrain local IRT / DKT / T-KT

1. Obtain ASSISTments 2012 / Junyi / XES3G5M from the original providers.
2. Train-only KC strata use cuts `f=0`, `0<f<20`, `20≤f<100`, `100≤f<500`, `f≥500` (see `analysis/leakage_audit_log.csv` L4).
3. `scripts/reproduce_one_dataset.sh` (or `.ps1`) retrains the local T-KT/DKT/IRT pipeline from a YAML config. It does **not** reproduce the locked ASSISTments T-KT ECE `0.1136`/`0.2280` or FAR `0.196`/`0.268`.
4. Four-partition ECE/Brier: `analysis/summary_4part_bucket.csv`.
5. Reliability figure (main-text Fig. 3): `manuscript-pack/figures/generate_fig2_reliability.py` (seed-42 prediction CSVs + `results/tables/kc_strata.csv`). Pipeline Fig. 1: `manuscript-pack/figures/generate_fig1_pipeline.py`.
6. T-KT is a local Transformer baseline, not published SimpleKT. Official SimpleKT `[4]` on ASSISTments is `results/reports/p0_official_simplekt_assist_ece.json`.
7. BKT is not a scored baseline (pyBKT 1.4.1 degenerated on ASSISTments seed 42); IRT is the classical reference.

Reviewers receive this zip, with `analysis/`, `a2b/`, and `figures/` at the zip root. On disk those trees stay in the living manuscript folder (the prefix used by repo scripts). Do not upload a separate `supplementary.pdf`.
