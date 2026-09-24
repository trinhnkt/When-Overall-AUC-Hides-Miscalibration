# Scientific locks

Frozen cells for the submission pack. Do not “improve” these in silence.

## Datasets and models

- Logs: ASSISTments 2012, Junyi Academy, XES3G5M.
- Main baselines: IRT, DKT, Transformer KT baseline (local implementations). Transformer KT is **not** published SimpleKT `[4]` and is **not** an official checkpoint.
- Official SimpleKT `[4]` is scored on ASSISTments learner-based AUC/ECE only (four unique partitions). Do not treat T-KT cells as that checkpoint.
- GKT / CL4KT are **not** scored and are not shipped in the review zip.

## Protocol

- Train-only KC strata: strict \(f=0\); very sparse \(0<f<20\); sparse \(20\le f<100\); medium \(100\le f<500\); dense \(f\ge 500\).
- Occupancy R/L/I: descriptive flags, not inferential guarantees.
- Seeds **42, 2024, 2025, 2026, 2027**. Seeds 2025 and 2026 share one learner partition (`fold_2` = `fold_3`). Four unique partitions + five trained checkpoints. Never “five independent folds.”
- Dual numbering: four-partition ECE/AUC vs seed-42 gate cells. Do not mix.

## Locked numbers (four unique partitions unless noted)

- ASSISTments T-KT (Transformer KT baseline) ECE: dense \(0.1136\pm0.0066\) (\(N=523{,}971\) R) → medium \(0.1541\pm0.0051\) → sparse \(0.2280\pm0.0197\) (\(N=415\) L). Abstract may round dense ECE to **0.114**.
- ASSISTments official SimpleKT `[4]` (same partitions; do not overwrite T-KT): AUC \(0.7700\pm0.0013\), ACC \(0.7522\pm0.0014\); ECE dense \(0.0203\pm0.0035\) / medium \(0.0262\pm0.0025\) / sparse \(0.0884\pm0.0187\) (\(N=415\) L).
- Junyi sparse bucket: **empty**.
- Junyi T-KT four-partition cells (after aligning prediction files to official folds; two inits on fold 0 averaged first; no retrain): overall AUC \(0.7220\pm0.0035\), ACC \(0.7267\pm0.0035\); dense ECE \(0.0817\pm0.0070\) (\(N=3{,}226{,}541\)); medium ECE \(0.1136\pm0.0155\) (\(N=3{,}706\)). Obsolete wrong-fold mix: dense \(N=3{,}232{,}614\) ECE \(0.0792\); medium \(N=3{,}836\) ECE \(0.1073\). Do not restore those. Assist T-KT ECE locks are unchanged.
- XES3G5M T-KT ECE essentially flat after padding exclusion (\(0.1176\), \(0.1129\), \(0.1254\); sparse \(N=1{,}969\) R). Obsolete padded cells \(0.1145/0.1114/0.1248\) (\(N=2{,}010\)) are not used.
- Table 8 XES E1 tail mass: **21.5%** (184/854 KCs with \(f_{\mathrm{train}}<100\) on masked a2b fold 0). Obsolete printed **22.5%** was the pre-mask profile.
- Table 7 (cold-start; formerly Table 8/9) XES very-sparse (same masked a2b series as Table 5): \(N=114\) L; T-KT ECE \(0.184\); DKT ECE \(0.173\). Flag follows the printed four-partition mean (\(100\le N<1000\)). Do not revert to padded \(N=112\) / \(0.183\) / \(0.184\) or flag I/L.
- Gate \(\tau=0.7\); FAR = \(P(y=0\mid p\ge\tau)\). Seed-42 T-KT FAR 0.196 dense → 0.268 sparse. Primary robustness unit: four unique partitions, mean \(\Delta\)FAR 0.056 (range 0.015–0.087) after averaging seeds 2025/2026 first. Five-run mean 0.047, sd 0.033 (not five independent folds).
- Locked seed-42 KC-cluster CI **[0.006, 0.138]** from `manuscript-pack/analysis/c2_fivefold_verdict.txt`. Do not substitute a recomputed CSV CI.

## Claims that stay off

- No causal effects from observational regressions.
- Repeated KC-fold rows are not independent KCs.
- No “pre-registered” selection rule without a verifiable preregistration.
- No invented generative-AI tool versions, IRB numbers, ORCID, publisher DOI `10.18178/ijiet`, volume, or production pages.

## If a result must be recomputed

Mark the old result **obsolete**. List every downstream table, figure, and prose claim. Do not change ASSISTments or Junyi numbers merely because XES3G5M is corrected.
