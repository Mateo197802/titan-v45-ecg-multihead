"""Render paired patient-cluster bootstrap deltas from the B1 aggregate receipt."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

METRICS = (
    ("brier", "Brier score", "#1f6d88"),
    ("ece", "10-bin ECE", "#c96a2b"),
)
ENDPOINT_ORDER = ("P4:ASMI", "P4:IMI", "P4:LVH", "P6:PVC", "P6:RBBB", "P8:PAC")


def render_figure(report_path: Path, output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import MaxNLocator

    report = json.loads(report_path.read_text(encoding="utf-8"))
    endpoints = report.get("endpoints")
    if not isinstance(endpoints, dict) or not endpoints:
        raise ValueError("B1 report must contain aggregated endpoints")
    ordered = [key for key in ENDPOINT_ORDER if key in endpoints]
    ordered.extend(sorted(set(endpoints) - set(ordered)))
    labels = []
    for key in ordered:
        support = endpoints[key]["source_support"]
        labels.append(
            f"{key.replace(':', ' ')}  (+{support['positive_records']:,}; "
            f"{support['patients_with_positive_records']:,} patients)"
        )

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    figure, axes = plt.subplots(1, 2, figsize=(12.5, 5.8), sharey=True)
    y = np.arange(len(ordered))
    for axis, (metric, title, color) in zip(axes, METRICS, strict=True):
        deltas = []
        lower = []
        upper = []
        for key in ordered:
            interval = endpoints[key]["paired_patient_cluster_bootstrap_delta"]["intervals"][metric]
            delta = interval["point_difference_calibrated_minus_raw"]
            ci = interval["ci95"]
            if delta is None or ci is None or not all(math.isfinite(value) for value in (delta, *ci)):
                raise ValueError(f"{key} {metric} requires finite paired estimates and intervals")
            deltas.append(float(delta))
            lower.append(float(ci[0]))
            upper.append(float(ci[1]))

        delta_array = np.asarray(deltas)
        axis.errorbar(
            delta_array,
            y,
            xerr=np.asarray([delta_array - lower, upper - delta_array]),
            fmt="o",
            markersize=5,
            color=color,
            ecolor=color,
            elinewidth=1.3,
            capsize=3,
            markeredgecolor="#24323a",
            markeredgewidth=0.6,
        )
        axis.axvline(0, color="#49545a", linewidth=1.0)
        min_bound = min(lower)
        max_bound = max(upper)
        padding = max((max_bound - min_bound) * 0.08, 0.01)
        axis.set_xlim(min_bound - padding, max(0.015, max_bound + padding))
        axis.set_title(title, loc="left", weight="bold")
        axis.set_xlabel("Calibrated minus raw; lower is better")
        axis.xaxis.set_major_locator(MaxNLocator(5))
        axis.grid(axis="x", color="#d7dde0", linewidth=0.7, alpha=0.8)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#647179")

    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[1].tick_params(labelleft=False)
    figure.suptitle("SPH calibration: paired change in probability error", x=0.23, ha="left", fontsize=14, weight="bold")
    figure.text(
        0.23,
        0.905,
        "Previously observed SPH; exploratory development only. Points and 95% patient-cluster CIs are conditional on fitted fold calibrators.",
        fontsize=9,
        color="#34434a",
    )
    figure.text(
        0.23,
        0.045,
        "Negative values indicate lower error than raw V4.5 scores. CIs do not refit calibrators; this is not independent or clinical validation.",
        fontsize=8.5,
        color="#34434a",
    )
    figure.subplots_adjust(left=0.23, right=0.98, top=0.84, bottom=0.17, wspace=0.23)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200, facecolor="white")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render_figure(args.report, args.output)
    print(f"Rendered B1 figure: {args.output}")


if __name__ == "__main__":
    main()
