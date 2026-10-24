# Manuscript sources

Living manuscript (named and anonymized Word/PDF, 12 pages, 24 October 2026).
IJIET/OJS does not name the author project folder; this directory is venue-neutral. Upload files keep the paper title. Word lives in `manuscript/`. PDFs live in `output/`. `output/OJS_UPLOAD/` holds the cover letter and the reviewer zip, not a second copy of the paper.

Extra tables are **Appendix A1–A4** in the main file. Do not upload `supplementary.pdf`.

| Path | Role |
|------|------|
| `manuscript/` | Named and anonymized Word |
| `output/` | Named and anonymized PDF |
| `../P0_IJIET_FINAL_SUBMISSION/` | Submission copies of the same Word and PDF files |
| `output/OJS_UPLOAD/` | Cover letter and reviewer zip |
| `analysis/` | Locked numeric artifacts |
| `audit/SCIENTIFIC_LOCKS.md` | Frozen ECE/FAR/XES cells |
| `docs/how_to_reproduce.md` | LEVEL A vs Track A |
| `figures/` | Fig. 1–3 |
| `tables/` | Numeric table copies |
| `a2b/` | Masked XES3G5M series (source of truth for XES ECE) |

**T-KT** is a local Transformer reference, not published SimpleKT.

Target: named and anonymized files use the paper title (`manuscript_paths.py`).

Office notes: `output/OJS_UPLOAD/README_SUBMIT.md`.
The named file and cover letter are for the editorial office only. Reviewers receive the anonymized PDF and the review zip.
