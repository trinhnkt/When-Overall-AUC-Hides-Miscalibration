# FINAL SUPERVISOR GATE 28OCT

Date: 2026-10-29. All audits in `audit/` were read for this gate, and every checker below was re-run on the final state of the three manuscript copies (named, living blind, submission blind).

## Final status: READY_FOR_SUPERVISOR_REVIEW

Not READY_FOR_SUBMISSION_PACKAGE: A6 is BLOCKED, because red cleanup must wait for the supervisor's review of the A/B changes. Also not done: PDF and .doc regeneration, and author sign-off (CONFIRMED BY ALL AUTHORS: YES (set on 2026-10-30 21:50 at the first author's instruction; basis = the first author's statement that all authors agree; individual written confirmations of authors 2-5 are not on file)).

## A items

| Item | Evidence | Status | Remaining action |
| --- | --- | --- | --- |
| A1 DKT token-0 | `audit/A1_DKT_TOKEN0_REPORT.md`; T0-a–T0-d and UT-A4 passed at commit 4ff6683 | PASS | None |
| A2 Matched gap method | `audit/A2_MATCHED_GAP_METHOD_TRACE.md`; III.E equations (8)–(9); artifact `rebuild/published_gap.py` | PASS | None |
| A3 Legacy purge | `audit/A3_LEGACY_RESULT_PURGE.md`; FAR and Brier recomputed from primary exports | PASS | None |
| A4 Tables 6 and 7 | `audit/A4_TABLE6_TABLE7_REPORT.md`; `scripts/table6_context.py --check` → "All values match" (re-run for this gate) | PASS | Supervisor to note the three recomputed ASSISTments descriptors (ρ −0.241, −0.326; median item support 32) |
| A5 Artifact v4 | `audit/A5_ARTIFACT_V4_REPORT.md`; clean copy 302/302 checks, exit 0; README has P0-BV200-15EW once; MANIFEST 219 files | PASS | None |
| A6 Red cleanup and blind QA | `audit/A6_FINAL_BLIND_QA.md`; checker re-run: red runs 2,584 / 2,584 / 33; tracked 0; comments none; Author and Last Modified By blank; P0-BV200 = 1 | BLOCKED | Supervisor reviews the red text; then run `a6_final_blind_qa.py clean … --approved` to make a NEW copy, open Fig. 3, export the PDF, and inspect it |

## B items

| Item | Evidence | Status | Remaining action |
| --- | --- | --- | --- |
| B1 Abstract | `audit/B1_ABSTRACT_REPORT.md`; `b1_abstract.py --check` PASS on three copies (197 words, five acronyms defined, every number in Table 5 / Table A2) | PASS | Supervisor wording review |
| B2 Notation | `audit/B2_NOTATION_REPORT.md`; `b2_notation.py --check` PASS (ID ≤ 1, no P-labels, no .0000 counts, no fractional counts); Fig. 3 title redrawn | PASS | None |
| B3 RQ3 | `audit/B3_RQ3_TRACE.md`; `results/B3_TABLE_A2_EFFECTS.csv` (range assertions pass: 0.0181–0.0774; −0.0131 to +0.0068; 0.0268) | PASS | None |
| B4 Table 2 | `audit/B4_TABLE2_CONFIG_TRACE.md` | PASS | None |
| B5 Stratified metrics | `audit/B5_METRIC_TRACE.md`; `results/B5_STRATIFIED_METRICS.csv`; Table A1 (16 rows) recomputed in the clean-copy run | PASS | None |
| B6 Model claims | `audit/B6_MODEL_CLAIM_AUDIT.md`; Abstract follows (B1) | PASS | None |
| B7 Text cleanup | `audit/B7_TEXT_CLEANUP.md`; XES evidence files now in `artifact_v4/audits/` | PASS | None |
| B8 Partition gaps | Table A5; `results/C1_PARTITION_INTERVALS.csv`; partition G values and Table 5 mean ± SD recomputed in the clean-copy run (DKT 0.0400 ± 0.0107; T-KT masked 0.0581 ± 0.0230) | PASS | None |

## C items (optional)

