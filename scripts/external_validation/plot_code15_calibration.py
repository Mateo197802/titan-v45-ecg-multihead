"""Render aggregate CODE calibration points; no private inputs are required."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ENDPOINTS = ("AFIB", "SB", "STACH", "RBBB", "1AVB")
MODELS = (("published", "Published", "#24577e", "o"),
          ("anchored_linear_residual_v1", "Frozen linear", "#9d4a18", "s"))


def render(source, destination):
    with source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    scope = {row["scope"] for row in rows}
    if scope != {"FIRST_ARCHIVE_ONLY_NO_PROMOTION"}:
        raise ValueError("this figure is scoped to the partial first-archive result")
    fig, axes = plt.subplots(2, 5, figsize=(13, 6), sharex=True, sharey=True)
    for i, profile in enumerate(("P6", "P8")):
        for j, endpoint in enumerate(ENDPOINTS):
            ax = axes[i, j]
            ax.plot([0, 1], [0, 1], color="#838b94", linestyle="--", linewidth=1)
            for model, name, color, marker in MODELS:
                values = sorted(
                    (row for row in rows if row["profile"] == profile and row["endpoint"] == endpoint
                     and row["model"] == model and int(row["n_ecg"]) > 0),
                    key=lambda row: int(row["bin"]),
                )
                ax.plot([float(row["mean_score"]) for row in values],
                        [float(row["observed_fraction"]) for row in values],
                        color=color, marker=marker, linewidth=1.3, markersize=3.2, label=name)
            ax.set_title(f"{profile} {endpoint}", fontsize=10)
            ax.set(xlim=(0, 1), ylim=(0, 1), xticks=(0, .5, 1), yticks=(0, .5, 1))
            ax.grid(color="#e9ecef", linewidth=.6)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .065), ncol=2, frameon=False)
    fig.supxlabel("Mean predicted score in nonempty bin", y=.025, fontsize=10)
    fig.supylabel("Observed benchmark positive fraction", x=.025, fontsize=10)
    fig.suptitle("CODE-15% first archive: calibration with frozen scoring", y=.98, fontsize=15)
    fig.text(.5, .925, "1,442 ECGs / 1,403 patients | nominal duration not certified | not a promotion result",
             ha="center", fontsize=10)
    fig.subplots_adjust(left=.08, right=.98, top=.84, bottom=.17, hspace=.34, wspace=.19)
    fig.savefig(destination, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    render(args.source, args.destination)
