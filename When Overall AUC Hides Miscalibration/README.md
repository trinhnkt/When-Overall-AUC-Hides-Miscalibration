# Experiment package

Code, configs, frozen tables, and manuscript sources for
*When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components*.

Start at the repository root `README.md`.

The living manuscript is 12 pages. Main-text Tables 1–6 and Appendix Tables A1–A4 stay in that file. Do not upload `supplementary.pdf`.

T-KT is a local Transformer reference, not published simpleKT. simpleKT is scored on ASSISTments 2012 only.

**LEVEL A** (no retrain): `bash scripts/rebuild_locked_tables.sh`

Locked Table 5 cells stay in `manuscript-pack/audit/SCIENTIFIC_LOCKS.md`. Validation-AUC summaries under `results/` (`A4_dkt_2x2.csv`, `A5_*`, `B1_tktc_*`, `B2_junyi_dkt_*`, `B3_simplekt_*`) do not replace those cells.
