# C2 — XES3G5M scope decision (OPTIONAL)

Status: DECIDED on 2026-10-30, SCOPE_ASSISTMENTS_FOCUSED (see Decision at the end). No experiment run, as instructed ("DO NOT START automatically").

| Option | Meaning | Work |
| --- | --- | --- |
| SCOPE_ASSISTMENTS_FOCUSED | XES3G5M stays descriptive only | None. The manuscript already matches this option. |
| SCOPE_MULTI_DATASET | rebuild XES3G5M from question-level events | New preprocessing, UT-B1–UT-B8, L8 must PASS, then retrain and score DKT and T-KT masked under the primary protocol. No legacy XES results may be used. |

## How the current manuscript reads (SCOPE_ASSISTMENTS_FOCUSED)

- Table 4: XES3G5M "Not evaluated".
- Table 6: XES3G5M protocol/evidence status "descriptive only"; L8 failed; no eligible model contrast.
- Table 7: train-derived and test-derived counts are reported, and the mean sparse N is "Not evaluated (descriptive only)".
- Section I and IV.C: XES3G5M contributes distribution and estimability, not model scores.
- Abstract (B1): ASSISTments 2012 is the only primary dataset.

If SCOPE_MULTI_DATASET is chosen, the retraining rule ("Do not retrain unless A1 fails or the supervisor requires it") needs the supervisor's written requirement first.

## Decision

**SCOPE_ASSISTMENTS_FOCUSED** — chosen by the author (NCS Nguyễn Khánh Trình) on 2026-10-30. Supervisor confirmation (PGS.TS. Nguyễn Văn Hậu): not yet recorded; the supervisor's review PDF leans to this option once level A is done and asks for the reason to be on record.

Reason on record:
1. XES3G5M cannot yet carry the primary protocol. Gate B (25/10/2026) found 301 repeated attempts at window boundaries (windows not non-overlapping), question 6232 absent from both sequence files, and no separate validation set for the validation-AUC checkpoint rule.
2. A rebuild is a large new experiment (event-level preprocessing, UT-B1–UT-B8, a new split, DKT and T-KT masked retrained five times each on about 5.5 million events), and retraining needs the supervisor's written requirement.
3. The manuscript already matches this scope: Table 4 "Not evaluated", Tables 6–7 "descriptive only", L8 failed, Section I, IV.C and the abstract use XES3G5M for distribution and estimability only. The only other mention is the ethics statement ("three publicly released datasets"), which is a factual description of the data used.
4. No legacy XES AUC or ECE is used anywhere.

Consequence: C2 needs no experiment for this submission. XES3G5M without leakage is a revision-round item if a reviewer asks; the limitation is stated in Section V.D, and the cover letter should say XES3G5M was audited and excluded because of L8.

Status: DECIDED (author), supervisor confirmation pending. No files other than this note were changed.

## Confirmation message 2026-10-30 20:37
A message in the working chat states: 'Duyệt nội dung bản đã sửa, Xác nhận quyết định C2' (approve the content of the revised version; confirm the C2 decision). The message does not name who approves. Recorded as the user's statement; it is not recorded as the supervisor's written approval. SCOPE_ASSISTMENTS_FOCUSED stands. Attach the supervisor's own message or signed note here if the supervisor is the approver.


- 2026-10-30 21:01: the author states in chat that PGS.TS. Nguyen Van Hau reviewed the revised content and confirmed C2 (SCOPE_ASSISTMENTS_FOCUSED). Recorded as author-reported; no written message, email or signed note from the supervisor is on file, and no date/time of the supervisor's reply was given. Gate unchanged: not READY_FOR_SUBMISSION_PACKAGE; CONFIRMED BY ALL AUTHORS stays NO. To close fully, save the supervisor's reply (email/Zalo screenshot/PDF) in audit/ and cite its file name here.
