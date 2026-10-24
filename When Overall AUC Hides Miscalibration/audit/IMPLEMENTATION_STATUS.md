# Implementation status

Source: Huong_dan_thuc_nghiem_bo_sung_NCS_Trinh_P0_IJIET_v2.pdf, 21/10/2026.

PASS is set only when an executable check prints PASS.

| Item | Status | Evidence |
| --- | --- | --- |
| A1 Freeze and export | PASS | `scripts/check_a1_freeze.py` printed `A1 = PASS` on 21/10/2026. Report: `audit/A1_FREEZE_AND_EXPORT_REPORT.md`. |
| A2 Analysis plan | PASS | `scripts/check_a2_plan.py` printed `A2 = PASS`. Locking commit `46e0208` at 16:02 is before the first result at 21:56. Report: `audit/A2_ANALYSIS_PLAN_CHECK.md`. |
| A3 Windowed scoring | PARTIAL_NOT_RECOVERED | `scripts/check_a3_window.py` printed `A3 = PARTIAL_NOT_RECOVERED`. UT-W1 and UT-W2 passed. Ban I DKT weights are NOT_RECOVERED. The A4 queue later scored all five folds. Report: `audit/A3_WINDOW_CONTEXT_REPORT.md`. |
| A4 Validation checkpoint | PASS | `scripts/check_a4_checkpoint.py` printed `UT-C1 = PASS` and `A4 = PASS`. Table: `results/A4_dkt_2x2.csv`. Report: `audit/A4_CHECKPOINT_SELECTION_REPORT.md`. |
| A5 Uncertainty | COMPLETED | `scripts/check_a5_uncertainty.py` was run twice with seed 20261021. The two primary CSVs were byte-identical. Report: `audit/A5_UNCERTAINTY_REPORT.md`. Decision: `audit/A_LEVEL_DECISION.md`. |
| B1 T-KT-c | COMPLETED | `scripts/check_b1_tktc.py` printed `UT-A1 = PASS` through `UT-A7 = PASS` before training. Five ASSISTments runs, `best_valid × chunk`. Table: `results/B1_tktc_uncertainty.csv`, byte-identical on a second run. Report: `audit/B1_TKTC_REPORT.md`. |
| B3 simpleKT | COMPLETED | `scripts/check_b3_simplekt.py` printed `B3_FILES = PASS`. Five ASSISTments runs. All-rows four-partition ECE stays within 0.005 of 0.0203/0.0884. Table: `results/B3_simplekt_uncertainty.csv`, byte-identical on a second run. Report: `audit/B3_SIMPLEKT_REPORT.md`. |
| B2 Junyi DKT | COMPLETED | Five runs, `best_valid × chunk`. Contrast is medium–dense. `scripts/check_b2_junyi.py` printed `B2_FILES = PASS`. Table: `results/B2_junyi_dkt_uncertainty.csv`. Report: `audit/B2_JUNYI_DKT_REPORT.md`. |
| B4 XES events | R7 | `scripts/check_b4_utb.py sample` printed `B4_SAMPLE = PASS`. Full data printed UT-B1–UT-B7 PASS and UT-B8 FAIL: 7651 questions, catalogue id 6232 has no attempt. No XES training. Report: `audit/B4_XES_EVENT_REPORT.md`. |
| B5 Manuscript | REDLINE | `docs/claim_evidence.csv` updated. `audit/B5_REDLINE.md` is ready for the supervisor. The anonymous file was not rebuilt. |
| C1 New partition | COMPLETED | Fold 5, shuffle seed 2028. `scripts/check_c1_fold5.py` printed `C1_SPLIT = PASS` and `C1_FILES = PASS`. Table: `results/C1_fold5_group_metrics.csv`. Report: `audit/C1_PARTITION_REPORT.md`. |
| C2 TKT_PE | COMPLETED | Ablation, ASSISTments fold 0, init seed 42. `scripts/check_c2_tktpe.py` printed `C2_FILES = PASS`. Table: `results/C2_tktpe_vs_tktc_fold0.csv`. Does not replace T-KT-c. Report: `audit/C2_TKTPE_REPORT.md`. |
| C3 Junyi simpleKT | COMPLETED | Five Junyi runs, `best_valid × chunk`. Contrast is medium–dense. `scripts/check_c3_simplekt_junyi.py` printed `C3_FILES = PASS`. Table: `results/C3_junyi_simplekt_uncertainty.csv`, byte-identical on a second run. XES simpleKT was not run. Report: `audit/C3_JUNYI_SIMPLEKT_REPORT.md`. |
| Ban I DKT/T-KT weights | NOT_RECOVERED | `legacy/BAN_I_WEIGHTS.md`. |
