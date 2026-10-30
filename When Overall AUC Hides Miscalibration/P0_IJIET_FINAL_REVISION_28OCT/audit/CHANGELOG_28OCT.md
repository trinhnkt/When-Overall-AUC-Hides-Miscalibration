# CHANGELOG_28OCT

## 2026-10-29

- Opened P0_IJIET_FINAL_REVISION_28OCT.
- Searched for `NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf`. The file was not found.
- Status set to BLOCKED. A1 left NOT_STARTED.
- Did not edit the manuscript. Did not change Table 5 or Table A2. Did not retrain.

## 2026-10-29 — A1

- Inspected DKT and `collate_fn` at commit `4ff6683`.
- Ran T0-a, T0-b, T0-c, T0-d, and UT-A4. All passed.
- A1 = PASS. Did not retrain. Did not edit the manuscript.

## 2026-10-29 — B4

- Read `configs/assist2012.yaml` and the model code at commit `4ff6683`. The YAML has no architecture or optimizer keys.
- Filled Table 2 in the named and blind manuscripts from those files and from the saved checkpoint keys.
- Wrote `audit/B4_TABLE2_CONFIG_TRACE.md`. B4 = PASS.
- Did not change Table 5 or Table A2. Did not retrain.

## 2026-10-29 — A2

- Traced the printed fold-0 matched gap 0.0351 and interval [0.0170, 0.0821] to `scripts/check_a5_uncertainty.py` and `results/A5_uncertainty_dkt_assist.csv`.
- The code permutes dense learners without replacement, appends rows until at least N_sparse, keeps exactly N_sparse rows, uses R = 2000, and subtracts the median dense ECE.
- Seed 20261021. Fold-0 bootstrap B = 2000, inner draws 200, percentiles 2.5 and 97.5. Empty sparse replicates are counted and omitted. The published fold-0 run had 0 invalid replicates.
- Updated Section III.E in the named and blind Word files. Equation (8) is the retained dense ECE. Equation (9) is G. FAR moved from (8) to (10).
- Wrote `audit/A2_MATCHED_GAP_METHOD_TRACE.md`. A2 = PASS.
- Did not change Table 5 or Table A2. Did not edit the abstract. Did not retrain. Did not regenerate the PDF.

## 2026-10-29 — A5

- Built `artifact_v4/` from commit `4ff6683`, with configs, seeds, training logs, the A1 log, the UT-A1–A7 log, and prediction exports for folds 0–4.
- A timestamped plan exists in commit `46e0208` (2026-10-21 16:02:55 +0700), before the first supplementary training log. Did not replace “pre-specified” or “locked protocol”.
- The 4ff6683 size-match keeps a prefix. The reproduce command uses the later random-subset draw.
- From a clean copy, `py -3 rebuild/reproduce_tables.py` exited 0 and matched Tables 4, 5, and A2, the matched gaps, and the fold-0 intervals.
- Rewrote Data and Code Availability in the named and blind Word files. Did not change table numbers. Did not retrain. Did not regenerate the PDF.

## 2026-10-29 - A3

- Classified every occurrence of unmasked T-KT, T-KT, Table A1/A3/A4, sparsification, regression, FAR, archived, final checkpoint, and full history in the manuscript as PRIMARY, SENSITIVITY, LEGACY, or INVALID.
- Removed the T-KT regression (unmasked), the controlled sparsification check (old models), the base-rate paragraph and IRT sentence, the Junyi T-KT seed sentence, and the archived-pairs sentences. Deleted Section IV.E; the threshold analysis is now IV.E.
- FAR path: recomputed. `scripts/a3_recompute_far_brier.py` computed FAR, E[FAR], FPR, and ΔFAR at τ = 0.7 from the folds 0-4 exports of ASSISTments DKT and T-KT masked, with a fold-0 KC-clustered bootstrap (B = 2000, seed 20261021). Rebuilt Tables A3 and A4 and the threshold results paragraph.
- Rebuilt Table A1 as the 15-bin Brier decomposition of the two primary models, and replaced the base-rate paragraph in IV.B with REL and RES from that table.
- Added `rebuild/far_brier.py` to artifact v4 and the A1/A3/A4 checks to `rebuild/reproduce_tables.py`. A clean-copy run passed 177 of 177 checks. Data and Code Availability now names Tables A1, A3, and A4.
- Wrote `audit/A3_LEGACY_RESULT_PURGE.md`. A3 = PASS.
- Did not edit the abstract. Did not change Table 4, Table 5, or Table A2. Did not retrain. Did not regenerate the PDF.

