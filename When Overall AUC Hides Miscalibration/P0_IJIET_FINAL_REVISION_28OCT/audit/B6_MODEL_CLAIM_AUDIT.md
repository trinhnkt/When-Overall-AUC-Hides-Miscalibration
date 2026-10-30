# B6 Model-dependence claims

Date: 2026-10-29

Status: PASS (body). The abstract sentence is replaced in B1.

Search terms: "presence depends on the model", "model-dependent presence", "the models differ as well", "depends on the model", and the broader patterns "presence", "depend", "differ as well". Script: `scripts/b6_model_claims.py --write` (named and both blind copies).

Primary evidence: on ASSISTments 2012 both DKT and T-KT masked have a positive raw ΔECE and a positive size-matched gap on every partition (Table 5; partition gaps in Table A5). The presence of the calibration difference therefore does not differ between the two models.

| Location | Before | After | Class |
| --- | --- | --- | --- |
| V.A first paragraph | "…but the size and the sign of the extra summaries depend on the protocol, the checkpoint, the sample size, the model, and the dataset." | "Both primary models showed the difference; its observed magnitude differed between them and across partitions, checkpoints, and datasets. Where a sign varied, it was the sign of the bias reference ΔECE*, not the presence of the calibration difference." | unsupported causal/presence claim, replaced |
| V.B | "The models differ as well." | "The two primary models showed the same direction with different observed magnitudes." | vague model claim, replaced |
| VI Conclusion | "…but their size and presence depend on the evaluation protocol, the checkpoint, the sample size, the model, and the dataset." | "The observed magnitude differed between the two primary models and across checkpoints, partitions, and datasets; these are descriptive differences, not designed comparisons." | unsupported presence claim, replaced |
| Abstract | "…but their size and presence depend on … the model, and the dataset." | rewritten in B1 | handled in B1 |
| II.A | "The best model depends on the data … [9]" | unchanged | cited literature, not our claim |
| III.A, III.E | "do not depend on predicted values", "depends on the number of bins", "dependence structure" | unchanged | methodological, not model identity |

ΔECE* sign statements remain in IV.B (for example "positive on fold 1 and fold 4") and are labelled as the bias-reference quantity. No remaining sentence uses "depends on" with model identity as the subject.
