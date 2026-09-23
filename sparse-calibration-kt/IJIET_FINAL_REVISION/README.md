# Manuscript sources

Living manuscript (named and anonymized Word/PDF, 13 pages, 21 September 2026).
Edit Word in `manuscript/`, then pack `output/OJS_UPLOAD/` for the editorial office.

Extra tables are **Appendix A1–A6** in the main file. Do not upload `supplementary.pdf`.

| Path | Role |
|------|------|
| `manuscript/` | Named and anonymized Word |
| `output/OJS_UPLOAD/` | Files for the journal OJS upload |
| `analysis/` | Locked numeric artifacts |
| `audit/SCIENTIFIC_LOCKS.md` | Frozen ECE/FAR/XES cells |
| `docs/how_to_reproduce.md` | LEVEL A vs Track A |
| `figures/` | Fig. 1–3 |
| `tables/` | Numeric table copies |
| `a2b/` | Masked XES3G5M series (source of truth for XES ECE) |

**T-KT** is a local Transformer reference, not published SimpleKT.

Target: named and anonymized files use the paper title (`manuscript_paths.py`).

Office files: `output/OJS_UPLOAD/` (see `README_SUBMIT.md` there).
The named file and cover letter are for the editorial office only. Reviewers receive the anonymized PDF and the review zip.