## 2026-10-29 — B5, C1, A4, B3, B6, B7, B2, B1, C3, A6, C2, artifact, gate

All manuscript edits went to the three copies in `scripts/msedit.py` (named, living blind, submission blind). Changed runs are red (FF0000) for review. No retraining. No metric value in Table 5 or Table A2 changed; only their N cells were rounded (B2).

- B5: `scripts/b5_stratified_metrics.py` wrote `results/B5_STRATIFIED_METRICS.csv`. Table A1 now has group-level N, AUC, ACC, Brier, UNC, REL, RES for DKT, T-KT masked, base rate, simpleKT (sensitivity), and Junyi DKT (post-hoc). IV.B paragraph on sparse vs dense REL and sparse-group AUC. `audit/B5_METRIC_TRACE.md`.
- C1: `scripts/c1_partition_intervals.py`; Table A5 added; one sentence each in III.E and IV.B. `audit/C1_PARTITION_INTERVALS.md`.
- A4: Tables 6 and 7 rebuilt from the split files by `scripts/table6_context.py` ("All values match"); IV.C rewritten. Three ASSISTments descriptors changed from the legacy file (ρ −0.227 → −0.241, −0.308 → −0.326; median item support 44.5 → 32). `audit/A4_TABLE6_TABLE7_REPORT.md`.
- B3: IV.D renamed "D. Sensitivity to checkpoint and test window"; RQ3 answer rewritten from Table A2. `audit/B3_RQ3_TRACE.md`.
- B6: V.A, V.B, and the Conclusion's first sentences revised. `audit/B6_MODEL_CLAIM_AUDIT.md`.
- B7: Junyi unmasked T-KT text removed; Fig. 3 and Table 5 captions shortened; XES claims sourced to artifact audits. `audit/B7_TEXT_CLEANUP.md`.
- B2: protocol defined once in III.C (ID once); Protocol ID column removed from Table 4; P-labels replaced by fold labels; counts rounded in Tables 4, 5, A2, A4 and in the text; Fig. 3 image redrawn with the title "ASSISTments 2012, primary protocol, fold 0" (`scripts/b2_fig3.py`; `p0_gate_d_rebuild.py` not re-run); follow-up for three remaining paraphrases and the Limitations sentence. `audit/B2_NOTATION_REPORT.md`.
- B1: Abstract rewritten (197 words) by `scripts/b1_abstract.py`; values from Table 5 and Table A2 only. `audit/B1_ABSTRACT_REPORT.md`.
- C3: Reference [21] given the Springer book title, LNCS vol. 16946, and publisher. The template's copyright/CC BY line was not added (standing instruction); flagged for decision. `audit/C3_FORMAT_REFERENCE_REPORT.md`.
- A6: checker and new-copy cleaner prepared (`scripts/a6_final_blind_qa.py`); not run, awaiting review. `audit/A6_FINAL_BLIND_QA.md` (BLOCKED).
- C2: not started. `audit/C2_XES_SCOPE_DECISION.md` (BLOCKED, decision needed).
- Artifact v4: rebuilt by `scripts/a5_build_artifact.py` with `predictions/base_rate_constants.csv` (`scripts/art_base_rate_constants.py`), `rebuild/partition_intervals.py`, `statistics/recorded/`, `scripts_28oct/`, and `audits/` (XES files). `rebuild/reproduce_tables.py` now checks the 16 rows of Table A1, the G column of Table A5, and the printed rounded counts. README has P0-BV200-15EW once. Data and Code Availability updated (`scripts/art_data_availability.py`).
- Gate: `docs/CLAIM_EVIDENCE_P4.csv` (`scripts/gate_claim_evidence.py`, 29 claims, all found in the three copies); `audit/FINAL_28OCT_GATE.md`.
- Did not regenerate the PDF or the .doc files. Did not commit or push.

## 2026-10-30 C3 template supplement
- Added the template copyright/CC BY line after the references (red, all three copies).
- Defined ECE, DKT, T-KT masked, LSTM, UKT, SD, CI, UT-A1..A7, UNC, RES, REL at first body use (red). No numbers changed. Details: audit/C3_FORMAT_REFERENCE_REPORT.md.


