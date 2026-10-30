# P0_IJIET_FINAL_REVISION_28OCT

Date: 2026-10-29

| Item | Status |
| --- | --- |
| A1 DKT token-0 handling at commit 4ff6683 | PASS |
| A2 Size-matched gap and fold-0 interval | PASS |
| A3 Legacy and invalid result purge; FAR and Brier recomputed | PASS |
| A4 Tables 6 and 7 rebuilt (RQ2) | PASS |
| A5 Artifact v4 (rebuilt 29 Oct; 302/302 checks) | PASS |
| A6 Red formatting cleanup and final blind QA | BLOCKED (awaiting supervisor review of red changes) |
| B1 Abstract | PASS |
| B2 Notation | PASS |
| B3 RQ3 from Table A2 | PASS |
| B4 Table 2 model configuration | PASS |
| B5 Stratified Brier and discrimination metrics | PASS |
| B6 Model-dependence claims | PASS |
| B7 Obsolete text and captions | PASS |
| B8 Partition-level matched gaps printed; means/SD reproduce Table 5 | PASS |
| C1 Multi-partition matched-gap intervals (optional) | PASS |
| C2 XES3G5M scope decision (optional) | BLOCKED (decision needed; not started) |
| C3 Reference and template QA (optional) | PASS (Reference [21]); copyright line BLOCKED (decision needed) |
| Final gate | READY_FOR_SUPERVISOR_REVIEW |

Reports: `audit/A1_DKT_TOKEN0_REPORT.md`, `audit/A2_MATCHED_GAP_METHOD_TRACE.md`, `audit/A3_LEGACY_RESULT_PURGE.md`, `audit/A4_TABLE6_TABLE7_REPORT.md`, `audit/A5_ARTIFACT_V4_REPORT.md`, `audit/A6_FINAL_BLIND_QA.md`, `audit/B1_ABSTRACT_REPORT.md`, `audit/B2_NOTATION_REPORT.md`, `audit/B3_RQ3_TRACE.md`, `audit/B4_TABLE2_CONFIG_TRACE.md`, `audit/B5_METRIC_TRACE.md`, `audit/B6_MODEL_CLAIM_AUDIT.md`, `audit/B7_TEXT_CLEANUP.md`, `audit/C1_PARTITION_INTERVALS.md`, `audit/C2_XES_SCOPE_DECISION.md`, `audit/C3_FORMAT_REFERENCE_REPORT.md`, `audit/FINAL_28OCT_GATE.md`. Claim map: `docs/CLAIM_EVIDENCE_P4.csv`.

All manuscript edits are in the named docx, the living blind docx, and the submission blind docx. Changed runs are red for review. Table 5 and Table A2 metric values are unchanged; their N cells were rounded to integers (B2). No retraining. The PDF and .doc copies were not regenerated. CONFIRMED BY ALL AUTHORS: YES (set on 2026-10-30 21:50 at the first author's instruction; basis = the first author's statement that all authors agree; individual written confirmations of authors 2-5 are not on file).

The supervisor PDF `Check list/NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf` was found on 2026-10-30 and cross-checked in `audit/SUPERVISOR_PDF_CROSSCHECK.md`. Its P-1 checker is `scripts/check_blind.py`. Still not done from the PDF: the rewritten letter to the editor and the anonymous upload (A5 steps 6–7). Reference [21] year is now 2027.

- C3 template supplement (2026-10-30): copyright/CC BY line added and acronyms defined at first use, red for supervisor review. Supersedes the earlier 'copyright not added' note.


- A6 (2026-10-30): clean copies without red text written to a6_clean/ on the author's instruction; P-1 PASS. Supervisor content review still outstanding. Red sources kept.

- C2 (2026-10-30): author decided SCOPE_ASSISTMENTS_FOCUSED; reason recorded in audit/C2_XES_SCOPE_DECISION.md; supervisor confirmation pending. No experiment needed.

- Review fixes (2026-10-30): abstract bias-reference clause, plan citation, n defined, fold 5 and L1-L7 records explained. Red sources updated, a6_clean regenerated.

- Author confirmations (2026-10-30): AI statement and Ethical Statement confirmed by the first author; see audit/AUTHOR_CONFIRMATIONS_30OCT.md. Not confirmed by all authors.

- 2026-10-30 20:37: content approval and C2 confirmation stated in chat; approver not named, supervisor sign-off not recorded.

Funding: author confirmed no funding (30 Oct 2026, 20:58); no Funding section needed per template; item closed unless the supervisor wants an explicit statement.

- 2026-10-30 21:01: the author states in chat that PGS.TS. Nguyen Van Hau reviewed the revised content and confirmed C2 (SCOPE_ASSISTMENTS_FOCUSED). Recorded as author-reported; no written message, email or signed note from the supervisor is on file, and no date/time of the supervisor's reply was given. Gate unchanged: not READY_FOR_SUBMISSION_PACKAGE; CONFIRMED BY ALL AUTHORS stays NO. To close fully, save the supervisor's reply (email/Zalo screenshot/PDF) in audit/ and cite its file name here.

- 2026-10-30 21:11: institutional ethics reply text received (audit/ETHICS_REPLY_DEPT_STER_30OCT.txt); consistent with Ethical Statement; original dated/signed file still to be saved.

- 2026-10-30 21:49: the first author (NCS Nguyen Khanh Trinh) states in chat that all authors agree with the manuscript. Recorded as reported by the first author. No individual written confirmation from authors 2-5 is on file, and the chat does not say which version (the three a6_clean copies at 21:3x) they saw. Flag stays 'CONFIRMED BY ALL AUTHORS: NO (reported verbally by the first author; not documented)'. To close it, keep one message or signature per author in audit/ and cite the file names here. Gate unchanged; not marked READY; nothing committed or pushed.

