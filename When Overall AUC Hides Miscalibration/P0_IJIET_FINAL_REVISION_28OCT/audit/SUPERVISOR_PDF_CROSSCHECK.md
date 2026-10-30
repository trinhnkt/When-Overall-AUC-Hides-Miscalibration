# Cross-check against the supervisor review (found 2026-10-30)

Source: `Check list/NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf` (PGS.TS. Nguyễn Văn Hậu, 28/10/2026, 19 pages). It was not on disk when the 28OCT work was done, so the tasks were run from the task texts. This note compares the work with the PDF itself.

## Dependency order (PDF section 2)

The order run (A1, B4, A2, A5, A3, B5, B8, C1, A4, B3, B6, B7, B1, B2, C3, A6, C2) matches the PDF. A6 last, after content approval, matches too.

## Acceptance conditions (PDF P-3)

| Item | PDF condition | State |
| --- | --- | --- |
| A1 | T0-b, T0-c PASS on five DKT checkpoints; row count matches theory; UT-A4 PASS; III.C describes the code | PASS (A1 report) |
| A2 | III.E has eq. (9), R, B, seed, invalid replicates | PASS |
| A3 | no number from unmasked T-KT; FAR recomputed or removed | PASS; rescan below |
| A4 | caption matches rows; counts in one place with train/test source; `table6_context.py` "All values match" | PASS |
| A5 | artifact recomputes main numbers from predictions; "pre-specified" has a timestamped plan or is changed | PASS (302/302; plan in commit 46e0208, 2026-10-21 16:02:55, before the first supplementary log). **Not done: the letter to the editor (PDF A5 step 7) and the anonymous upload/zip (steps 6)** |
| A6 | last; P-1 PASS on all five lines | BLOCKED (see below) |
| B1 | ≤ 200 words, acronyms defined, numbers match Table 5 and A2 | PASS (197 words) |
| B2 | "P0-BV200" at most once; no " P1"; no fractional counts | PASS |
| B3–B8 | per PDF | PASS |

## P-1 checker (PDF appendix), transcribed as `scripts/check_blind.py`

Run with `python -I` on 2026-10-30:

| File | Red runs (non-empty, FF0000) | Tracked | comments.xml | Author | Last Modified By | P0-BV200 |
| --- | --- | --- | --- | --- | --- | --- |
| manuscript-pack blind | FAIL: 557 runs, 4,560 words | PASS 0 | PASS | PASS blank | PASS blank | 1 |
| 07_submission blind | FAIL: 32 runs, 3,608 words | PASS 0 | PASS | PASS blank | PASS blank | 1 |

The red text is the 28OCT revision, kept red for the supervisor's review as the PDF's A6 step 1 prescribes. The supervisor's own 28/10 file had 2,492 red words and 16 protocol labels.

## Review questions the PDF asks (section 6)

1. Artifact recomputes Tables 4, 5, A2, matched gaps, and fold-0 intervals from prediction exports: yes. Clean-copy run, exit 0, 302/302 checks (`A5_ARTIFACT_V4_REPORT.md`).
2. Prediction exports for DKT and T-KT masked: all five runs (folds 0–4); B5, B8, and C1 were done from them.
3. Other places using unmasked T-KT or final-epoch numbers: rescan with `scripts/q3_legacy_scan.py`. Remaining hits are scope statements ("Unmasked T-KT is not used as a finding", "Junyi T-KT was not retrained with a mask", artifact does not contain unmasked T-KT) and the final/full and final/200 cells of Table A2, which the PDF allows. Four mentions of "archived audit records" (Table 3 caption, III.F, two spots) describe the L1–L7 audit records, not numbers; the supervisor may prefer different wording.
4. Planning document with verifiable timestamp: yes, commit 46e0208 (`artifact_v4/code/docs/analysis_plan_P0_v2.md`). "pre-specified" kept only where that plan applies.
5. Scope: not decided (C2 file). The PDF leans to SCOPE_ASSISTMENTS_FOCUSED once level A is done, but asks for a recorded reason.
6. Source of the authors of Reference [26] (P. J. Chen, M. E. Hsieh, T. Y. Tsai): not checked, not changed. The PDF suggests the organization author "Junyi Academy" if Kaggle names no individuals.
7. OJS accepts .docx? Not known. The .doc/.pdf copies were not regenerated.
8. Document behind the ethics-exemption sentence: not known; text untouched.
9. "Manuscript received Month date, 2026…" and the copyright line: placeholders kept; no dates written; the template's copyright/CC BY line was added on 2026-10-30 (red, see C3 supplement).
10. AI-tool declaration (Cursor 3.18.9 with Grok 4.6 and 4.7, ChatGPT GPT-5.6, Claude Opus 5.5): not verified and not changed. Only the authors can confirm the versions.

## Changes made because of the PDF

- Reference [21] year changed from 2026 to 2027, the year in Springer's citation block as read by the supervisor and the Crossref print date (`scripts/c3_reference21_year.py`; formatting check unchanged).
- `docs/CLAIM_EVIDENCE_P4.csv` gained the column `recompute_level` (24 claims recomputed from prediction exports, 2 from the split files, 3 audit-report claims), as P-4 asks for each row.

- Update 2026-10-30 20:12: the first author confirmed the AI tools/versions (question 10) and the Ethical Statement (question 8). Recorded in audit/AUTHOR_CONFIRMATIONS_30OCT.md; the ethics document name is still not named, and the AI statement wording on 'experimental results' is flagged for the authors.
