# Changelog

## 2026-10-25

- Opened correction project `P0_IJIET_FINAL_CORRECTION_2026`.
- Searched the project for `Huong_dan_hop_nhat_P0_IJIET_NCS_Trinh_A_B_C_D_E.docx`. The file is not present.
- Gate A set to BLOCKED. Gates B–E left NOT_STARTED.
- No manuscript, number, title, abstract, or conclusion edit.

## 2026-10-25 — Gate A

- Read `Check list\25.10\Huong_dan_hop_nhat_P0_IJIET_NCS_Trinh_A_B_C_D_E.docx`.
- Ran `tests/test_protocol_v2.py`: 15 passed.
- Checked `runs/manifest.csv`, `results/A4_dkt_2x2.csv`, and the DKT train logs for folds 0–4.
- Gate A set to FAIL. A-1 FAIL. A-2 PASS. Gates B–E remain NOT_STARTED.
- No manuscript edit.

## 2026-10-25 — Task A lock

- Wrote `docs/PROTOCOL_DECISION_LOG.md` from `runs/manifest.csv`. All 54 prediction checksums matched.
- Computed Brier for the DKT 2×2 cells into `results/A4_dkt_2x2_brier.csv`.
- Wrote `audit/GATE_A_REPORT.md`.
- Verdict: GATE_A_PASS_WITH_SCOPE_REDUCTION.
- No manuscript edit. Gates B–E not started.

## 2026-10-25 — Task B

- Chose path B2. Did not retrain DKT, masked T-KT, or simpleKT on XES3G5M.
- Added `tests/test_xes_events.py`. `py -3 -m pytest -q tests/test_xes_events.py`: 8 passed.
- Audited both question-level sequence files. Learner overlap 0. Events 5,549,184. KC attachments 6,412,912. Distinct questions 7,651. Question 6232 is absent. 301 train responses are repeated at a window boundary.
- Wrote `audit/GATE_B_XES_REPORT.md`.
- XES_STATUS = DESCRIPTIVE_AUDIT_ONLY. Legacy XES AUC/ECE excluded.
- No manuscript edit. Gates C–E not started.

## 2026-10-25 — Task C

- Replayed ASSISTments DKT, ASSISTments T-KT masked, and Junyi DKT from the prediction files with seed 20261021.
- The replay matched the published uncertainty tables within 1e-10.
- Stored 30,000 size-match draws and 6,000 fold-0 bootstrap replicates.
- Wrote `audit/JUNYI_DELTAECESTAR_TRACE.csv` and `audit/GATE_C_REPORT.md`.
- −0.0032 reproduces as round(mean of the four per-partition ΔECE* values, 4). Not flagged as a numerical discrepancy. Manuscript not edited.
- Verdict: GATE_C_PASS. Gates D and E not started.

## 2026-10-25 — Task D

- Wrote `results/results_primary.csv`, `results_sensitivity.csv`, `results_legacy.csv`, and `results_invalid.csv`.
- Wrote `docs/claim_evidence.csv`.
- Rebuilt Tables 2, 4, 5, and 6, Table A2, and Fig. 3 from the locked exports.
- Rewrote the abstract, research questions, results, discussion, and conclusion in the named and blind Word files.
- Legacy numbers and unmasked T-KT are not current findings. XES3G5M stays a descriptive audit.
- Verdict: GATE_D_PASS. Report: `audit/GATE_D_CONSISTENCY_REPORT.md`.

## 2026-10-25 — Task E

- Built `artifact_final/` with manifest, splits, training hashes, prediction exports, audits, statistics, rebuild notes, and the submission folder.
- Recolored remaining red runs in the blind and named Word files. The blind submission copy has no `FF0000` left.
- Updated the cover letter. Did not change the title punctuation and did not add a CC BY line.
- Verdict: NOT_READY_TO_SUBMIT. Author confirmation, reference verification, and the blind PDF are still open.

## 2026-10-25 — Task E, second pass

- Copied prediction checksums and the claim-to-file index into `00_manifest`.
- Added simpleKT and T-KT masked config notes, support counts, and a leakage-test log (23 passed).
- Compared `IJIET_template.doc`. Copied its CC BY 4.0 author line. Did not copy its sample dates.
- Exported the blind PDF (12 pages). Title metadata uses the hyphen. Author metadata is empty.
- Verdict remains NOT_READY_TO_SUBMIT. Author confirmation and an external reference check are still open.
