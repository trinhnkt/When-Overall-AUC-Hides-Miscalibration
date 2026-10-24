# IJIET OJS upload (protocol manuscript)

**Journal:** International Journal of Information and Education Technology (www.ijiet.org)  
**Title:** When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components  
**Date packed:** 24 October 2026  
**Length:** named **12 pages**, blind **12 pages**. IJIET: no word limit; every table stays in the single Word file (main Tables 1–6 + Appendix A1–A4). Title 20 pt.

This is a protocol/diagnostic paper. TSCDA is **not** named. GKT/CL4KT are **not** scored.  
**T-KT** is a local Transformer reference, not published SimpleKT.

Submission rules (www.ijiet.org): one editable `.doc`/`.pdf` with every figure and
table embedded; abstract 150–250 words (currently 240); at most 7 keywords (currently 6);
double-blind review; AI use disclosed (Cursor 3.18.9 with Grok 4.6 and Grok 4.7).
APC is **800 USD after** acceptance. Authors keep copyright (CC BY 4.0).
Do not submit through `ijiet.com` — that is a different journal.

The paper is stored once. Word is in `manuscript-pack/manuscript/`.
PDFs are in `manuscript-pack/output/`. This folder keeps the cover letter,
the reviewer zip, and these notes. It does not keep a second copy of the paper.

## Upload these files

| OJS slot | File | Who sees it |
|----------|------|-------------|
| Manuscript (editor) | `manuscript-pack/manuscript/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.doc` (or `.docx`) | Editorial office |
| Manuscript PDF (editor) | `manuscript-pack/output/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.pdf` | Editorial office |
| Review file (double-blind) | `manuscript-pack/output/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components_blind.pdf` | Reviewers |
| Optional Word for review | `manuscript-pack/manuscript/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components_blind.doc` | Reviewers if OJS asks for Word |
| Code for review | `code_for_review_anonymous.zip` (this folder) | Reviewers |
| Cover letter | `cover_letter_ijiet.txt` (this folder) | Editor only |

Do **not** send reviewers the named PDF/Word.  
Do **not** upload `supplementary.pdf` — every table remains in the single Word manuscript; IJIET has no word limit.

C8 (signatures, ≥3 days) and A2 backup venues are for the supervisor, not OJS.

## Checks already done

- Table 5 locks stay: T-KT ECE 0.1136 / 0.2280; FAR 0.196 / 0.268; DKT ECE 0.0602 / 0.2333
- Validation-AUC checks are in the text, not in new tables. Summaries are in the review zip at `results/validation_checkpoint/`
- XES3G5M model-based results stay withheld (check L8)
- Blind PDF has no author names or github.com/trinhnkt
- Zip excludes identity-bearing draft sources and named Word
- Reference [19] cites the Junyi Kaggle dump as Chen/Hsieh/Tsai, 2020
- GitHub repo is **private** during review; do not send reviewers a clone URL

Editor-only code URL (not for reviewers): https://github.com/trinhnkt/Sparse-Concept-and-Calibration
