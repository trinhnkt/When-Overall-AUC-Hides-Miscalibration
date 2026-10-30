# C3 — Reference and template QA (OPTIONAL)

Status: PASS for Reference [21]. BLOCKED (decision needed) for the copyright/CC BY line.

Scripts: `scripts/c3_springer_meta.py` (DOI metadata), `scripts/c3_template_scan.py` (template text), `scripts/c3_reference21.py` (edit, applied to the three copies; red for review).

## Reference [21]

Sources checked on 2026-10-29:

- Springer chapter page https://link.springer.com/chapter/10.1007/978-3-032-37673-2_33 (fetched as text): authors Xiaoran Yan, Cheng Tang, Atsushi Shimada; "Part of the book series: Lecture Notes in Computer Science ((LNAI, volume 16946))"; conference series "Joint European Conference on Machine Learning and Knowledge Discovery in Databases"; first online 05 September 2026. The "Cite this paper" block itself was not returned (the page is cut at that heading, and the HTML request from a script gets a bot page).
- DOI content negotiation (doi.org, IEEE style and BibTeX) and Crossref: title "Recovering Stranded Discrimination in Knowledge Tracing: Per-Item Bias Correction via Empirical-Bayes Shrinkage"; booktitle "Machine Learning and Knowledge Discovery in Databases. Research Track"; publisher Springer Nature Switzerland; pages 586–602; year 2026 (Sep.); DOI 10.1007/978-3-032-37673-2_33. Crossref also lists a print date of 2027 for the volume.

| Field | Before | After | Source |
| --- | --- | --- | --- |
| Authors | X. Yan, C. Tang, and A. Shimada | unchanged | Springer page, DOI |
| Title | unchanged (title case, as the template asks) | unchanged | DOI |
| Book title | "Proc. Eur. Conf. Mach. Learn. Princ. Pract. Knowl. Discov. Databases (ECML PKDD)" | "Machine Learning and Knowledge Discovery in Databases. Research Track (ECML PKDD)" | DOI booktitle |
| Series, volume | absent | Lecture Notes in Computer Science, vol. 16946 | Springer page |
| Publisher | absent | Springer | DOI publisher |
| Year | 2026 | 2026 | DOI (online Sep. 2026) |
| Pages | 586–602 | unchanged | DOI |
| DOI | 10.1007/978-3-032-37673-2_33 | unchanged | DOI |

New text: X. Yan, C. Tang, and A. Shimada, “Recovering Stranded Discrimination in Knowledge Tracing: Per-Item Bias Correction via Empirical-Bayes Shrinkage,” in Machine Learning and Knowledge Discovery in Databases. Research Track (ECML PKDD), Lecture Notes in Computer Science, vol. 16946. Springer, 2026, pp. 586–602. doi: 10.1007/978-3-032-37673-2_33

Update 2026-10-30: the supervisor's review (`Check list/NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf`, C3) reports that Springer's page gives the citation year 2027 (First Online 05/09/2026), and Crossref's print date is 2027. The year in [21] is therefore now 2027 (`scripts/c3_reference21_year.py`). The review also says to copy a copyright line from the template only if the template has one; the template has it, and the standing instruction not to put the copyright line back still blocks it, so it stays a decision for the supervisor.

The layout follows Reference [14] (Bhattacharjee and Wayllace), the other Springer LNCS entry in the list. If the supervisor reads the Springer "Cite this paper" box in a browser and it gives 2027, change only the year.

## Template comparison (`07_submission/IJIET_template.doc`)

| Template item | Template text | Manuscript | Action |
| --- | --- | --- | --- |
| Copyright / licence line | "Copyright © 2026 by the authors. This is an open access article distributed under the Creative Commons Attribution License which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited (CC BY 4.0)." | absent | Not added. The template has it, but the standing instruction for this revision is "Do not put the copyright line back". Decision needed from the supervisor or author. |
| Received/revised/accepted line | example dates in the template | "Manuscript received Month date, 2026; revised Month date, 2026; accepted Month date, 2026" | Unchanged. No dates invented. |
| DOI, volume, issue of this paper | not given in the template | none | None invented. |
| Abstract | 150–250 words; "no abbreviations" | 197 words; acronyms defined at first use (required by B1) | No change. The template's no-abbreviation advice conflicts with the B1 rule; flagged only. |
| References | list all authors, "et al." if more than three; title words capitalized | the list uses "et al." after three names and title case | No change. |

## Template supplement, 2026-10-30 (`scripts/c3_template_fixes.py`)

This section supersedes the "Not added" row above. The author asked to check the manuscript against the template and supplement it, and the supervisor's C3 item says to copy the copyright line when the template has one. Every change below is red for review, applied to all three manuscript copies, and reversible by deleting the paragraph or restoring the old wording.

1. Copyright line. A new paragraph in the template's `FigureCaption` style after the last reference, with the template's wording: "Copyright © 2026 by the authors. This is an open access article distributed under the Creative Commons Attribution License which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited (CC BY 4.0)." In the template "CC BY 4.0" is a hyperlink to https://creativecommons.org/licenses/by/4.0/; the same hyperlink was added to all three copies by `scripts/c3_copyright_link.py` (verified by opening them in Word). No author names, dates, DOI, volume or issue were added.
2. Acronyms defined at first use in the body, as the template requires (it asks for this even after the abstract):

| Acronym | Where | Now reads |
| --- | --- | --- |
| ECE | RQ1 | expected calibration error (ECE) |
| DKT | RQ3 | deep knowledge tracing (DKT) |
| T-KT masked | contributions paragraph | the causally masked Transformer (T-KT masked) |
| LSTM | III.D | a long short-term memory (LSTM) network |
| UKT | II | Uncertainty-Aware Knowledge Tracing (UKT), the title of the cited work |
| SD | IV.A | standard deviation (SD) |
| CI | Table 5 caption | 95% confidence interval (CI) |
| UT-A1 to UT-A7 | Data and Code Availability | unit tests UT-A1 through UT-A7 |
| UNC, RES, REL | Brier decomposition | uncertainty UNC, resolution RES, reliability REL |

3. No number, table value or figure changed. Checks after the edit: `b1_abstract.py --check` PASS (197 words), `b2_notation.py --check` PASS, `table6_context.py --check` all values match, `fmt_check.py` reports only the known loss in "Two secondary analyses…", `check_blind.py` shows no tracked changes, no comments, empty Author and Last Modified By, one `P0-BV200`. The red-run count rises from the added text; A6 still turns red into Automatic after review.
4. Still open: the abstract keeps its defined acronyms (the template advises none, B1 requires definitions); Funding and Acknowledgment text as already in the manuscript; page layout and the .doc/PDF copies were not regenerated.
