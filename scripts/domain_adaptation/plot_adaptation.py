"""Render study plots from public aggregate CSVs only."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib
from verify_adaptation_delivery import read_csv, verify

matplotlib.use("Agg")
from matplotlib import pyplot as plt

DISPLAY = {"frozen_backbone_mlp": "Frozen", "partial_transformer_mlp": "Transformer",
           "partial_transformer_resnet_mlp": "Transformer + ResNet", "masked_mimic_partial": "MIMIC SSL + Transformer",
           "multisource_groupdro": "Multisource GroupDRO", "full_regularized": "Full regularized"}
ENDPOINTS = ("AFIB", "SB", "STACH", "RBBB", "1AVB")


def learning(evidence, output):
    rows = [r for r in read_csv(evidence / "FINETUNING_LEARNING_CURVES.csv") if r["mode"] in DISPLAY]
    runs = defaultdict(list)
    for row in rows:
        runs[row["mode"], row["normalization"], row["seed"]].append(row)
    names = sorted({key[:2] for key in runs})
    colors = dict(zip(names, plt.get_cmap("tab10").colors, strict=False))
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.4), sharey=True)
    for ax, metric, title in zip(axes, ("validation_macro_ap", "validation_macro_f1_at_half"),
                                 ("Macro-AUPRC", "Macro-F1 at threshold 0.5"), strict=True):
        seen = set()
        for key, subset in sorted(runs.items()):
            mode, normalization, seed = key
            variant = key[:2]
            title_suffix = " (robust)" if normalization == "robust_shared_gain" else ""
            label = DISPLAY[mode] + title_suffix if variant not in seen else "_nolegend_"
            seen.add(variant)
            ax.plot([int(row["epoch"]) for row in subset], [float(row[metric]) for row in subset],
                    "o-", ms=3, lw=1.5 if seed == "20261112" else 1, alpha=1 if seed == "20261112" else .5,
                    color=colors[variant], label=label)
        ax.set(xlabel="Epoch", title=title, ylim=(0, 1))
        ax.grid(axis="y", alpha=.22)
    fig.suptitle("Duration-aware TITAN: CODE development validation")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .025), ncol=3, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, .16, 1, .94))
    fig.savefig(output / "CODE_VALIDATION_LEARNING_CURVES.png", dpi=180)
    plt.close(fig)


def holdout(evidence, output):
    models = {"P6": ("Published P6", "#267393"), "P8": ("Published P8", "#4a5b43"),
              "candidate": ("Selected adaptation", "#b14131")}
    fig, axes = plt.subplots(2, 5, figsize=(13, 5.6), sharex="row", sharey="row")
    pr, calibration = (read_csv(evidence / name) for name in ("PRECISION_RECALL_CURVES.csv", "CALIBRATION_CURVES.csv"))
    for i, endpoint in enumerate(ENDPOINTS):
        axes[0, i].set_title(endpoint)
        axes[1, i].plot((0, 1), (0, 1), "--", color=".65", lw=1)
        for model, (name, color) in models.items():
            points = [r for r in pr if r["endpoint"] == endpoint and r["model"] == model and r["precision"] and r["recall"]]
            axes[0, i].plot([float(r["recall"]) for r in points], [float(r["precision"]) for r in points],
                            color=color, label=name, lw=1.5)
            bins = [r for r in calibration if r["endpoint"] == endpoint and r["model"] == model and r["mean_score"]]
            axes[1, i].plot([float(r["mean_score"]) for r in bins], [float(r["observed_fraction"]) for r in bins],
                            "o-", color=color, ms=3, lw=1.1)
        axes[0, i].set(xlim=(0, 1), ylim=(0, 1), xlabel="Recall")
        axes[1, i].set(xlim=(0, 1), ylim=(0, 1), xlabel="Mean score")
        for ax in axes[:, i]:
            ax.grid(alpha=.2)
    axes[0, 0].set_ylabel("Precision")
    axes[1, 0].set_ylabel("Observed fraction")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc="lower center", frameon=False, fontsize=9)
    fig.suptitle("Reserved evaluation within CODE; publisher flags, not hospital confirmation")
    fig.tight_layout(rect=(0, .07, 1, .94))
    fig.savefig(output / "CODE_HOLDOUT_PRECISION_AND_CALIBRATION.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = verify(args.evidence)
    args.output.mkdir(exist_ok=True)
    learning(args.evidence, args.output)
    if manifest["within_code_results_present"]:
        holdout(args.evidence, args.output)
