#!/usr/bin/env python3
"""Rebuild the Gate D source tables, Fig. 3, and the manuscript text.

Reads prediction exports and the Gate C tables. Does not invent cells.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from sklearn.metrics import accuracy_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ece_uncertainty import ece  # noqa: E402

CORR = ROOT / "P0_IJIET_FINAL_CORRECTION_2026"
PRED = ROOT / "results" / "predictions"
DETAIL = CORR / "results" / "C_partition_detail.csv"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
PROTOCOL = "P0-BV200-15EW"

DOCS = [
    ROOT / "manuscript-pack" / "manuscript" / (
        "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing "
        "on Rarely Practiced Knowledge Components_blind.docx"
    ),
    ROOT / "manuscript-pack" / "manuscript" / (
        "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing "
        "on Rarely Practiced Knowledge Components.docx"
    ),
]


def four(values: dict[str, float]) -> tuple[float, float]:
    units = np.array([
        values["fold0"],
        values["fold1"],
        0.5 * (values["fold2"] + values["fold3"]),
        values["fold4"],
    ], dtype=float)
    return float(units.mean()), float(units.std(ddof=1))


def overall_for(pattern: str) -> tuple[float, float, float]:
    aucs, accs, ns = {}, {}, {}
    for fold, seed in PAIRS:
        path = PRED / pattern.format(fold=fold, seed=seed)
        frame = pd.read_csv(path, usecols=["y", "p", "no_history"])
        kept = frame[frame["no_history"] == 0]
        y = kept["y"].to_numpy()
        p = kept["p"].to_numpy(dtype=float)
        key = f"fold{fold}"
        aucs[key] = float(roc_auc_score(y, p))
        accs[key] = float(accuracy_score(y, (p >= 0.5).astype(int)))
        ns[key] = float(len(kept))
    return four(aucs)[0], four(accs)[0], four(ns)[0], four(aucs)[1], four(accs)[1], four(ns)[1]


def bin_curve(y, p, n_bins=15):
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    conf, acc = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p <= hi) if lo == 0 else (p > lo) & (p <= hi)
        if not np.any(mask):
            continue
        conf.append(float(np.mean(p[mask])))
        acc.append(float(np.mean(y[mask])))
    return np.array(conf), np.array(acc)


def write_fig3(path: Path) -> None:
    specs = [
        ("pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz", "DKT"),
        ("pred_assist2012_tktc_best_validxchunk_fold0_42.csv.gz", "T-KT masked"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), sharex=True, sharey=True)
    colors = {"dense": "#1f4e79", "sparse": "#c0392b"}
    for ax, (name, title) in zip(axes, specs):
        frame = pd.read_csv(PRED / name, usecols=["y", "p", "group", "no_history"])
        kept = frame[frame["no_history"] == 0]
        ax.plot([0, 1], [0, 1], ls="--", c="0.55", lw=0.8)
        for group in ("dense", "sparse"):
            sub = kept[kept["group"] == group]
            y = sub["y"].to_numpy()
            p = sub["p"].to_numpy(dtype=float)
            conf, acc = bin_curve(y, p)
            ax.plot(
                conf, acc, marker="o", ms=3.5, lw=1.2, color=colors[group],
                label=f"{group}  ECE {ece(y, p):.4f}  N {len(y)}",
            )
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Mean predicted probability")
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        ax.grid(alpha=0.25, lw=0.4)
    axes[0].set_ylabel("Observed frequency")
    fig.suptitle(
        "ASSISTments 2012, protocol P0-BV200-15EW, fold 0 only",
        fontsize=10,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def metric_row(**kwargs) -> dict:
    base = {
        "dataset": "",
        "model": "",
        "partition": "",
        "protocol_id": PROTOCOL,
        "checkpoint_rule": "",
        "history_rule": "",
        "mask_rule": "",
        "leakage_status": "",
        "metric": "",
        "value": "",
        "uncertainty": "",
        "prediction_file": "",
        "analysis_script": "scripts/p0_gate_c_export.py",
        "status": "",
    }
    base.update(kwargs)
    return base


def write_registries(detail: pd.DataFrame) -> None:
    rows_p, rows_s, rows_l, rows_i = [], [], [], []
    for _, row in detail.iterrows():
        status = "PRIMARY" if row["role"] == "PRIMARY" else "SENSITIVITY"
        bucket = rows_p if status == "PRIMARY" else rows_s
        leak = "L8 not applicable; one KC per row"
        mask = "lstm_shift_pad0" if row["model"] == "dkt" else "causal_and_pad_2n"
        if row["dataset"] == "junyi":
            status = "SENSITIVITY"
            bucket = rows_s
        common = dict(
            dataset=row["dataset"],
            model=row["model"],
            partition=row["unique_partition"],
            protocol_id=PROTOCOL,
            checkpoint_rule="best_valid",
            history_rule="chunk_le_200",
            mask_rule=mask,
            leakage_status=leak,
            prediction_file=row["source_prediction_file"],
            analysis_script="scripts/p0_gate_c_export.py",
            status=status,
        )
        mapping = {
            "ECE_focal": row["ECE_focal"],
            "ECE_dense": row["ECE_dense"],
            "DeltaECE": row["DeltaECE"],
            "ECE0": row["ECE0"],
            "DeltaECE_star": row["DeltaECE_star"],
            "matched_gap": row["matched_gap"],
            "AUC": row["AUC"],
            "ACC": row["ACC"],
            "Brier": row["Brier"],
            "NLL": row["NLL"],
            "N_focal": row["N_focal"],
            "N_dense": row["N_dense"],
        }
        for metric, value in mapping.items():
            uncertainty = ""
            if metric == "matched_gap" and row["partition"] == "fold0":
                uncertainty = f"fold0 matched CI {row['CI95_low']:.6f} to {row['CI95_high']:.6f}"
            bucket.append(metric_row(**common, metric=metric, value=value, uncertainty=uncertainty))
    a4 = pd.read_csv(ROOT / "results" / "A4_dkt_2x2.csv")
    for _, row in a4.iterrows():
        if row["eval_context"] == "slide":
            continue
        kind = "PRIMARY" if row["select_rule"] == "best_valid" and row["eval_context"] == "chunk" else "SENSITIVITY"
        target = rows_p if kind == "PRIMARY" else rows_s
        # Primary chunk rows are already in the Gate C export. Keep the grid in sensitivity
        # except we do not duplicate the primary cell as a second primary claim.
        if kind == "PRIMARY":
            continue
        target.append(metric_row(
            dataset="assist2012",
            model="dkt",
            partition=f"fold{int(row['partition'])}" if False else row["partition"],
            protocol_id="P0-DKT-2x2",
            checkpoint_rule=row["select_rule"],
            history_rule="full" if row["eval_context"] == "full" else "chunk_le_200",
            mask_rule="lstm_shift_pad0",
            leakage_status="L8 not applicable; one KC per row",
            metric="DeltaECE",
            value=row["delta_ece"],
            uncertainty="",
            prediction_file="results/A4_dkt_2x2.csv",
            analysis_script="scripts/p0_a5_dkt_assist.py",
            status="SENSITIVITY",
        ))
    legacy = [
        ("assist2012", "dkt", "ECE_dense", 0.0602),
        ("assist2012", "dkt", "ECE_sparse", 0.2333),
        ("assist2012", "dkt", "DeltaECE_star", 0.078),
        ("assist2012", "simplekt", "ECE_dense", 0.0203),
        ("assist2012", "simplekt", "ECE_sparse", 0.0884),
        ("junyi", "dkt", "ECE_dense", 0.0389),
        ("junyi", "dkt", "ECE_medium", 0.2513),
        ("junyi", "dkt", "DeltaECE_star", 0.181),
    ]
    for dataset, model, metric, value in legacy:
        rows_l.append(metric_row(
            dataset=dataset, model=model, partition="four_partition_archived",
            protocol_id="BAN_I_FINAL_FULL", checkpoint_rule="final", history_rule="full",
            mask_rule="not_recovered", leakage_status="not re-audited on recovered weights",
            metric=metric, value=value, uncertainty="",
            prediction_file="NOT_RECOVERED", analysis_script="none", status="LEGACY",
        ))
    invalid = [
        ("assist2012", "tkt_unmasked", "ECE_dense", 0.1136),
        ("assist2012", "tkt_unmasked", "ECE_sparse", 0.2280),
        ("junyi", "tkt_unmasked", "ECE_medium", 0.1136),
        ("junyi", "tkt_unmasked", "ECE_dense", 0.0817),
    ]
    for dataset, model, metric, value in invalid:
        rows_i.append(metric_row(
            dataset=dataset, model=model, partition="archived",
            protocol_id="UNMASKED_T_KT", checkpoint_rule="final", history_rule="full",
            mask_rule="no causal mask", leakage_status="training lookahead; INVALID for a main claim",
            metric=metric, value=value, uncertainty="",
            prediction_file="NOT_RECOVERED", analysis_script="none", status="INVALID",
        ))
    rows_i.append(metric_row(
        dataset="xes3g5m", model="any", partition="release",
        protocol_id="NONE", checkpoint_rule="", history_rule="",
        mask_rule="", leakage_status="L8 FAIL",
        metric="AUC_or_ECE", value="NOT_EVALUATED", uncertainty="",
        prediction_file="none", analysis_script="scripts/check_b4_utb.py",
        status="NOT_EVALUATED",
    ))
    out = ROOT / "results"
    pd.DataFrame(rows_p).to_csv(out / "results_primary.csv", index=False)
    pd.DataFrame(rows_s).to_csv(out / "results_sensitivity.csv", index=False)
    pd.DataFrame(rows_l).to_csv(out / "results_legacy.csv", index=False)
    pd.DataFrame(rows_i).to_csv(out / "results_invalid.csv", index=False)
    for name in (
        "results_primary.csv", "results_sensitivity.csv", "results_legacy.csv", "results_invalid.csv"
    ):
        shutil.copy(out / name, CORR / "results" / name)


def write_claims() -> None:
    claims = [
        ("C01", "Overall AUC can hide frequency-stratified calibration differences, and the difference depends on protocol, checkpoint, sample size, model, and dataset.", "Abstract; Conclusion", "assist2012", "dkt", PROTOCOL, "P0-P4", "interpretation", "", "", "L8 not applicable", "results/C_unique_partition_summary.csv", "scripts/p0_gate_c_export.py", "SUPPORTED"),
        ("C02", "ASSISTments DKT four-partition ECE sparse 0.0982, dense 0.0089, DeltaECE 0.0893, DeltaECE* -0.0081, matched gap 0.0400.", "Abstract; IV.B; Table 5", "assist2012", "dkt", PROTOCOL, "P0-P4", "ECE and contrasts", "0.098172; 0.008907; 0.089265; -0.008065; 0.039960", "SD in Table 5; not a CI", "L8 not applicable", "P0_IJIET_FINAL_CORRECTION_2026/results/C_unique_partition_summary.csv", "scripts/p0_gate_c_export.py", "SUPPORTED"),
        ("C03", "ASSISTments DKT fold 0 matched gap 0.0351, 95% interval 0.0170 to 0.0821. One partition only.", "Abstract; IV.B; Table 5; Fig. 3", "assist2012", "dkt", PROTOCOL, "P0", "matched_gap", "0.035150", "0.016960 to 0.082110", "L8 not applicable", "results/predictions/pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz", "scripts/p0_gate_c_export.py", "SUPPORTED"),
        ("C04", "T-KT masked fold 0 matched interval 0.0233 to 0.0878; four-partition DeltaECE* 0.0068.", "Abstract; IV.B; Table 5", "assist2012", "tktc", PROTOCOL, "P0 and P0-P4", "matched_gap; DeltaECE_star", "0.036542; 0.006782", "0.023294 to 0.087776 on fold 0", "causal mask tests PASS", "results/predictions/pred_assist2012_tktc_best_validxchunk_fold0_42.csv.gz", "scripts/p0_gate_c_export.py", "SUPPORTED"),
        ("C05", "Junyi has no sparse group. Post-hoc four-partition DeltaECE* is -0.0032.", "Abstract; IV.B; Table 5; Conclusion", "junyi", "dkt", PROTOCOL, "P0-P4", "DeltaECE_star", "-0.003150", "fold 0 matched CI 0.001048 to 0.043440; not a test of DeltaECE*", "L8 not applicable", "P0_IJIET_FINAL_CORRECTION_2026/audit/JUNYI_DELTAECESTAR_TRACE.csv", "scripts/p0_gate_c_export.py", "CONDITIONAL"),
        ("C06", "XES3G5M is a descriptive audit only. Model AUC and ECE are not reported.", "Abstract; IV.B; V.A; Conclusion; cover letter", "xes3g5m", "none", "NONE", "release", "model metrics", "NOT_EVALUATED", "", "L8 FAIL", "P0_IJIET_FINAL_CORRECTION_2026/audit/GATE_B_XES_REPORT.md", "tests/test_xes_events.py", "SUPPORTED"),
        ("C07", "Fold 0 DKT 2x2 changes window and checkpoint separately. A versus D is not a single-cause contrast.", "IV.D; Table A2", "assist2012", "dkt", "P0-DKT-2x2", "fold0", "sparse ECE", "0.2251; 0.2179; 0.1045; 0.0916", "", "L8 not applicable", "results/A4_dkt_2x2.csv", "scripts/p0_a5_dkt_assist.py", "SUPPORTED"),
        ("C08", "DeltaECE* is a bias reference, not a significance test. The fold-0 interval is not a claim about all four partitions.", "III.E; IV.B; V.A; V.D", "assist2012", "dkt", PROTOCOL, "P0-P4", "interpretation", "", "", "L8 not applicable", "src/ece_uncertainty.py", "scripts/p0_gate_c_export.py", "SUPPORTED"),
        ("C09", "FAR under the primary protocol was not recomputed.", "IV.F", "assist2012", "dkt", PROTOCOL, "P0-P4", "FAR", "NOT_EVALUATED", "", "L8 not applicable", "none", "none", "UNSUPPORTED"),
    ]
    frame = pd.DataFrame(claims, columns=[
        "claim_id", "claim_text", "manuscript_location", "dataset", "model", "protocol_id",
        "fold/partition", "metric/estimand", "value", "CI", "leakage_status",
        "prediction_file", "analysis_script", "status",
    ])
    frame.to_csv(ROOT / "docs" / "claim_evidence.csv", index=False)
    shutil.copy(ROOT / "docs" / "claim_evidence.csv", CORR / "docs" / "claim_evidence.csv")


def set_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def find_one(doc: Document, prefix: str):
    hits = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} hits for {prefix!r}")
    return hits[0]


def fill(table, rows: list[list[str]]) -> None:
    if len(rows) > len(table.rows):
        raise SystemExit("table is shorter than the new content")
    for i, row in enumerate(rows):
        cells = table.rows[i].cells
        if len(row) != len(cells):
            raise SystemExit(f"row {i} has {len(row)} values for {len(cells)} cells")
        for cell, value in zip(cells, row):
            cell.text = value
    for i in range(len(rows), len(table.rows)):
        for cell in table.rows[i].cells:
            cell.text = ""


def add_column(table) -> None:
    grid = table._tbl.find(qn("w:tblGrid"))
    column = OxmlElement("w:gridCol")
    column.set(qn("w:w"), "1200")
    grid.append(column)
    for tr in table._tbl.findall(qn("w:tr")):
        last = tr.findall(qn("w:tc"))[-1]
        tr.append(last.__copy__())


def replace_fig3(doc: Document, png: bytes) -> None:
    replaced = False
    for rel in doc.part.rels.values():
        if rel.target_ref.endswith("image3.png"):
            rel.target_part._blob = png
            replaced = True
    if not replaced:
        raise SystemExit("image3.png was not found")
    caption = find_one(doc, "Fig. 3.")
    drawing_para = None
    previous = None
    for paragraph in doc.paragraphs:
        if paragraph._p is caption._p:
            drawing_para = previous
            break
        if paragraph._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
            previous = paragraph
    if drawing_para is None:
        raise SystemExit("Fig. 3 drawing was not found")
    cx, cy = "6583680", "3017520"  # 7.2 in by 3.3 in
    for node in drawing_para._p.xpath('.//*[local-name()="extent" or local-name()="ext"]'):
        if node.get("cx") is not None:
            node.set("cx", cx)
            node.set("cy", cy)


def fmt_pm(mean: float, sd: float) -> str:
    return f"{mean:.4f} ± {sd:.4f}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    detail = pd.read_csv(DETAIL)
    write_registries(detail)
    write_claims()
    fig_path = ROOT / "manuscript-pack" / "figures" / "fig3_primary.png"
    write_fig3(fig_path)
    png = fig_path.read_bytes()

    dkt_auc = overall_for("pred_assist2012_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz")
    tkt_auc = overall_for("pred_assist2012_tktc_best_validxchunk_fold{fold}_{seed}.csv.gz")
    jun_auc = overall_for("pred_junyi_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz")
    skt_auc = overall_for("pred_assist2012_simplekt_best_validxchunk_fold{fold}_{seed}.csv.gz")
    print("AUC DKT", dkt_auc)
    print("AUC TKT", tkt_auc)
    print("AUC JUN", jun_auc)
    print("AUC SKT", skt_auc)

    a4 = pd.read_csv(ROOT / "results" / "A4_dkt_2x2.csv")
    grid_rows = [["Fold", "final/full", "final/200", "best/full", "best/200", "ΔECE* best/200", "N sparse best/200", "reason missing"]]
    for fold in range(5):
        block = a4[a4["partition"] == f"fold{fold}"]
        def cell(rule, context, column="delta_ece"):
            hit = block[(block["select_rule"] == rule) & (block["eval_context"] == context)]
            return f"{float(hit.iloc[0][column]):.4f}"
        grid_rows.append([
            f"fold {fold}",
            cell("final", "full"),
            cell("final", "chunk"),
            cell("best_valid", "full"),
            cell("best_valid", "chunk"),
            cell("best_valid", "chunk", "delta_ece_star"),
            cell("best_valid", "chunk", "n_sparse"),
            "none",
        ])

    texts = manuscript_text(dkt_auc, tkt_auc, jun_auc, skt_auc)
    words = len(texts["Abstract—"].split())
    print("abstract words", words)
    if not 180 <= words <= 220:
        raise SystemExit(f"abstract word count {words} is outside 180–220")

    for path in DOCS:
        doc = Document(path)
        for prefix, text in texts.items():
            set_text(find_one(doc, prefix), text)
        fill(doc.tables[1], table2_rows())
        add_column(doc.tables[3])
        add_column(doc.tables[3])
        fill(doc.tables[3], table4_rows(dkt_auc, tkt_auc, jun_auc, skt_auc))
        fill(doc.tables[4], table5_rows())
        fill(doc.tables[5], table6_rows())
        fill(doc.tables[7], grid_rows)
        replace_fig3(doc, png)
        doc.save(path)
        print("saved", path.name)


def manuscript_text(dkt, tkt, jun, skt) -> dict[str, str]:
    dkt_auc, dkt_acc, dkt_n, dkt_auc_sd, dkt_acc_sd, dkt_n_sd = dkt
    tkt_auc, tkt_acc, tkt_n, tkt_auc_sd, tkt_acc_sd, tkt_n_sd = tkt
    jun_auc, jun_acc, jun_n, jun_auc_sd, jun_acc_sd, jun_n_sd = jun
    skt_auc, skt_acc, skt_n, skt_auc_sd, skt_acc_sd, skt_n_sd = skt
    return {
        "Abstract—": (
            "Abstract—Knowledge-tracing models are usually ranked by overall AUC, which can hide "
            "calibration differences among knowledge components that learners rarely practice. We lock "
            "one protocol on ASSISTments 2012: the validation-AUC checkpoint, test windows of at most 200, "
            "15 equal-width bins, and four unique learner partitions. Deep knowledge tracing had mean ECE "
            "0.0982 on sparse components and 0.0089 on dense components (ΔECE = 0.0893). Its fold-0 "
            "size-matched gap was 0.0351 (learner-cluster 95% interval 0.0170 to 0.0821). The four-partition "
            "bias reference ΔECE* was −0.0081 and is not a significance test. A causally masked Transformer "
            "under the same protocol had a fold-0 matched interval of 0.0233 to 0.0878 and a four-partition "
            "ΔECE* of 0.0068. Junyi Academy has no sparse group; its post-hoc medium-versus-dense ΔECE* is "
            "−0.0032. XES3G5M is a descriptive audit only, after a failed leakage check and no corrected "
            "retraining. Groups use training counts only, and empty test windows are dropped. "
            "The four-partition SD is descriptive, because the partitions are not independent samples. "
            "Unmasked Transformer scores are excluded. Overall AUC can hide frequency-stratified "
            "calibration differences, but their size "
            "and presence depend on the protocol, the checkpoint, the sample size, the model, and the dataset."
        ),
        "Applying the protocol": (
            "The study addresses three research questions. Only ASSISTments 2012, under protocol "
            "P0-BV200-15EW, is used for the primary answers. Junyi Academy is a post-hoc check. "
            "XES3G5M contributes distribution and estimability, not model scores."
        ),
        "RQ1:": (
            "RQ1: Under the locked protocol, how does ECE differ between sparse and dense knowledge "
            "components on ASSISTments 2012, once the bias reference and a size-matched comparison are reported separately?"
        ),
        "RQ2:": (
            "RQ2: When is a sparse-versus-dense contrast estimable, and when must model-based results be withheld?"
        ),
        "RQ3:": (
            "RQ3: On ASSISTments 2012, how does the DKT contrast change when the checkpoint and the test window are varied one at a time?"
        ),
        "For RQ1": (
            "For RQ1, DKT and a causally masked Transformer are the primary models. Across four unique "
            "partitions their sparse ECE exceeds their dense ECE. The size-matched gap is positive, and "
            "the fold-0 interval for that gap excludes 0. ΔECE* does not stay positive on every partition, "
            "so the bias reference and the matched interval are not the same statement. Section IV gives "
            "the partition means. For RQ2, Junyi Academy has no sparse group. XES3G5M has a low-frequency "
            "tail in its KC-level file, but check L8 failed and no corrected model was trained, so it is a "
            "descriptive audit only. For RQ3, the DKT grid in Table A2 separates the final checkpoint from "
            "the validation-AUC checkpoint and the full test history from windows of 200. Changing both at "
            "once is not attributed to either factor alone."
        ),
        "The paper makes three contributions": (
            "The paper makes three contributions. First, it specifies a protocol that groups knowledge "
            "components by training frequency, labels sample support, defines ΔECE* as a bias reference "
            "rather than a test, and states eight leakage checks. Second, it reports ASSISTments DKT and "
            "T-KT masked under that protocol, with the raw contrast, the bias reference, and the "
            "size-matched gap kept apart. Third, it states the limits of the evidence: Junyi Academy is "
            "post-hoc and has no sparse group, XES3G5M is a descriptive audit only, and a change of both "
            "checkpoint and test window is not a single-cause result. Unmasked T-KT is not used as a finding."
        ),
        "Table 2 summarizes": (
            "Table 2 lists the runs that supply the primary and sensitivity scores. DKT is an LSTM over "
            "KC–response tokens and pads with index 0. T-KT masked is a two-layer Transformer over the same "
            "tokens, with a causal mask and padding id 2n. Both were trained on ASSISTments 2012 for at most "
            "50 epochs, with patience 8, and the saved checkpoint is the one with the highest validation AUC. "
            "Test sequences are scored in non-overlapping windows of at most 200. simpleKT is the pyKT "
            "implementation and is a sensitivity analysis, not a primary model. The one-parameter IRT fit "
            "returns the training base rate for unseen learners, so its AUC is 0.5000 by construction and "
            "it is not a ranking model. BKT was not scored."
        ),
        "The three local models": (
            "The primary checkpoint is the validation-AUC checkpoint, not the final epoch. The final epoch "
            "and the full test history remain in the sensitivity grid (Table A2). That grid was pre-specified "
            "for ASSISTments DKT. Junyi DKT uses the same checkpoint and window rules, but it was not in the "
            "pre-specified plan and is not called pre-specified. The original weights behind the archived "
            "final-checkpoint pairs were not recovered. Those pairs are not results of this protocol."
        ),
        "is positive only if": (
            "is positive only if the sparse–dense difference exceeds this upper bound on expected "
            "small-sample bias. ECE0 is computed from the focal N of that partition. Fold 2 and fold 3 "
            "are averaged first, and the reported ΔECE* is the mean of the four unique partitions. It is "
            "not the result of subtracting ECE0 once from the mean ΔECE. ΔECE* is not a confidence interval, "
            "not a hypothesis test, and not a p-value. The size-matched gap, and the learner-cluster interval "
            "computed on fold 0 only, are different quantities."
        ),
        "Table 4 reports": (
            f"Table 4 reports overall AUC and accuracy on rows with a nonempty test window. Under the "
            f"primary protocol, ASSISTments DKT has AUC {dkt_auc:.4f} ± {dkt_auc_sd:.4f} and accuracy "
            f"{dkt_acc:.4f} ± {dkt_acc_sd:.4f}. T-KT masked has AUC {tkt_auc:.4f} ± {tkt_auc_sd:.4f} and "
            f"accuracy {tkt_acc:.4f} ± {tkt_acc_sd:.4f}. The mean and SD use four unique partitions. "
            f"Junyi DKT, under the same scoring rules but as a post-hoc check, has AUC {jun_auc:.4f} ± "
            f"{jun_auc_sd:.4f}. simpleKT on ASSISTments, also post-hoc, has AUC {skt_auc:.4f} ± "
            f"{skt_auc_sd:.4f} and is not ranked against the primary models. These figures are not "
            "benchmark scores from a different split."
        ),
        "Table 4. Overall": (
            "Table 4. Overall AUC and accuracy on nonempty test windows (mean ± SD across four unique "
            "learner partitions). N is that mean count. Fold 2 and fold 3 are one partition and are "
            "averaged before the SD. The SD is descriptive. Protocol P0-BV200-15EW. Junyi DKT and "
            "simpleKT are post-hoc sensitivity rows, not primary claims."
        ),
        "On ASSISTments 2012, ECE rose": (
            "On ASSISTments 2012, under protocol P0-BV200-15EW, sparse ECE is higher than dense ECE for "
            "both primary models (Table 5). For DKT the four-partition means are 0.0982 ± 0.0093 sparse "
            "and 0.0089 ± 0.0013 dense, so ΔECE = 0.0893 ± 0.0091. ΔECE* = −0.0081 ± 0.0122. The "
            "size-matched gap is 0.0400 ± 0.0107. On fold 0 that gap is 0.0351, and the learner-cluster "
            "95% interval is 0.0170 to 0.0821 (N sparse = 430). ΔECE* on that fold is −0.0088. The "
            "matched gap is positive on all four partitions. ΔECE* is positive only on P1. The interval "
            "is for fold 0. It is not a test of the other partitions, and ΔECE* is not that interval. "
            "For T-KT masked the four-partition sparse and dense ECE are 0.1199 ± 0.0247 and "
            "0.0158 ± 0.0032 (ΔECE = 0.1041 ± 0.0215). ΔECE* = 0.0068 ± 0.0207, positive on P1 and P4 "
            "and negative on P0 and P2. The matched gap is 0.0581 ± 0.0230. The fold-0 gap is 0.0365, "
            "with interval 0.0233 to 0.0878. The mask, the checkpoint, and the window were introduced "
            "together, so this is not a mask-only effect. simpleKT is sensitivity only and is not in Table 5."
        ),
        "On Junyi Academy, which has no sparse group": (
            "Junyi Academy has no sparse group. Its DKT medium-versus-dense contrast uses the same "
            "checkpoint and window, but it is post-hoc. The four-partition means are ECE 0.0345 ± 0.0080 "
            "on medium and 0.0043 ± 0.0021 on dense (ΔECE = 0.0302 ± 0.0069; mean N medium = 3676.75). "
            "ΔECE* = −0.0032 ± 0.0067. That value is the mean of the per-partition references, not "
            "0.0302 minus the bound at a single N. The matched gap is 0.0115 ± 0.0073. The fold-0 "
            "interval is 0.0010 to 0.0434 and applies to that partition. XES3G5M has no model row. "
            "Check L8 failed, the windows repeat responses at some boundaries, and no corrected model "
            "was trained. Its frequency distribution remains a descriptive audit."
        ),
        "Fig. 3 shows": (
            "Fig. 3 shows the fold-0 reliability diagrams for the two primary models on ASSISTments 2012. "
            "The sparse curves use 430 responses and 15 bins. They are visual checks, not the four-partition estimate."
        ),
        "Table 5. Final-checkpoint": (
            "Table 5. Calibration under protocol P0-BV200-15EW (mean ± SD across four unique partitions; "
            "15 equal-width bins; nonempty windows). ΔECE* uses each partition’s own N and is a bias "
            "reference, not a confidence interval. The 95% interval is the fold-0 learner-cluster interval "
            "of the size-matched gap only. Support: Limited if 100 ≤ N < 1,000, Reliable if N ≥ 1,000. "
            "Junyi is post-hoc. XES3G5M is not evaluated."
        ),
        "Fig. 3. Final-checkpoint": (
            "Fig. 3. Reliability diagrams for the primary protocol on ASSISTments 2012, fold 0, "
            "15 equal-width bins, nonempty windows. Left: DKT. Right: T-KT masked. Dense and sparse "
            "groups only. N sparse = 430 in each panel. This is one partition. Table 5 holds the "
            "four-partition means. Junyi and XES3G5M are not plotted."
        ),
        "Whether a sparse contrast": (
            "Whether a sparse contrast can be estimated is a property of the counts (Table 6; RQ2). "
            "ASSISTments 2012 has a nonempty sparse group. Under the primary protocol its mean sparse "
            "N is 397.75, which is Limited, and its dense group is Reliable, so the contrast is eligible. "
            "Junyi Academy has no sparse group; the post-hoc contrast is medium versus dense, and the "
            "medium group is Reliable. XES3G5M has low-frequency KC rows, but the model contrast is not "
            "eligible: check L8 failed and the dataset is a descriptive audit only. Strict cold-start "
            "and very-sparse groups are not given a primary ECE."
        ),
        "Under two alternative grids": (
            "Table A2 is the ASSISTments DKT grid of checkpoint and test window. Every cell is ΔECE. "
            "No cell is missing. On fold 0, final × full is 0.1689 and final × window 200 is 0.1620, "
            "so the window alone moves sparse ECE only from 0.2251 to 0.2179. At that same window, "
            "the validation-AUC checkpoint moves sparse ECE from 0.2179 to 0.0916 (ΔECE 0.1620 to 0.0846). "
            "Final × full versus validation × window 200 changes both factors; that gap is not assigned "
            "to the checkpoint alone and is not assigned to the window alone. Raw ΔECE stays positive "
            "in every cell. ΔECE* does not. The alternative frequency grids of the archived final-checkpoint "
            "analysis were not repeated here and are not a current result."
        ),
        "At a fixed threshold": (
            "A threshold probe of false advances was not recomputed on the primary-protocol predictions. "
            "FAR is Not evaluated under P0-BV200-15EW. Tables A3 and A4 remain an archived final-checkpoint "
            "probe. They are not a finding of this protocol, and they are not used in the abstract or the conclusion."
        ),
        "Three patterns stand out": (
            "The results support a limited claim. Overall AUC can hide frequency-stratified calibration "
            "differences, but the size and the sign of the extra summaries depend on the protocol, the "
            "checkpoint, the sample size, the model, and the dataset. On ASSISTments 2012, DKT and "
            "T-KT masked have a positive raw ΔECE and a positive size-matched gap. The fold-0 interval "
            "for that gap excludes 0. ΔECE* does not exclude a small-sample explanation on every "
            "partition, and it is not a significance test. The fold-0 interval is not evidence that all "
            "four partitions are significant. Junyi Academy has no sparse group. Its post-hoc ΔECE* is "
            "−0.0032. XES3G5M is a descriptive audit only. The study does not claim that a validation "
            "checkpoint removes sparse miscalibration, and it does not claim that the final checkpoint "
            "causes it."
        ),
        "The datasets differed first": (
            "The datasets differ first in whether a sparse contrast exists (Table 6). Junyi Academy’s "
            "exercise-level components all have at least 100 training responses under this split, so "
            "the sparse group is empty. ASSISTments 2012 has a Limited sparse group and is the only "
            "dataset with a primary model contrast. XES3G5M can describe frequency and estimability, "
            "but its model scores were produced by a route that fails L8. Those scores are excluded. "
            "The models differ as well. simpleKT was not a primary comparison. The study does not "
            "identify a mechanism that would make rare practice itself the cause of miscalibration."
        ),
        "Several limitations qualify": (
            "Several limits qualify these findings. The label is the next response, not a mastery "
            "decision, and no classroom trial was run. The primary contrast is one dataset, ASSISTments "
            "2012, with a Limited sparse group. Four unique partitions describe variability. They are "
            "not four independent population samples, and fold 2 is the same learners as fold 3. "
            "ΔECE* is a bias reference. The matched interval covers fold 0 only. T-KT masked changed "
            "the mask, the checkpoint, and the window together. The archived full-history pairs are "
            "not this protocol, and their weights were not recovered. Junyi DKT is post-hoc. Junyi "
            "T-KT was not retrained with a mask. XES3G5M is a descriptive audit only. BKT was not "
            "scored. FAR was not recomputed. None of the analyses identifies a causal effect of "
            "training frequency on calibration."
        ),
        "Overall AUC does not show": (
            "Overall AUC can hide frequency-stratified calibration differences, but their size and "
            "presence depend on the evaluation protocol, the checkpoint, the sample size, the model, "
            "and the dataset. On ASSISTments 2012, under the locked validation-AUC and window-200 "
            "protocol, DKT and a causally masked Transformer show a higher sparse ECE than dense ECE. "
            "The fold-0 size-matched interval excludes 0. The four-partition bias reference ΔECE* is "
            "−0.0081 for DKT and 0.0068 for the masked Transformer, and that reference is not a "
            "significance test. Junyi Academy has no sparse group; its post-hoc ΔECE* is −0.0032. "
            "XES3G5M is a descriptive audit only, with no model-based result. The study does not "
            "recommend a new tracing model or a classroom policy. It asks evaluations that feed "
            "instructional rules to report calibration and support by training frequency, and to "
            "keep the bias reference separate from a size-matched interval."
        ),
        "Table 2. Training settings": (
            "Table 2. Configuration of the scored neural models. Primary rows are ASSISTments DKT and "
            "T-KT masked under P0-BV200-15EW. simpleKT is sensitivity. No missing setting was filled in. "
            "The base-rate reference is not a neural model and is omitted here."
        ),
        "Table A2. Final-checkpoint": (
            "Table A2. ASSISTments DKT sensitivity grid. Each main cell is ΔECE = ECE sparse − ECE dense. "
            "best/200 is the primary protocol. ΔECE* in the extra column is the bias reference for that "
            "primary cell, not a confidence interval. Fold 2 and fold 3 share learners. No cell is missing. "
            "This table does not attribute the final/full versus best/200 gap to one factor."
        ),
        "Table A1. Final-checkpoint": (
            "Table A1. Archived final-checkpoint, full-history Brier decomposition. Not a result under "
            "protocol P0-BV200-15EW. Not used as a current finding."
        ),
        "Table A3. Threshold": (
            "Table A3. Archived threshold probe. Not evaluated under protocol P0-BV200-15EW. Not a current finding."
        ),
        "Table A4. ΔFAR": (
            "Table A4. Archived threshold probe across partitions. Not evaluated under protocol "
            "P0-BV200-15EW. Not a current finding."
        ),
    }


def table2_rows() -> list[list[str]]:
    return [
        ["Setting", "DKT", "T-KT masked", "simpleKT"],
        ["Mask and input", "LSTM; KC–response token; pad 0", "Causal mask; pad id 2n; same tokens", "pyKT causal attention; items and KCs"],
        ["Training", "ASSISTments; ≤ 50 epochs; patience 8", "ASSISTments; ≤ 50 epochs; patience 8", "ASSISTments; pyKT; sensitivity"],
        ["Checkpoint rule", "Maximum validation AUC", "Maximum validation AUC", "Maximum validation AUC"],
        ["Test history", "Non-overlapping windows ≤ 200", "Non-overlapping windows ≤ 200", "Windows ≤ 200"],
        ["Splits", "Learner-disjoint; folds 0–4; fold 2 = fold 3", "Same partitions", "Same partitions"],
        ["Provenance", "Code 4ff6683; prediction exports", "Code 4ff6683; mask tests passed", "Post-hoc; not a primary model"],
        ["Role", "Primary", "Primary", "Sensitivity"],
        ["Protocol", "P0-BV200-15EW", "P0-BV200-15EW", "Same scoring rules; post-hoc"],
        ["Not in this table", "Unmasked T-KT is invalid", "Junyi T-KT was not trained", "XES models were not trained"],
    ]


def table4_rows(dkt, tkt, jun, skt) -> list[list[str]]:
    def line(dataset, model, stats, protocol, role):
        auc, acc, n, auc_sd, acc_sd, n_sd = stats
        return [
            dataset,
            f"{model} ({role})",
            f"{auc:.4f} ± {auc_sd:.4f}",
            f"{acc:.4f} ± {acc_sd:.4f}",
            f"{n:.1f}",
            protocol,
        ]
    rows = [[
        "Dataset", "Model", "AUC ± SD", "ACC ± SD", "N", "Protocol ID",
    ]]
    rows.append(line("ASSISTments 2012", "DKT", dkt, PROTOCOL, "primary"))
    rows.append(line("ASSISTments 2012", "T-KT masked", tkt, PROTOCOL, "primary"))
    rows.append(line("Junyi Academy", "DKT", jun, PROTOCOL, "post-hoc"))
    rows.append(line("ASSISTments 2012", "simpleKT", skt, PROTOCOL, "sensitivity"))
    rows.append(["XES3G5M", "Any model", "Not evaluated", "Not evaluated", "Not evaluated", "NONE"])
    while len(rows) < 8:
        rows.append([""] * 6)
    return rows


def table5_rows() -> list[list[str]]:
    return [
        ["Dataset", "Model", "Group (support)", "N", "ECE", "ΔECE", "ΔECE*", "Matched gap", "95% CI (fold 0 gap)"],
        ["ASSISTments", "DKT", "sparse (Limited)", "397.75", "0.0982 ± 0.0093", "0.0893 ± 0.0091", "−0.0081 ± 0.0122", "0.0400 ± 0.0107", "0.0170 to 0.0821"],
        ["ASSISTments", "DKT", "dense (Reliable)", "517329.5", "0.0089 ± 0.0013", "same contrast", "same reference", "same gap", "same interval"],
        ["ASSISTments", "T-KT masked", "sparse (Limited)", "397.75", "0.1199 ± 0.0247", "0.1041 ± 0.0215", "0.0068 ± 0.0207", "0.0581 ± 0.0230", "0.0233 to 0.0878"],
        ["ASSISTments", "T-KT masked", "dense (Reliable)", "517329.5", "0.0158 ± 0.0032", "same contrast", "same reference", "same gap", "same interval"],
        ["Junyi (post-hoc)", "DKT", "medium (Reliable)", "3676.75", "0.0345 ± 0.0080", "0.0302 ± 0.0069", "−0.0032 ± 0.0067", "0.0115 ± 0.0073", "0.0010 to 0.0434"],
        ["Junyi (post-hoc)", "DKT", "dense (Reliable)", "3200666.3", "0.0043 ± 0.0021", "same contrast", "same reference", "same gap", "same interval"],
    ]


def table6_rows() -> list[list[str]]:
    header = ["Question", "ASSISTments 2012", "Junyi Academy", "XES3G5M"]
    body = [
        ["Sparse group present?", "Yes", "No", "KC-level tail only; not a model contrast"],
        ["L1–L7", "PASS for the local models", "PASS for the local models", "Not a license for model scores"],
        ["L8", "Not applicable (one KC per row)", "Not applicable (one KC per row)", "FAIL"],
        ["Eligible model contrast?", "Yes: DKT and T-KT masked", "Post-hoc medium versus dense only", "No"],
        ["Direction", "Matched gap positive; ΔECE* mixed", "Matched gap positive; ΔECE* −0.0032", "Not evaluated"],
        ["Uncertainty", "Fold-0 matched CI; four-partition SD is descriptive", "Fold-0 matched CI; post-hoc", "Not evaluated"],
        ["Protocol", "P0-BV200-15EW primary", "Same rules, not pre-specified", "Descriptive audit only"],
        ["Primary claim?", "Yes", "No", "No"],
    ]
    rows = [header] + body
    while len(rows) < 15:
        rows.append(["", "", "", ""])
    return rows


if __name__ == "__main__":
    main()