| Item | Evidence | Status | Remaining action |
| --- | --- | --- | --- |
| C1 Partition intervals | `audit/C1_PARTITION_INTERVALS.md`; Table A5; `artifact_v4/rebuild/partition_intervals.py` | PASS | None |
| C2 XES3G5M scope | `audit/C2_XES_SCOPE_DECISION.md`; manuscript is consistent with SCOPE_ASSISTMENTS_FOCUSED | BLOCKED | Supervisor/author chooses SCOPE_ASSISTMENTS_FOCUSED or SCOPE_MULTI_DATASET |
| C3 Reference/template | `audit/C3_FORMAT_REFERENCE_REPORT.md`; Reference [21] corrected from DOI metadata | PASS (copyright line BLOCKED) | Decide whether to add the template's CC BY 4.0 line (it is in the template; the standing instruction says not to add it); optionally confirm the year in Springer's "Cite this paper" box |

## Cross-checks re-run for this gate

| Check | Result |
| --- | --- |
| `fmt_check.py` (italic, bold, sub/superscript vs HEAD) | only the known A3 paragraph "Two secondary analyses…" |
| `gate_claim_evidence.py` → `docs/CLAIM_EVIDENCE_P4.csv` | 29 claims (Abstract 8, Section I 9, V.A 6, Conclusion 6), all found verbatim in the three copies |
| Protocol naming | "primary protocol" 19 times per copy; "locked protocol", "window-200 protocol", "under this protocol" 0 times |

## Supervisor PDF (found 2026-10-30)

`audit/SUPERVISOR_PDF_CROSSCHECK.md` compares this work with the review. No gate status changed. Two edits followed: Reference [21] year 2027; `recompute_level` column in `docs/CLAIM_EVIDENCE_P4.csv`. The PDF's P-1 checker (`scripts/check_blind.py`) reports red runs as the only FAIL line (A6).

## Not done

- The rewritten letter to the editor and the anonymous upload/zip (PDF A5 steps 6–7).
- Questions 6–10 of the PDF's section 6 (Reference [26] authors, OJS file type, ethics document, AI-tool versions) are not answerable from the files.

- PDF and .doc copies were not regenerated.
- No commit or push.
- No retraining.
- Author confirmations remain NO.

- Update 2026-10-30: C3 template supplement applied (copyright line, acronym definitions); all checks re-run and pass; gate status unchanged (READY_FOR_SUPERVISOR_REVIEW).


- Update 2026-10-30: A6 clean copies created; P-1 PASS. Gate still READY_FOR_SUPERVISOR_REVIEW (C2 scope decision, letter, upload pending).

- Update 2026-10-30: C2 decided (SCOPE_ASSISTMENTS_FOCUSED, author; supervisor confirmation pending). Remaining: letter to editor, anonymous zip/upload, .doc/PDF export, questions 6-10.

- Update 2026-10-30 20:37: a message states the revised content is approved and C2 confirmed (approver not named). Gate not changed to READY_FOR_SUBMISSION_PACKAGE: the supervisor's own written approval, the letter, the anonymous zip/upload, and the Funding/ethics-document answers are still open.

- 2026-10-30 21:01: the author states in chat that PGS.TS. Nguyen Van Hau reviewed the revised content and confirmed C2 (SCOPE_ASSISTMENTS_FOCUSED). Recorded as author-reported; no written message, email or signed note from the supervisor is on file, and no date/time of the supervisor's reply was given. Gate unchanged: not READY_FOR_SUBMISSION_PACKAGE; CONFIRMED BY ALL AUTHORS stays NO. To close fully, save the supervisor's reply (email/Zalo screenshot/PDF) in audit/ and cite its file name here.

- 2026-10-30 21:49: the first author (NCS Nguyen Khanh Trinh) states in chat that all authors agree with the manuscript. Recorded as reported by the first author. No individual written confirmation from authors 2-5 is on file, and the chat does not say which version (the three a6_clean copies at 21:3x) they saw. Flag stays 'CONFIRMED BY ALL AUTHORS: NO (reported verbally by the first author; not documented)'. To close it, keep one message or signature per author in audit/ and cite the file names here. Gate unchanged; not marked READY; nothing committed or pushed.

