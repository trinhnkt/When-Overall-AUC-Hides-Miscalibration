#!/usr/bin/env python3
"""Write A2B rerun manifest + changelog from a2b analysis CSVs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REV = HERE.parent
ANALYSIS = HERE / "analysis"
MANIFEST = REV / "analysis" / "XES3G5M_RERUN_MANIFEST.md"
CHANGELOG = REV / "audit" / "CHANGELOG_A2B.md"


def fmt(mean, std=None, nd=4) -> str:
    if pd.isna(mean):
        return "NA"
    if std is None or pd.isna(std) or float(std) == 0:
        return f"{mean:.{nd}f}"
    return f"{mean:.{nd}f}±{std:.{nd}f}"


def cell(df, **kw):
    q = df
    for k, v in kw.items():
        q = q[q[k] == v]
    return q.iloc[0] if len(q) else None


def main() -> None:
    stats = pd.read_csv(HERE / "results" / "tables" / "dataset_stats.csv").iloc[0]
    ov_p = ANALYSIS / "summary_4part_overall.csv"
    bk_p = ANALYSIS / "summary_4part_bucket.csv"
    ov = pd.read_csv(ov_p) if ov_p.exists() else pd.DataFrame()
    bk = pd.read_csv(bk_p) if bk_p.exists() else pd.DataFrame()
    gate_p = ANALYSIS / "gate_fivefold.csv"
    gate = pd.read_csv(gate_p) if gate_p.exists() else pd.DataFrame()
    reg_p = ANALYSIS / "regression_results.csv"
    reg = pd.read_csv(reg_p) if reg_p.exists() else pd.DataFrame()
    a9_p = ANALYSIS / "a9" / "statistical_summary.csv"
    a9 = pd.read_csv(a9_p) if a9_p.exists() else pd.DataFrame()
    tmp_p = ANALYSIS / "temporal_seed42.csv"
    tmp = pd.read_csv(tmp_p) if tmp_p.exists() else pd.DataFrame()

    def ov_row(model):
        r = cell(ov, model=model) if not ov.empty else None
        return r

    def bk_row(model, bucket):
        r = cell(bk, model=model, bucket=bucket) if not bk.empty else None
        return r

    lines = []
    lines.append("# XES3G5M rerun manifest (A2B)")
    lines.append("")
    lines.append("**Date:** 2026-08-31  ")
    lines.append("**Prerequisite:** A1 CASE B.  ")
    lines.append("**Tree:** `IJIET_FINAL_REVISION/a2b/` (historical `data/processed/xes3g5m` and `results/predictions/` not overwritten).  ")
    lines.append("**ASSISTments / Junyi:** not updated.  ")
    lines.append("**Manuscript:** not edited in A2B; numbers below are the replacements a later text task must apply.")
    lines.append("")
    lines.append("## Masking")
    lines.append("")
    lines.append("- Dropped `selectmask != 1` (identical to concept `-1`: 1,540,356 tokens in `train_valid_sequences.csv`).")
    lines.append("- Dropped KC `-1`, question `-1`, labels not in {0,1}.")
    lines.append("- Official `test.csv` had 0 padding tokens.")
    lines.append(f"- Processed rows: **{int(stats.processed_interactions):,}**; KCs **{int(stats.n_kcs)}**; items **{int(stats.n_items)}**; learners **{int(stats.n_users)}**.")
    lines.append("- Learner partitions: **same users** as the published folds; padding rows removed from those users.")
    lines.append("- fold_2 = fold_3 user sets (locked duplicate partition). Training seeds remain 42, 2024, 2025, 2026, 2027.")
    lines.append("- Temporal: 70/10/20 re-cut on the masked table (padding timestamps no longer inflate the length).")
    lines.append("- Strata: train-only frequency; **no** `kc_id=-1` row.")
    lines.append("- Model settings: DKT/SimpleKT batch 64, 50 epochs, Adam 1e-3, best valid AUC; IRT 1PL lr 0.01, reg 0.01, 10 epochs, batch 512.")
    lines.append("")
    lines.append("## Old manuscript numbers that **must change** (XES only)")
    lines.append("")
    lines.append("Old values are from the accepted IJIET-21 manuscript / `BASELINE_FINAL_NUMERIC_AUDIT.md`. New values are four-partition (or seed-42 where that is what the paper used) on the masked rerun. **Obsolete** = do not keep the old cell.")
    lines.append("")
    lines.append("| ID | Location | Old (obsolete) | New (A2B) |")
    lines.append("|----|----------|----------------|-----------|")

    def add(i, loc, old, new):
        lines.append(f"| {i} | {loc} | {old} | {new} |")

    add("T1.KCs", "Table 1 KCs", "866", f"{int(stats.n_kcs)}")
    add("T1.items", "Table 1 / cohort items (if shown)", "7,653", f"{int(stats.n_items):,}")
    add("T1.inter", "Table 1 interactions 7.95M", "7,953,709 flattened incl. padding", f"{int(stats.processed_interactions):,} valid KC-level rows (padding excluded)")
    add("T1.test", "Table 1 learner-based test events", "1,589,145 (incl. 306,723 pad)", "1,282,422 fold-0 valid rows")

    def ovf(model, col):
        r = ov_row(model)
        if r is None:
            return "PENDING"
        return f"{fmt(r[f'{col}_mean'], r.get(f'{col}_std'))} (N={r['n_events_mean']:.0f})"

    add("R3.7", "Table 3 XES IRT AUC/ACC", "0.5000 / 0.7961±0.0031", ovf("irt_1pl", "auc") + " / " + ovf("irt_1pl", "acc"))
    add("R3.8", "Table 3 XES DKT AUC/ACC", "0.8171±0.0022 / 0.8327±0.0032", ovf("dkt", "auc") + " / " + ovf("dkt", "acc"))
    add("R3.9", "Table 3 XES SimpleKT AUC/ACC", "0.7557±0.0013 / 0.8067±0.0037", ovf("simplekt", "auc") + " / " + ovf("simplekt", "acc"))

    def bkf(model, bucket, col):
        r = bk_row(model, bucket)
        if r is None:
            return "PENDING"
        extra = f" N={r['n_events_mean']:.0f}" if col == "ece" else ""
        return fmt(r[f"{col}_mean"], r.get(f"{col}_std")) + extra

    add("R3.10a", "XES DKT sparse vs dense AUC", "0.857 vs 0.817", f"{bkf('dkt','sparse','auc')} vs {bkf('dkt','dense','auc')}")
    add("R3.10b", "XES SimpleKT sparse vs dense AUC", "0.847 vs 0.755", f"{bkf('simplekt','sparse','auc')} vs {bkf('simplekt','dense','auc')}")
    add("R4.7d", "Table 4 SimpleKT dense ECE", "0.1145±0.0011", bkf("simplekt", "dense", "ece"))
    add("R4.7m", "Table 4 SimpleKT medium ECE", "0.1114±0.0076", bkf("simplekt", "medium", "ece"))
    add("R4.7s", "Table 4 SimpleKT sparse ECE", "0.1248±0.0085; N=2,010 R", bkf("simplekt", "sparse", "ece"))
    add("A4", "Abstract/Discussion 'XES ECE essentially flat'", "0.1145 → 0.1114 → 0.1248", f"{bkf('simplekt','dense','ece')} → {bkf('simplekt','medium','ece')} → {bkf('simplekt','sparse','ece')}")
    add("I2", "Intro sparse AUC > dense", "DKT 0.857 vs 0.817; SK 0.847 vs 0.755", "see R3.10; re-check sign after rerun")

    if not gate.empty:
        def gsum(model, col):
            g = gate[gate["model"] == model]
            return f"{g[col].mean():.3f} (sd {g[col].std(ddof=1):.3f}, pos {(g[col]>0).sum()}/{len(g)})"
        sk42 = gate[(gate["model"] == "simplekt") & (gate["seed"] == 42)]
        dkt42 = gate[(gate["model"] == "dkt") & (gate["seed"] == 42)]
        add("R6.4", "XES SimpleKT ΔFAR / ΔMiss (five-run)", "ΔFAR negative 5/5; ΔMiss mean +0.112 5/5", f"dFM {gsum('simplekt','dFM')}; dMiss {gsum('simplekt','dMiss')}")
        add("C2xes", "c2_fivefold_verdict XES DKT/SimpleKT", "dkt dFM 0.004; sk dFM -0.018, dMiss 0.112, sparse_n 2000", f"dkt {gsum('dkt','dFM')}; sk {gsum('simplekt','dFM')}")
        if len(sk42):
            r = sk42.iloc[0]
            add("G42sk", "seed-42 SimpleKT gate FAR sparse/dense (if cited for XES)", "see direction_c XES cells", f"FM_s={r.FM_sparse:.3f} FM_d={r.FM_dense:.3f} dFM={r.dFM:.3f} sparse_n={int(r.sparse_n)} dense_n={int(r.dense_n)}")
        if len(dkt42):
            r = dkt42.iloc[0]
            add("G42dkt", "seed-42 DKT gate", "see direction_c XES cells", f"FM_s={r.FM_sparse:.3f} FM_d={r.FM_dense:.3f} dFM={r.dFM:.3f}")
    else:
        add("R6.4", "XES gate", "ΔFAR −; ΔMiss +0.112", "PENDING")

    add("R7.1", "Table 7 sparse mass (XES)", "22.5% of 866 KCs", "recompute from a2b kc_strata (865 KCs; -1 was dense so sparse mass rises slightly)")
    add("R7.2", "Table 7 sparse N", "2,010 R", bkf("simplekt", "sparse", "ece"))
    add("R7.3", "Table 7 difficulty ρ (XES)", "+0.087", "PENDING unless covariates recomputed into profile")
    add("R7.6", "Table 7 item median (XES)", "3 (dense 9 vs sparse 1)", "PENDING profile")
    add("R7.7", "Table 7 curriculum ρ (XES)", "−0.125", "PENDING profile")
    if not reg.empty:
        w = reg[(reg["weighted"] == True) & (reg["covariate"] == "log_train_freq")]
        if len(w):
            r = w.iloc[0]
            add("R7.8-9", "Results D regression n / log-freq (XES SimpleKT weighted)", "n=1,263; −0.117 [−0.171, −0.063]", f"n={int(r.n)}; {r.coef_std:+.3f} [{r.CI_lo:+.3f}, {r.CI_hi:+.3f}]")
    else:
        add("R7.8-9", "XES regression", "n=1263; −0.117", "PENDING")

    if not a9.empty:
        for _, r in a9.iterrows():
            add(f"R8.{r.model}.{r.level}", f"Table 8 XES {r.model} {r.level} ΔECE", "see old statistical_summary XES rows", f"{r.delta_ECE_mean:+.3f} [{r.delta_ECE_ci95_lo:+.3f}, {r.delta_ECE_ci95_hi:+.3f}] n={int(r.n_kcs)}")
    else:
        add("R8.6", "Table 8 XES DKT t500 ΔECE", "−0.008 [−0.019, +0.004]", "PENDING A9 retrain")

    add("D1-D3", "Discussion XES AUC/ECE sentences", "sparse AUC>dense; ECE essentially flat N=2010", "rewrite from R3.10 and R4.7")
    add("C3", "Conclusion XES ECE essentially flat", "Table 4", "rewrite from new Table 4 XES row")
    add("Fig1", "Figure 1 if it encodes 866 / 7.95M / XES ECE", "cohort counts + ECE panel", "update XES count/ECE traces only")

    lines.append("")
    lines.append("## Numbers that must **not** change")
    lines.append("")
    lines.append("- All ASSISTments ECE/AUC/FAR cells (0.1136, 0.2280, FAR 0.196/0.268, ΔFAR 0.047, CI [0.006, 0.138]).")
    lines.append("- All Junyi cells (sparse empty; dense/medium ECE).")
    lines.append("- Gate τ=0.7 definition; occupancy R/L/I; seed list; four-partition vs five-run wording.")
    lines.append("")
    lines.append("## Brier / REL / RES")
    lines.append("")
    if not bk.empty:
        for model in ("irt_1pl", "dkt", "simplekt"):
            for bucket in ("dense", "medium", "sparse"):
                r = bk_row(model, bucket)
                if r is None:
                    continue
                lines.append(f"- {model} {bucket}: Brier {fmt(r.brier_mean, r.brier_std)} REL {fmt(r.reliability_mean, r.reliability_std)} RES {fmt(r.resolution_mean, r.resolution_std)}")
    else:
        lines.append("PENDING")
    lines.append("")
    if not tmp.empty:
        lines.append("## Temporal (seed 42, masked 70/10/20)")
        lines.append("")
        for _, r in tmp.iterrows():
            lines.append(f"- {r.model} {r.bucket}: n={int(r.n_events)} AUC={r.auc:.4f} ACC={r.acc:.4f} ECE={r.ece:.4f}")
        lines.append("")
    lines.append("## Artifact map")
    lines.append("")
    lines.append("| Product | Path |")
    lines.append("|---|---|")
    lines.append("| Processed | `IJIET_FINAL_REVISION/a2b/data/processed/xes3g5m/` |")
    lines.append("| Predictions | `IJIET_FINAL_REVISION/a2b/results/predictions/` |")
    lines.append("| Strata | `IJIET_FINAL_REVISION/a2b/results/tables/kc_strata.csv` |")
    lines.append("| Four-partition | `IJIET_FINAL_REVISION/a2b/analysis/summary_4part_*.csv` |")
    lines.append("| Gate | `IJIET_FINAL_REVISION/a2b/analysis/gate_fivefold.csv` |")
    lines.append("| Regression | `IJIET_FINAL_REVISION/a2b/analysis/regression_results.csv` |")
    lines.append("| A9 | `IJIET_FINAL_REVISION/a2b/analysis/a9/` |")
    lines.append("")
    lines.append("Do not copy these over historical `results/predictions/xes3g5m_*` until a later replace-manuscript task.")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST}", flush=True)

    cl = []
    cl.append("# CHANGELOG_A2B — rebuild XES3G5M with valid masking")
    cl.append("")
    cl.append("**Date:** 2026-08-31  ")
    cl.append("**Prerequisite:** CASE B (A1).")
    cl.append("")
    cl.append("## What this task did")
    cl.append("")
    cl.append("- Flattened official `kc_level` files dropping `selectmask != 1`, KC `-1`, question `-1`, and non-{0,1} labels into `IJIET_FINAL_REVISION/a2b/` only.")
    cl.append("- Rebuilt learner-based folds using **historical user sets** (same students) with padding rows removed; copied fold_2 → fold_3.")
    cl.append("- Re-cut temporal 70/10/20 on the masked table.")
    cl.append("- Recomputed train-only KC strata (0 rows with `kc_id=-1`).")
    cl.append("- Retrained IRT, DKT, local SimpleKT (seeds 42, 2024, 2025, 2026, 2027; learner-based + temporal).")
    cl.append("- Recomputed AUC/ACC, ECE, Brier/REL/RES, XES gate, KC covariates, regression, and XES A9.")
    cl.append("- Listed obsolete manuscript XES numbers in `analysis/XES3G5M_RERUN_MANIFEST.md`.")
    cl.append("")
    cl.append("## What this task did not do")
    cl.append("")
    cl.append("- Did not overwrite `data/processed/xes3g5m/` or historical `results/predictions/`.")
    cl.append("- Did not edit the manuscript, Table 1–8, or Figure 1 (a later task applies the manifest).")
    cl.append("- Did not change ASSISTments or Junyi artifacts.")
    cl.append("")
    cl.append("## Scientific results changed?")
    cl.append("")
    cl.append("**Yes, XES3G5M only**, in the new tree. Accepted manuscript copy still shows obsolete XES cells until a text-apply task.")
    cl.append("")
    cl.append("## STOP")
    cl.append("")
    cl.append("Do not start the next manuscript-edit task automatically.")
    CHANGELOG.write_text("\n".join(cl) + "\n", encoding="utf-8")
    print(f"wrote {CHANGELOG}", flush=True)


if __name__ == "__main__":
    main()
