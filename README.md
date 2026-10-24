# When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components

A protocol for knowledge tracing on rarely practiced knowledge components: train-only frequency groups, occupancy-aware reporting, expected calibration error and Brier decomposition, reliability diagrams, and eight leakage checks. Check L8 withholds model-based results on XES3G5M. This is not a new KT architecture and not a classroom trial.

**T-KT** is a local Transformer reference, not published simpleKT. simpleKT is scored on ASSISTments 2012 only.

This file is written for double-blind review. It does not name authors, a target journal, or a public code URL. Reviewers receive an anonymized code bundle with the manuscript; do not treat this README as a camera-ready citation.

## Manuscript

The living manuscript is 12 pages (24 October 2026). Main-text Tables 1–6 and Appendix Tables A1–A4 stay in the single Word file. Do not upload a separate `supplementary.pdf`. The Overleaf zip is not the submission file.

Named and anonymized Word files:

`When Overall AUC Hides Miscalibration/manuscript-pack/manuscript/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.docx`

`When Overall AUC Hides Miscalibration/manuscript-pack/manuscript/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components_blind.docx`

The matching `.doc` and `.pdf` files use the same stem. PDFs are in `manuscript-pack/output/`. The editorial office receives the named file. Reviewers receive the anonymized PDF and `manuscript-pack/output/OJS_UPLOAD/code_for_review_anonymous.zip`.

Table 5 remains the final-checkpoint, full-history result. Locked ASSISTments cells include DKT ECE `0.0602` / `0.2333`, T-KT ECE `0.1136` / `0.2280`, and FAR `0.196` / `0.268`. Validation-AUC checkpoint checks are reported in the text and are not extra tables. Their summaries are:

- `When Overall AUC Hides Miscalibration/results/A4_dkt_2x2.csv`
- `When Overall AUC Hides Miscalibration/results/A5_uncertainty_dkt_assist.csv`
- `When Overall AUC Hides Miscalibration/results/A5_secondary_dkt_assist.csv`
- `When Overall AUC Hides Miscalibration/results/B1_tktc_uncertainty.csv`
- `When Overall AUC Hides Miscalibration/results/B1_tktc_secondary.csv`
- `When Overall AUC Hides Miscalibration/results/B2_junyi_dkt_uncertainty.csv`
- `When Overall AUC Hides Miscalibration/results/B2_junyi_dkt_secondary.csv`
- `When Overall AUC Hides Miscalibration/results/B3_simplekt_uncertainty.csv`
- `When Overall AUC Hides Miscalibration/results/B3_simplekt_secondary.csv`

The same nine files are packed for reviewers at `results/validation_checkpoint/` inside the anonymous zip. They do not replace Table 5.

Other locked cells are in `When Overall AUC Hides Miscalibration/manuscript-pack/audit/SCIENTIFIC_LOCKS.md`.

## Datasets

Raw logs are **not** shipped. Obtain them from the original providers and place dumps under `When Overall AUC Hides Miscalibration/data/` (see `When Overall AUC Hides Miscalibration/data/README.md`):

1. [ASSISTments 2012](https://sites.google.com/site/assistmentsdata/) — 2012–2013 release with affect
2. [Junyi Academy Online Learning Activity Dataset](https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy) on Kaggle — **not** Junyi2015 / PSLC DataShop; the operational KC is `ucid`
3. [XES3G5M](https://github.com/pykt-team/pykt-toolkit)

## Reproduce

**LEVEL A** (review-facing): rebuild locked tables from frozen CSVs. No retrain. Does not change the Table 5 cells above.

```bash
cd "When Overall AUC Hides Miscalibration"
pip install -r requirements.txt
bash scripts/rebuild_locked_tables.sh      # Windows: scripts/rebuild_locked_tables.ps1
```

**Track A** retrains local IRT / DKT / T-KT and does **not** recreate those locked cells. See `When Overall AUC Hides Miscalibration/manuscript-pack/docs/how_to_reproduce.md`.

## Repository layout

| Path | Role |
|------|------|
| `When Overall AUC Hides Miscalibration/src/` | Preprocess, models, metrics, leakage audit |
| `When Overall AUC Hides Miscalibration/scripts/` | LEVEL A rebuild, Track A runners |
| `When Overall AUC Hides Miscalibration/configs/` | Dataset / model YAML |
| `When Overall AUC Hides Miscalibration/results/` | Validation-AUC summaries and frozen tables |
| `When Overall AUC Hides Miscalibration/manuscript-pack/` | Living manuscript, figures, frozen analysis |
| `When Overall AUC Hides Miscalibration/tests/` | Unit tests |

## Citation

During review, cite the anonymized accompanying artifact, not a journal article and not a public repository.

```bibtex
@software{sparse_concept_calibration_kt,
  title = {When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components},
  year  = {2026},
  note  = {Anonymized review artifact}
}
```

A journal name, volume, and DOI should be added only after acceptance.

## License

- Code: [MIT](LICENSE)
- Manuscript text, figures, and appendix tables: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
