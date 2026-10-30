# A6 — Red formatting cleanup and final blind QA

Status: BLOCKED. The task says "Do this ONLY after all A/B changes have been reviewed." The A/B changes of 28–29 Oct are still red and have not been reviewed by the supervisor, so no red text was converted and no clean copy was made.

## Prepared

`scripts/a6_final_blind_qa.py`

- `check [path …]`, read-only P-1 checker: red runs = 0 (FF0000 or C00000 in document, headers, footers, footnotes, endnotes; text boxes are inside document.xml and are counted), tracked changes (w:ins, w:del, w:moveFrom, w:moveTo) = 0, no comments part, core.xml Author blank, Last Modified By blank, P0-BV200 ≤ 1.
- `clean SRC DEST --approved` writes a NEW file only. It refuses if DEST exists or equals SRC, sets red to `w:color w:val="auto"` (Font Color Automatic, not fixed black, theme attributes removed), blanks Author and Last Modified By, then runs `check` on DEST. It refuses to run without `--approved`.

Update 2026-10-30: the supervisor's PDF (`Check list/NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf`) was found. Its P-1 script is saved verbatim as `scripts/check_blind.py` and gives: red runs FAIL (557 runs, 4,560 words in the manuscript-pack blind; 32 runs, 3,608 words in the submission blind), tracked changes 0, comments.xml False, Author and Last Modified By blank, P0-BV200 once. `a6_final_blind_qa.py` stays as a stricter extra check (it also counts empty runs and C00000), and its `clean` step still runs only with `--approved`. After the new copy is made, run `python -I check_blind.py <new blind>.docx`; all five lines must PASS. The PDF says to open Fig. 3 separately and to paste the script output unedited as evidence.

## Current state (read-only check, 2026-10-29, after B1/B2/C3)

| File | Red runs | Tracked | Comments | Author | Last Modified By | P0-BV200 |
| --- | --- | --- | --- | --- | --- | --- |
| manuscript-pack/manuscript/…Components.docx (named) | 2,582 (FAIL) | 0 | none | blank | blank | 1 |
| manuscript-pack/manuscript/…_blind.docx | 2,582 (FAIL) | 0 | none | blank | blank | 1 |
| artifact_final/07_submission/…_blind.docx | 30 (FAIL) | 0 | none | blank | blank | 1 |

The two manuscript-pack copies carry red from the earlier review rounds as well as from this revision; the submission blind carries only red marks on runs edited in this revision. Counts are run properties, not changed words.

## To finish A6 after approval

1. Supervisor approves the red text (or lists edits).
2. `py -3 scripts/a6_final_blind_qa.py clean "<07_submission blind.docx>" "<new folder>/…_blind_A6.docx" --approved`; expected: all six checks PASS.
3. Open the new copy in Word: check Fig. 3 (title "ASSISTments 2012, primary protocol, fold 0"), tables, captions, headers, footers, and shapes.
4. Export the PDF from Word and inspect it page by page; record the result here.

The 28/10 source files are not overwritten by this procedure.

## 2026-10-30 A6 executed on the author's explicit instruction ("xoa bo chu do")
- New copies only; the red sources were not touched: 6_clean/manuscript-pack_manuscript_A6_clean.docx, 6_clean/manuscript-pack_manuscript_blind_A6_clean.docx, 6_clean/07_submission_blind_A6_clean.docx.
- Method: 6_final_blind_qa.py clean SRC DEST --approved. Every FF0000 run became w:color auto (Automatic, not fixed Black); Author and Last Modified By blank.
- Verification (scripts/a6_verify_clean.py): text identical to the red sources, same zip parts, P-1 check_blind.py PASS on all five lines (0 red runs), one P0-BV200, Word opens each file (12 pages, copyright hyperlink kept) and exports to PDF.
- Caveat: the supervisor's review of the 28OCT content has not happened yet. If the supervisor wants to see the changes, send the red copies; the clean copies are for submission. Figure 3 is an image: its red lines are plot series, not text, and its title reads "primary protocol".
- Not done: .doc/PDF deliverables from the clean copies, letter to the editor, anonymous zip/upload.
