# Author confirmations recorded 2026-10-30

Source: messages from the first author (NCS Nguyễn Khánh Trình) in the working chat, 2026-10-30 20:12 (UTC+7). They answer questions 10 and 8 of the supervisor's review (`Check list/NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf`, section 6). The supervisor and the other authors have not confirmed anything through this record.

| PDF question | Author's message | Recorded as | Manuscript |
| --- | --- | --- | --- |
| 10. AI tools and versions in the Generative AI Statement | "xác nhận dùng AI" | The first author confirms that the tools and versions named in the statement (Cursor 3.18.9 with Grok 4.6 and Grok 4.7; ChatGPT, GPT-5.6; Claude, Claude Opus 5.5) are the ones the team used. | Statement unchanged. |
| 8. Ethical Statement | "Xác nhận đạo đức" | The first author confirms the Ethical Statement as written: secondary analysis of three de-identified public datasets, no new participants or consent, no protocol number, no exemption from data-protection law claimed. | Statement unchanged. |

## Still open
- Question 8 also asks which institutional document is the basis for "Under the research policy of the authors' institution … does not require prospective human-subjects review". The confirmation does not name it; keep the document ready in case the editor asks.
- "CONFIRMED BY ALL AUTHORS" stays NO. Only the first author's confirmation is recorded here.
- The AI statement says "No AI tool was used to generate or alter experimental results". In the 28OCT revision an AI assistant in Cursor wrote and ran analysis scripts that produced the new tables (B5 Brier/AUC by group, C1 intervals, Table A5, the artifact recomputation). The models were trained and scored by the authors' pipeline; the assistant did not change a training run or a prediction file. The authors should decide whether the sentence should say "No AI tool trained a model or changed a prediction; AI-assisted scripts recomputed the tables, and the authors checked the outputs against the prediction files." Also check that the tool list covers the assistant used during the revision (Cursor, and the model it ran on). Not changed.

## Addendum 2026-10-30 20:28
The first author restated the tool list verbatim: 'Cursor 3.18.9 (Grok 4.6 và 4.7), ChatGPT GPT-5.6, Claude Opus 5.5'. This matches the Generative AI Statement as written; no change made. Note for the authors: the assistant that ran the 28-30 OCT revision in Cursor identifies itself as Claude Sonnet 5.5, which is not in this list. If the team used it for the revision, add it (and its use for scripts and text edits) to the statement; if not, the list stands.

## Addendum 2026-10-30 20:36
The first author confirmed that Claude Sonnet 5.5 was also used. The Generative AI Statement now names Claude Sonnet 5.5 (inside Cursor) with its role in the final revision, and 'No AI tool was used to generate or alter experimental results' became 'No AI tool trained a model or changed a prediction file.' (scripts/c5_ai_statement.py; red in the source copies; a6_clean regenerated). Funding: no statement in the manuscript; the template allows removing the section if there is none; the authors still need to confirm there is no funding.

## Addendum 2026-10-30 20:37
Message: 'Duyệt nội dung bản đã sửa, Xác nhận quyết định C2'. Approver not named; recorded as a statement in the chat, not as the supervisor's sign-off, and not as 'CONFIRMED BY ALL AUTHORS' (still NO). The a6_clean copies reviewed are those regenerated at 20:36 (AI statement with Claude Sonnet 5.5; P-1 PASS).

## Funding (30 Oct 2026, 20:58)
Author statement in chat: the study had no funding (not signed by the other authors). IJIET template: 'If there is no funding, this section can be removed.' The manuscript has no Funding section, so no text change was made. Optional: add 'This research received no external funding.' before Acknowledgment (would require editing the three red sources and regenerating a6_clean).

- 2026-10-30 21:01: the author states in chat that PGS.TS. Nguyen Van Hau reviewed the revised content and confirmed C2 (SCOPE_ASSISTMENTS_FOCUSED). Recorded as author-reported; no written message, email or signed note from the supervisor is on file, and no date/time of the supervisor's reply was given. Gate unchanged: not READY_FOR_SUBMISSION_PACKAGE; CONFIRMED BY ALL AUTHORS stays NO. To close fully, save the supervisor's reply (email/Zalo screenshot/PDF) in audit/ and cite its file name here.

## Ethics reply from the institution (30 Oct 2026, 21:11)
Text of the reply from the Department of Science, Technology and External Relations (Hung Yen University of Technology and Engineering) saved verbatim in audit/ETHICS_REPLY_DEPT_STER_30OCT.txt. It confirms: secondary analysis of de-identified public data; no new participants or personal data; Junyi under CC BY-NC-SA 4.0; no EdTech sponsor; no prospective ethics review and no protocol number under institutional policy; GDPR/FERPA compliance basis = handling limited to released, de-identified records. The manuscript's Ethical Statement (P152) says the same on every point; no text change needed. Differences kept on purpose: the blind copy says 'the authors' institution' (not named); XES3G5M MIT license is also stated in the paper (the reply does not mention it, which is harmless). Open: the pasted text has no date, letter number or signature. Keep the original email/PDF in audit/ and cite its file name. The earlier request letter (P0_IJIET_FINAL_SUBMISSION/audit/THU_PHONG_QLKH_ETHICS.txt) names 'Phòng Quản lý khoa học'; the reply comes from the Department of Science, Technology and External Relations - confirm it is the same office.

- 2026-10-30 21:49: the first author (NCS Nguyen Khanh Trinh) states in chat that all authors agree with the manuscript. Recorded as reported by the first author. No individual written confirmation from authors 2-5 is on file, and the chat does not say which version (the three a6_clean copies at 21:3x) they saw. Flag stays 'CONFIRMED BY ALL AUTHORS: NO (reported verbally by the first author; not documented)'. To close it, keep one message or signature per author in audit/ and cite the file names here. Gate unchanged; not marked READY; nothing committed or pushed.

- 2026-10-30 21:50: CONFIRMED BY ALL AUTHORS: YES (set on 2026-10-30 21:50 at the first author's instruction; basis = the first author's statement that all authors agree; individual written confirmations of authors 2-5 are not on file). Earlier lines in this file that say the flag 'stays NO' describe the state before this instruction. Not marked READY; nothing committed or pushed; supervisor's written approval and the original ethics email are still not on file.

- 2026-10-30 22:23: the first author confirms the cover-letter statement 'The manuscript has not been published and is not under consideration elsewhere' (submission/cover_letter_ijiet_30OCT.txt). Letter unchanged.
