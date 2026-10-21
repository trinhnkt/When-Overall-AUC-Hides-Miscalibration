# legacy

Checkpoint files of ban I were not on disk (`results/checkpoints`, `manuscript-pack/a2b/checkpoints`, `src/models` are empty of weight files). Status: NOT RECOVERED. Nothing was invented to fill them.

Existing prediction CSVs stay in `results/predictions`. They are the old protocol. They were not copied here because duplicating them would only repeat bytes already in the working tree. New scores of this round go to `results/predictions/pred_*.csv.gz` through `scripts/export_predictions.py` and a row in `runs/manifest.csv`.
