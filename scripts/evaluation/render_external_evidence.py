"""Render five publication figures from authenticated, public aggregates."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from external_evidence_tables import ENDPOINTS, MODELS, calculate, verified_sources
from matplotlib.patches import Rectangle

STEMS = (
    "figure_01_global_comparison", "figure_02_classwise_metrics", "figure_03_sensitivity_ppv",
    "figure_04_confusion_matrices", "figure_05_observed_precision_recall",
)
COLORS = {"P6": "#5e6874", "P8": "#32708b", "candidate": "#9f4836"}
NAMES = {"P6": "Published P6", "P8": "Published P8", "candidate": "Adapted model"}


def setup(fig, title, footer):
    fig.suptitle(title, x=.06, y=.98, ha="left", fontsize=16, weight="bold")
    fig.text(.06, .025, footer, ha="left", fontsize=8, color="#414950")


def tidy(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dce1e4", linewidth=.65)
    ax.set_axisbelow(True)


def plots(src):
    detail, macro, _, pr = calculate(src)
    by = {(r["model"], r["endpoint"]): r for r in detail}
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 4), layout="constrained")
    fig.get_layout_engine().set(rect=(0.04, .075, .92, .81))
    setup(fig, "Matched performance on reserved CODE-15%", "Same 4,921 ECGs / 3,891 patients; five endpoints. Whiskers: patient-bootstrap 95% CI for F1 only.")
    for ax, key, title in zip(axes, ("macro_f1", "macro_auroc", "macro_auprc"), ("Macro-F1", "Macro-AUROC", "Macro-AUPRC"), strict=True):
        tidy(ax)
        for i, r in enumerate(macro):
            value = r[key]
            ax.bar(i, value, color=COLORS[r["model"]], width=.65)
            above = value
            if key == "macro_f1":
                lo, hi = float(r["macro_f1_ci_low"]), float(r["macro_f1_ci_high"])
                ax.errorbar(i, value, [[value-lo], [hi-value]], fmt="none", color="#24282c", capsize=4, lw=1)
                above = hi
            ax.text(i, above+.025, f"{value:.3f}", ha="center", fontsize=9)
        ax.set(xticks=range(3), xticklabels=("P6", "P8", "Adapted"), ylim=(0, 1.09), title=title, ylabel="Score (0 to 1)")
        ax.set_yticks([0, .25, .5, .75, 1])
    yield fig
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), layout="constrained")
    fig.get_layout_engine().set(rect=(.04, .13, .92, .75))
    setup(fig, "Performance by ECG endpoint", "F1 uses each system's locked decision cut. AUROC and AUPRC summarize score ranking.")
    for ax, key, title in zip(axes, ("f1", "auroc", "auprc"), ("F1", "AUROC", "AUPRC (average precision)"), strict=True):
        tidy(ax)
        for i, m in enumerate(MODELS):
            ax.bar([j + (i-1)*.24 for j in range(5)], [by[m,e][key] for e in ENDPOINTS],
                   width=.22, color=COLORS[m], label=NAMES[m])
        ax.set(xticks=range(5), xticklabels=ENDPOINTS, ylim=(0, 1.03), title=title, ylabel="Score (0 to 1)")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(.5, .067), ncol=3, frameon=False)
    yield fig
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout="constrained")
    fig.get_layout_engine().set(rect=(.04, .13, .92, .74))
    setup(fig, "Sensitivity and positive predictive value", "Patient-bootstrap 95% intervals. Thresholds differ by system; these are operating-point measures.")
    for ax, key, title in zip(axes, ("sensitivity", "ppv"), ("Sensitivity", "Positive predictive value (PPV)"), strict=True):
        tidy(ax)
        for i, m in enumerate(MODELS):
            rr = [by[m, e] for e in ENDPOINTS]
            vals = [r[key] for r in rr]
            lo = [float(r[f"{key}_ci_low"]) for r in rr]
            hi = [float(r[f"{key}_ci_high"]) for r in rr]
            ax.vlines([j+(i-1)*.23 for j in range(5)], lo, hi, color=COLORS[m], linewidth=1.5)
            ax.plot([j+(i-1)*.23 for j in range(5)], vals, "o", ms=5, color=COLORS[m], label=NAMES[m])
        ax.set(xticks=range(5), xticklabels=ENDPOINTS, ylim=(0, 1.04), title=title, ylabel="Proportion")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(.5, .067), ncol=3, frameon=False)
    yield fig
    fig, axes = plt.subplots(1, 5, figsize=(12.6, 3.4), layout="constrained")
    fig.get_layout_engine().set(rect=(.035, .15, .93, .69))
    setup(fig, "Binary confusion matrices: adapted model", "Raw counts per endpoint. Rows are publisher reference labels; columns are model calls.")
    for ax, endpoint in zip(axes, ENDPOINTS, strict=True):
        r = by["candidate", endpoint]
        matrix = [[int(r["tn"]), int(r["fp"])], [int(r["fn"]), int(r["tp"])]]
        palette = matplotlib.colormaps["Blues"]
        for i, row in enumerate(matrix):
            for j, v in enumerate(row):
                tag = (("TN", "FP"), ("FN", "TP"))[i][j]
                ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, facecolor=palette(v / sum(row))))
                ax.text(j, i, f"{tag}\n{v:,}", ha="center", va="center", weight="bold",
                        color="white" if v / sum(row) > .62 else "#152532")
        ax.set(xticks=[0,1], yticks=[0,1], xticklabels=("Negative", "Positive"), yticklabels=("Negative", "Positive"),
               xlabel="Predicted", title=endpoint, xlim=(-.5, 1.5), ylim=(1.5, -.5), aspect="equal")
        if endpoint == ENDPOINTS[0]:
            ax.set_ylabel("Reference")
    yield fig
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.8), layout="constrained")
    fig.get_layout_engine().set(rect=(.04, .10, .92, .80))
    setup(fig, "Observed Precision–Recall operating points", "Actual published 0.01 threshold grid; undefined precision omitted. No interpolation. ROC points unavailable.")
    for ax, endpoint in zip(list(axes.flat)[:5], ENDPOINTS, strict=True):
        tidy(ax)
        for m in MODELS:
            rr = [r for r in pr if r["model"] == m and r["endpoint"] == endpoint and r["precision"] != ""]
            ax.scatter([float(r["recall"]) for r in rr], [float(r["precision"]) for r in rr],
                       s=9, alpha=.7, color=COLORS[m], label=NAMES[m])
        ax.set(xlim=(-.02, 1.02), ylim=(-.02, 1.02), xlabel="Recall", ylabel="Precision (PPV)", title=endpoint)
    axes.flat[5].axis("off")
    axes.flat[5].legend(*axes.flat[0].get_legend_handles_labels(), loc="center", frameon=False)
    yield fig


def render(src, output):
    output.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "font.size": 9, "axes.labelsize": 9,
                                "axes.titlesize": 11, "svg.hashsalt": "titan-external-evidence-v1",
                                "pdf.fonttype": 42}):
        for stem, fig in zip(STEMS, plots(src), strict=True):
            svg = output / f"{stem}.svg"
            fig.savefig(svg, metadata={"Date": None})
            svg.write_bytes(b"\n".join(line.rstrip() for line in svg.read_bytes().splitlines()) + b"\n")
            fig.savefig(output / f"{stem}.pdf", metadata={"CreationDate": datetime(2026, 11, 13, tzinfo=timezone.utc)})
            fig.savefig(output / f"{stem}.png", dpi=300)
            plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    render(verified_sources(Path(__file__).resolve().parents[2]), args.output)