## 2026-10-30 A6
- Created a6_clean/*_A6_clean.docx (red -> Automatic, new copies, text unchanged). See audit/A6_FINAL_BLIND_QA.md.

## 2026-10-30 C2
- Recorded SCOPE_ASSISTMENTS_FOCUSED with reasons. No manuscript change.

## 2026-10-30 review fixes (scripts/c4_review_fixes.py, b1_abstract.py)
- Abstract: added that the conservative small-sample bias reference averaged -0.0081 for DKT (Table 5); 199 words; trimmed 'training-count', 'with a difference of', 'and'. Claim ABS-9 added to docs/CLAIM_EVIDENCE_P4.csv (30 claims, 0 not found).
- III.C: 'pre-specified' now cites the analysis plan committed 2026-10-21 (commit 46e0208, before the first supplementary run) and included in artifact v4; n in 'padding id 2n' defined (code: pad_index = 2 * n_kcs).
- Data and Code Availability: 'fold 5' explained as an additional run the paper does not report; per-partition L1-L7 records behind Table 3 stated as not shipped (runner code only).
- a6_clean/ regenerated from the updated red sources; P-1 PASS.

## 2026-10-30 reference [26] (scripts/c3_reference26.py)
- Checked against the Kaggle dataset page (read 2026-10-30): authors P. J. Chen, M. E. Hsieh, T. Y. Tsai, year 2020, licence CC BY-NC-SA 4.0 as printed in Kaggle's own citation. Title completed with Kaggle's subtitle; access date set to Oct. 30, 2026. Answers PDF question 6. a6_clean regenerated.

## 2026-10-30 AI statement (scripts/c5_ai_statement.py)
- Added Claude Sonnet 5.5 and the scripts-for-tables role; replaced the 'experimental results' sentence. Author-confirmed. a6_clean regenerated.

## 30 Oct 2026 - full-text audit
Full recomputation (303 PASS, 0 FAIL) and line-by-line text audit; no manuscript change. See audit/FULL_TEXT_AUDIT_30OCT.md.

## 30 Oct 2026 - review fixes 1, 2, 3, 5, 6 (scripts/c6_review_fixes.py)
- III.F and Table 3 caption: 'three local models' replaced (audit covers the partition files and the training/scoring code of the locally implemented models, DKT and T-KT masked; simpleKT sentence kept).
- III.E: 8 literal N_sparse / ECE_sparse tokens now subscripts.
- Table A2: leftover 'reason missing' column removed (all cells were 'none'); no value changed.
- IV.A: last sentence rewritten. Table 1 caption: test events vs nonempty-history rows explained.
- Items 4, 7, 8, 9 of audit/MANUSCRIPT_REVIEW_30OCT.md left open for the authors. Red sources edited, a6_clean regenerated (12 pages, 0 red runs), all checks pass; no number changed.

- 30 Oct 2026 (review item 4): Data and Code Availability now explains fold 5 (scripts/c7_fold5.py): one additional run, labelled fold 5, added after the analysis plan; training logs included, predictions/weights not; not reported. Reason for not reporting is not stated (not recorded in audit files). Clean copies regenerated.

- 30 Oct 2026 (review items 1 and 7, scripts/c8_items1_7.py): after reading code and records. III.F now says the archived audit computes L1, L4, L7 from split files per partition (artifact code/scripts/p0_si_s10_leakage.py; records manuscript-pack/analysis/si_s10_leakage.csv) while L2, L3, L5, L6 are fixed PASS entries recorded from the pipeline code, not recomputed. This replaces the c6 wording about DKT/T-KT code. III.C: T-KT masked has no positional encoding (protocol_v2.TKTc). Clean copies regenerated.

- 30 Oct 2026 (review item 7, scripts/c9_table2_pos.py): Table 2 gets a 'Positional encoding' row: DKT none (recurrent); T-KT masked none, causal mask only (protocol_v2.TKTc); simpleKT cosine (pykt.models.simplekt.CosinePositionalEmbedding, pykt-toolkit 0.0.38 installed on the author's machine; confirm it is the version used for the runs). III.C sentence kept. Clean copies regenerated.

- 2026-10-30 21:5x pyKT version for simpleKT: pykt-toolkit 0.0.38, installed from a local copy (direct_url.json: file:./third_party/pykt-toolkit; artifact_v4 code/requirements-lock.txt line 97 says the same). The local copy is not in the workspace and the run outputs do not log the version, so 'this install produced the runs' rests on the lock file and the only installed copy. Its simplekt.py has CosinePositionalEmbedding (Table 2 row is consistent). Not yet written in the manuscript.

- 30 Oct 2026 21:5x (scripts/c10_table2_simplekt.py): Table 2 simpleKT positional-encoding cell 'Cosine (pyKT)' -> 'As in pyKT'. Reason: the pyKT version used for the runs is not recorded (requirements-lock.txt points to ./third_party/pykt-toolkit, absent from the workspace; installed 0.0.38 cannot be shown to be the run version). Clean copies regenerated.
