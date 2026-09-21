# Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing

Khanh-Trinh Nguyen, Tuan Dao Minh, Duong Nguyen Tien, Chi Thanh Nguyen, and Van-Hau Nguyen  
*International Journal of Information and Education Technology* (IJIET) · **DOI pending**

A protocol paper for Knowledge Tracing on sparse concepts: train-only KC strata, occupancy-aware reporting, ECE/Brier, reliability diagrams, L1–L7 leakage control, and a frozen one-command table rebuild. It is not a new KT architecture and not a classroom trial.

**T-KT** is a local Transformer reference, not published SimpleKT.

## Paper

Named and blind PDFs are **13 pages** each (21 September 2026; IJIET has no page cap; template is binding) in [`sparse-calibration-kt/IJIET_FINAL_REVISION/output/OJS_UPLOAD/`](sparse-calibration-kt/IJIET_FINAL_REVISION/output/OJS_UPLOAD/). Extra tables are **Appendix A1–A6** in the main Word/PDF.

| Artefact | Path |
|----------|------|
| Named PDF | [Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing.pdf](sparse-calibration-kt/IJIET_FINAL_REVISION/output/OJS_UPLOAD/Reproducible%20Sparse-Concept%20and%20Calibration%20Diagnostics%20for%20Knowledge%20Tracing.pdf) |
| Blind PDF | […_blind.pdf](sparse-calibration-kt/IJIET_FINAL_REVISION/output/OJS_UPLOAD/Reproducible%20Sparse-Concept%20and%20Calibration%20Diagnostics%20for%20Knowledge%20Tracing_blind.pdf) |
| Appendix | Tables A1–A6 inside the main PDF (do not upload `supplementary.pdf`) |
| Locked numbers | [`IJIET_FINAL_REVISION/audit/SCIENTIFIC_LOCKS.md`](sparse-calibration-kt/IJIET_FINAL_REVISION/audit/SCIENTIFIC_LOCKS.md) |

## Datasets

Raw logs are **not** shipped. Obtain them from the original providers and place dumps under `sparse-calibration-kt/data/` (see [`data/README.md`](sparse-calibration-kt/data/README.md)):

1. [ASSISTments 2012](https://sites.google.com/site/assistmentsdata/) — 2012–2013 release with affect
2. [Junyi Academy Online Learning Activity Dataset](https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy) on Kaggle — **not** Junyi2015 / PSLC DataShop; the operational KC is `ucid`
3. [XES3G5M](https://github.com/pykt-team/pykt-toolkit)

## Reproduce

**LEVEL A** (review-facing): rebuild locked tables from frozen CSVs. No retrain. Does not change ASSISTments T-KT ECE `0.1136` / `0.2280` or FAR `0.196` / `0.268`.

```bash
cd sparse-calibration-kt
pip install -r requirements.txt
bash scripts/rebuild_locked_tables.sh      # Windows: scripts/rebuild_locked_tables.ps1
```

**Track A** retrains local IRT / DKT / T-KT and does **not** recreate those locked cells. See [`how_to_reproduce.md`](sparse-calibration-kt/IJIET_FINAL_REVISION/docs/how_to_reproduce.md).

## Repository layout

| Path | Role |
|------|------|
| `sparse-calibration-kt/src/` | Preprocess, models, metrics, leakage audit |
| `sparse-calibration-kt/scripts/` | LEVEL A rebuild, Track A runners |
| `sparse-calibration-kt/configs/` | Dataset / model YAML |
| `sparse-calibration-kt/results/tables/` | Frozen numeric tables |
| `sparse-calibration-kt/IJIET_FINAL_REVISION/` | Living manuscript, figures, Appendix sources, OJS pack |
| `sparse-calibration-kt/tests/` | Unit tests |

## Citation

```bibtex
@article{nguyen2026reproducible,
  title   = {Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing},
  author  = {Nguyen, Khanh-Trinh and Dao Minh, Tuan and Nguyen Tien, Duong
             and Nguyen, Chi Thanh and Nguyen, Van-Hau},
  journal = {International Journal of Information and Education Technology},
  year    = {2026},
  note    = {DOI pending}
}
```

Or use [`CITATION.cff`](CITATION.cff).

## License

- Code: [MIT](LICENSE)
- Manuscript text, figures, and appendix tables: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
