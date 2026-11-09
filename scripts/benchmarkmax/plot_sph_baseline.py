"""Render exploratory binned curves from the published aggregate-only SPH audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = {"P6:AFIB": "#007d78", "P8:PAC": "#ce5b42", "P4:ASMI": "#967000",
          "P4:LVH": "#53528d", "P4:IMI": "#42749a"}


def save(fig, output, stem):
    paths = []
    for extension in ("png", "pdf"):
        path = output / f"{stem}.{extension}"
        options = {"dpi": 300} if extension == "png" else {
            "metadata": {"Creator": "TITAN BenchmarkMax", "CreationDate": None, "ModDate": None}
        }
        fig.savefig(path, **options)
        paths.append(path.name)
    plt.close(fig)
    return paths


def render(report, output):
    if report.get("schema") != "TITAN_V46_SPH_OBSERVED_BASELINE_DIAGNOSTIC_V1":
        raise ValueError("expected aggregate SPH baseline diagnostic")
    if set(report["endpoints"]) != set(COLORS):
        raise ValueError("unexpected endpoint set")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for kind in ("roc", "pr", "calibration"):
        fig, axis = plt.subplots(figsize=(10, 6.5), layout="constrained")
        for name, endpoint in report["endpoints"].items():
            color = COLORS[name]
            if kind == "calibration":
                bins = [b for b in endpoint["score_bins_uniform_20"] if b["mean_score"] is not None]
                axis.plot([b["mean_score"] for b in bins], [b["statement_fraction"] for b in bins],
                          marker=".", linewidth=1.4, color=color, label=name)
            else:
                curve = endpoint["exploratory_binned_threshold_curve"]
                x = [row["false_positive_rate" if kind == "roc" else "sensitivity"] for row in curve]
                y = [row["sensitivity" if kind == "roc" else "precision"] for row in curve]
                label = (f"{name} (AUROC {endpoint['frozen_auroc']:.3f})" if kind == "roc" else
                         f"{name} (AP {endpoint['frozen_average_precision']:.3f}; "
                         f"baseline {endpoint['statement_prevalence']:.3f})")
                axis.plot(x, y, linewidth=1.5, color=color, label=label)
        if kind in {"roc", "calibration"}:
            axis.plot([0, 1], [0, 1], "--", color="#777777", linewidth=1)
        titles = {"roc": "Binned ROC diagnostic", "pr": "Binned precision-recall diagnostic",
                  "calibration": "Binned statement calibration"}
        labels = {"roc": ("False-positive rate", "Sensitivity"),
                  "pr": ("Sensitivity", "Precision"),
                  "calibration": ("Mean score in bin", "Fraction with coded statement")}
        axis.set(title=titles[kind], ylabel=labels[kind][1], xlim=(0, 1), ylim=(0, 1))
        axis.set_xlabel(labels[kind][0] + "\nObserved SPH statements; 20-bin curves are descriptive, not threshold selection.", fontsize=8)
        axis.grid(alpha=0.2)
        axis.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
        files.extend(save(fig, output, f"sph_baseline_{kind}"))
    fig, axes = plt.subplots(5, 1, figsize=(8, 11), sharex=True, layout="constrained")
    for axis, (name, endpoint) in zip(axes, report["endpoints"].items(), strict=True):
        bins = endpoint["score_bins_uniform_20"]
        x = (np.arange(len(bins)) + 0.5) / len(bins)
        for group, label, color in (("positive", "Statement recorded", COLORS[name]),
                                     ("negative", "Statement not recorded", "#5b6068")):
            values = np.array([item[group] for item in bins], dtype=float)
            total = values.sum()
            axis.step(x, values / total if total else values, where="mid", label=label, color=color)
        axis.set_ylabel(name)
        axis.grid(alpha=0.15)
    axes[0].legend(frameon=False, fontsize=8, loc="upper center", ncol=2)
    axes[-1].set_xlabel("Frozen model score (20 bins)")
    fig.suptitle("Within-reference score distributions")
    fig.supylabel("Fraction within reference group")
    files.extend(save(fig, output, "sph_baseline_score_distributions"))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps({"files": render(json.loads(args.input.read_text(encoding="utf-8")), args.output_dir)}))


if __name__ == "__main__":
    main()
